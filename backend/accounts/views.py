from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserSerializer, UserUpdateSerializer
from .models import User

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
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logout(request)
        return Response({'detail': 'logged out'})


class UserInfoView(APIView):
    """
    GET: 返回当前登录用户信息（使用 UserSerializer）
    PATCH: 使用 UserUpdateSerializer 对当前登录用户进行部分更新（支持 multipart/form-data 上传 avatar）
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({'detail': 'unauthenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({'detail': 'unauthenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        # 使用事务保证原子性
        with transaction.atomic():
            serializer = UserUpdateSerializer(instance=user, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # 保存后返回完整的用户信息（含绝对 avatar URL）
            out = UserSerializer(user, context={'request': request}).data
            return Response(out, status=status.HTTP_200_OK)