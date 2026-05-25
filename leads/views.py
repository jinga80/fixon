import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Lead

ALLOWED_INTERESTS = {"point_shower", "point_infuser", "night_pack", "perio", "medical_tourism", "consulting"}


@csrf_exempt
@require_POST
def signup(request):
    """설문/가입 제출 수신 (same-origin fetch, JSON)."""
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    # 봇 허니팟 — 채워져 있으면 조용히 성공 처리
    if (data.get("company") or "").strip():
        return JsonResponse({"ok": True})

    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "이름을 입력해 주세요."}, status=400)

    interests = [i for i in (data.get("interests") or []) if i in ALLOWED_INTERESTS][:10]

    Lead.objects.create(
        name=name[:100],
        clinic=(data.get("clinic") or "").strip()[:200],
        phone=(data.get("phone") or "").strip()[:40],
        email=(data.get("email") or "").strip()[:254],
        interests=interests,
        preorder=bool(data.get("preorder")),
        note=(data.get("note") or "").strip()[:1000],
        source=(data.get("source") or "web").strip()[:60],
    )
    return JsonResponse({"ok": True})
