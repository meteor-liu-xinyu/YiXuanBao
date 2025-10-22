from rest_framework import serializers
from .models import User

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('nickname','email','avatar','gender','phone','birthday','address','wechat','qq','github')