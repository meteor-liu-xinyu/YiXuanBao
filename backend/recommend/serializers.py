from rest_framework import serializers

class PatientPayloadSerializer(serializers.Serializer):
    """
    Validate/normalize patient info coming from frontend.
    - 更宽容地接收 economic_level（允许 null / 空字符串会被视作 None）
    - 支持 region 为字符串或数组：如果前端传数组，会把它转换为 "省/市/区" 格式的字符串并保留原数组到 region_values
    - 其它字段保留原先的校验规则
    """
    disease_code = serializers.CharField(required=False, allow_blank=True)
    disease_name = serializers.CharField(required=False, allow_blank=True)
    urgency = serializers.ChoiceField(choices=['emergency', 'urgent', 'routine'], required=False, allow_blank=True)
    # region 支持字符串；若前端传入数组，会在 to_internal_value 里转换为字符串并写入 region_values
    region = serializers.CharField(required=False, allow_blank=True)
    region_values = serializers.ListField(child=serializers.CharField(), required=False)
    user_lat = serializers.FloatField(required=False)
    user_lng = serializers.FloatField(required=False)
    # 改动：允许 null（后端不再拒绝 null）
    economic_level = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=2)
    age = serializers.IntegerField(required=False, min_value=0, max_value=150)
    # extra free-form fields allowed
    extra = serializers.DictField(required=False, child=serializers.JSONField(), allow_empty=True)

    def to_internal_value(self, data):
        """
        在标准反序列化之前做一些兼容处理：
        - 将 economic_level: '' -> None
        - 将 region: list -> join 成 'a/b/c' 字符串，并将原数组放到 region_values
        - 将字符串形式的数字尝试转换为 int（economic_level）
        """
        # make a shallow mutable copy (data might be QueryDict etc.)
        raw = dict(data or {})

        # economic_level: treat '' as None, try to cast numeric strings to int
        if 'economic_level' in raw:
            val = raw.get('economic_level')
            if val == '':
                raw['economic_level'] = None
            else:
                # attempt to normalize numeric strings to int
                try:
                    if val is not None and not isinstance(val, int):
                        raw['economic_level'] = int(val)
                except Exception:
                    # leave as-is; serializer validation will handle invalid types
                    pass

        # region: accept list or string. If list -> convert to joined labels and set region_values
        if 'region' in raw:
            region_val = raw.get('region')
            if isinstance(region_val, (list, tuple)):
                # keep original values
                raw['region_values'] = [str(x) for x in region_val]
                # join into a readable string (省/市/区)
                try:
                    raw['region'] = '/'.join([str(x) for x in region_val if x is not None and str(x) != ''])
                except Exception:
                    raw['region'] = ''
            else:
                # if region is a non-empty string but front may provide JSON like '["a","b"]'
                # we won't try to parse JSON here to avoid overreach; keep string as-is.
                pass

        return super().to_internal_value(raw)