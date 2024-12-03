from django.contrib import admin

from seminare.submits.models import Submit


# Register your models here.
@admin.register(Submit)
class SubmitAdmin(admin.ModelAdmin):
    list_display = ["problem", "type", "created_at", "score", "graded", "enrollment"]
    list_filter = ["type", "graded"]
    search_fields = [
        "problem__name",
        "enrollment__user__username",
        "enrollment__user__first_name",
        "enrollment__user__last_name",
    ]
