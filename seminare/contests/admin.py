from django.contrib import admin

from seminare.contests.models import Category, Contest


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "contest"]
    list_filter = ["contest"]
