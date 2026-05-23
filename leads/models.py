from django.db import models

PRODUCT_LABELS = {
    "point_shower": "Point Shower",
    "point_infuser": "Point Infuser",
    "night_pack": "Night Pack Splint",
    "perio": "Perio (Touch/MTS)",
}


class Lead(models.Model):
    """SIDEX 설문/커뮤니티 가입으로 수집되는 원장(회원) 리드."""

    name = models.CharField("이름", max_length=100)
    clinic = models.CharField("병원/소속", max_length=200, blank=True)
    phone = models.CharField("연락처", max_length=40, blank=True)
    email = models.EmailField("이메일", max_length=254, blank=True)
    interests = models.JSONField("관심 제품", default=list, blank=True)
    preorder = models.BooleanField("사전예약 알림 동의", default=False)
    note = models.TextField("메모", blank=True)
    source = models.CharField("유입경로", max_length=60, default="web")
    created_at = models.DateTimeField("등록일시", auto_now_add=True)

    class Meta:
        verbose_name = "리드(원장 회원)"
        verbose_name_plural = "리드(원장 회원)"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} · {self.clinic}".strip(" ·") or self.name

    @property
    def interests_display(self):
        return ", ".join(PRODUCT_LABELS.get(i, i) for i in (self.interests or []))
