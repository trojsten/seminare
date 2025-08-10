from rest_framework import serializers, viewsets

from seminare.contests.utils import get_current_contest
from seminare.problems.models import ProblemSet


class ProblemSetSerializer(serializers.ModelSerializer):
    class Meta:  # pyright:ignore
        model = ProblemSet
        fields = [
            "slug",
            "name",
            "start_date",
            "end_date",
            "is_public",
            "rule_engine",
            "rule_engine_options",
        ]


class ProblemSetViewSet(viewsets.ModelViewSet):
    serializer_class = ProblemSetSerializer
    lookup_field = "slug"

    def get_queryset(self):
        current_contest = get_current_contest(self.request)
        return ProblemSet.objects.filter(contest=current_contest)
