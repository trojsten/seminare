from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ContestRole, Enrollment, School, User

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
    list_filter = ["role"]
    search_fields = ["user__username", "contest__name"]
