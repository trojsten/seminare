from django.db.models import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from seminare.content.models import MenuGroup, MenuItem
from seminare.contests.utils import get_current_contest
from seminare.organizer.forms import MenuGroupForm, MenuItemForm
from seminare.organizer.tables import MenuGroupTable, MenuItemTable
from seminare.organizer.views import MixinProtocol, WithMenuGroup, WithMenuItem
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormTableView,
    GenericFormView,
    GenericTableView,
)
from seminare.users.mixins.permissions import ContestAdminRequired


class WithMenuGroupQuerySet(MixinProtocol):
    def get_queryset(self):
        contest = get_current_contest(self.request)
        return MenuGroup.objects.filter(contest=contest)


class WithMenuItemQuerySet(MixinProtocol):
    def get_queryset(self):
        contest = get_current_contest(self.request)
        return MenuItem.objects.filter(group__contest=contest)


class MenuGroupListView(ContestAdminRequired, WithMenuGroupQuerySet, GenericTableView):
    table_title = "Zoznam skupín menu"
    table_class = MenuGroupTable
    table_links = [
        ("green", "mdi:plus", "Pridať", reverse_lazy("org:menu_group_create"))
    ]

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Menu", "")]


class MenuGroupUpdateView(
    ContestAdminRequired, WithMenuGroup, GenericFormTableView, UpdateView
):
    form_table_title = "Upraviť menu skupinu"
    form_class = MenuGroupForm
    table_class = MenuItemTable
    success_url = reverse_lazy("org:menu_group_list")

    def get_object(self, queryset=None):
        return self.menu_group

    def get_queryset(self) -> QuerySet[MenuItem]:
        return MenuItem.objects.filter(group=self.menu_group)

    def get_form_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať položku",
                reverse("org:menu_item_create", args=[self.object.id]),
            )
        ]

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["contest"] = get_current_contest(self.request)
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Menu", reverse("org:menu_group_list")),
            (self.object.title, ""),
            ("Upraviť skupinu", ""),
        ]


class MenuGroupCreateView(ContestAdminRequired, GenericFormView, CreateView):
    form_title = "Nová menu skupina"
    form_class = MenuGroupForm
    success_url = reverse_lazy("org:menu_group_list")

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
            ("Menu", reverse("org:menu_group_list")),
            ("Nová skupina", ""),
        ]


class MenuGroupDeleteView(
    ContestAdminRequired, WithMenuGroupQuerySet, GenericDeleteView
):
    success_url = reverse_lazy("org:menu_group_list")

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Menu", reverse("org:menu_group_list")),
            (self.object.title, ""),
            ("Vymazať skupinu", ""),
        ]


class MenuItemListView(ContestAdminRequired, WithMenuGroup, GenericTableView):
    table_title = "Zoznam položiek menu"
    table_class = MenuItemTable

    def get_queryset(self):
        return MenuItem.objects.filter(group=self.menu_group)

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Menu", reverse("org:menu_group_list")),
            (self.menu_group.title, ""),
            ("Položky", ""),
        ]

    def get_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať položku",
                reverse("org:menu_item_create", args=[self.menu_group.id]),
            )
        ]


class MenuItemUpdateView(
    ContestAdminRequired, WithMenuItem, GenericFormView, UpdateView
):
    form_table_title = "Upraviť položku menu"
    form_class = MenuItemForm

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["group"] = self.menu_group
        return kw

    def get_object(self, queryset=None):
        return self.menu_item

    def get_success_url(self):
        return reverse("org:menu_item_list", args=[self.menu_group.id])

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Menu", reverse("org:menu_group_list")),
            (self.menu_group.title, ""),
            ("Položky", reverse("org:menu_item_list", args=[self.menu_group.id])),
            (self.menu_item.title, ""),
            ("Upraviť položku", ""),
        ]


class MenuItemCreateView(
    ContestAdminRequired, WithMenuGroup, GenericFormView, CreateView
):
    form_title = "Nová položka menu"
    form_class = MenuItemForm

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["group"] = self.menu_group
        return kw

    def get_success_url(self):
        return reverse("org:menu_item_list", args=[self.menu_group.id])

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Menu", reverse("org:menu_group_list")),
            (self.menu_group.title, ""),
            ("Položky", reverse("org:menu_item_list", args=[self.menu_group.id])),
            ("Nová položka", ""),
        ]


class MenuItemDeleteView(ContestAdminRequired, WithMenuItem, GenericDeleteView):
    def get_object(self, queryset=None):
        return self.menu_item

    def get_success_url(self):
        return reverse("org:menu_item_list", args=[self.menu_group.id])

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Menu", reverse("org:menu_group_list")),
            (self.object.title, ""),
            ("Položky", reverse("org:menu_item_list", args=[self.menu_group.id])),
            (self.menu_item.title, ""),
            ("Vymazať položku", ""),
        ]
