from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserInfoView,
    GetCSRFTokenView,  # 新增导入
    UserHistoryView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('userinfo/', UserInfoView.as_view(), name='userinfo'),
    path('csrf/', GetCSRFTokenView.as_view(), name='csrf'),
    # history endpoints for logged-in users
    path('history/', UserHistoryView.as_view(), name='user-history'),
    path('history/<int:pk>/', UserHistoryView.as_view(), name='user-history-detail'),
]

try:
    from .admin_views import AdminUserListCreateView, AdminUserRetrieveUpdateDestroyView, AdminOverviewView

    urlpatterns += [
        path('admin/users/', AdminUserListCreateView.as_view(), name='admin-user-list'),
        path('admin/users/<int:pk>/', AdminUserRetrieveUpdateDestroyView.as_view(), name='admin-user-detail'),
        path('admin/overview/', AdminOverviewView.as_view(), name='admin-overview'),
    ]
except Exception as exc:
    import sys, traceback
    sys.stderr.write("Warning: failed to import accounts.admin_views - admin endpoints disabled\n")
    traceback.print_exc(file=sys.stderr)