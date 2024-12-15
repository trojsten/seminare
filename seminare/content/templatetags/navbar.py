from django import template
from django.contrib.sites.shortcuts import get_current_site

from seminare.content.models import MenuItem

register = template.Library()


@register.inclusion_tag("navbar/menu.html", takes_context=True)
def navbar_menu(context):
    site = get_current_site(context["request"])
    items = MenuItem.objects.filter(group__site=site)

    return {
        "items": items,
    }
