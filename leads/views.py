import json
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from .models import BoardCell, BoardPresence, Lead

# 보드 화이트리스트 — 임의 보드 생성 방지
ALLOWED_BOARDS = {"action"}
PRESENCE_WINDOW = 35  # 초: 이 시간 내 접속자를 '온라인'으로 표시

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


# ============================================================
# 실시간 공유 작업 보드 (action.html)
# ============================================================

def _board_snapshot(board, me=""):
    """보드 전체 셀 + 온라인 접속자 + 서버 시각."""
    cells = {}
    for c in BoardCell.objects.filter(board=board):
        cells[c.key] = {
            "v": c.value,
            "by": c.updated_by,
            "at": c.updated_at.isoformat(),
        }
    cutoff = timezone.now() - timedelta(seconds=PRESENCE_WINDOW)
    online = list(
        BoardPresence.objects.filter(board=board, last_seen__gte=cutoff)
        .order_by("-last_seen")
        .values_list("name", flat=True)
    )
    return {
        "ok": True,
        "cells": cells,
        "online": online,
        "serverTime": timezone.now().isoformat(),
    }


def _touch_presence(board, name):
    name = (name or "").strip()[:60]
    if not name:
        return
    BoardPresence.objects.update_or_create(
        board=board, name=name, defaults={"last_seen": timezone.now()}
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def board(request):
    """GET = 스냅샷 조회(+프레즌스 갱신), POST = 셀 업서트."""
    if request.method == "GET":
        board_name = (request.GET.get("board") or "action").strip()
        if board_name not in ALLOWED_BOARDS:
            return JsonResponse({"ok": False, "error": "unknown board"}, status=400)
        _touch_presence(board_name, request.GET.get("me", ""))
        return JsonResponse(_board_snapshot(board_name))

    # POST — 셀 1건 업서트
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    board_name = (data.get("board") or "action").strip()
    if board_name not in ALLOWED_BOARDS:
        return JsonResponse({"ok": False, "error": "unknown board"}, status=400)

    key = (data.get("key") or "").strip()[:120]
    if not key:
        return JsonResponse({"ok": False, "error": "key required"}, status=400)

    value = ("" if data.get("value") is None else str(data.get("value")))[:2000]
    who = (data.get("by") or "").strip()[:60]

    BoardCell.objects.update_or_create(
        board=board_name, key=key,
        defaults={"value": value, "updated_by": who},
    )
    _touch_presence(board_name, who)
    return JsonResponse(_board_snapshot(board_name))


@csrf_exempt
@require_POST
def board_reset(request):
    """보드 전체 초기화 — 모든 참여자 공유 상태 삭제."""
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, TypeError):
        data = {}
    board_name = (data.get("board") or "action").strip()
    if board_name not in ALLOWED_BOARDS:
        return JsonResponse({"ok": False, "error": "unknown board"}, status=400)
    BoardCell.objects.filter(board=board_name).delete()
    return JsonResponse(_board_snapshot(board_name))
