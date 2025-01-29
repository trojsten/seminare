from django.urls import reverse

from seminare.content.models import MenuGroup
from seminare.style.tables import Table


class MenuTable(Table):
    fields = [
        "title",
    ]

    labels = {
        "title": "Názov",
    }

    def get_links(
        self, object: MenuGroup, context: dict
    ) -> list[tuple[str, str] | tuple[str, str, str]]:
        return [
            (
                "mdi:delete",
                "Vymazať",
                reverse("menu_delete", args=[object.id])
                + "?return="
                + reverse("menu_list"),
            )
        ]
