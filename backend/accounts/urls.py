from django.urls import path
from django.http import JsonResponse
from django.views import View

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserInfoView,
    GetCSRFTokenView,
    CheckUsernameView,
    HistoryListCreateView,
    HistoryDestroyView,
    ClearHistoryView,
)

from .admin_views import (
    AdminUserListCreateView, 
    AdminUserRetrieveUpdateDestroyView, 
    AdminOverviewView, 
    AdminUserHistoryDeleteView
)

# ⭐ 添加 accounts API 根视图
class AccountsAPIRoot(View):
    def get(self, request):
        return JsonResponse({
            'module': 'accounts',
            'endpoints': {
                'register': '/api/accounts/register/',
                'login': '/api/accounts/login/',
                'logout': '/api/accounts/logout/',
                'userinfo': '/api/accounts/userinfo/',
                'csrf': '/api/accounts/csrf/',
                'check_username': '/api/accounts/check-username/',
                'history': '/api/accounts/history/',
            }
        })

urlpatterns = [
    path('', AccountsAPIRoot.as_view(), name='accounts-root'),  # ⭐ 添加根路径
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('userinfo/', UserInfoView.as_view(), name='userinfo'),
    path('csrf/', GetCSRFTokenView.as_view(), name='csrf'),
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),
    path('history/', HistoryListCreateView.as_view(), name='history-list'),
    path('history/clear/', ClearHistoryView.as_view(), name='history-clear'),
    path('history/<int:pk>/', HistoryDestroyView.as_view(), name='history-detail'),
    # Admin API
    path('admin/users/', AdminUserListCreateView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', AdminUserRetrieveUpdateDestroyView.as_view(), name='admin-user-detail'),
    path('admin/overview/', AdminOverviewView.as_view(), name='admin-overview'),
    path('admin/users/<int:pk>/history/', AdminUserHistoryDeleteView.as_view(), name='admin-user-history-delete'),
]