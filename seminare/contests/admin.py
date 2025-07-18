from django.contrib import admin

from seminare.contests.models import Contest, RuleData


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name"]


@admin.register(RuleData)
class RuleDataAdmin(admin.ModelAdmin):
    list_display = ["contest", "user", "engine", "created_at"]
    list_filter = ["contest", "engine"]
    search_fields = ["user__username", "contest__name"]
