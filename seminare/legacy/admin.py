from django.contrib import admin

from seminare.legacy.models import OldProblem, OldRound


@admin.register(OldRound)
class OldRoundAdmin(admin.ModelAdmin):
    list_display = ["old_round_id", "problem_set", "contest"]
    list_filter = ["contest"]


@admin.register(OldProblem)
class OldProblemAdmin(admin.ModelAdmin):
    pass
