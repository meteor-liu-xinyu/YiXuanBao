from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    只读序列化器：返回用户信息给前端。
    - avatar: 返回绝对 URL（如果没有则返回默认头像路径）
    - real_name: 组合 first_name + last_name（模型没有 real_name 字段时使用此方法避免 500）
    - birthday 允许不传(required=False)，允许传 null (allow_null=True)，并接受常见输入格式。
    - age: 基于 birthday 计算年龄（若无生日返回 None）
    - nickname / preferred_region / preferred_specialty 等使用 SerializerMethodField 安全读取（若模型没有对应字段返回 None）
    """
    avatar = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()

    # 下面这些字段如果模型上没有也不会导致序列化器构建失败
    nickname = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    preferred_region = serializers.SerializerMethodField()
    preferred_specialty = serializers.SerializerMethodField()

    birthday = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=[
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
        ]
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'nickname', 'email', 'gender', 'phone',
            'real_name', 'address', 'birthday',
            'preferred_region', 'preferred_specialty', 'avatar',
            'date_joined', 'is_staff', 'is_superuser', 'age'
        )
        read_only_fields = ('id', 'username', 'date_joined', 'is_staff', 'is_superuser')

    def get_avatar(self, obj):
        request = self.context.get('request')
        avatar_field = getattr(obj, 'avatar', None)
        avatar_url = None
        try:
            if avatar_field and hasattr(avatar_field, 'url') and avatar_field.url:
                avatar_url = avatar_field.url
                if not str(avatar_url).startswith('/'):
                    avatar_url = '/' + str(avatar_url)
        except Exception:
            avatar_url = None

        # fallback 默认头像
        if not avatar_url:
            if getattr(settings, 'MEDIA_URL', None):
                avatar_url = settings.MEDIA_URL.rstrip('/') + '/avatars/default.png'
            else:
                avatar_url = '/default-avatar.png'

        if request is not None:
            return request.build_absolute_uri(avatar_url)
        return avatar_url

    def get_age(self, obj):
        if getattr(obj, 'birthday', None):
            today = date.today()
            b = obj.birthday
            return today.year - b.year - ((today.month, today.day) < (b.month, b.day))
        return None

    def get_real_name(self, obj):
        first = getattr(obj, 'first_name', '') or ''
        last = getattr(obj, 'last_name', '') or ''
        full = (first + ' ' + last).strip()
        return full or None

    # 以下方法安全返回可能不存在的字段
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


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    可写序列化器：用于 PATCH 更新用户。
    - 接受 write-only 的 real_name 字段（来自前端），会在 update 时映射到模型的 first_name（可根据需求改为拆分）
    - avatar: ImageField 接受 multipart 上传；avatar=None 表示删除头像
    - birthday: 可为空，接受常见格式
    """
    avatar = serializers.ImageField(required=False, allow_null=True)
    real_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    birthday = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=[
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
        ]
    )

    class Meta:
        model = User
        fields = (
            'nickname', 'email', 'avatar', 'gender', 'phone',
            'birthday', 'address', 'wechat', 'qq', 'github',
            'first_name', 'last_name', 'real_name'
        )
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True},
            'nickname': {'required': False, 'allow_blank': True},
            'real_name': {'required': False, 'allow_blank': True},
            'address': {'required': False, 'allow_blank': True},
            'gender': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
            'avatar': {'required': False, 'allow_null': True},
        }

    def validate_birthday(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("生日不能晚于今天")
        return value

    def update(self, instance, validated_data):
        """
        自定义 update：
        - real_name -> first_name（简化策略）
        - 处理 avatar 的删除/替换
        - 规范 birthday 的空字符串为 None
        - 其余字段交给父类处理
        """
        real_name = validated_data.pop('real_name', None)
        if real_name is not None:
            instance.first_name = real_name

        if 'avatar' in validated_data:
            avatar_val = validated_data.pop('avatar')
            if avatar_val is None:
                try:
                    if getattr(instance, 'avatar', None):
                        instance.avatar.delete(save=False)
                except Exception:
                    pass
                instance.avatar = None
            else:
                instance.avatar = avatar_val

        if 'birthday' in validated_data and validated_data.get('birthday') == '':
            validated_data['birthday'] = None

        instance = super().update(instance, validated_data)
        instance.save()
        return instance