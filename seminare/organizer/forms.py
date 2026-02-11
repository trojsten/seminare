from django import forms
from django.core.validators import FileExtensionValidator

from seminare.content.models import MenuGroup, MenuItem, Page, Post
from seminare.problems.models import Problem, ProblemSet, Text
from seminare.rules import get_rule_engine_class
from seminare.style.forms import DateTimeInput
from seminare.users.models import ContestRole
from seminare.users.widgets import UserAutocompleteInput


class ProblemSetForm(forms.ModelForm):
    class Meta:
        model = ProblemSet
        fields = [
            "name",
            "slug",
            "start_date",
            "end_date",
            "is_finalized",
            "is_public",
            "rule_engine",
            "rule_engine_options",
            "statement_pdf",
            "solution_pdf",
        ]
        labels = {
            "name": "Názov",
            "slug": "URL adresa",
            "start_date": "Začiatok",
            "end_date": "Koniec",
            "is_finalized": "Finalizovať výsledky",
            "is_public": "Zverejniť",
            "rule_engine": "Rule Engine",
            "rule_engine_options": "Nastavenia pre Rule Engine",
            "statement_pdf": "PDF zadania",
            "solution_pdf": "PDF vzoráky",
        }
        help_texts = {
            "start_date": "Dátum zverejnenia sady úloh.",
            "end_date": "Riešenia bude možné odovzdávať najneskôr v tento deň.",
            "is_public": "Sada úloh sa bude zobrazovať na stránke.",
            "is_finalized": "Výsledky budú finalizované a nebudú sa už dať meniť.",
            "rule_engine": "Cesta k triede, ktorá implementuje pravidlá a hodnotenie.",
            "rule_engine_options": "Špecifické nastavenia pre Rule Engine.",
        }
        widgets = {
            "start_date": DateTimeInput(),
            "end_date": DateTimeInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.is_finalized:
            self.fields["is_finalized"].disabled = True
            self.fields[
                "is_finalized"
            ].help_text = "Táto sada úloh už bola finalizovaná."

    def clean(self):
        data = super().clean()

        if not data:
            return data

        try:
            rule_engine = get_rule_engine_class(data["rule_engine"])
        except Exception:
            raise forms.ValidationError(
                {"rule_engine": "Zadaná cesta k triede Rule Engine nie je platná."}
            )

        if data.get("rule_engine_options") is None:
            data["rule_engine_options"] = {}

        try:
            self.instance.rule_engine_options = data["rule_engine_options"]
            rule_engine(self.instance)
        except Exception as e:
            raise forms.ValidationError(
                {
                    "rule_engine_options": f"Chyba pri spracovaní nastavení pre Rule Engine: {e}"
                }
            )

        return data


class GradingForm(forms.Form):
    comment = forms.CharField(required=False)
    comment_file = forms.FileField(required=False)

    score = forms.DecimalField(required=False)


class GradingUploadForm(forms.Form):
    file = forms.FileField(
        validators=[FileExtensionValidator(["zip"])],
        required=True,
        help_text="ZIP súbor s opravenými riešeniami.",
    )


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = [
            "name",
            "number",
            "file_points",
            "judge_points",
            "text_points",
            "text_answer",
            "judge_namespace",
            "judge_task",
            "points_publicly_visible",
        ]
        labels = {
            "name": "Názov",
            "number": "Číslo",
            "file_points": "Body za popis",
            "judge_points": "Body za program",
            "text_points": "Body za odpoveď",
            "points_publicly_visible": "Zverejniť body za popis",
        }

    def __init__(self, *args, **kwargs):
        self.problem_set = kwargs.pop("problem_set")
        super(ProblemForm, self).__init__(*args, **kwargs)

        if self.instance.id:
            texts = {t.type: t for t in self.instance.text_set.all()}
        else:
            texts = {}

        for text_type, label in Text.Type.choices:
            initial = ""
            if self.instance.id:
                if current_text := texts.get(text_type):
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

    def __init__(self, *, contest, **kwargs):
        super().__init__(**kwargs)
        self.contest = contest

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if not self.contest:
            return slug

        obj = Page.objects.filter(contest=self.contest, slug=slug)
        if self.instance.id:
            obj = obj.exclude(id=self.instance.id)

        if obj.exists():
            raise forms.ValidationError("Stránka s touto adresou už existuje.")

        return slug

    def save(self, commit: bool = True) -> Page:
        page: Page = super().save(commit=False)
        page.contest = self.contest
        if commit:
            page.save()
        return page


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "slug", "content"]
        labels = {
            "title": "Názov",
            "slug": "Slug",
            "content": "Obsah",
        }

    def __init__(self, *, user, contest, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.contest = contest

    def save(self, commit=True) -> Post:
        post = super().save(commit=False)
        if not hasattr(post, "author"):
            post.author = self.user

        if commit or not post.id:
            post.save()
        post.contests.add(self.contest)

        return post


class NewFolderForm(forms.Form):
    name = forms.CharField(label="Názov")


class FileUploadForm(forms.Form):
    name = forms.CharField(
        label="Názov súboru",
        required=False,
        help_text="Ak necháš prázdne, použije sa názov nahraného súboru.",
    )
    file = forms.FileField(label="Súbor")


class RoleForm(forms.ModelForm):
    class Meta:
        model = ContestRole
        fields = ["user", "role"]
        labels = {
            "user": "Organizátor",
            "role": "Rola",
        }
        widgets = {"user": UserAutocompleteInput}

    def __init__(self, *, contest, **kwargs):
        super().__init__(**kwargs)
        self.contest = contest

        if self.instance.pk:
            self.fields["user"].disabled = True

    def clean_user(self):
        user = self.cleaned_data["user"]

        if self.instance.pk:
            return self.instance.user

        obj = ContestRole.objects.filter(contest=self.contest, user=user)

        if obj.exists():
            raise forms.ValidationError("Tento použivatel už má pre túto súťaž práva.")

        return user

    def save(self, commit: bool = True) -> ContestRole:
        role: ContestRole = super().save(commit=False)
        role.contest = self.contest
        if commit:
            role.save()
        return role


class MenuGroupForm(forms.ModelForm):
    class Meta:
        model = MenuGroup
        fields = ["title", "order"]
        labels = {
            "title": "Názov",
            "order": "Poradie",
        }

    def __init__(self, *, contest, **kwargs):
        super().__init__(**kwargs)
        self.contest = contest

    def save(self, commit: bool = True) -> MenuGroup:
        menu_group: MenuGroup = super().save(commit=False)
        menu_group.contest = self.contest
        if commit:
            menu_group.save()
        return menu_group


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["title", "order", "url", "icon"]
        labels = {
            "title": "Názov",
            "url": "URL",
            "icon": "Ikona",
            "order": "Poradie",
        }
        help_texts = {
            "icon": 'Ikona z Material Design Icons (napr. mdi:home), pozri <a class="link" href="https://icon-sets.iconify.design/mdi/">zoznam</a>.',
            "url": "Odkaz môze byť buď relatívny: /kola, alebo absolútny: https://trojsten.sk/ls",
        }

    def __init__(self, *, group, **kwargs):
        super().__init__(**kwargs)
        self.group = group

    def save(self, commit: bool = True) -> MenuItem:
        menu_item: MenuItem = super().save(commit=False)
        menu_item.group = self.group
        if commit:
            menu_item.save()
        return menu_item
