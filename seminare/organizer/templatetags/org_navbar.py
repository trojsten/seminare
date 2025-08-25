from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("org/_navbar.html")
def org_navbar():
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

    return {"menu_sections": sections}
