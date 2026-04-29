from django.db.models import F
from django.forms import Form
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

from seminare.contests.utils import get_current_contest
from seminare.organizer.tables import LateSubmitTable
from seminare.organizer.views import MixinProtocol
from seminare.organizer.views.generic import GenericFormView, GenericTableView
from seminare.submits.models import FileSubmit
from seminare.users.mixins.permissions import ContestAdminRequired


class WithLatesubmitQuerySet(MixinProtocol):
    def get_queryset(self):
        contest = get_current_contest(self.request)

        return FileSubmit.objects.filter(
            problem__problem_set__contest=contest,
            created_at__gt=F("problem__problem_set__end_date"),
        ).select_related(
            "enrollment__user",
            "problem__problem_set",
        )


class LateSubmitListView(
    ContestAdminRequired, WithLatesubmitQuerySet, GenericTableView
):
    table_title = "Zoznam oneskorených odovzdaní"
    table_class = LateSubmitTable

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Oneskorenci", "")]


class LateSubmitAcceptView(
    ContestAdminRequired, WithLatesubmitQuerySet, GenericFormView
):
    form_class = Form
    form_title = "Naozaj chceš akceptovať submit?"
    form_submit_label = "Akceptovať"

    success_url = reverse_lazy("org:late_submit_list")

    def get_object(self) -> FileSubmit:
        return get_object_or_404(
            self.get_queryset()
            .select_related("problem__problem_set", "enrollment__user")
            .filter(late_accepted=False, id=self.kwargs["submit_id"].split("-")[1])
        )

    @property
    def form_description(self):
        submit = self.get_object()

        return f"Naozaj chceš akceptovať oneskorený submit {submit.submit_id} v úlohe {submit.problem} ({submit.problem.problem_set}) od používateľa {submit.enrollment.user.display_name}? Tuto akciu nebude možné vrátiť späť."

    def form_valid(self, form):
        submit = self.get_object()
        submit.late_accepted = True
        submit.save()

        return super().form_valid(form)
