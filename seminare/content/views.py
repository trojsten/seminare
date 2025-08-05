from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from seminare.content.models import Page, Post
from seminare.users.logic.permissions import has_contest_role
from seminare.users.models import ContestRole, User


class PageDetailView(DetailView):
    template_name = "page/detail.html"

    def get_object(self, queryset=...):
        site = get_current_site(self.request)
        return get_object_or_404(Page, slug=self.kwargs["slug"], contest__site=site)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            assert isinstance(self.request.user, User)
            ctx["is_organizer"] = has_contest_role(
                self.request.user, self.object.contest, ContestRole.Role.ORGANIZER
            )
        else:
            ctx["is_organizer"] = False
        return ctx


class PostListView(ListView):
    template_name = "post/list.html"
    paginate_by = 15

    def get_queryset(self):
        site = get_current_site(self.request)
        return Post.objects.filter(contests__site=site)


class PostDetailView(DetailView):
    template_name = "post/detail.html"

    def get_object(self, queryset=...):
        site = get_current_site(self.request)
        return get_object_or_404(Post, slug=self.kwargs["slug"], contests__site=site)
