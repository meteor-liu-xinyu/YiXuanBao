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
    - age: 基于 birthday 计算年龄（若无生日返回 None）
    """
    avatar = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'nickname', 'email', 'avatar', 'gender', 'phone',
            'birthday', 'age', 'address', 'wechat', 'qq', 'github',
            'date_joined', 'is_staff', 'is_superuser',
            'real_name', 'first_name', 'last_name'
        )
        read_only_fields = ('id', 'username', 'date_joined')

    def get_avatar(self, obj):
        request = self.context.get('request')
        # 先尝试从模型字段取得 url
        avatar_field = getattr(obj, 'avatar', None)
        avatar_url = None
        try:
            if avatar_field and hasattr(avatar_field, 'url') and avatar_field.url:
                avatar_url = avatar_field.url
                if not str(avatar_url).startswith('/'):
                    avatar_url = '/' + str(avatar_url)
        except Exception:
            avatar_url = None

        # fallback 默认头像（前端可也使用 public/default-avatar.png）
        if not avatar_url:
            # 优先返回 MEDIA 下的默认头像（若配置了 MEDIA_URL）
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
        # 如果模型没有 real_name 字段，组合 first_name + last_name
        first = getattr(obj, 'first_name', '') or ''
        last = getattr(obj, 'last_name', '') or ''
        full = (first + ' ' + last).strip()
        return full or None


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    可写序列化器：用于 PATCH 更新用户。
    - 接受 write-only 的 real_name 字段（来自前端），会在 update 时映射到模型的 first_name（可根据需求改为拆分）
    - avatar: ImageField 接受 multipart 上传
    """
    avatar = serializers.ImageField(required=False, allow_null=True)
    real_name = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = (
            'nickname', 'email', 'avatar', 'gender', 'phone',
            'birthday', 'address', 'wechat', 'qq', 'github',
            'first_name', 'last_name', 'real_name'
        )

    def validate_birthday(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("生日不能晚于今天")
        return value

    def update(self, instance, validated_data):
        # 处理前端传来的 real_name（写入 first_name；如需拆分可在此处实现）
        real_name = validated_data.pop('real_name', None)
        if real_name is not None:
            # 简单策略：把整段写入 first_name，或按空格拆分到 first/last
            instance.first_name = real_name
        # 其余字段按 ModelSerializer 的默认行为更新
        return super().update(instance, validated_data)