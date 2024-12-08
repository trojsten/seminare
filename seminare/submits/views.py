# Create your views here.
from django.views.generic import DetailView, TemplateView

from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit


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
