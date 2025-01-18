from django.db.models import QuerySet

from seminare.organizer.tables import ProblemTable
from seminare.organizer.views import WithContest, WithProblemSet
from seminare.organizer.views.generic import GenericTableView
from seminare.problems.models import Problem


class ProblemListView(WithContest, WithProblemSet, GenericTableView):
    table_class = ProblemTable
    table_title = "Úlohy"

    def get_queryset(self) -> QuerySet[Problem]:
        return Problem.objects.filter(problem_set=self.problem_set).order_by("number")

    def get_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať",
                "#",
                # reverse("org:problemset_create", args=[self.contest.id]),
            )
        ]
