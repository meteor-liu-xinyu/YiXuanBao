from django.db import models
from django.utils import timezone

class Hospital(models.Model):
    """
    完整的 Hospital 模型，包含：
      - name, region, specialty, address, contact
      - grade_level (医院等级：数值化)
      - longitude/latitude (地理坐标)
      - avg_cost (平均诊疗费用)
      - bed_count (床位数)
      - specialty_score (专科能力评分 0-100)
      - success_rate (治疗成功率 0-1)
      - avg_wait_hours (平均候诊时间，小时)
      - equipment_score (设备水平评分 0-100)
      - reputation_index (社会声誉 0-100)
      - created_at / updated_at
    另外提供 helper 方法：as_dict(), composite_score()（委托给外部 utils）
    """
    GRADE_CHOICES = (
        (3, '三级甲等 (3)'),
        (2, '二级甲等 (2)'),
        (1, '一级 (1)'),
        (0, '其他 (0)'),
    )

    name = models.CharField("医院名称", max_length=200, unique=True)
    # region 允许自由文本（可存 "省/市/区" 或城市名），如需更细粒度可再拆分为 province/city/area
    region = models.CharField("地区", max_length=150, blank=True, db_index=True, help_text="例如：省/市/区")
    specialty = models.CharField("专科/擅长", max_length=300, blank=True, help_text="逗号分隔多个专科")
    address = models.CharField("详细地址", max_length=255, blank=True)
    contact = models.CharField("联系方式", max_length=100, blank=True)

    # 基础评分属性
    grade_level = models.IntegerField("医院等级", choices=GRADE_CHOICES, default=0, db_index=True,
                                      help_text="数值：3=三甲, 2=二级甲等, 1=一级, 0=其他")
    # 使用 DecimalField 能保证精度，作为经纬度的备选：这里用 FloatField（简单）
    longitude = models.FloatField("经度", null=True, blank=True, help_text="WGS84，经度")
    latitude = models.FloatField("纬度", null=True, blank=True, help_text="WGS84，纬度")

    avg_cost = models.FloatField("平均诊疗费用", null=True, blank=True,
                                 help_text="货币单位的平均诊疗费用（用于与用户经济承受比较）")
    bed_count = models.IntegerField("床位数", null=True, blank=True)

    # 专科、设备、声誉等评分（0-100 scale）
    specialty_score = models.FloatField("专科能力评分", default=50.0, help_text="0-100 标度")
    equipment_score = models.FloatField("设备水平评分", default=50.0, help_text="0-100 标度")
    reputation_index = models.FloatField("社会声誉指数", default=50.0, help_text="0-100 标度")

    # 成功率与候诊时间
    success_rate = models.FloatField("治疗成功率", default=0.8, help_text="0-1 标度")
    avg_wait_hours = models.FloatField("平均候诊时间(小时)", null=True, blank=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ('-grade_level', 'name')
        indexes = [
            models.Index(fields=['region']),
            models.Index(fields=['grade_level']),
        ]
        verbose_name = "医院"
        verbose_name_plural = "医院"

    def __str__(self):
        return self.name

    def as_dict(self):
        """简便地把主要字段导出为 dict（供 API 或前端使用）"""
        return {
            "id": self.pk,
            "name": self.name,
            "region": self.region,
            "specialty": self.specialty,
            "address": self.address,
            "contact": self.contact,
            "grade_level": self.grade_level,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "avg_cost": self.avg_cost,
            "bed_count": self.bed_count,
            "specialty_score": self.specialty_score,
            "success_rate": self.success_rate,
            "avg_wait_hours": self.avg_wait_hours,
            "equipment_score": self.equipment_score,
            "reputation_index": self.reputation_index,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def composite_score(self, weights=None):
        """
        返回一个基于模型字段的聚合评分（0..100）。
        该方法会委托到 hospital.utils.compute_hospital_base_score（如果可用），便于和推荐逻辑复用。
        """
        try:
            from .utils import compute_hospital_base_score
            return compute_hospital_base_score(self, weights=weights)
        except Exception:
            # 简单回退计算
            score = 0.0
            # grade_level 占比放大
            score += (self.grade_level or 0) * 10.0
            score += (self.specialty_score or 50.0) * 0.2
            score += (self.success_rate or 0.8) * 20.0
            score += (self.equipment_score or 50.0) * 0.1
            score += (self.reputation_index or 50.0) * 0.1
            return min(100.0, max(0.0, score))