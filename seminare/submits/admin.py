from django.contrib import admin

from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit


@admin.register(FileSubmit)
class FileSubmitAdmin(admin.ModelAdmin):
    list_display = ["problem", "created_at", "score", "scored_by"]


@admin.register(JudgeSubmit)
class JudgeSubmitAdmin(admin.ModelAdmin):
    list_display = ["problem", "created_at", "score", "scored_by", "judge_id"]


@admin.register(TextSubmit)
class TextSubmitAdmin(admin.ModelAdmin):
    list_display = ["problem", "created_at", "score", "scored_by"]
