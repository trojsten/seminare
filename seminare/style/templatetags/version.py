from django import template

import seminare

register = template.Library()


@register.simple_tag()
def version():
    return seminare.VERSION
