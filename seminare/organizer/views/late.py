from django.db.models import F, QuerySet
from django.forms import Form
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

from seminare.contests.utils import get_current_contest
from seminare.organizer.tables import LateSubmitTable
from seminare.organizer.views import MixinProtocol
from seminare.organizer.views.generic import GenericFormView, GenericTableView
from seminare.submits.models import BaseSubmit, FileSubmit
from seminare.users.mixins.permissions import ContestAdminRequired


class WithLatesubmitQuerySet(MixinProtocol):
    def get_submits_queryset(self):
        contest = get_current_contest(self.request)

        qs: list[QuerySet] = []
        for submit_cls in BaseSubmit.get_submit_types():
            qs.append(
                submit_cls.objects.filter(
                    problem__problem_set__contest=contest,
                    created_at__gte=F("problem__problem_set__end_date"),
                )
                .select_related(
                    "enrollment__user",
                    "problem__problem_set",
                )
                .only(
                    "id",
                    "problem__problem_set",
                    "problem__problem_set__name",
                    "problem__problem_set__end_date",
                    "problem__problem_set__is_finalized",
                    "problem__name",
                    "problem__number",
                    "enrollment",
                    "created_at",
                    "late_accepted",
                )
            )

        if len(qs) == 0:
            return FileSubmit.objects.none()
        elif len(qs) == 1:
            return qs[0]

        return qs[0].union(*qs[1:])

    def get_queryset(self):
        return self.get_submits_queryset().order_by("-created_at")


class LateSubmitListView(
    ContestAdminRequired, WithLatesubmitQuerySet, GenericTableView
):
    table_title = "Zoznam oneskorených odovzdaní"
    table_class = LateSubmitTable

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Oneskorenci", "")]


class LateSubmitAcceptView(GenericFormView):
    form_class = Form
    form_title = "Naozaj chceš akceptovať submit?"
    form_submit_label = "Akceptovať"

    success_url = reverse_lazy("org:late_submit_list")

    def get_object(self) -> BaseSubmit:
        qs = BaseSubmit.get_submit_by_id_queryset(self.kwargs["submit_id"])
        if qs is None:
            raise Http404()
        return get_object_or_404(
            qs.select_related("problem__problem_set", "enrollment__user").filter(
                late_accepted=False
            )
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
