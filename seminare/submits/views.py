from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, TemplateView

from seminare.problems.models import Problem
from seminare.submits.forms import FileFieldForm
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.logic.enrollment import get_enrollment
from seminare.users.models import Enrollment


def file_submit_create_view(request: HttpRequest, **kwargs):
    problem = get_object_or_404(Problem, id=kwargs['problem'])
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to perform this action.")

    if request.method == "POST":
        form = FileFieldForm(request.POST, request.FILES)
        if form.is_valid():
            for file in form.cleaned_data["files"]:
                file: File
                file_submit = FileSubmit(
                    file=file,
                    problem=problem,
                    enrollment=get_enrollment(request.user, problem.problem_set),
                )
                file_submit.save()
                break

        return HttpResponseRedirect(problem.get_absolute_url())

    return HttpResponse(status=405, content=f"Method {request.method} not allowed")


class SubmitListView(TemplateView):
    template_name = "submits/list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        user = self.request.user
        problem_id = self.kwargs.get("problem_id")
        fs = FileSubmit.objects.filter(enrollment__user=user, problem=problem_id).all()
        js = JudgeSubmit.objects.filter(enrollment__user=user, problem=problem_id).all()
        ts = TextSubmit.objects.filter(enrollment__user=user, problem=problem_id).all()
        context = super().get_context_data()
        context["file_submits"] = fs
        context["judge_submits"] = js
        context["text_submits"] = ts
        return context


class FileSubmitDetailView(DetailView):
    model = FileSubmit
    template_name = "submits/detail_file.html"
    context_object_name = "submit"


class JudgeSubmitDetailView(DetailView):
    model = JudgeSubmit
    template_name = "submits/detail_judge.html"
    context_object_name = "submit"


class TextSubmitDetailView(DetailView):
    model = TextSubmit
    template_name = "submits/detail_text.html"
    context_object_name = "submit"
