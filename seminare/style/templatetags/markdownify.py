from django import template
from django.core.files.storage import default_storage
from django.utils.safestring import mark_safe
from markdown import markdown

from seminare.contests.models import Contest
from seminare.problems.models import Problem
from seminare.style.markdown_extensions import SeminareExtension

register = template.Library()


@register.filter
def markdownify(content, obj=None):
    url_root = None
    if isinstance(obj, Contest):
        url_root = default_storage.url(str(obj.data_root))
    if isinstance(obj, Problem):
        url_root = default_storage.url(str(obj.get_data_root(absolute=True)))

    return mark_safe(
        markdown(
            content,
            extensions=[
                "abbr",
                "admonition",
                "attr_list",
                "fenced_code",
                "footnotes",
                "md_in_html",
                "sane_lists",
                "tables",
                "smarty",
                SeminareExtension(image_root=url_root),
            ],
        )
    )
