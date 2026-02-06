from django.core.files.storage import default_storage
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from seminare.content.models import Page
from seminare.problems.models import Problem, ProblemSet
from seminare.style.tables import Table
from seminare.users.models import ContestRole


class ProblemSetTable(Table):
    fields = [
        "name",
        "start_date",
        "end_date",
    ]

    labels = {
        "name": "Názov",
        "start_date": "Začiatok",
        "end_date": "Koniec",
    }

    templates = {
        "start_date": "tables/fields/date.html",
        "end_date": "tables/fields/date.html",
    }

    def get_links(
        self, object: ProblemSet, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        links = [
            (
                "mdi:cards",
                "Úlohy",
                reverse("org:problem_list", args=[object.slug]),
            ),
        ]

        if context["is_contest_administrator"]:
            links.append(
                (
                    "mdi:pencil",
                    "Upraviť",
                    reverse("org:problemset_update", args=[object.slug]),
                ),
            )

        return links


class ProblemTable(Table):
    fields = [
        "number",
        "name",
    ]

    labels = {
        "name": "Názov",
        "number": "č.",
    }

    def get_links(
        self, object: Problem, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        links = [
            (
                "mdi:comment-arrow-left",
                "Opravovanie",
                reverse(
                    "org:grading_overview",
                    args=[
                        object.problem_set.slug,
                        object.number,
                    ],
                ),
            ),
        ]
        if context["is_contest_administrator"]:
            links.append(
                (
                    "mdi:pencil",
                    "Upraviť",
                    reverse(
                        "org:problem_update",
                        args=[
                            object.problem_set.slug,
                            object.number,
                        ],
                    ),
                ),
            )
        return links


class PageTable(Table):
    fields = ["slug", "title"]
    labels = {"slug": "URL adresa", "title": "Názov"}

    def get_links(
        self, object: Page, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        return [
            ("mdi:eye", "Pozrieť", reverse("page_detail", args=[object.slug])),
            ("mdi:pencil", "Upraviť", reverse("org:page_update", args=[object.id])),
            ("mdi:delete", "Vymazať", reverse("org:page_delete", args=[object.id])),
        ]


class PostTable(Table):
    fields = ["title", "created_at", "author"]
    labels = {
        "title": "Nadpis",
        "created_at": "Dátum vytvorenia",
        "author": "Autor",
    }
    templates = {"created_at": "tables/fields/datetime.html"}

    def get_links(
        self, object: Page, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        return [
            (
                "mdi:pencil",
                "Upraviť",
                reverse("org:post_update", args=[object.id]),
            ),
            (
                "mdi:delete",
                "Vymazať",
                reverse("org:post_delete", args=[object.id]),
            ),
        ]


class FileTable(Table):
    fields = ["icon", "name"]
    labels = {"icon": "", "name": "Názov"}

    def get_icon_content(self, object):
        if object["is_dir"]:
            return mark_safe("<iconify-icon icon='mdi:folder'></iconify-icon>")
        return mark_safe("<iconify-icon icon='mdi:file'></iconify-icon>")

    def get_name_content(self, object):
        return object["file"].name

    def get_links(
        self, object: dict, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        links = []

        path_query = "?" + urlencode({"path": str(object["rel"])})
        if object["is_dir"]:
            links.append(
                ("mdi:folder-open", "Otvoriť", reverse("org:file_list") + path_query)
            )
        else:
            links.append(
                ("mdi:download", "Stiahnuť", default_storage.url(object["file"]))
            )
        links.append(("mdi:delete", "Vymazať", reverse("org:file_delete") + path_query))
        return links


class RoleTable(Table):
    fields = ["user", "role"]
    labels = {"user": "Používateľ", "role": "Rola"}

    templates = {"user": "tables/fields/user.html"}

    def get_role_content(self, object: ContestRole):
        return object.get_role_display()
        return {
            ContestRole.Role.ORGANIZER: "Organizátor",
            ContestRole.Role.ADMINISTRATOR: "Administrátor",
        }.get(object.role, "?")

    def get_links(
        self, object: ContestRole, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        return [
            # ("mdi:eye", "Pozrieť", reverse("page_detail", args=[object.slug])),
            ("mdi:pencil", "Upraviť", reverse("org:role_update", args=[object.id])),
            ("mdi:delete", "Vymazať", reverse("org:role_delete", args=[object.id])),
        ]
