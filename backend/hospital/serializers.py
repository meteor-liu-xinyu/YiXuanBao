from rest_framework import serializers
from .models import Hospital
from math import isfinite

class HospitalSerializer(serializers.ModelSerializer):
    composite_score = serializers.SerializerMethodField(read_only=True)
    # If request context contains user_lat/user_lng, serializer computes distance (km)
    distance_km = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'region', 'specialty', 'address', 'contact',
            'grade_level', 'longitude', 'latitude',
            'avg_cost', 'bed_count', 'specialty_score', 'success_rate',
            'avg_wait_hours', 'equipment_score', 'reputation_index',
            'created_at', 'updated_at',
            'composite_score', 'distance_km'
        ]
        read_only_fields = ('created_at', 'updated_at', 'composite_score', 'distance_km')

    def get_composite_score(self, obj):
        # Allow caller to pass weight config in serializer context to compute score similarly to recommend
        weights = self.context.get('score_weights')
        try:
            # delegate to model helper (which uses utils)
            s = obj.composite_score(weights=weights)
            # ensure finite numeric
            if s is None or (isinstance(s, float) and not isfinite(s)):
                return None
            return round(float(s), 4)
        except Exception:
            return None

    def get_distance_km(self, obj):
        req = self.context.get('request')
        if not req:
            return None
        try:
            user_lat = req.query_params.get('user_lat') or req.data.get('user_lat') if hasattr(req, 'data') else None
            user_lng = req.query_params.get('user_lng') or req.data.get('user_lng') if hasattr(req, 'data') else None
        except Exception:
            user_lat = user_lng = None
        if user_lat is None or user_lng is None:
            return None
        try:
            user_lat = float(user_lat); user_lng = float(user_lng)
            if obj.latitude is None or obj.longitude is None:
                return None
            # Haversine formula
            from .utils import haversine_km
            d = haversine_km(user_lat, user_lng, obj.latitude, obj.longitude)
            return round(d, 3)
        except Exception:
            return None