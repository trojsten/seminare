import gzip
import json
from pathlib import Path

from django.http import FileResponse, HttpResponse

from seminare import settings


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
