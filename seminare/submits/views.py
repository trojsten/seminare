import json
import os.path
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, View
from django.views.generic.edit import FormView

from seminare import settings
from seminare.problems.models import Problem
from seminare.submits.forms import FileFieldForm, JudgeSubmitForm, TextSubmitForm
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.submits.utils import combine_images_into_pdf, enqueue_judge_submit
from seminare.users.logic.enrollment import get_enrollment
from seminare.users.mixins.permissions import ContestOrganizerRequired


class SubmitCreateView(FormView):
    submit: BaseSubmit

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to perform this action.")
        self.problem = get_object_or_404(Problem, id=kwargs["problem"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.submit.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("submit_detail", args=[self.submit.submit_id])


class FileSubmitCreateView(SubmitCreateView):
    form_class = FileFieldForm

    def form_valid(self, form):
        files = form.cleaned_data["files"]
        final_file = files[0]
        _, ext = os.path.splitext(files[0].name)
        if len(files) > 1 or ext.lower() in {".jpg", ".jpeg", ".png"}:
            final_file = combine_images_into_pdf(files)

        self.submit = FileSubmit(
            file=final_file,
            problem=self.problem,
            enrollment=get_enrollment(self.request.user, self.problem.problem_set),
        )

        return super().form_valid(form)


class JudgeSubmitCreateView(SubmitCreateView):
    form_class = JudgeSubmitForm

    def form_valid(self, form):
        program = form.cleaned_data["program"]

        submit = enqueue_judge_submit(
            self.problem.judge_namespace,
            self.problem.judge_task,
            self.request.user,
            program,
        )

        self.submit = JudgeSubmit(
            program=program,
            problem=self.problem,
            judge_id=submit.public_id,
            protocol_key=submit.protocol_key,
            enrollment=get_enrollment(self.request.user, self.problem.problem_set),
        )

        return super().form_valid(form)


class TextSubmitCreateView(SubmitCreateView):
    form_class = TextSubmitForm

    def form_valid(self, form):
        text = form.cleaned_data["text"]

        self.submit = TextSubmit(
            value=text,
            problem=self.problem,
            enrollment=get_enrollment(self.request.user, self.problem.problem_set),
        )

        return super().form_valid(form)


class SubmitDetailView(ContestOrganizerRequired, DetailView):
    context_object_name = "submit"
    template_name = "submits/detail.html"

    def check_access(self) -> bool:
        submit = self.get_object()
        if submit is None:
            return False

        return submit.enrollment.user == self.request.user or super().check_access()

    def get_object(self, queryset=...):
        return BaseSubmit.get_submit_by_id(self.kwargs["submit_id"])


@method_decorator(csrf_exempt, name="dispatch")
class JudgeReportView(View):
    def post(self, request, *args, **kwargs):
        if not settings.JUDGE_TOKEN:
            return JsonResponse(
                {"errors": "Judge not configured.", "ok": False}, status=403
            )

        json_data = json.loads(request.body)

        if json_data["token"] != settings.JUDGE_TOKEN:
            return JsonResponse(
                {"errors": "Wrong access token.", "ok": False}, status=403
            )

        submit: JudgeSubmit = get_object_or_404(
            JudgeSubmit, judge_id=json_data["public_id"]
        )

        submit.protocol = json_data["protocol"]

        if "final_score" in submit.protocol:
            # TODO: get maximum points from RuleEngine (to the time of submit)
            max_points = submit.problem.judge_points
            submit.score = Decimal(str(submit.protocol["final_score"])) * max_points

        submit.save()

        return JsonResponse({"ok": True})
