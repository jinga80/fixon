"""
Point Shower — URL routing.

WhiteNoise 가 `public/` 의 모든 파일을 루트 URL 로 자동 서빙하므로
별도 view 가 필요 없습니다. 헬스체크 endpoint 만 추가합니다.
"""

from django.http import JsonResponse
from django.urls import path


def healthz(_request):
    return JsonResponse({"status": "ok", "service": "pointshower"})


urlpatterns = [
    path("healthz", healthz, name="healthz"),
]
