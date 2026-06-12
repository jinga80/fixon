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


class BoardCell(models.Model):
    """실시간 공유 작업 보드 — 필드 단위 셀(충돌 없는 협업)."""

    board = models.CharField("보드", max_length=60, default="action")
    key = models.CharField("키", max_length=120)
    value = models.TextField("값", blank=True)
    updated_by = models.CharField("수정자", max_length=60, blank=True)
    updated_at = models.DateTimeField("수정시각", auto_now=True)

    class Meta:
        verbose_name = "보드 셀"
        verbose_name_plural = "보드 셀"
        unique_together = ("board", "key")
        ordering = ["board", "key"]

    def __str__(self):
        return f"{self.board}:{self.key}={self.value[:30]}"


class BoardPresence(models.Model):
    """보드 접속 현황 — 누가 지금 보고 있는지(프레즌스)."""

    board = models.CharField("보드", max_length=60, default="action")
    name = models.CharField("이름", max_length=60)
    last_seen = models.DateTimeField("최근접속", auto_now=True)

    class Meta:
        verbose_name = "보드 접속현황"
        verbose_name_plural = "보드 접속현황"
        unique_together = ("board", "name")

    def __str__(self):
        return f"{self.board}:{self.name}"
