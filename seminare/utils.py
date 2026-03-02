import gzip
import json
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import FileResponse, HttpResponse
from django.template.loader import render_to_string

from seminare.contests.models import Contest


def compress_data(data: dict) -> bytes:
    return gzip.compress(json.dumps(data).encode("utf-8"))


def decompress_data(data: bytes) -> dict:
    return json.loads(gzip.decompress(data).decode("utf-8"))


def sendfile(filename: str | Path, as_attachement: bool = False):
    filename = str(filename)

    if settings.DEBUG:
        return FileResponse(open(filename, "rb"), as_attachment=as_attachement)

    response = HttpResponse()
    response["X-Sendfile"] = filename
    if as_attachement:
        response["X-Sendfile-As-Attachment"] = True
    return response


def send_mail(
    emails: list[str],
    subject: str,
    template_name: str,
    contest: Contest,
    context: dict = {},
    reply_to: list[str] | None = None,
):
    context["contest"] = contest

    text_content = render_to_string(f"emails/{template_name}.txt", context)
    html_content = render_to_string(f"emails/{template_name}.html", context)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        f"{contest.name} <noreply@trojsten.sk>",
        emails,
        reply_to=reply_to if reply_to is not None else [contest.contact_email],
    )

    email.attach_alternative(html_content, "text/html")

    email.send()
