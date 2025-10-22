from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import FieldDoesNotExist

User = get_user_model()


class IsStaff(permissions.BasePermission):
    """仅允许 is_staff 的用户访问（管理员）。"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class AdminListSerializer(serializers.ModelSerializer):
    """
    供列表显示用的只读序列化器（安全读取模型上可能缺失的字段）。
    用于 admins 与 recent_logins 列表的返回。
    """
    nickname = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    preferred_region = serializers.SerializerMethodField()
    preferred_specialty = serializers.SerializerMethodField()
    birthday = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'nickname', 'avatar_url', 'gender', 'phone', 'birthday',
            'preferred_region', 'preferred_specialty',
            'is_staff', 'is_active', 'last_login', 'date_joined'
        )

    def get_nickname(self, obj):
        return getattr(obj, 'nickname', None)

    def get_avatar_url(self, obj):
        av = getattr(obj, 'avatar', None)
        try:
            if av and hasattr(av, 'url') and av.url:
                return av.url
        except Exception:
            return None
        return None

    def get_preferred_region(self, obj):
        return getattr(obj, 'preferred_region', None)

    def get_preferred_specialty(self, obj):
        return getattr(obj, 'preferred_specialty', None)

    def get_birthday(self, obj):
        b = getattr(obj, 'birthday', None)
        return None if not b else str(b)


class AdminUserSerializer(serializers.ModelSerializer):
    """
    管理端可读写用户序列化器（兼容模型字段差异）：
    - 明确在类中声明那些可能不存在于模型的字段，避免 DRF 将它们当作模型字段去查找。
    - 写入时使用 hasattr 检查再 setattr，且根据模型字段的 null 属性决定如何处理 None。
    - 在 create/update 之前会规范 validated_data 中的可选字段（将 None 转为 '' 若模型不允许 null）
    """
    # display helpers
    avatar_url = serializers.SerializerMethodField(read_only=True)
    read_real_name = serializers.SerializerMethodField(read_only=True)

    # explicitly declare optional fields so DRF won't try to build them from model
    # include first_name/last_name and allow null/blank so serializer accepts empty values
    first_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    nickname = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    preferred_region = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    preferred_specialty = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    wechat = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    qq = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    github = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # write fields
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    real_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    # DateField should not have allow_blank; allow_null=True is enough
    birthday = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d'])

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password',
            'first_name', 'last_name', 'real_name',
            'nickname', 'avatar', 'avatar_url', 'gender', 'phone', 'birthday',
            'address', 'preferred_region', 'preferred_specialty',
            'wechat', 'qq', 'github',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'read_real_name'
        )
        read_only_fields = ('id', 'date_joined', 'read_real_name', 'avatar_url')

    def get_avatar_url(self, obj):
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

    def _model_field_allows_null(self, model_cls, field_name):
        """
        返回模型字段是否存在且允许 null（True/False）。
        如果模型没有该字段，返回 False（外部逻辑会跳过写入）。
        """
        try:
            f = model_cls._meta.get_field(field_name)
            return bool(getattr(f, 'null', False))
        except FieldDoesNotExist:
            return False

    def _normalize_value_for_model(self, model_cls, field_name, value):
        """
        如果 value is None 且模型字段不允许 null，则将 None -> ''（空字符串）。
        否则保持原值（包括 None）。
        """
        if value is None:
            if self._model_field_allows_null(model_cls, field_name):
                return None
            return ''
        return value

    def _normalize_validated_fields(self, validated_data, fields):
        """
        在调用 super().create/update 之前规范化 validated_data 中的字段：
        - 如果某字段存在于 validated_data 并且其值为 None，则根据模型可空性把它转换为 ''（若模型不允许 null）或保留 None（若允许）。
        这样避免 super().update 将 None 直接写入导致 IntegrityError。
        """
        for f in fields:
            if f in validated_data and validated_data[f] is None:
                validated_data[f] = self._normalize_value_for_model(User, f, None)

    def create(self, validated_data):
        # Normalize validated_data for optional fields before create
        optional_fields = ('first_name', 'last_name', 'nickname', 'gender', 'phone', 'address',
                           'preferred_region', 'preferred_specialty', 'wechat', 'qq', 'github')
        self._normalize_validated_fields(validated_data, optional_fields)

        pwd = validated_data.pop('password', None)
        real_name = validated_data.pop('real_name', None)
        avatar_val = validated_data.pop('avatar', serializers.empty)
        birthday_val = validated_data.pop('birthday', serializers.empty)

        # ModelSerializer.create will handle model fields; declared serializer-only fields are ignored
        user = super().create(validated_data)

        # apply extras if model has attributes
        if real_name is not None and hasattr(user, 'first_name'):
            user.first_name = real_name

        if avatar_val is not serializers.empty and hasattr(user, 'avatar'):
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

        # set declared optional fields if model supports them; use normalization for None
        for opt in ('first_name', 'last_name', 'nickname', 'gender', 'phone', 'address',
                    'preferred_region', 'preferred_specialty', 'wechat', 'qq', 'github'):
            if opt in self.initial_data and hasattr(user, opt):
                raw = self.initial_data.get(opt)
                val = self._normalize_value_for_model(User, opt, raw)
                setattr(user, opt, val)

        # set password if provided
        if pwd:
            user.set_password(pwd)

        user.save()
        return user

    def update(self, instance, validated_data):
        # Normalize validated_data for optional fields before update
        optional_fields = ('first_name', 'last_name', 'nickname', 'gender', 'phone', 'address',
                           'preferred_region', 'preferred_specialty', 'wechat', 'qq', 'github')
        self._normalize_validated_fields(validated_data, optional_fields)

        pwd = validated_data.pop('password', None)
        real_name = validated_data.pop('real_name', None)
        avatar_val = validated_data.pop('avatar', serializers.empty)
        birthday_val = validated_data.pop('birthday', serializers.empty)

        # first: update model fields handled by super()
        instance = super().update(instance, validated_data)

        # apply extras safely
        if real_name is not None and hasattr(instance, 'first_name'):
            instance.first_name = real_name

        if avatar_val is not serializers.empty and hasattr(instance, 'avatar'):
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

        # update declared optional fields from initial_data if model supports them
        for opt in ('first_name', 'last_name', 'nickname', 'gender', 'phone', 'address',
                    'preferred_region', 'preferred_specialty', 'wechat', 'qq', 'github'):
            if opt in self.initial_data and hasattr(instance, opt):
                raw = self.initial_data.get(opt)
                val = self._normalize_value_for_model(User, opt, raw)
                setattr(instance, opt, val)

        # set password if provided
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
            qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q) | qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q)
        return qs


class AdminUserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStaff]
    serializer_class = AdminUserSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        instance.delete()


class AdminOverviewView(APIView):
    """
    返回两个列表:
      - admins: 所有管理员账户（is_staff=True）
      - recent_logins: 最近 20 条有 last_login 的用户（按 last_login 降序）
    """
    permission_classes = [permissions.IsAuthenticated, IsStaff]

    def get(self, request, *args, **kwargs):
        admins_qs = User.objects.filter(is_staff=True).order_by('-date_joined')
        recent_qs = User.objects.filter(last_login__isnull=False).order_by('-last_login')[:20]

        admins = AdminListSerializer(admins_qs, many=True, context={'request': request}).data
        recent = AdminListSerializer(recent_qs, many=True, context={'request': request}).data

        return Response({'admins': admins, 'recent_logins': recent})