from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("org/_navbar.html", takes_context=True)
def org_navbar(context):
    sections = []

    sections.append(
        (
            "Section",
            [
                ("mdi:home", "Test", "#"),
                (
                    "mdi:abacus",
                    "Sady úloh",
                    reverse("org:problemset_list", args=[context.get("contest").id]),
                ),
            ],
        )
    )

    return {"menu_sections": sections}
