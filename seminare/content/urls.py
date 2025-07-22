from django.urls import path

from seminare.content import views

urlpatterns = [
    path("pages/<path:slug>/", views.PageDetailView.as_view(), name="page_detail"),
    path("posts/", views.PostListView.as_view(), name="post_list"),
]
