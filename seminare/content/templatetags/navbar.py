from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from seminare.content.models import MenuGroup, MenuItem

register = template.Library()


@register.inclusion_tag("navbar/menu.html", takes_context=True)
def navbar_menu(context):
    site = get_current_site(context["request"])
    items = list(MenuItem.objects.filter(group__site=site).all())

    context["items"] = items

    user = context["user"]
    if user.is_authenticated:
        group = MenuGroup(id=-1, title=user.display_name)
        logout = MenuItem(
            group=group,
            title="Odhlásiť sa",
            icon="mdi:logout",
            url=reverse("oidc_logout"),
        )
        setattr(logout, "post", True)

        items.extend(
            [
                MenuItem(
                    group=group,
                    title="Môj profil",
                    icon="mdi:user",
                    url="https://id.trojsten.sk/",
                ),
                logout,
            ]
        )

    return context
