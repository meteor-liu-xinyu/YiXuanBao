from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PatientPayloadSerializer
from hospital.models import Hospital
from hospital.serializers import HospitalSerializer
from rest_framework.permissions import AllowAny

class RecommendView(APIView):
    """
    POST /api/recommend/
    Accepts patient payload (see PatientPayloadSerializer), returns recommended hospitals.
    Current logic: return ALL hospitals (serialized) as recommendation results.
    Response format:
      {
        "results": [ { hospital fields..., "recommendation_score": <opt> , "score_breakdown": <opt> }, ... ],
        "count": <n>,
        "payload": { ...validated payload... }
      }
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PatientPayloadSerializer(data=request.data or {})
        if not serializer.is_valid():
            return Response({'detail': 'invalid payload', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data

        # Current simple behavior: return all hospitals
        qs = Hospital.objects.all()

        # serialize hospitals using hospital.serializers.HospitalSerializer
        # pass request to context so HospitalSerializer can compute distance if it supports it
        ser = HospitalSerializer(qs, many=True, context={'request': request})
        hospitals_data = ser.data

        # (optionally) you can compute per-hospital recommendation_score here.
        # For now we don't score — but attach empty fields to keep response shape consistent.
        results = []
        for h in hospitals_data:
            # attach placeholder fields
            h['recommendation_score'] = h.get('composite_score', 0)  # optional fallback
            h['score_breakdown'] = {}
            results.append(h)

        return Response({'results': results, 'count': len(results), 'payload': payload}, status=status.HTTP_200_OK)