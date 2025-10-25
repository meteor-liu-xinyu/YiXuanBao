from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import Hospital
from .serializers import HospitalSerializer
from .utils import compute_recommendation_score

class HospitalListCreateView(generics.ListCreateAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [AllowAny]  # adjust for admin operations as needed

class HospitalRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [AllowAny]  # adjust permissions per your needs

class RecommendHospitalView(APIView):
    """
    POST /hospital/recommend/
    Accepts JSON payload describing user request:
      - disease_code, disease_name
      - urgency: 'emergency'|'urgent'|'routine'
      - region (string)
      - user_lat, user_lng (floats) optional for distance
      - economic_level (0/1/2)
      - age (int)
    Returns list of hospitals ordered by recommendation score, with breakdown.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.data or {}
        # Fetch candidates (optionally filter by region or specialty)
        qs = Hospital.objects.all()

        # optional quick filter: region substring
        region_q = payload.get('region')
        if region_q:
            qs = qs.filter(region__icontains=region_q)

        # Collect and score
        hospitals = list(qs)
        scored = []
        for h in hospitals:
            score, breakdown = compute_recommendation_score(h, payload)
            # serialize with context (include request to compute distance if needed)
            serializer = HospitalSerializer(h, context={'request': request})
            data = serializer.data
            data['recommendation_score'] = round(score, 4)
            data['score_breakdown'] = breakdown
            scored.append((score, data))

        # sort by score desc
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [d for s, d in scored]

        return Response({'results': results, 'count': len(results)}, status=status.HTTP_200_OK)