from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import MultipleObjectsReturned
from django.urls import reverse

from seminare.contests.models import Contest

register = template.Library()


@register.inclusion_tag("org/_navbar.html", takes_context=True)
def org_navbar(context):
    sections = []

    contest_id = None
    if hasattr(context["request"], "resolver_match"):
        contest_id = context["request"].resolver_match.kwargs.get("contest_id")

    site = get_current_site(context["request"])
    if not contest_id:
        try:
            contest = Contest.objects.get(site=site)
        except (Contest.DoesNotExist, MultipleObjectsReturned):
            contest = None
    else:
        contest = Contest.objects.filter(id=contest_id, site=site).first()

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

    if content_section:
        sections.append(("Obsah", content_section))

    return {"menu_sections": sections}
