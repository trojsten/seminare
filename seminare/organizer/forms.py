from django import forms

from seminare.problems.models import Problem, ProblemSet, Text
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


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ["name", "number"]
        labels = {"name": "Názov", "number": "Číslo"}

    def __init__(self, *args, **kwargs):
        self.problem_set = kwargs.pop("problem_set")
        super(ProblemForm, self).__init__(*args, **kwargs)

        for text_type, label in Text.Type.choices:
            initial = ""
            if self.instance:
                if current_text := self.instance.text_set.filter(
                    type=text_type
                ).first():
                    initial = current_text.text
            self.fields[f"text_{text_type}"] = forms.CharField(
                required=False, widget=forms.Textarea, label=label, initial=initial
            )

    def save(self, commit=True):
        problem: Problem = super(ProblemForm, self).save(commit=False)
        problem.problem_set = self.problem_set
        problem.save()

        data = self.cleaned_data

        for text_type in Text.Type.values:
            value = data[f"text_{text_type}"]
            if not value:
                problem.text_set.filter(type=text_type).delete()
            else:
                Text.objects.update_or_create(
                    type=text_type, problem=problem, defaults={"text": value}
                )
        return problem
