from typing import Any

from rest_framework import serializers, viewsets

from seminare.contests.utils import get_current_contest
from seminare.problems.models import ProblemSet


class ProblemSetSerializer(serializers.ModelSerializer):
    class Meta:  # pyright:ignore
        model = ProblemSet
        exclude = ["id", "contest"]

    def validate(self, attrs):
        contest = self.context["contest"]
        if self.instance:
            assert isinstance(self.instance, ProblemSet)
            self.instance.contest = contest
            self.instance.full_clean()
        else:
            ProblemSet(**attrs, contest=contest).full_clean()
        return attrs


class ProblemSetViewSet(viewsets.ModelViewSet):
    serializer_class = ProblemSetSerializer
    lookup_field = "slug"

    def get_queryset(self):
        current_contest = get_current_contest(self.request)
        return ProblemSet.objects.filter(contest=current_contest)

    def get_serializer_context(self) -> dict[str, Any]:
        ctx = super().get_serializer_context()
        ctx["contest"] = get_current_contest(self.request)
        return ctx

    def perform_create(self, serializer):
        contest = get_current_contest(self.request)
        serializer.save(contest=contest)
