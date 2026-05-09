from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def is_past(value):
    return value < timezone.now()


@register.filter
def is_future(value):
    return value > timezone.now()
