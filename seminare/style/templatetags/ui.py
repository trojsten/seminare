from django import template

register = template.Library()


@register.inclusion_tag("_ui/label.html")
def label(message, color="gray", *, icon="", help=""):
    return {"message": message, "color": color, "icon": icon, "help": help}


@register.inclusion_tag("_ui/message.html")
def message(message, type="info"):
    return {"message": message, "type": type}


@register.inclusion_tag("_ui/breadcrumbs.html")
def breadcrumbs(*args):
    if isinstance(args[0], list):
        return {"crumbs": args[0]}

    crumbs = []
    for i in range(0, len(args), 2):
        crumbs.append(args[i : i + 2])

    return {"crumbs": crumbs}


@register.inclusion_tag("_ui/org_breadcrumbs.html")
def org_breadcrumbs(*args):
    return breadcrumbs(*args)
