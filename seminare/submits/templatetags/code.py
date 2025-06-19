from django import template
from django.db.models.fields.files import FieldFile
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from pygments import highlight as pyg_highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer

from seminare.submits.utils import get_extension

register = template.Library()


@register.simple_tag()
def highlight(file: FieldFile, language: str | None = None):
    try:
        with file.open("r") as f:
            code = f.read()
    except UnicodeDecodeError:
        return mark_safe(render_to_string("public/_protocol_binary.html"))

    if not language:
        language = get_extension(file.name or "").lstrip(".")

    try:
        lexer = get_lexer_by_name(language)
    except ValueError:
        lexer = guess_lexer(code)

    return mark_safe(pyg_highlight(code, lexer, HtmlFormatter(cssclass="codehilite")))
