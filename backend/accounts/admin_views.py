from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination

User = get_user_model()


class IsStaff(permissions.BasePermission):
    """仅允许 is_staff 的用户访问（管理员）。"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class AdminUserSerializer(serializers.ModelSerializer):
    """
    管理端可读写用户序列化器（更稳健）：
    - Meta.fields 只列出模型必有字段，其他可选字段通过 SerializerMethodField 提供只读显示（不会在序列化器构建时查找模型字段）
    - create/update 在写入时会使用 hasattr 检查再 setattr，避免在模型缺字段时报错
    """
    # read-only convenience fields (safe: use getattr so absent fields return None)
    nickname = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    preferred_region = serializers.SerializerMethodField()
    preferred_specialty = serializers.SerializerMethodField()
    wechat = serializers.SerializerMethodField()
    qq = serializers.SerializerMethodField()
    github = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    read_real_name = serializers.SerializerMethodField()

    # write fields (handled in create/update with hasattr checks)
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    real_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    birthday = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ'], write_only=True)

    class Meta:
        model = User
        # 只把模型通常具备的字段放在 Meta.fields，避免 DRF 在构建时报错
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'read_real_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined',
            # readonly / derived fields:
            'nickname', 'gender', 'phone', 'address',
            'preferred_region', 'preferred_specialty',
            'wechat', 'qq', 'github', 'avatar_url',
            # writable extras:
            'avatar', 'password', 'real_name', 'birthday',
        )
        read_only_fields = ('id', 'username', 'date_joined', 'read_real_name')

    # ---------- SerializerMethodField getters ----------
    def get_nickname(self, obj):
        return getattr(obj, 'nickname', None)

    def get_gender(self, obj):
        return getattr(obj, 'gender', None)

    def get_phone(self, obj):
        return getattr(obj, 'phone', None)

    def get_address(self, obj):
        return getattr(obj, 'address', None)

    def get_preferred_region(self, obj):
        return getattr(obj, 'preferred_region', None)

    def get_preferred_specialty(self, obj):
        return getattr(obj, 'preferred_specialty', None)

    def get_wechat(self, obj):
        return getattr(obj, 'wechat', None)

    def get_qq(self, obj):
        return getattr(obj, 'qq', None)

    def get_github(self, obj):
        return getattr(obj, 'github', None)

    def get_avatar_url(self, obj):
        # provide URL when possible, safe against absent avatar field
        av = getattr(obj, 'avatar', None)
        try:
            if av and hasattr(av, 'url') and av.url:
                return av.url
        except Exception:
            return None
        return None

    def get_read_real_name(self, obj):
        first = getattr(obj, 'first_name', '') or ''
        last = getattr(obj, 'last_name', '') or ''
        full = (first + ' ' + last).strip()
        return full or None

    # ---------- validation ----------
    def validate_birthday(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("生日不能晚于今天")
        return value

    # ---------- create / update ----------
    def _safe_setattr(self, instance, key, value):
        """
        在写入自定义字段前检查模型是否有该属性；如果没有则跳过。
        对 avatar 传 None 表示删除（如果模型支持 avatar 字段，则处理删除）。
        """
        if not hasattr(instance, key):
            return
        # special handling for avatar deletion
        if key == 'avatar' and value is None:
            try:
                if getattr(instance, 'avatar', None):
                    instance.avatar.delete(save=False)
            except Exception:
                pass
            setattr(instance, 'avatar', None)
            return
        setattr(instance, key, value)

    def create(self, validated_data):
        pwd = validated_data.pop('password', None)
        real_name = validated_data.pop('real_name', None)
        avatar_val = validated_data.pop('avatar', serializers.empty)
        birthday_val = validated_data.pop('birthday', serializers.empty)

        # create only with fields that actually belong to the model (ModelSerializer will do this)
        user = super().create(validated_data)

        # apply extras if model supports them
        if real_name is not None and hasattr(user, 'first_name'):
            user.first_name = real_name

        if avatar_val is not serializers.empty:
            # avatar_val may be None (delete) or a file
            if hasattr(user, 'avatar'):
                if avatar_val is None:
                    try:
                        if getattr(user, 'avatar', None):
                            user.avatar.delete(save=False)
                    except Exception:
                        pass
                    user.avatar = None
                else:
                    user.avatar = avatar_val

        if birthday_val is not serializers.empty and hasattr(user, 'birthday'):
            user.birthday = birthday_val

        if pwd:
            user.set_password(pwd)

        user.save()
        return user

    def update(self, instance, validated_data):
        pwd = validated_data.pop('password', None)
        real_name = validated_data.pop('real_name', None)
        avatar_val = validated_data.pop('avatar', serializers.empty)
        birthday_val = validated_data.pop('birthday', serializers.empty)

        # first: use super to update model fields that exist
        instance = super().update(instance, validated_data)

        # apply extras safely
        if real_name is not None and hasattr(instance, 'first_name'):
            instance.first_name = real_name

        if avatar_val is not serializers.empty:
            if hasattr(instance, 'avatar'):
                if avatar_val is None:
                    try:
                        if getattr(instance, 'avatar', None):
                            instance.avatar.delete(save=False)
                    except Exception:
                        pass
                    instance.avatar = None
                else:
                    instance.avatar = avatar_val

        if birthday_val is not serializers.empty and hasattr(instance, 'birthday'):
            instance.birthday = birthday_val

        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 500


class AdminUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStaff]
    serializer_class = AdminUserSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')
        q = self.request.query_params.get('search') or self.request.query_params.get('q')
        if q:
            q = q.strip()
            # safe filters (these fields are usually present on auth.User)
            qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q) | qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q)
        return qs


class AdminUserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStaff]
    serializer_class = AdminUserSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        instance.delete()