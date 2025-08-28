import os.path

from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from rest_framework.response import Response
from rest_framework.views import APIView

from seminare.contests.utils import get_current_contest
from seminare.organizer.file_utils import (
    delete_subtree,
    list_folder,
    resolve_path,
    upload_file,
)


class FileAPIView(APIView):
    def get(self, request, path=""):
        contest = get_current_contest(request)

        cpath = resolve_path(contest, path)
        fs_path = default_storage.path(cpath)
        if os.path.isfile(fs_path):
            return HttpResponseRedirect(default_storage.url(cpath))

        dirs, files = list_folder(contest, path)
        dirs = [f.name for f in dirs]
        files = [f.name for f in files]
        return Response({"folders": dirs, "files": files})

    def post(self, request, path=""):
        if "file" not in request.data:
            return Response({"error": "Provide a file."}, status=400)

        name = request.data.get("name", request.data["file"].name)

        contest = get_current_contest(request)
        upload_file(contest, path, name, request.data["file"])
        return Response({"ok": True})

    def delete(self, request, path):
        contest = get_current_contest(request)
        delete_subtree(contest, path)
        return Response({"ok": True})
