from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.urls import reverse
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


class PageListView(ListView):
    model = Page
    template_name = "page/list.html"
    paginate_by = 15

    def get_queryset(self):
        site = get_current_site(self.request)
        return Page.objects.filter(site=site)


class PageDetailView(DetailView):
    template_name = "page/detail.html"

    def get_object(self, queryset=...):
        site = get_current_site(self.request)
        return get_object_or_404(Page, slug=self.kwargs["slug"], site=site)


class PageCreateView(GenericFormView, CreateView):
    template_name = "page/edit.html"
    form_class = forms.PageForm
    form_title = "Pridať stránku"

    def get_success_url(self):
        return reverse("page_detail", args=(self.request.POST["slug"],))


class PageEditView(GenericFormView, UpdateView):
    model = Page
    form_class = forms.PageForm
    template_name = "page/edit.html"
    form_title = "Upraviť stránku"

    def get_success_url(self):
        return reverse("page_detail", args=(self.request.POST["slug"],))


class PageDeleteView(DeleteView):
    model = Page
    template_name = "page/confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["return"] = self.request.GET.get("return", None)
        return ctx

    def get_success_url(self):
        return reverse("page_list")


class PostListView(ListView):
    model = Post
    template_name = "post/list.html"
    paginate_by = 15

    def get_queryset(self):
        site = get_current_site(self.request)
        return Post.objects.filter(contests__site=site)


class PostCreateView(GenericFormView, CreateView):
    template_name = "post/edit.html"
    form_class = forms.PostForm
    form_title = "Pridať príspevok"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"].fields["author"].initial = self.request.user.id
        return ctx

    def get_success_url(self):
        return reverse("post_list")


class PostEditView(GenericFormView, UpdateView):
    model = Post
    template_name = "post/edit.html"
    form_class = forms.PostForm
    form_title = "Upraviť príspevok"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"].fields["author"].initial = self.object.author
        return ctx

    def get_success_url(self):
        return reverse("post_edit", args=(self.kwargs["pk"],))


class PostDeleteView(DeleteView):
    model = Post
    template_name = "post/confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["return"] = self.request.GET.get("return", None)
        return ctx

    def get_success_url(self):
        return reverse("post_list")
