import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import BoardCell, BoardPresence, Lead


@admin.action(description="선택 항목 CSV 내보내기")
def export_csv(modeladmin, request, queryset):
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = "attachment; filename=leads.csv"
    resp.write("﻿")  # Excel 한글 BOM
    w = csv.writer(resp)
    w.writerow(["등록일시", "이름", "병원/소속", "연락처", "이메일", "관심제품", "사전예약", "유입", "메모"])
    for o in queryset:
        w.writerow([
            o.created_at.strftime("%Y-%m-%d %H:%M"),
            o.name, o.clinic, o.phone, o.email,
            o.interests_display, "Y" if o.preorder else "",
            o.source, o.note,
        ])
    return resp


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "clinic", "phone", "email", "interests_col", "preorder", "source")
    list_filter = ("preorder", "source", "created_at")
    search_fields = ("name", "clinic", "phone", "email")
    readonly_fields = ("created_at",)
    actions = [export_csv]
    date_hierarchy = "created_at"

    @admin.display(description="관심 제품")
    def interests_col(self, obj):
        return obj.interests_display


@admin.register(BoardCell)
class BoardCellAdmin(admin.ModelAdmin):
    list_display = ("board", "key", "value", "updated_by", "updated_at")
    list_filter = ("board",)
    search_fields = ("key", "value", "updated_by")


@admin.register(BoardPresence)
class BoardPresenceAdmin(admin.ModelAdmin):
    list_display = ("board", "name", "last_seen")
    list_filter = ("board",)
