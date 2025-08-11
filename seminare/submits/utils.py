from io import BytesIO
from pathlib import Path
from typing import TypeAlias

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.base import ContentFile
from judge_client.client import JudgeClient, Submit
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


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


def enqueue_judge_submit(namespace: str, task: str, user: User, file: File) -> Submit:
    judge = JudgeClient(judge_token=settings.JUDGE_TOKEN, judge_url=settings.JUDGE_URL)

    return judge.submit(
        namespace=namespace,
        task=task,
        external_user_id=user.username,
        filename=file.name or "",
        program=file.read(),
    )


def get_extension(path: str | Path) -> str:
    if isinstance(path, str):
        path = Path(path)

    suffixes = path.suffixes

    # If it is tar, return whole extension
    if len(suffixes) > 1 and suffixes[-2] == ".tar":
        return suffixes[-2] + suffixes[-1]
    elif len(suffixes) > 0:
        return suffixes[-1]

    return ""
