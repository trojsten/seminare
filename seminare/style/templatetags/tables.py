from typing import Any, Iterable

from django import template

from seminare.style.tables import Table

register = template.Library()


@register.inclusion_tag("tables/table.html")
def render_table(table: Table, objects: Iterable, hide_header=False, **kwargs):
    if "extra_context" in kwargs and len(kwargs) == 1:
        kwargs = kwargs["extra_context"]

    return {
        "table": table,
        "objects": objects,
        "hide_header": hide_header,
        "extra_context": kwargs,
    }


@register.simple_tag()
def get_label(table: Table, field: str):
    if field in table.labels:
        return table.labels[field]
    return field.title()


@register.simple_tag()
def get_cell(table: Table, field: str, object: Any, extra_context=None):
    if extra_context is None:
        extra_context = {}
    return table.render_field(field, object, extra_context)


@register.simple_tag()
def get_links(table: Table, object: Any, extra_context=None):
    if extra_context is None:
        extra_context = {}
    return table.get_links(object, extra_context)


@register.inclusion_tag("tables/paginator.html", takes_context=True)
def paginator(context, page):
    context["ellipsis"] = page.paginator.ELLIPSIS
    context["pages"] = page.paginator.get_elided_page_range(page.number)
    context["page"] = page
    return context
