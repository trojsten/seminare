from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from seminare.content.models import Page
from seminare.organizer.forms import PageForm
from seminare.organizer.tables import PageTable
from seminare.organizer.views import MixinProtocol
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormView,
    GenericTableView,
)
from seminare.users.mixins.permissions import ContestOrganizerRequired


class WithPageQuerySet(MixinProtocol):
    def get_queryset(self):
        site = get_current_site(self.request)
        return Page.objects.filter(contest__site=site)


class PageListView(ContestOrganizerRequired, WithPageQuerySet, GenericTableView):
    table_title = "Zoznam stránok"
    table_class = PageTable
    table_links = [("green", "mdi:plus", "Pridať", reverse_lazy("org:page_create"))]

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Stránky", "")]


class PageUpdateView(
    ContestOrganizerRequired, WithPageQuerySet, GenericFormView, UpdateView
):
    form_title = "Upraviť stránku"
    form_class = PageForm
    success_url = reverse_lazy("org:page_list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["site"] = get_current_site(self.request)
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Stránky", reverse("org:page_list")),
            (self.object, ""),
            ("Upraviť", ""),
        ]


class PageCreateView(ContestOrganizerRequired, GenericFormView, CreateView):
    form_title = "Nová stránka"
    form_class = PageForm
    success_url = reverse_lazy("org:page_list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["site"] = get_current_site(self.request)
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Stránky", reverse("org:page_list")),
            ("Nová", ""),
        ]


class PageDeleteView(ContestOrganizerRequired, WithPageQuerySet, GenericDeleteView):
    success_url = reverse_lazy("org:page_list")

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Stránky", reverse("org:page_list")),
            (self.object, ""),
            ("Vymazať", ""),
        ]
