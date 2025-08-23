from django.contrib import admin

from seminare.problems.models import Problem, ProblemSet, ProblemSetFrozenResults, Text


class TextInline(admin.TabularInline):
    model = Text
    extra = 2


@admin.register(ProblemSet)
class ProblemSetAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    search_fields = ["name"]


@admin.register(ProblemSetFrozenResults)
class ProblemSetFrozenResultsAdmin(admin.ModelAdmin):
    list_display = ["problem_set", "table"]
    search_fields = ["problem_set", "table"]


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "problem_set"]
    search_fields = ["name", "problem_set__name"]
    inlines = [TextInline]


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ["problem", "type"]
    search_fields = ["problem__name"]
