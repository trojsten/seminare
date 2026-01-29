import filecmp
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Iterable

from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from django.http import FileResponse, HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views.generic import FormView, TemplateView, View

from seminare.organizer.forms import GradingForm, GradingUploadForm
from seminare.organizer.views import (
    MixinProtocol,
    WithBreadcrumbs,
    WithProblem,
    WithSubmit,
)
from seminare.organizer.views.generic import GenericFormView
from seminare.rules import RuleEngine
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.mixins.permissions import ContestOrganizerRequired
from seminare.users.models import Enrollment


class WithSubmitList(WithProblem, MixinProtocol):
    @cached_property
    def rule_engine(self) -> RuleEngine:
        return self.problem.problem_set.get_rule_engine()

    def get_submits(
        self,
        enrollments: Iterable[Enrollment],
        limit_types: Iterable[str] | None = None,
    ) -> dict[int, dict[str, BaseSubmit | None]]:
        """
        Returns one submit of each type for every user.
        Returned as dict [enrollment_id][submit_type]
        """
        submits_user = defaultdict(dict)

        for submit_cls in BaseSubmit.get_submit_types():
            if limit_types and submit_cls.type not in limit_types:
                continue

            submit_objs = self.rule_engine.get_enrollments_problems_effective_submits(
                submit_cls, enrollments, [self.problem]
            ).select_related("scored_by")

            for submit in submit_objs:
                submits_user[submit.enrollment_id][submit_cls.type] = submit

        return submits_user

    def get_users_with_submits(self, limit_types=None):
        data = []
        enrollments = self.rule_engine.get_enrollments().select_related("user")
        submits = self.get_submits(enrollments, limit_types)

        for enrollment in enrollments:
            row: dict = {"user": enrollment.user}
            if not submits[enrollment.id]:
                continue

            row.update(submits[enrollment.id])
            if limit_types and len(limit_types) == 1:
                row["submit"] = submits[enrollment.id].get(limit_types[0])
            data.append(row)

        return data


class GradingOverviewView(
    ContestOrganizerRequired,
    WithSubmitList,
    WithBreadcrumbs,
    TemplateView,
):
    template_name = "org/grading/overview.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem"] = self.problem
        ctx["users"] = self.get_users_with_submits(self.problem.accepted_submit_types)
        ctx["links"] = [
            (
                "default",
                "mdi:human-queue",
                "Hromadné opravovanie",
                reverse(
                    "org:bulk_grading",
                    args=[self.problem_set.slug, self.problem.number],
                ),
            )
        ]
        return ctx

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list")),
            (self.problem.problem_set, ""),
            (
                "Úlohy",
                reverse(
                    "org:problem_list",
                    args=[self.problem.problem_set.slug],
                ),
            ),
            (self.problem, ""),
            ("Opravovanie", ""),
        ]


class GradingSubmitView(ContestOrganizerRequired, WithSubmit, WithSubmitList, FormView):
    template_name = "org/grading/submit.html"
    form_class = GradingForm

    @cached_property
    def problem(self):
        return self.submit.problem

    def get_other_submits(self):
        submit_cls = self.submit.__class__
        submits = submit_cls.objects.filter(
            enrollment=self.submit.enrollment, problem=self.submit.problem
        )
        deadlines = self.rule_engine.get_important_dates()

        out = []
        for deadline, label in deadlines:
            out.append({"type": "deadline", "time": deadline, "label": label})
        for submit in submits:
            out.append(
                {
                    "type": "submit",
                    "time": submit.created_at,
                    "submit": submit,
                }
            )

        out.sort(key=lambda x: x["time"])

        return out

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["other_submits"] = self.get_other_submits()
        ctx["other_users"] = self.get_users_with_submits([self.submit.type])
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial["score"] = self.submit.score
        initial["comment"] = self.submit.comment
        return initial

    def form_valid(self, form):
        if "comment_file" in form.cleaned_data and self.submit.type == FileSubmit.type:
            assert isinstance(self.submit, FileSubmit)
            self.submit.comment_file = form.cleaned_data.get("comment_file")

        self.submit.comment = form.cleaned_data.get("comment")
        self.submit.score = form.cleaned_data.get("score")
        self.submit.scored_by = self.request.user
        self.submit.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "org:grading_submit",
            args=[
                self.submit.problem.problem_set.slug,
                self.submit.problem.number,
                self.submit.submit_id,
            ],
        )


