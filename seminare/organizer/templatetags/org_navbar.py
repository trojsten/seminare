from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from seminare.contests.models import Contest

register = template.Library()


@register.inclusion_tag("org/_navbar.html", takes_context=True)
def org_navbar(context):
    sections = []

    site = get_current_site(context["request"])
    contest = Contest.objects.filter(site=site).first()

    if contest:
        sections.append(
            (
                "Zadania",
                [
                    (
                        "mdi:abacus",
                        "Sady úloh",
                        reverse("org:problemset_list", args=[contest.id]),
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
        content_section.append(
            ("mdi:newspaper", "Príspevky", reverse("org:post_list", args=[contest.id]))
        )

    if content_section:
        sections.append(("Obsah", content_section))

    return {"menu_sections": sections}
