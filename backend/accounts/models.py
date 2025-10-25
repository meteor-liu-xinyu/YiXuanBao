from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    自定义用户模型，继承 AbstractUser，只添加额外字段，避免重复定义已存在的字段。
    db_table 设为 users_user（可按需修改）。
    """
    nickname = models.CharField('昵称', max_length=30, blank=True, null=True)
    avatar = models.ImageField(
        '头像',
        upload_to='avatars/',
        blank=True,
        null=True,
        default='avatars/default.png'
    )
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_OTHER = 'other'
    gender_choices = (
        (GENDER_MALE, '男'),
        (GENDER_FEMALE, '女'),
        (GENDER_OTHER, '其他'),
    )
    gender = models.CharField('性别', max_length=10, choices=gender_choices, blank=True, null=True)
    phone = models.CharField('手机号', max_length=20, blank=True, null=True)
    birthday = models.DateField('生日', blank=True, null=True)

    email = models.EmailField('邮箱地址', blank=True, null=True)  # AbstractUser 已有 email，但可覆盖为可空
    address = models.CharField('联系地址', max_length=255, blank=True, null=True)
    preferred_region = models.CharField('偏好地区', max_length=255, blank=True, null=True)
    preferred_region_values = models.JSONField('偏好地区值', blank=True, null=True, default=list)

    # 第三方账号
    wechat = models.CharField('微信号', max_length=50, blank=True, null=True)
    qq = models.CharField('QQ号', max_length=20, blank=True, null=True)
    github = models.CharField('GitHub', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'users_user'