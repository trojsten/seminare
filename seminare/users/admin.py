from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Enrollment, School, User

admin.site.register(User, UserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["name"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["user", "school", "grade", "category"]
    list_filter = ["school", "grade", "category"]


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name", "edu_id", "adress"]
