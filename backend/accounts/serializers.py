from rest_framework import serializers
from django.conf import settings
from .models import User
from datetime import date

class UserSerializer(serializers.ModelSerializer):
    """
    只读序列化器，用于返回用户信息给前端，avatar 返回绝对 URL（或默认头像）。
    """
    avatar = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'nickname', 'email', 'avatar', 'gender', 'phone',
            'birthday', 'age', 'address', 'wechat', 'qq', 'github', 'date_joined'
        )

    def get_avatar(self, obj):
        request = self.context.get('request')
        try:
            avatar_field = obj.avatar
            if avatar_field and hasattr(avatar_field, 'url'):
                url = avatar_field.url
            else:
                # 如果用户没有上传头像，返回 media 下默认头像
                url = settings.MEDIA_URL + 'avatars/default.png'
        except Exception:
            url = settings.MEDIA_URL + 'avatars/default.png'
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_age(self, obj):
        if obj.birthday:
            today = date.today()
            return today.year - obj.birthday.year - ((today.month, today.day) < (obj.birthday.month, obj.birthday.day))
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    可写序列化器，用于 PATCH/PUT 更新用户。支持 avatar 的 multipart 上传。
    """
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'nickname', 'email', 'avatar', 'gender', 'phone',
            'birthday', 'address', 'wechat', 'qq', 'github'
        )

    def validate_birthday(self, value):
        # 简单验证：生日不能在未来
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("生日不能晚于今天")
        return value