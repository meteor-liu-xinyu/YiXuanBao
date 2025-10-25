from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import UserSerializer, UserUpdateSerializer
from .models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from django.conf import settings

# 以下用于服务器端图片处理（可选）
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io

from django.utils import timezone

# History APIs for authenticated users:
# GET  /api/accounts/history/            -> list user's history
# POST /api/accounts/history/            -> push new history entry (entry in request.data)
# DELETE /api/accounts/history/          -> clear all history
# DELETE /api/accounts/history/<int:pk>/ -> delete single entry by id
#
# Entry format expected: dict with optional keys id, created_at, summary, payload, result
# Server will ensure id and created_at if missing. Keep history list capped (e.g., 200 items).

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFTokenView(APIView):
    """
    GET /api/accounts/csrf/  -> 在响应中设置 csrftoken cookie，并返回 token 字符串（可由前端读取）
    用途：前端在 App 启动时调用一次，确保浏览器有 csrftoken cookie，后续 POST/PUT/PATCH/DELETE 可发送 X-CSRFToken。
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        token = get_token(request)  # 也会在 response 中确保 cookie 被设置（由 ensure_csrf_cookie）
        return Response({'csrftoken': token})

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'detail': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'detail': 'username exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password)
        return Response({'detail': 'created'}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)  # 创建 Session，浏览器会保存 sessionid cookie
        return Response({'detail': 'logged in', 'username': user.username})


class LogoutView(APIView):
    """
    退出登录：处理 session logout，并在响应中删除 session/csrf cookie。
    注意：如果你使用 session authentication，前端必须带上 csrftoken 与 cookie（withCredentials）。
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # 注：SessionAuthentication 会进行 CSRF 校验，对于前端未正确发送 csrftoken 会抛 403。
        # 在这里假设认证/CSRF 已由 DRF 的默认机制处理（推荐）
        logout(request)  # 清除服务器端 session
        res = Response({'detail': 'logged out'}, status=status.HTTP_200_OK)
        # 显式删除 session cookie
        try:
            session_cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
            res.delete_cookie(session_cookie_name, path='/', domain=None)
        except Exception:
            pass
        # 删除 csrf cookie（如果你使用 csrftoken cookie）
        try:
            csrf_cookie_name = getattr(settings, 'CSRF_COOKIE_NAME', 'csrftoken')
            res.delete_cookie(csrf_cookie_name, path='/', domain=None)
        except Exception:
            pass
        return res


class UserInfoView(APIView):
    """
    GET: 返回当前登录用户信息（使用 UserSerializer）
    PATCH: 使用 UserUpdateSerializer 对当前登录用户进行部分更新（支持 multipart/form-data 上传 avatar）。
    支持：
      - 通过表单上传文件 avatar（multipart/form-data）
      - 通过 avatar=null 或 avatar='' 删除头像（前端可按此规则发送）
    注意：
      - 仅当请求体中明确包含 avatar 字段且其值为空('', 'null', 'None', None) 时才视作删除头像请求，
        如果请求体完全没有 avatar 字段则不会删除原有头像。
      - 上传文件优先于删除指示（如果同时上传文件，则以上传文件为准）。
    """
    permission_classes = [permissions.IsAuthenticated]
    # 支持 JSON 与表单/文件上传
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        user = request.user

        # 判定前端是否明确请求删除头像：只有当请求体包含 avatar 字段且其值为空时才删除
        remove_avatar = False
        if 'avatar' in request.data and request.data.get('avatar') in ('', 'null', 'None', None):
            remove_avatar = True

        with transaction.atomic():
            # 先处理上传文件（若有上传文件，优先使用上传文件）
            upload_file = request.FILES.get('avatar')
            new_avatar_file = None

            if upload_file:
                try:
                    # 使用 Pillow 对图片做基本处理并转换为 JPEG（如需保留原格式可调整）
                    img = Image.open(upload_file)
                    img = img.convert('RGB')
                    # 缩放到最大 300x300（按需调整）
                    img.thumbnail((300, 300), Image.ANTIALIAS)

                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    buffer.seek(0)
                    size = buffer.getbuffer().nbytes

                    new_avatar_file = InMemoryUploadedFile(
                        buffer,               # file
                        'avatar',             # field_name
                        upload_file.name or 'avatar.jpg',  # name
                        'image/jpeg',         # content_type
                        size,                 # size
                        None                  # charset
                    )
                except Exception:
                    # 如果压缩/转换失败，回退使用原始上传文件（确保文件指针回到开头）
                    try:
                        upload_file.seek(0)
                    except Exception:
                        pass
                    new_avatar_file = upload_file

            # 使用 serializer 验证并保存其它字段（partial update）
            serializer = UserUpdateSerializer(instance=user, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)

            # 如果上传了新头像文件，则以上传文件为准覆盖保存
            if new_avatar_file:
                serializer.save(avatar=new_avatar_file)
            else:
                # 先保存其它字段
                serializer.save()
                # 如果前端明确请求删除头像（并且没有上传新文件），则删除存储的头像并清空字段
                if remove_avatar:
                    try:
                        if getattr(user, 'avatar', None):
                            user.avatar.delete(save=False)
                        user.avatar = None
                        user.save()
                    except Exception:
                        # 记录或忽略删除失败（按需改为 raise）
                        pass

            # 确保从数据库刷新实例后序列化返回最新数据
            user.refresh_from_db()
            out = UserSerializer(user, context={'request': request}).data
            return Response(out, status=status.HTTP_200_OK)


class UserHistoryView(APIView):
    """
    用户历史记录接口（基于登录用户）：
    GET  /api/accounts/history/            -> 返回列表
    POST /api/accounts/history/            -> 新增一条（body: entry dict）
    DELETE /api/accounts/history/          -> 清空全部
    DELETE /api/accounts/history/<int:pk>/ -> 删除单条
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    MAX_HISTORY = 200

    def get(self, request, *args, **kwargs):
        user = request.user
        hist = getattr(user, 'history', None) or []
        return Response({'history': hist})

    def post(self, request, *args, **kwargs):
        user = request.user
        entry = request.data or {}
        try:
            # ensure id + created_at
            eid = entry.get('id') or int(timezone.now().timestamp() * 1000)
            entry['id'] = eid
            entry['created_at'] = entry.get('created_at') or timezone.now().isoformat()
        except Exception:
            entry['id'] = int(timezone.now().timestamp() * 1000)
            entry['created_at'] = timezone.now().isoformat()

        hist = getattr(user, 'history', None) or []
        # push to front, dedupe by id
        new_hist = [entry] + [h for h in hist if h.get('id') != entry['id']]
        # cap
        new_hist = new_hist[: self.MAX_HISTORY]
        user.history = new_hist
        user.save(update_fields=['history'])
        return Response({'history': new_hist}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None, *args, **kwargs):
        user = request.user
        # if pk provided in kwargs -> delete single
        if pk is not None:
            try:
                pid = int(pk)
            except Exception:
                return Response({'detail': 'invalid id'}, status=status.HTTP_400_BAD_REQUEST)
            hist = getattr(user, 'history', None) or []
            remaining = [h for h in hist if h.get('id') != pid]
            user.history = remaining
            user.save(update_fields=['history'])
            return Response({'history': remaining}, status=status.HTTP_200_OK)
        # else clear all
        user.history = []
        user.save(update_fields=['history'])
        return Response({'history': []}, status=status.HTTP_200_OK)