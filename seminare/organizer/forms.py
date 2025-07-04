from django import forms

from seminare.content.models import Page, Post
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
        fields = [
            "name",
            "number",
            "file_points",
            "judge_points",
            "text_points",
            "judge_namespace",
            "judge_task",
            "text_answer",
        ]
        labels = {
            "name": "Názov",
            "number": "Číslo",
            "file_points": "Body za popis",
            "judge_points": "Body za program",
            "text_points": "Body za odpoveď",
        }

    def __init__(self, *args, **kwargs):
        self.problem_set = kwargs.pop("problem_set")
        super(ProblemForm, self).__init__(*args, **kwargs)

        for text_type, label in Text.Type.choices:
            initial = ""
            if self.instance.id:
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


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["title", "slug", "content"]
        labels = {
            "title": "Názov",
            "slug": "URL adresa",
            "content": "Obsah",
        }

    def __init__(self, *, site, **kwargs):
        super().__init__(**kwargs)
        self.site = site

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if not self.site:
            return slug

        obj = Page.objects.filter(site=self.site, slug=slug)
        if self.instance.id:
            obj = obj.exclude(id=self.instance.id)

        if obj.exists():
            raise forms.ValidationError("Stránka s touto adresou už existuje.")

        return slug

    def save(self, commit: bool = True) -> Page:
        page = super().save(commit=False)
        page.site = self.site
        if commit:
            page.save()
        return page


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]

    def __init__(self, *, user, contest, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.contest = contest

    def save(self, commit=True) -> Post:
        post = super().save(commit=False)
        if not hasattr(post, "author"):
            post.author = self.user

        if not post.id:
            post.save()
        post.contests.add(self.contest)

        return post
