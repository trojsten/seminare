from django import template

register = template.Library()


@register.inclusion_tag("_ui/label.html")
def label(message, color="gray", *, icon="", help=""):
    return {"message": message, "color": color, "icon": icon, "help": help}


@register.inclusion_tag("_ui/message.html")
def message(message, type="info", *, icon=""):
    return {"message": message, "type": type, "icon": icon}


MESSAGE_TYPES = {
    "debug": "info",
    "info": "info",
    "success": "success",
    "warning": "warning",
    "error": "error",
}

MESSAGE_ICONS = {
    "info": "mdi:information",
    "success": "mdi:check",
    "warning": "mdi:warning",
    "error": "mdi:cross-circle",
}


@register.inclusion_tag("_ui/messages.html", takes_context=True)
def flash_messages(context):
    items = []

    for message in context.get("messages", []):
        message_type = MESSAGE_TYPES.get(message.level_tag, "info")
        items.append(
            {
                "text": message.message,
                "type": message_type,
                "icon": MESSAGE_ICONS[message_type],
            }
        )

    return {"flash_messages": items}


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
