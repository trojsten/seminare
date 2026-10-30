from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from seminare.content.models import Post
from seminare.content.notifications import notify_post_published
from seminare.organizer.forms import PostForm, PostFormWithSites
from seminare.organizer.tables import PostTable
from seminare.organizer.views import MixinProtocol, WithContest
from seminare.organizer.views.generic import (
    GenericDeleteView,
    GenericFormView,
    GenericTableView,
)
from seminare.users.logic.permissions import is_contest_administrator
from seminare.users.mixins.permissions import (
    ContestOrganizerRequired,
)
from seminare.users.models import User


class WithPostQuerySet(WithContest, MixinProtocol):
    def get_queryset(self):
        return (
            Post.objects.filter(contests__id=self.contest.id)
            .select_related("author")
            .distinct()
        )


class PostListView(ContestOrganizerRequired, WithPostQuerySet, GenericTableView):
    paginate_by = 50
    table_class = PostTable
    table_title = "Zoznam príspevkov"

    def get_table_links(self):
        return [
            (
                "green",
                "mdi:plus",
                "Pridať",
                reverse("org:post_create"),
            ),
            ("default", "mdi:eye", "Pozrieť na stránke", reverse("post_list")),
        ]

    def get_table_context(self):
        return {
            "contest": self.contest,
            "user": self.request.user,
            "is_admin": is_contest_administrator(self.request.user, self.contest),
        }

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [("Príspevky", "")]


class PostCreateView(
    ContestOrganizerRequired, WithContest, GenericFormView, CreateView
):
    form_title = "Nový príspevok"

    def get_success_url(self) -> str:
        return reverse("org:post_list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        kw["contest"] = self.contest
        return kw

    def get_form_class(self):
        assert isinstance(self.request.user, User)

        if is_contest_administrator(self.request.user, self.contest):
            return PostFormWithSites

        return PostForm

    def form_valid(self, form):
        response = super().form_valid(form)

        notify_post_published(self.object)

        return response

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Príspevky", reverse("org:post_list")),
            ("Nový", ""),
        ]


class PostUpdateView(
    ContestOrganizerRequired, WithPostQuerySet, GenericFormView, UpdateView
):
    form_title = "Upraviť príspevok"

    def get_success_url(self) -> str:
        return reverse("org:post_list")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        kw["contest"] = self.contest
        return kw

    def get_form_class(self):
        assert isinstance(self.request.user, User)

        if is_contest_administrator(self.request.user, self.contest):
            return PostFormWithSites

        return PostForm

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Príspevky", reverse("org:post_list")),
            (self.object, ""),
            ("Upraviť", ""),
        ]

    def get_queryset(self):
        assert isinstance(self.request.user, User)

        if is_contest_administrator(self.request.user, self.contest):
            return super().get_queryset()
        else:
            return super().get_queryset().filter(author=self.request.user)


class PostDeleteView(ContestOrganizerRequired, WithPostQuerySet, GenericDeleteView):
    def get_success_url(self) -> str:
        return reverse("org:post_list")

    def get_breadcrumbs(self) -> list[tuple[str, str]]:
        return [
            ("Príspevky", reverse("org:post_list")),
            (self.object, ""),
            ("Vymazať", ""),
        ]

    def get_queryset(self):
        assert isinstance(self.request.user, User)

        if is_contest_administrator(self.request.user, self.contest):
            return super().get_queryset()
        else:
            return super().get_queryset().filter(author=self.request.user)
