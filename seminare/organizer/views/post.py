from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from seminare.content.models import Post
from seminare.organizer.forms import PostForm
from seminare.organizer.tables import PostTable
from seminare.organizer.views import MixinProtocol, WithContest
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormView,
    GenericTableView,
)


class WithPostQuerySet(WithContest, MixinProtocol):
    def get_queryset(self):
        return Post.objects.filter(contests__id=self.contest.id).distinct()


class PostListView(WithPostQuerySet, GenericTableView):
    # TODO: Permission checking

    paginate_by = 50
    table_class = PostTable
    table_title = "Zoznam príspevkov"

    def get_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať",
                reverse("org:post_create", args=[self.contest.id]),
            ),
            ("default", "mdi:eye", "Pozrieť na stránke", reverse("post_list")),
        ]

    def get_table_context(self):
        return {"contest": self.contest}

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Príspevky", "")]


class PostCreateView(WithContest, GenericFormView, CreateView):
    form_title = "Nový príspevok"
    form_class = PostForm

    def get_success_url(self) -> str:
        return reverse("org:post_list", args=[self.contest.id])

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        kw["contest"] = self.contest
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Príspevky", reverse("org:post_list", args=[self.contest.id])),
            ("Nový", ""),
        ]


class PostUpdateView(WithPostQuerySet, GenericFormView, UpdateView):
    form_title = "Upraviť príspevok"
    form_class = PostForm

    def get_success_url(self) -> str:
        return reverse("org:post_list", args=[self.contest.id])

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        kw["contest"] = self.contest
        return kw

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Príspevky", reverse("org:post_list", args=[self.contest.id])),
            (self.object, ""),
            ("Upraviť", ""),
        ]


class PostDeleteView(WithPostQuerySet, GenericDeleteView):
    def get_success_url(self) -> str:
        return reverse("org:post_list", args=[self.contest.id])

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Príspevky", reverse("org:post_list", args=[self.contest.id])),
            (self.object, ""),
            ("Vymazať", ""),
        ]
