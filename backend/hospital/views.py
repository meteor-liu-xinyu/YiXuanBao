from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .models import Hospital
from .serializers import HospitalSerializer

class RecommendHospitalView(APIView):
    """
    占位推荐接口：接收 POST 数据（region, disease），按 region/specialty 过滤并返回医院列表。
    permission: AllowAny（不需要认证）
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        region = request.data.get('region', '') or ''
        disease = request.data.get('disease', '') or ''
        qs = Hospital.objects.all()
        if region:
            qs = qs.filter(region__icontains=region)
        if disease:
            qs = qs.filter(specialty__icontains=disease)
        serializer = HospitalSerializer(qs[:50], many=True)
        return Response({'hospitals': serializer.data})

    def options(self, request, *args, **kwargs):
        # 返回允许的方法，方便调试（OPTIONS 不需要 CSRF）
        return Response(status=200)