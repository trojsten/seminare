from django.urls import reverse

from seminare.content.models import Page
from seminare.problems.models import Problem, ProblemSet
from seminare.style.tables import Table


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
                reverse("org:problem_list", args=[object.id]),
            ),
        ]

        if context["is_contest_administrator"]:
            links.append(
                (
                    "mdi:pencil",
                    "Upraviť",
                    reverse("org:problemset_update", args=[object.id]),
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
                    args=[object.id],
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
                            object.problem_set_id,
                            object.id,
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
