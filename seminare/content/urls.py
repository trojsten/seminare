from django.urls import path

from seminare.content import views

urlpatterns = [
    path("prispevky/", views.PostListView.as_view(), name="post_list"),
    path("prispevky/<slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("<path:slug>/", views.PageDetailView.as_view(), name="page_detail"),
]
