from django import forms
from django.utils import formats


class DateInput(forms.DateInput):
    input_type = "date"

    def format_value(self, value):
        return formats.localize_input(value, "%Y-%m-%d")
