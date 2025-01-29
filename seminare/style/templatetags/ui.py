from django import template

register = template.Library()


@register.inclusion_tag("_ui/label.html")
def label(message, color="gray", *, icon="", help=""):
    return {"message": message, "color": color, "icon": icon, "help": help}
