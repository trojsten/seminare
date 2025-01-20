from django import forms

from seminare.content import models


class PageForm(forms.ModelForm):
    template_name_div = "forms/div.html"

    class Meta:
        model = models.Page
        fields = ["title", "slug", "site", "content"]
        labels = {
            "title": "Nadpis",
            "slug": "Slug",
            "site": "Stránka",
            "content": "Obsah",
        }


class PostForm(forms.ModelForm):
    template_name_div = "forms/div.html"

    class Meta:
        model = models.Post
        fields = ["title", "contests", "content", "author"]
        labels = {
            "title": "Nadpis",
            "contests": "Súťaže",
            "content": "Obsah",
        }
        widgets = {"author": forms.HiddenInput()}
