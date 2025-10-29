from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# API 根视图
def api_root(request):
    return JsonResponse({
        'message': 'YiXuanBao API',
        'version': '1.0',
        'endpoints': {
            'accounts': '/api/accounts/',
            'hospital': '/api/hospital/',
            'recommend': '/api/recommend/',
        }
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', api_root),
    path('api/accounts/', include('accounts.urls')),
    path('api/hospital/', include('hospital.urls')),
    path('api/recommend/', include('recommend.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)