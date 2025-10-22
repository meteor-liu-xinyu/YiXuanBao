from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserInfoView,
    GetCSRFTokenView,  # 新增导入
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('userinfo/', UserInfoView.as_view(), name='userinfo'),
    path('csrf/', GetCSRFTokenView.as_view(), name='csrf'),
]