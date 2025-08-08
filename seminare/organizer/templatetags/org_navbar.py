from django import template
from django.urls import reverse

from seminare.contests.utils import get_current_contest

register = template.Library()


@register.inclusion_tag("org/_navbar.html", takes_context=True)
def org_navbar(context):
    sections = []

    contest = get_current_contest(context["request"])

    if contest:
        sections.append(
            (
                "Zadania",
                [
                    (
                        "mdi:abacus",
                        "Sady úloh",
                        reverse("org:problemset_list"),
                    ),
                ],
            )
        )

    content_section = [
        (
            "mdi:file-document",
            "Stránky",
            reverse("org:page_list"),
        )
    ]
    if contest:
        content_section.append(("mdi:newspaper", "Príspevky", reverse("org:post_list")))

    if content_section:
        sections.append(("Obsah", content_section))

    return {"menu_sections": sections}
