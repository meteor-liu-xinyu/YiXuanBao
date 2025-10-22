from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # 基于默认 UserAdmin 扩展显示字段
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'nickname', 'email', 'avatar', 'gender', 'phone', 'birthday', 'address')}),
        (_('Third-party'), {'fields': ('wechat','qq','github')}),
        (_('Permissions'), {'fields': ('is_active','is_staff','is_superuser','groups','user_permissions')}),
        (_('Important dates'), {'fields': ('last_login','date_joined')}),
    )
    list_display = ('username', 'nickname', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'nickname', 'email', 'phone')
    ordering = ('-date_joined',)