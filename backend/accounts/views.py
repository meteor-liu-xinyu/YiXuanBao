from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserSerializer, UserUpdateSerializer
from .models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token

# 以下用于服务器端图片处理（可选）
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io

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
    """
    permission_classes = [permissions.IsAuthenticated]  # 要求登录
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        user = request.user

        # 先处理前端可能发送的“删除头像”指示
        # 前端可能发送 avatar: '', 'null', 'None' 等，统一处理为删除头像
        avatar_flag = request.data.get('avatar', None)
        remove_avatar = False
        if avatar_flag in ('', 'null', 'None') or avatar_flag is None and 'avatar' in request.data and request.data.get('avatar') in ('', 'null', 'None'):
            # 如果确实明确想删除头像（注意：如果前端完全不包含 avatar 字段，这里不应该删除）
            # 这里仅在 avatar 字段存在但为空时视为删除
            if 'avatar' in request.data and (request.data.get('avatar') in ('', 'null', 'None') or request.data.get('avatar') is None):
                remove_avatar = True

        with transaction.atomic():
            serializer = UserUpdateSerializer(instance=user, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)

            # 如果有文件上传，优先处理并可做服务器端压缩
            new_avatar_file = None
            upload_file = request.FILES.get('avatar')
            if upload_file:
                try:
                    # 使用 Pillow 压缩/缩放上传图片（生成 JPEG，quality 可调）
                    img = Image.open(upload_file)
                    img = img.convert('RGB')  # 保证为 RGB，便于保存为 JPEG
                    # 缩放到最大 800px（根据需要调整），这里示例缩放为 300x300
                    img.thumbnail((300, 300), Image.ANTIALIAS)

                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    buffer.seek(0)

                    new_file = InMemoryUploadedFile(
                        buffer, 'avatar', upload_file.name, 'image/jpeg',
                        buffer.getbuffer().nbytes, None
                    )
                    new_avatar_file = new_file
                except Exception:
                    # 如果处理失败，回退使用原始文件（让 serializer 直接保存）
                    new_avatar_file = upload_file

            # 如果前端明确要求删除头像
            if remove_avatar and not upload_file:
                # 直接清空 user.avatar 字段
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()

            # 调用 save：如果有 new_avatar_file，则通过 save(avatar=new_avatar_file) 传入
            if new_avatar_file:
                serializer.save(avatar=new_avatar_file)
            else:
                serializer.save()

            # 返回最新完整用户信息（avatar 已由 UserSerializer 返回绝对 URL）
            out = UserSerializer(user, context={'request': request}).data
            return Response(out, status=status.HTTP_200_OK)