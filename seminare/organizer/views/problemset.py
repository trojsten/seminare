from django.db.models import QuerySet
from django.views.generic import ListView

from seminare.organizer.views import WithContest
from seminare.problems.models import ProblemSet


class ProblemSetListView(WithContest, ListView):
    template_name = "org/problem_set/list.html"

    def get_queryset(self) -> QuerySet[ProblemSet]:
        return ProblemSet.objects.filter(contest=self.contest).order_by(
            "-end_date", "-start_date"
        )
