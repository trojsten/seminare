from django.http import Http404, HttpRequest, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView

from seminare.content.models import Page, Post
from seminare.contests.utils import get_current_contest
from seminare.users.logic.permissions import has_contest_role, is_contest_organizer
from seminare.users.models import ContestRole, User


class PageDetailView(DetailView):
    template_name = "page/detail.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        self.contest = get_current_contest(self.request)

        if self.request.user.is_authenticated:
            assert isinstance(self.request.user, User)
            self.is_organizer = has_contest_role(
                self.request.user, self.contest, ContestRole.Role.ORGANIZER
            )
        else:
            self.is_organizer = False

        self.page = Page.objects.filter(
            slug=self.kwargs["slug"], contest=self.contest
        ).first()

        if self.page is None:
            if self.is_organizer and not self.kwargs.get("slug").startswith("org/"):
                return redirect("org:page_create", slug=self.kwargs["slug"])
            raise Http404()

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=...):
        return self.page

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_organizer"] = self.is_organizer
        return ctx


class PostListView(ListView):
    template_name = "post/list.html"
    paginate_by = 15

    def get_queryset(self):
        self.contest = get_current_contest(self.request)
        return Post.objects.filter(contests__id=self.contest.id).select_related(
            "author"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_organizer"] = isinstance(
            self.request.user, User
        ) and is_contest_organizer(self.request.user, self.contest)
        ctx["links"] = []
        if ctx["is_organizer"]:
            ctx["links"].append(
                (
                    "green",
                    "mdi:plus",
                    "Vytvoriť príspevok",
                    reverse("org:post_create"),
                )
            )
        return ctx


class PostDetailView(DetailView):
    template_name = "post/detail.html"

    def get_object(self, queryset=...):
        self.contest = get_current_contest(self.request)
        return get_object_or_404(
            Post.objects.select_related("author"),
            slug=self.kwargs["slug"],
            contests__id=self.contest.id,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_organizer"] = isinstance(
            self.request.user, User
        ) and is_contest_organizer(self.request.user, self.contest)
        ctx["links"] = []
        if ctx["is_organizer"]:
            ctx["links"].append(
                (
                    "green",
                    "mdi:pencil",
                    "Upraviť príspevok",
                    reverse("org:post_update", args=[self.object.id]),
                )
            )
        return ctx
