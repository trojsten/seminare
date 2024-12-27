from django.db.models import QuerySet

from seminare.organizer.tables import ProblemSetTable
from seminare.organizer.views import WithContest
from seminare.organizer.views.generic import GenericTableView
from seminare.problems.models import ProblemSet


class ProblemSetListView(WithContest, GenericTableView):
    # TODO: Permission checking

    table_class = ProblemSetTable
    table_title = "Sady úloh"

    def get_queryset(self) -> QuerySet[ProblemSet]:
        return ProblemSet.objects.filter(contest=self.contest).order_by(
            "-end_date", "-start_date"
        )
