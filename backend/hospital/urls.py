from django.urls import path
from django.http import JsonResponse
from django.views import View
from .views import (
    HospitalListCreateView,
    HospitalRetrieveUpdateDestroyView,
    RecommendHospitalView
)

urlpatterns = [
    path('', HospitalListCreateView.as_view(), name='hospital-list'),
    path('<int:pk>/', HospitalRetrieveUpdateDestroyView.as_view(), name='hospital-detail'),
    path('recommend/', RecommendHospitalView.as_view(), name='recommend'),
]