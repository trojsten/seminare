import os.path
import shutil
from pathlib import PurePath
from typing import IO

from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.http import Http404

from seminare.contests.models import Contest


def resolve_path(contest: Contest, path: str) -> str:
    contest_root: PurePath = contest.data_root
    contest_path: PurePath = PurePath(os.path.normpath(contest_root / path))
    if not contest_path.is_relative_to(contest_root):
        raise PermissionDenied()
    return str(contest_path)


def list_folder(contest: Contest, path: str) -> tuple[list[PurePath], list[PurePath]]:
    cpath = resolve_path(contest, path)
    if not default_storage.exists(cpath):
        if path == "":
            create_folder(contest, path)
        else:
            raise Http404()

    fs_path = default_storage.path(cpath)
    if not os.path.isdir(fs_path):
        raise Http404()

    fs_dirs, fs_files = default_storage.listdir(cpath)

    dirs = [PurePath(cpath) / f for f in fs_dirs]
    dirs.sort()
    files = [PurePath(cpath) / f for f in fs_files]
    files.sort()

    return dirs, files


def create_folder(contest: Contest, path: str) -> None:
    cpath = resolve_path(contest, path)
    fs_path = default_storage.path(cpath)
    os.makedirs(fs_path, exist_ok=True)


def upload_file(contest: Contest, path: str, name: str, file: IO) -> None:
    cpath = resolve_path(contest, str(PurePath(path) / name))

    if default_storage.exists(cpath):
        default_storage.delete(cpath)

    default_storage.save(cpath, file)


def delete_subtree(contest: Contest, path: str) -> None:
    cpath = resolve_path(contest, path)
    fs_path = default_storage.path(cpath)

    if os.path.isdir(fs_path):
        shutil.rmtree(fs_path)
    else:
        default_storage.delete(fs_path)
