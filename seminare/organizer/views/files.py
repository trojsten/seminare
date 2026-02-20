from pathlib import PurePath

from django.forms import Form
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlencode

from seminare.organizer.file_utils import (
    create_folder,
    delete_subtree,
    list_folder,
    resolve_path,
    upload_file,
)
from seminare.organizer.forms import FileUploadForm, NewFolderForm
from seminare.organizer.tables import FileTable
from seminare.organizer.views import WithContest
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormView,
    GenericTableView,
)
from seminare.users.mixins.permissions import ContestOrganizerRequired


class FileListView(ContestOrganizerRequired, WithContest, GenericTableView):
    table_title = "Správa súborov"
    table_class = FileTable

    def get_table_links(self):
        path = "?" + urlencode({"path": self.request.GET.get("path", "")})
        return [
            (
                "green",
                "mdi:folder-plus",
                "Priečinok",
                reverse("org:file_new_folder") + path,
            ),
            (
                "green",
                "mdi:upload",
                "Súbor",
                reverse("org:file_upload") + path,
            ),
        ]

    def get_queryset(self):  # pyright: ignore
        # Yeah, this is not exactly a QuerySet, but it is passed right to the FileTable.
        path = self.request.GET.get("path", "")
        cpath = PurePath(resolve_path(self.contest, path))
        dirs, files = list_folder(self.contest, self.request.GET.get("path", ""))
        root = self.contest.data_root

        rows = []
        if cpath != root:
            rows.append(
                {
                    "file": cpath.parent.with_name(".."),
                    "is_dir": True,
                    "rel": cpath.parent.relative_to(root),
                }
            )

        rows += [{"file": f, "is_dir": True, "rel": f.relative_to(root)} for f in dirs]
        rows += [
            {"file": f, "is_dir": False, "rel": f.relative_to(root)} for f in files
        ]
        return rows


class NewFolderView(ContestOrganizerRequired, WithContest, GenericFormView):
    form_class = NewFolderForm
    form_title = "Nový priečinok"

    def form_valid(self, form) -> HttpResponse:
        path = PurePath(self.request.GET.get("path", ""))
        create_folder(self.contest, str(path / form.cleaned_data["name"]))
        return HttpResponseRedirect(
            reverse("org:file_list") + "?" + urlencode({"path": str(path)})
        )


class FileUploadView(ContestOrganizerRequired, WithContest, GenericFormView):
    form_class = FileUploadForm
    form_title = "Nahrať súbor"
    form_multipart = True

    def form_valid(self, form) -> HttpResponse:
        path = self.request.GET.get("path", "")
        name = form.cleaned_data["file"].name
        if form.cleaned_data["name"]:
            name = form.cleaned_data["name"]

        upload_file(self.contest, path, name, form.cleaned_data["file"])
        return HttpResponseRedirect(
            reverse("org:file_list") + "?" + urlencode({"path": path})
        )


class FileDeleteView(ContestOrganizerRequired, WithContest, GenericDeleteView):
    form_class = Form

    def get_object(self, queryset=None):
        return self.request.GET.get("path")

    def form_valid(self, form) -> HttpResponse:
        delete_subtree(self.contest, self.request.GET.get("path", ""))
        path = PurePath(self.request.GET.get("path", ""))
        return HttpResponseRedirect(
            reverse("org:file_list") + "?" + urlencode({"path": str(path.parent)})
        )
