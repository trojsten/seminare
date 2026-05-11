from django import template

from seminare.content.models import Post
from seminare.contests.utils import get_current_contest

register = template.Library()


@register.inclusion_tag("post/_overview.html", takes_context=True)
def posts_overview(context):
    contest = get_current_contest(context["request"])

    context["posts"] = Post.objects.filter(contests__id=contest.id).select_related(
        "author"
    )[:3]

    return context
