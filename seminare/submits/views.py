from io import BytesIO

from django.core.files.base import ContentFile
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from seminare.problems.models import Problem
from seminare.submits.forms import FileFieldForm
from seminare.submits.models import FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.models import Enrollment


def file_submit_create_view(request: HttpRequest, **kwargs):
    problem = get_object_or_404(Problem, id=kwargs["problem"])
    if request.method == "POST":
        form = FileFieldForm(request.POST, request.FILES)
        if form.is_valid():
            files = form.cleaned_data["files"]
            final_file = files[0]
            if len(files) > 1:
                final_file = combine_images_into_pdf(files)
            file_submit = FileSubmit(
                file=final_file,
                problem=problem,
                enrollment=Enrollment.objects.filter(user=request.user).first(),
            )
            file_submit.save()
        return HttpResponseRedirect(problem.get_absolute_url())
    return HttpResponse(status=405, content=f"Method {request.method} not allowed")


def combine_images_into_pdf(files):
    """
    Combines multiple image files into a single PDF.
    Assumes all files are images; validation should be handled in the form.
    """
    # @TODO Nieco co vygrcalo GPT, trva to dost dlho - takze mozno async ? :thinking:
    try:
        output = BytesIO()
        pdf_canvas = canvas.Canvas(output, pagesize=A4)
        width, height = A4

        for file in files:
            img = Image.open(file)
            img = img.convert("RGB")  # Convert to RGB mode

            # Scale the image to fit the page
            img_width, img_height = img.size
            scale = min(width / img_width, height / img_height)
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            x_offset = (width - scaled_width) / 2
            y_offset = (height - scaled_height) / 2

            # Draw the image on the PDF canvas
            img_path = BytesIO()
            img.save(img_path, format="PNG")
            img_path.seek(0)
            pdf_canvas.drawImage(
                ImageReader(img_path), x_offset, y_offset, scaled_width, scaled_height
            )
            pdf_canvas.showPage()  # Start a new page

        pdf_canvas.save()

        # Create a Django ContentFile from the output PDF
        output.seek(0)
        pdf_content = ContentFile(output.read(), name="combined_files.pdf")
        return pdf_content
    except Exception as e:
        raise RuntimeError(f"Failed to combine files into a PDF: {e}")


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
