from django.urls import path

from seminare.content import views

urlpatterns = [
    path("pages/<slug>/", views.PageDetailView.as_view(), name="page_detail"),
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path("posts/create", views.PostCreateView.as_view(), name="post_create"),
    path("posts/<int:pk>", views.PostEditView.as_view(), name="post_edit"),
    path("posts/<int:pk>/delete", views.PostDeleteView.as_view(), name="post_delete"),
]
