from rest_framework import serializers

class PatientPayloadSerializer(serializers.Serializer):
    """
    Validate/normalize patient info coming from frontend.
    Fields are optional so frontend can send partial data; backend will handle accordingly.
    """
    disease_code = serializers.CharField(required=False, allow_blank=True)
    disease_name = serializers.CharField(required=False, allow_blank=True)
    urgency = serializers.ChoiceField(choices=['emergency', 'urgent', 'routine'], required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    user_lat = serializers.FloatField(required=False)
    user_lng = serializers.FloatField(required=False)
    economic_level = serializers.IntegerField(required=False, min_value=0, max_value=2)
    age = serializers.IntegerField(required=False, min_value=0, max_value=150)
    # extra free-form fields allowed
    extra = serializers.DictField(required=False, child=serializers.JSONField(), allow_empty=True)