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


class FileSubmitCreateView(FormView):
    form_class = FileFieldForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to perform this action.")
        self.problem = get_object_or_404(Problem, id=kwargs["problem"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        files = form.cleaned_data["files"]
        final_file = files[0]
        _, ext = os.path.splitext(files[0].name)
        if len(files) > 1 or ext.lower() in [".jpg", ".jpeg", ".png"]:
            final_file = combine_images_into_pdf(files)
        file_submit = FileSubmit(
            file=final_file,
            problem=self.problem,
            enrollment=get_enrollment(self.request.user, self.problem.problem_set),
        )
        file_submit.save()
        self.file_submit = file_submit
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("submit_detail", args=[self.file_submit.submit_id])


class JudgeSubmitCreateView(FormView):
    form_class = JudgeSubmitForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to perform this action.")
        self.problem = get_object_or_404(Problem, id=kwargs["problem"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        program = form.cleaned_data["program"]

        submit = enqueue_judge_submit(
            self.problem.judge_namespace,
            self.problem.judge_task,
            self.request.user,
            program,
        )

        judge_submit = JudgeSubmit(
            program=program,
            problem=self.problem,
            judge_id=submit.public_id,
            protocol_key=submit.protocol_key,
            enrollment=get_enrollment(self.request.user, self.problem.problem_set),
        )
        judge_submit.save()
        self.judge_submit = judge_submit
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("submit_detail", args=[self.judge_submit.submit_id])


class TextSubmitCreateView(FormView):
    form_class = TextSubmitForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to perform this action.")
        self.problem = get_object_or_404(Problem, id=kwargs["problem"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        text = form.cleaned_data["text"]

        text_submit = TextSubmit(
            value=text,
            problem=self.problem,
            enrollment=get_enrollment(self.request.user, self.problem.problem_set),
        )
        text_submit.save()
        self.text_submit = text_submit
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("submit_detail", args=[self.text_submit.submit_id])


class SubmitDetailView(DetailView):
    # TODO: Permission check
    context_object_name = "submit"
    template_name = "submits/detail.html"

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
