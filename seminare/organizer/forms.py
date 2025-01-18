from django import forms

from seminare.problems.models import ProblemSet
from seminare.style.forms import DateInput


class ProblemSetForm(forms.ModelForm):
    class Meta:
        model = ProblemSet
        fields = ["name", "start_date", "end_date", "is_public"]
        labels = {
            "name": "Názov",
            "start_date": "Začiatok",
            "end_date": "Koniec",
            "is_public": "Zverejniť",
        }
        help_texts = {
            "end_date": "Riešenia bude možné odovzdávať najneskôr v tento deň.",
            "is_public": "Sada úloh sa bude zobrazovať na stránke.",
        }
        widgets = {
            "start_date": DateInput(),
            "end_date": DateInput(),
        }


class GradingForm(forms.Form):
    comment = forms.CharField(required=False)
    score = forms.DecimalField(required=False)
