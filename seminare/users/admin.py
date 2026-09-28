from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    ContestRole,
    Enrollment,
    Notification,
    NotificationPreferences,
    School,
    User,
)


class NotificationPreferencesInline(admin.TabularInline):
    model = NotificationPreferences


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "School",
            {
                "fields": [
                    "current_school",
                    "current_grade",
                    "current_school_updated_at",
                ]
            },
        ),
    )  # pyright:ignore  # ty: ignore[unsupported-operator]
    autocomplete_fields = BaseUserAdmin.autocomplete_fields + ("current_school",)  # pyright:ignore  # ty: ignore[unsupported-operator]
    inlines = [*BaseUserAdmin.inlines, NotificationPreferencesInline]


admin.site.register(User, UserAdmin)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["user", "school", "grade"]
    list_filter = ["school", "grade"]


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    search_fields = ["name", "edu_id", "address"]
    list_display = ["name", "short_name", "edu_id", "address"]


@admin.register(ContestRole)
class ContestRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "contest", "role"]
    list_filter = ["role", "contest"]
    search_fields = ["user__username", "contest__name"]


@admin.register(Notification)
class NotificationsAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ["user", "type", "contest", "created_at", "viewed_at"]
    list_filter = ["type", "contest"]
