"""
Point Shower — URL routing.

WhiteNoise 가 `public/` 의 모든 정적 파일을 루트 URL 로 서빙하고,
Django 는 헬스체크 · 설문 수집 API · 관리자(admin) 만 처리합니다.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from leads.views import board, board_reset, signup


def healthz(_request):
    return JsonResponse({"status": "ok", "service": "pointshower"})


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("api/signup", signup, name="signup"),
    path("api/board", board, name="board"),
    path("api/board/reset", board_reset, name="board_reset"),
    path("admin/", admin.site.urls),
]
