from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from seminare.contests.utils import get_current_contest
from seminare.organizer.forms import RoleForm
from seminare.organizer.tables import RoleTable
from seminare.organizer.views import MixinProtocol
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormView,
    GenericTableView,
)
from seminare.users.mixins.permissions import ContestAdminRequired
from seminare.users.models import ContestRole


class WithRoleQuerySet(MixinProtocol):
    def get_queryset(self):
        contest = get_current_contest(self.request)
        return ContestRole.objects.filter(contest=contest)


class RoleListView(ContestAdminRequired, WithRoleQuerySet, GenericTableView):
    table_title = "Zoznam organizátorov"
    table_class = RoleTable
    table_links = [("green", "mdi:plus", "Pridať", reverse_lazy("org:role_create"))]

    def get_queryset(self):
        return super().get_queryset().order_by("-role")

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Organizátori", "")]


class RoleUpdateView(
    ContestAdminRequired, WithRoleQuerySet, GenericFormView, UpdateView
):
    form_title = "Upraviť organizátora"
    form_class = RoleForm
    success_url = reverse_lazy("org:role_list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["contest"] = get_current_contest(self.request)
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Organizátori", reverse("org:role_list")),
            (self.object.user.display_name, ""),
            ("Upraviť", ""),
        ]


class RoleCreateView(ContestAdminRequired, GenericFormView, CreateView):
    form_title = "Nový organizátor"
    form_class = RoleForm
    success_url = reverse_lazy("org:role_list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["contest"] = get_current_contest(self.request)
        return kw

    def get_initial(self):
        initial = super().get_initial()
        if self.kwargs.get("slug"):
            initial["slug"] = self.kwargs["slug"]
        return initial

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Organizátori", reverse("org:role_list")),
            ("Nový", ""),
        ]


class RoleDeleteView(ContestAdminRequired, WithRoleQuerySet, GenericDeleteView):
    success_url = reverse_lazy("org:role_list")

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Organizátori", reverse("org:role_list")),
            (self.object.user.display_name, ""),
            ("Vymazať", ""),
        ]
