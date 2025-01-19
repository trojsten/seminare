from django import forms

from seminare.content import models


class ProblemSetForm(forms.ModelForm):
    class Meta:
        model = models.Post
        fields = ["title", "contests", "content"]
        labels = {
            "title": "Nadpis",
            "contests": "Súťaže",
            "content": "Obsah",
        }
