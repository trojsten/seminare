from functools import cached_property

from django.db.models import Count
from django.forms import Form
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from seminare.camps.models import Camp, CampAttendee
from seminare.contests.utils import get_current_contest
from seminare.organizer.forms import CampAttendeeForm, CampForm
from seminare.organizer.tables import CampAttendeeTable, CampTable
from seminare.organizer.views import MixinProtocol
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormTableView,
    GenericFormView,
    GenericTableView,
)
from seminare.organizer.views.page import PageCreateView
from seminare.users.mixins.permissions import ContestAdminRequired


class WithCampQuerySet(MixinProtocol):
    def get_queryset(self):
        contest = get_current_contest(self.request)

        return Camp.objects.filter(
            problem_set__contest=contest,
        )

    @cached_property
    def camp(self) -> Camp:
        return get_object_or_404(self.get_queryset().filter(pk=self.kwargs["pk"]))


class WithCampAttendeeQuerySet(MixinProtocol):
    def get_queryset(self):
        contest = get_current_contest(self.request)

        return CampAttendee.objects.filter(
            camp__problem_set__contest=contest,
        ).select_related("camp")

    @cached_property
    def attendee(self) -> CampAttendee:
        return get_object_or_404(
            self.get_queryset().filter(
                pk=self.kwargs["attendee_pk"], camp__pk=self.kwargs["camp_pk"]
            )
        )

    @cached_property
    def camp(self) -> Camp:
        return self.attendee.camp

    def get_object(self, queryset=None):
        return self.attendee


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
    form_table_title = "Upraviť sústredenie"
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

    def get_form_table_links(self):
        camp = self.get_object()

        links = [
            (
                "default",
                "mdi:magic",
                "Vytvoriť stŕanku",
                reverse("org:camp_page_create", args=[camp.id]),
            )
        ]

        if not camp.is_finalized:
            links.append(
                (
                    "green",
                    "mdi:plus",
                    "Pridať účastníka",
                    reverse("org:camp_attendee_create", args=[camp.id]),
                )
            )

        return links

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


class CampAttendeeCreateView(
    ContestAdminRequired, WithCampQuerySet, GenericFormView, CreateView
):
    form_title = "Pridať účastníka sústredenia"
    form_class = CampAttendeeForm

    def get_queryset(self):
        return super().get_queryset().filter(is_finalized=False)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["camp"] = self.camp
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Sústredenia", reverse("org:camp_list")),
            (self.camp.name, reverse("org:camp_update", args=[self.camp.pk])),
            ("Pridať účastníka", ""),
        ]

    def get_success_url(self):
        return reverse("org:camp_update", args=[self.camp.pk])


class CampAttendeeUpdateView(
    ContestAdminRequired, WithCampAttendeeQuerySet, GenericFormView, UpdateView
):
    form_title = "Upraviť účastníka sústredenia"
    form_class = CampAttendeeForm

    def get_queryset(self):
        return super().get_queryset().filter(camp__is_finalized=False)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["camp"] = self.camp
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Sústredenia", reverse("org:camp_list")),
            (self.camp.name, reverse("org:camp_update", args=[self.camp.pk])),
            ("Účastníci", ""),
            (
                self.attendee.user.display_name
                if self.attendee.user is not None
                else self.attendee.name,
                "",
            ),
            ("Upraviť", ""),
        ]

    def get_success_url(self):
        return reverse("org:camp_update", args=[self.camp.pk])


class CampAttendeeDeleteView(
    ContestAdminRequired, WithCampAttendeeQuerySet, GenericDeleteView
):
    def get_queryset(self):
        return super().get_queryset().filter(camp__is_finalized=False)

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Sústredenia", reverse("org:camp_list")),
            (self.camp.name, reverse("org:camp_update", args=[self.camp.pk])),
            ("Účastníci", ""),
            (
                self.attendee.user.display_name
                if self.attendee.user is not None
                else self.attendee.name,
                "",
            ),
            ("Odstrániť", ""),
        ]

    def get_success_url(self):
        return reverse("org:camp_update", args=[self.camp.pk])


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
        if not self.camp.problem_set.is_finalized:
            form.add_error(
                None,
                "Sústredenie nemôže byť zfinalizované, pretože sada úloh ešte nie je finalizovaná.",
            )
            return self.form_invalid(form)

        self.camp.is_finalized = True
        self.camp.save()

        self.camp.problem_set.get_rule_engine().close_camp(self.camp)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("org:camp_list")


class CampPageCreateView(ContestAdminRequired, WithCampQuerySet, PageCreateView):
    def get_initial(self):
        initial = super().get_initial()
        initial["title"] = self.camp.name
        initial["slug"] = (
            f"akcie/sustredenia/{self.camp.start_date.strftime('%Y')}/ROCNE_OBDOBIE"
        )

        content = []
        content.append(
            f"## {self.camp.name}, {self.camp.start_date.strftime('%d. %m. %Y')} - {self.camp.end_date.strftime('%d. %m. %Y')}"
        )
        content.append("---")
        content.append("")
        content.append("## Účastníci")
        content.append("")
        content.append("| Meno | Ročník | Škola |")
        content.append("|------|--------|-------|")
        for attendee in self.camp.attendees.select_related(
            "user", "user__current_school"
        ).filter(is_organizer=False):
            if attendee.user is None:
                content.append(f"| {attendee.name} | ? | ? |")
                continue

            user = attendee.user
            school = user.current_school

            school_display = "?"
            if school:
                school_display = f'<abbr data-tippy-content="{school}">{school.short_name if school.short_name else school.name}</abbr>'

            content.append(
                f"| {user.display_name} | {user.get_current_grade_display()} | {school_display} |"
            )
        content.append("")
        content.append("## Vedúci")
        content.append("")
        content.append("| Meno | Škola |")
        content.append("|------|-------|")
        for attendee in self.camp.attendees.select_related(
            "user", "user__current_school"
        ).filter(is_organizer=True):
            if attendee.user is None:
                content.append(f"| {attendee.name} | ? |")
                continue

            user = attendee.user
            school = user.current_school

            school_display = "?"
            if school:
                school_display = f'<abbr data-tippy-content="{school}">{school.short_name if school.short_name else school.name}</abbr>'

            content.append(f"| {user.display_name} | {school_display} |")

        initial["content"] = "\n".join(content)

        return initial
