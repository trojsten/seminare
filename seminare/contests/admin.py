from django.contrib import admin

from seminare.contests.models import Contest


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name"]
