from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from seminare.content import forms
from seminare.content.models import Page, Post
from seminare.organizer.views.generic import GenericFormView


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


class PostCreateView(GenericFormView, CreateView):
    template_name = "post/edit.html"
    form_class = forms.ProblemSetForm
    form_title = "Pridať príspevok"


class PostEditView(GenericFormView, UpdateView):
    template_name = "post/edit.html"
    form_class = forms.ProblemSetForm
    form_title = "Upraviť príspevok"


class PostDeleteView(DeleteView):
    model = Post
    template_name = "post/confirm_post_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["return"] = self.request.GET.get("return", None)
        return ctx
