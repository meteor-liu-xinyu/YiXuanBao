from django.urls import path
from .views import RecommendHospitalView

urlpatterns = [
    path('recommend/', RecommendHospitalView.as_view(), name='recommend'),
]