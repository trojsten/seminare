import os.path
from io import BytesIO

from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from seminare.problems.models import Problem
from seminare.submits.forms import FileFieldForm
from seminare.submits.models import BaseSubmit, FileSubmit
from seminare.users.logic.enrollment import get_enrollment


def file_submit_create_view(request: HttpRequest, **kwargs):
    # TODO: Refactor
    problem = get_object_or_404(Problem, id=kwargs["problem"])
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to perform this action.")

    if request.method == "POST":
        form = FileFieldForm(request.POST, request.FILES)
        if form.is_valid():
            files = form.cleaned_data["files"]
            final_file = files[0]
            _, ext = os.path.splitext(files[0].name)
            if len(files) > 1 or ext.lower() in [".jpg", ".jpeg", ".png"]:
                final_file = combine_images_into_pdf(files)
            file_submit = FileSubmit(
                file=final_file,
                problem=problem,
                enrollment=get_enrollment(request.user, problem.problem_set),
            )
            file_submit.save()
        return HttpResponseRedirect(problem.get_absolute_url())
    return HttpResponse(status=405, content=f"Method {request.method} not allowed")


def combine_images_into_pdf(files):
    """
    Combines multiple image files into a single PDF.
    Assumes all files are images; validation should be handled in the form.
    """
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
            img.save(img_path, format="JPEG")
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


class SubmitDetailView(DetailView):
    # TODO: Permission check
    context_object_name = "submit"
    template_name = "submits/detail.html"

    def get_object(self, queryset=...):
        return BaseSubmit.get_submit_by_id(self.kwargs["submit_id"])
