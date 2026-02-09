from django import template
from django.urls import reverse

from seminare.contests.utils import get_current_contest
from seminare.users.logic.permissions import is_contest_administrator

register = template.Library()


@register.inclusion_tag("org/_navbar.html", takes_context=True)
def org_navbar(context):
    contest = get_current_contest(context["request"])
    user = context["user"]

    content_section = [
        (
            "mdi:file-document",
            "Stránky",
            reverse("org:page_list"),
        ),
        ("mdi:newspaper", "Príspevky", reverse("org:post_list")),
        ("mdi:folder", "Súbory", reverse("org:file_list")),
    ]

    sections = [
        (
            "Zadania",
            [
                (
                    "mdi:abacus",
                    "Sady úloh",
                    reverse("org:problemset_list"),
                ),
            ],
        ),
        ("Obsah", content_section),
    ]

    if is_contest_administrator(user, contest):
        sections.append(
            (
                "Správa",
                [
                    (
                        "mdi:account-tie",
                        "Organizátori",
                        reverse("org:role_list"),
                    ),
                    (
                        "mdi:hamburger-menu",
                        "Navigácia",
                        reverse("org:menu_group_list"),
                    ),
                ],
            )
        )

    return {"menu_sections": sections}
