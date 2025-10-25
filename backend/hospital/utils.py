import math

# Default scoring weights (tunable)
DEFAULT_WEIGHTS = {
    'grade': 0.20,            # hospital grade weight
    'specialty_score': 0.18,  # specialty capability
    'success_rate': 0.18,     # historical success rate
    'equipment_score': 0.10,  # equipment quality
    'reputation': 0.10,       # social reputation
    'avg_wait_hours': 0.06,   # penalty for waiting time
    'bed_count': 0.04,        # capacity
    'avg_cost': 0.06,         # cost compatibility to user's economic level
    'distance': 0.08          # proximity factor
}

# Haversine distance (km)
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def normalize(value, from_min, from_max):
    if value is None:
        return 0.0
    if from_max == from_min:
        return 0.0
    v = (value - from_min) / (from_max - from_min)
    return max(0.0, min(1.0, v))

def compute_hospital_base_score(hospital, weights=None):
    """
    Compute a base score for a hospital aggregated from static fields (no user input).
    Returns a numeric score roughly 0..100.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # scale grade_level (0..3) -> 0..1
    grade_norm = (hospital.grade_level or 0) / 3.0

    # other fields: specialty_score, equipment_score, reputation_index expected 0..100
    specialty_norm = (hospital.specialty_score or 50.0) / 100.0
    equipment_norm = (hospital.equipment_score or 50.0) / 100.0
    reputation_norm = (hospital.reputation_index or 50.0) / 100.0

    # success_rate expected 0..1
    success_norm = hospital.success_rate if hospital.success_rate is not None else 0.8

    # bed_count: normalize 0..1000 (cap)
    bed_norm = normalize(hospital.bed_count or 0, 0, 1000)

    # avg_wait_hours: lower is better -> map to 0..1 where 0 wait ->1 score, 24 hours ->0
    wait_norm = 1.0 - normalize(hospital.avg_wait_hours if hospital.avg_wait_hours is not None else 4.0, 0, 24)

    # avg_cost left for compatibility with user's economic level later; here produce normalized 0..1 by cost scale (0..20000)
    cost_norm = 1.0 - normalize(hospital.avg_cost if hospital.avg_cost is not None else 2000.0, 0, 20000)

    # Compose
    score = 0.0
    score += weights.get('grade', 0) * grade_norm
    score += weights.get('specialty_score', 0) * specialty_norm
    score += weights.get('success_rate', 0) * success_norm
    score += weights.get('equipment_score', 0) * equipment_norm
    score += weights.get('reputation', 0) * reputation_norm
    score += weights.get('avg_wait_hours', 0) * wait_norm
    score += weights.get('bed_count', 0) * bed_norm
    score += weights.get('avg_cost', 0) * cost_norm

    # normalize to 0..100
    return max(0.0, min(100.0, score * 100.0))

def compute_recommendation_score(hospital, user_payload, weights=None):
    """
    Compute recommendation score for a hospital given a user payload.
    user_payload dict may contain:
      - disease_code, disease_name
      - urgency: 'emergency'|'urgent'|'routine'
      - region (str)
      - user_lat, user_lng (floats)
      - economic_level (0/1/2)
      - age (int)
    Returns tuple: (score_float, breakdown_dict)
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    base = compute_hospital_base_score(hospital, weights)

    breakdown = {'base': round(base, 4)}

    score = base

    # Distance: if user's coordinates provided, compute haversine and apply a distance factor
    user_lat = user_payload.get('user_lat')
    user_lng = user_payload.get('user_lng')
    distance_km = None
    distance_factor = 1.0
    if user_lat is not None and user_lng is not None and hospital.latitude is not None and hospital.longitude is not None:
        try:
            distance_km = haversine_km(float(user_lat), float(user_lng), float(hospital.latitude), float(hospital.longitude))
            # Map distance into a proximity score 0..1 (0 at >=200km, 1 at 0km)
            prox = 1.0 - normalize(distance_km, 0, 200.0)
            distance_factor = prox
            # apply as multiplicative effect on a distance weight
            dist_weight = weights.get('distance', 0)
            score = score * (1.0 - dist_weight) + (score * dist_weight * distance_factor)
            breakdown['distance_km'] = round(distance_km, 3)
            breakdown['distance_factor'] = round(distance_factor, 4)
        except Exception:
            pass
    else:
        # if no coords: if region matches string, small boost
        user_region = user_payload.get('region')
        if user_region:
            if isinstance(user_region, str) and user_region.strip() and hospital.region and user_region.strip().lower() in hospital.region.lower():
                # boost by 3% of score
                score += 0.03 * score
                breakdown['region_match_boost'] = 0.03

    # economic compatibility: if avg_cost exists, compute how close to user's economic_level ("budget")
    econ = user_payload.get('economic_level')
    if econ is not None and hospital.avg_cost is not None:
        # define expected cost by economic_level
        # 0 -> low budget ~ 0-2000, 1 -> medium ~ 2000-8000, 2 -> high -> 8000+
        if econ == 0:
            target = 1500.0
        elif econ == 1:
            target = 5000.0
        else:
            target = 15000.0
        # closer cost -> higher compatibility; use gaussian-like metric
        diff = abs((hospital.avg_cost or 0) - target)
        # map diff -> 0..1 where 0 diff ->1, diff >= target*2 ->0
        compat = 1.0 - normalize(diff, 0, target * 2 if target>0 else 10000)
        cost_weight = weights.get('avg_cost', 0)
        score = score * (1.0 - cost_weight) + score * cost_weight * compat
        breakdown['cost_compat'] = round(compat, 4)

    # urgency: increase weight on specialty and success_rate for emergencies
    urgency = user_payload.get('urgency')
    if urgency == 'emergency':
        # boost success_rate contribution
        boost = 1.06
        score *= boost
        breakdown['urgency_boost'] = boost
    elif urgency == 'urgent':
        score *= 1.03
        breakdown['urgency_boost'] = 1.03

    # specialty match: if user provides disease_name or code, and hospital.specialty contains keywords,
    # small boost proportional to specialty_score
    disease_name = (user_payload.get('disease_name') or '') or ''
    disease_code = (user_payload.get('disease_code') or '') or ''
    specialty_match = 0.0
    if disease_name:
        if hospital.specialty and disease_name.lower() in hospital.specialty.lower():
            specialty_match = min(1.0, (hospital.specialty_score or 50.0) / 100.0)
    elif disease_code:
        # compare ICD code first letter to specialty (heuristic)
        if hospital.specialty and disease_code[0:1].lower() in hospital.specialty.lower():
            specialty_match = min(1.0, (hospital.specialty_score or 50.0) / 100.0)
    if specialty_match:
        spec_weight = weights.get('specialty_score', 0)
        score = score * (1.0 - spec_weight) + score * spec_weight * (1.0 + specialty_match * 0.2)
        breakdown['specialty_match'] = round(specialty_match, 4)

    # penalize long waiting hours (lower is better) — we already incorporated wait into base,
    # but we can apply an additional penalty if wait is large and urgency is emergency
    if hospital.avg_wait_hours is not None:
        wait = hospital.avg_wait_hours
        if wait > 6 and urgency == 'emergency':
            # reduce score 5%
            score *= 0.95
            breakdown['wait_penalty'] = 0.95

    # bed_count increases score slightly
    if hospital.bed_count:
        bed_bonus = normalize(hospital.bed_count, 0, 1000) * 0.02  # up to +2%
        score *= (1.0 + bed_bonus)
        breakdown['bed_bonus'] = round(bed_bonus, 4)

    # cap and normalize final score 0..100
    final = max(0.0, min(100.0, score))
    breakdown['final'] = round(final, 4)
    return final, breakdown