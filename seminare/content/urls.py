from django.urls import path

from seminare.content import views

urlpatterns = [
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path("posts/<slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("<path:slug>/", views.PageDetailView.as_view(), name="page_detail"),
]
