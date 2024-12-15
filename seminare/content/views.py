from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from seminare.content.models import Page, Post


class PageDetailView(DetailView):
    template_name = "page/detail.html"

    def get_object(self, queryset=...):
        site = get_current_site(self.request)
        return get_object_or_404(Page, slug=self.kwargs["slug"], site=site)


class PostListView(ListView):
    template_name = "post/list.html"
    paginate_by = 15

    def get_queryset(self):
        site = get_current_site(self.request)
        return Post.objects.filter(contests__site=site)
