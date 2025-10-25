from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q

User = get_user_model()


class IsStaff(permissions.BasePermission):
    """仅允许 is_staff 的用户访问（管理员）。"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class AdminListSerializer(serializers.ModelSerializer):
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
    avatar_url = serializers.SerializerMethodField(read_only=True)
    read_real_name = serializers.SerializerMethodField(read_only=True)

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

    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    real_name = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
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
        try:
            f = model_cls._meta.get_field(field_name)
            return bool(getattr(f, 'null', False))
        except FieldDoesNotExist:
            return False

    def _normalize_value_for_model(self, model_cls, field_name, value):
        if value is None:
            if self._model_field_allows_null(model_cls, field_name):
                return None
            return ''
        return value

    def _normalize_validated_fields(self, validated_data, fields):
        for f in fields:
            if f in validated_data and validated_data[f] is None:
                validated_data[f] = self._normalize_value_for_model(User, f, None)

    def _pop_model_fields_only(self, validated_data):
        model_field_names = {f.name for f in User._meta.fields}
        extras = {}
        for key in list(validated_data.keys()):
            if key not in model_field_names:
                extras[key] = validated_data.pop(key)
        return extras

    def validate(self, data):
        """
        在创建用户时，强制要求 username 与 password 存在（前端也会做校验）。
        data: validated data at serializer.validate time (password may be in initial_data when using multipart)
        """
        if self.instance is None:
            username = data.get('username') or self.initial_data.get('username')
            password = data.get('password') or self.initial_data.get('password')
            if not username or not str(username).strip():
                raise serializers.ValidationError({'username': '用户名不能为空'})
            if not password or not str(password).strip():
                raise serializers.ValidationError({'password': '密码不能为空'})
        return data

    def create(self, validated_data):
        optional_fields = ('first_name', 'last_name', 'nickname', 'gender', 'phone', 'address',
                           'preferred_region', 'preferred_specialty', 'wechat', 'qq', 'github')
        self._normalize_validated_fields(validated_data, optional_fields)

        pwd = validated_data.pop('password', None)
        real_name = validated_data.pop('real_name', None)
        avatar_val = validated_data.pop('avatar', serializers.empty)
        birthday_val = validated_data.pop('birthday', serializers.empty)

        extras = self._pop_model_fields_only(validated_data)

        user = super().create(validated_data)

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

        for opt, raw in extras.items():
            if hasattr(user, opt):
                val = self._normalize_value_for_model(User, opt, raw)
                setattr(user, opt, val)

        if pwd:
            user.set_password(pwd)

        user.save()
        return user

    def update(self, instance, validated_data):
        optional_fields = ('first_name', 'last_name', 'nickname', 'gender', 'phone', 'address',
                           'preferred_region', 'preferred_specialty', 'wechat', 'qq', 'github')
        self._normalize_validated_fields(validated_data, optional_fields)

        pwd = validated_data.pop('password', None)
        real_name = validated_data.pop('real_name', None)
        avatar_val = validated_data.pop('avatar', serializers.empty)
        birthday_val = validated_data.pop('birthday', serializers.empty)

        extras = self._pop_model_fields_only(validated_data)

        instance = super().update(instance, validated_data)

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

        for opt, raw in extras.items():
            if hasattr(instance, opt):
                val = self._normalize_value_for_model(User, opt, raw)
                setattr(instance, opt, val)

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
        field = self.request.query_params.get('field')
        if q:
            q = q.strip()
            if field == 'username':
                qs = qs.filter(username__icontains=q)
            elif field == 'email':
                qs = qs.filter(email__icontains=q)
            elif field == 'nickname':
                qs = qs.filter(nickname__icontains=q)
            elif field == 'real_name':
                qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
            else:
                qs = qs.filter(
                    Q(username__icontains=q) |
                    Q(email__icontains=q) |
                    Q(first_name__icontains=q) |
                    Q(last_name__icontains=q)
                )
        return qs


class AdminUserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStaff]
    serializer_class = AdminUserSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        instance.delete()


class AdminOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaff]

    def get(self, request, *args, **kwargs):
        admins_qs = User.objects.filter(is_staff=True).order_by('-date_joined')
        recent_qs = User.objects.filter(last_login__isnull=False).order_by('-last_login')[:20]

        admins = AdminListSerializer(admins_qs, many=True, context={'request': request}).data
        recent = AdminListSerializer(recent_qs, many=True, context={'request': request}).data

        return Response({'admins': admins, 'recent_logins': recent})