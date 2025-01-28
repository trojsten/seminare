from django import template

register = template.Library()


@register.inclusion_tag("_ui/label.html")
def label(message, color="gray", *, icon="", help=""):
    return {"message": message, "color": color, "icon": icon, "help": help}


@register.inclusion_tag("_ui/breadcrumbs.html")
def breadcrumbs(*args):
    crumbs = []
    for i in range(0, len(args), 2):
        crumbs.append(args[i : i + 2])

    return {"crumbs": crumbs}
