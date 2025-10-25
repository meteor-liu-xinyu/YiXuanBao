from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserInfoView,
    GetCSRFTokenView,
    CheckUsernameView,
)

from .admin_views import AdminUserListCreateView, AdminUserRetrieveUpdateDestroyView, AdminOverviewView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('userinfo/', UserInfoView.as_view(), name='userinfo'),
    path('csrf/', GetCSRFTokenView.as_view(), name='csrf'),
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),
    # Admin API - 仅供管理员使用
    path('admin/users/', AdminUserListCreateView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', AdminUserRetrieveUpdateDestroyView.as_view(), name='admin-user-detail'),
    path('admin/overview/', AdminOverviewView.as_view(), name='admin-overview'),
]