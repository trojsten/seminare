from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from seminare.problems.models import Problem
from seminare.submits.forms import FileFieldForm
from seminare.submits.models import BaseSubmit, FileSubmit
from seminare.users.logic.enrollment import get_enrollment


def file_submit_create_view(request: HttpRequest, **kwargs):
    problem = get_object_or_404(Problem, id=kwargs["problem"])
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


class SubmitDetailView(DetailView):
    # TODO: Permission check
    context_object_name = "submit"
    template_name = "submits/detail.html"

    def get_object(self, queryset=...):
        return BaseSubmit.get_submit_by_id(self.kwargs["submit_id"])
