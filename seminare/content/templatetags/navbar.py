from django import template
from django.urls import reverse

from seminare.content.models import MenuGroup, MenuItem
from seminare.contests.utils import get_current_contest
from seminare.users.logic.permissions import is_contest_organizer

register = template.Library()


@register.inclusion_tag("navbar/menu.html", takes_context=True)
def navbar_menu(context):
    contest = get_current_contest(context["request"])
    items = list(
        MenuItem.objects.filter(group__contest=contest).select_related("group").all()
    )

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

        if is_contest_organizer(user, contest):
            items.append(
                MenuItem(
                    group=group,
                    title="Organizátorské rozhranie",
                    icon="mdi:account-tie",
                    url=reverse("org:contest_dashboard"),
                )
            )

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
