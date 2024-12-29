from django import template

register = template.Library()


@register.inclusion_tag("org/_navbar.html", takes_context=True)
def org_navbar(context):
    sections = []

    sections.append(
        (
            "Section",
            [
                ("mdi:home", "Test", "#"),
            ],
        )
    )

    return {"menu_sections": sections}
