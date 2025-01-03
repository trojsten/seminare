from django.urls import reverse

from seminare.problems.models import ProblemSet
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

    def get_links(
        self, object: ProblemSet, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        return [
            (
                "mdi:pencil",
                "Upraviť",
                reverse("org:problemset_update", args=[object.contest_id, object.id]),
            )
        ]