class BulkGradingView(ContestOrganizerRequired, WithSubmitList, GenericFormView):
    form_class = GradingUploadForm
    form_title = "Hromadné opravovanie"
    form_description = mark_safe(
        "Hromadné opravovanie funguje tak, že si stiahneš ZIP so všetkými riešeniami a pozeráš si ich lokálne. Keď niektoré riešenie opravíš, zapíšeš komentár a body do príslušných súborov <code>komentar.txt</code> a <code>body.txt</code> v priečinku riešiteľa. Poprípade môžeš aj nahrať upravený súbor s riešením a komentárom tak, že mu zmeníš príponu z <code>.pdf</code> na <code>.komentar.pdf</code>."
    )
    form_header_template = "org/grading/_bulk_header.html"
    form_multipart = True

    def form_valid(self, form):
        enrollments = self.rule_engine.get_enrollments().select_related("user")

        submits = self.get_submits(enrollments)

        with zipfile.ZipFile(form.cleaned_data["file"]) as zip_file:
            for file_info in zip_file.infolist():
                if not file_info.is_dir():
                    folder, file_name = file_info.filename.split("/")[:2]
                    user_id = int(folder.split("-")[-1])
                    submit = submits[user_id].get("file")

                    if submit is None:
                        continue

                    assert isinstance(submit, FileSubmit)

                    if not submit:
                        continue

                    if file_name == "body.txt":
                        score = float(zip_file.read(file_info).decode("utf-8").strip())
                        if score == submit.score:
                            continue

                        submit.score = score
                        submit.scored_by = self.request.user
                        submit.save(update_fields=["score", "scored_by"])
                    elif file_name == "komentar.txt":
                        comment = zip_file.read(file_info).decode("utf-8").strip()
                        if comment == submit.comment:
                            continue

                        submit.comment = comment
                        submit.scored_by = self.request.user
                        submit.save(update_fields=["comment", "scored_by"])
                    elif file_name.split(".")[-2] == "komentar":
                        assert isinstance(submit.comment_file, FieldFile)

                        if submit.comment_file and filecmp.cmp(
                            submit.comment_file.path,
                            zip_file.open(file_info).read(),
                            shallow=False,
                        ):
                            continue

                        raw_data = zip_file.read(file_info)

                        submit.comment_file.save(
                            file_name,
                            ContentFile(raw_data),
                            save=True,
                        )
                        submit.scored_by = self.request.user
                        submit.save(update_fields=["comment_file", "scored_by"])

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["problem"] = self.problem
        return ctx

    def get_form_links(self):
        return [
            (
                "default",
                "mdi:download",
                "Stiahnuť ZIP na opravovanie",
                reverse(
                    "org:bulk_grading_download",
                    args=[self.problem_set.slug, self.problem.number],
                ),
            )
        ]

    def get_success_url(self):
        return reverse(
            "org:grading_overview", args=[self.problem_set.slug, self.problem.number]
        )

    def get_breadcrumbs(self):
        return [
            ("Sady úloh", reverse("org:problemset_list")),
            (self.problem.problem_set, ""),
            (
                "Úlohy",
                reverse(
                    "org:problem_list",
                    args=[self.problem.problem_set.slug],
                ),
            ),
            (self.problem, ""),
            (
                "Opravovanie",
                reverse(
                    "org:grading_overview",
                    args=[self.problem_set.slug, self.problem.number],
                ),
            ),
            ("Hromadné opravovanie", ""),
        ]


class BulkGradingDownloadView(ContestOrganizerRequired, WithSubmitList, View):
    def get(self, request, *args, **kwargs):
        enrollments = self.rule_engine.get_enrollments().select_related("user")
        enrollments_by_id = {enrollment.id: enrollment for enrollment in enrollments}

        zip_buffer = BytesIO()

        with zipfile.ZipFile(
            zip_buffer, "w", compression=zipfile.ZIP_DEFLATED
        ) as zip_file:
            i = 0
            for enrollment_id, data in self.get_submits(enrollments).items():
                enrollment = enrollments_by_id[enrollment_id]
                user_name = slugify(enrollment.user.display_name)
                zip_path = f"{i:03d}-{user_name}-{enrollment.id}/"
                for type, submit in data.items():
                    if type == "file":
                        assert isinstance(submit, FileSubmit)
                        path = submit.file.path
                        zip_file.write(
                            path, f"{zip_path}{user_name}{Path(path).suffix}"
                        )
                        if submit.comment_file:
                            path = submit.file.path
                            zip_file.write(
                                path,
                                f"{zip_path}{user_name}.komentar{Path(path).suffix}",
                            )
                        if submit.score is not None:
                            zip_file.writestr(
                                f"{zip_path}body.txt",
                                f"{submit.score}",
                            )
                        if submit.comment:
                            zip_file.writestr(f"{zip_path}komentar.txt", submit.comment)
                    elif type == "judge":
                        assert isinstance(submit, JudgeSubmit)
                        path = submit.program.path
                        zip_file.write(path, f"{zip_path}judge{Path(path).suffix}")
                    elif type == "text":
                        assert isinstance(submit, TextSubmit)
                        zip_file.writestr(
                            f"{zip_path}answer.txt",
                            submit.value,
                        )
                i += 1

        zip_buffer.seek(0)

        return FileResponse(
            zip_buffer,
            as_attachment=True,
            filename=f"{self.problem.name}.zip",
        )
