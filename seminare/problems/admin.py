from django.contrib import admin

from seminare.problems.models import Problem, ProblemSet, Text


@admin.register(ProblemSet)
class ProblemSetAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    search_fields = ["name"]


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "problem_set"]
    search_fields = ["name", "problem_set__name"]


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ["problem", "type"]
    search_fields = ["problem__name"]
