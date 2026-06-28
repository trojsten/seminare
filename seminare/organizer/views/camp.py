from functools import cached_property

from django.db.models import Count
from django.forms import Form
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from seminare.camps.models import Camp
from seminare.contests.utils import get_current_contest
from seminare.organizer.forms import CampForm
from seminare.organizer.tables import CampAttendeeTable, CampTable
from seminare.organizer.views import MixinProtocol
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormTableView,
    GenericFormView,
    GenericTableView,
)
from seminare.users.mixins.permissions import ContestAdminRequired


class WithCampQuerySet(MixinProtocol):
    def get_queryset(self):
        contest = get_current_contest(self.request)

        return Camp.objects.filter(
            problem_set__contest=contest,
        )

    @cached_property
    def camp(self):
        return get_object_or_404(self.get_queryset().filter(pk=self.kwargs["pk"]))


class CampListView(ContestAdminRequired, WithCampQuerySet, GenericTableView):
    table_title = "Zoznam sústredení"
    table_class = CampTable
    table_links = [("green", "mdi:plus", "Pridať", reverse_lazy("org:camp_create"))]

    def get_queryset(self):
        return super().get_queryset().annotate(attendees_count=Count("attendees"))

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Sústredenia", "")]


class CampCreateView(ContestAdminRequired, GenericFormView, CreateView):
    form_title = "Nové sústredenie"
    form_class = CampForm
    form_multipart = True
    success_url = reverse_lazy("org:camp_list")

    def get_form_datalists(self):
        return [
            ("location", Camp.objects.values_list("location", flat=True).distinct())
        ]

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["contest"] = get_current_contest(self.request)
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Sústredenia", reverse("org:camp_list")),
            ("Nové", ""),
        ]


class CampUpdateView(
    ContestAdminRequired, WithCampQuerySet, GenericFormTableView, UpdateView
):
    form_title = "Upraviť sústredenie"
    form_class = CampForm
    form_multipart = True

    table_class = CampAttendeeTable

    success_url = reverse_lazy("org:camp_list")

    def get_form_datalists(self):
        return [
            ("location", Camp.objects.values_list("location", flat=True).distinct())
        ]

    def get_object(self, queryset=None):
        contest = get_current_contest(self.request)

        return Camp.objects.filter(
            problem_set__contest=contest,
        ).get(pk=self.kwargs["pk"])

    def get_queryset(self):
        return self.get_object().attendees.select_related("user").all()

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["contest"] = get_current_contest(self.request)
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Sústredenia", reverse("org:camp_list")),
            (self.object, ""),
            ("Upraviť", ""),
        ]


class CampAttendeeDeleteView(ContestAdminRequired, WithCampQuerySet, GenericDeleteView):
    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Sústredenia", reverse("org:camp_list")),
            (self.object.camp, reverse("org:camp_update", args=[self.object.camp.pk])),
            (self.object.user.display_name, ""),
            ("Odstrániť účastníka", ""),
        ]

    def get_object(self, queryset=None):
        camp = (
            self.get_queryset()
            .filter(is_finalized=False)
            .get(pk=self.kwargs["camp_pk"])
        )

        return camp.attendees.get(pk=self.kwargs["attendee_pk"])

    def get_success_url(self):
        return reverse("org:camp_update", args=[self.object.camp.pk])


class CampFinalizeView(ContestAdminRequired, WithCampQuerySet, GenericFormView):
    form_class = Form
    form_title = "Zfinalizovať sústredenie?"
    form_description = "Naozaj chceš zamraziť sústredenie a aktualizovať im levely? Túto akciu nebude možné vrátiť späť."
    form_submit_label = "Zfinalizovať sústredenie"

    def get_breadcrumbs(self):
        return [
            ("Sústredenia", reverse("org:camp_list")),
            (self.camp, ""),
            ("Zfinalizovať", ""),
        ]

    def form_valid(self, form):
        self.camp.is_finalized = True
        self.camp.save()

        self.camp.problem_set.get_rule_engine().close_camp(self.camp)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("org:camp_list")
