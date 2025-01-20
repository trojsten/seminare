from django.urls import path

from seminare.content import views

urlpatterns = [
    path("pages/", views.PageListView.as_view(), name="page_list"),
    path("pages/create/", views.PageCreateView.as_view(), name="page_create"),
    path("pages/<slug>/", views.PageDetailView.as_view(), name="page_detail"),
    path("pages/<slug>/edit/", views.PageEditView.as_view(), name="page_edit"),
    path("pages/<slug>/delete/", views.PageDeleteView.as_view(), name="page_delete"),
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path("posts/create/", views.PostCreateView.as_view(), name="post_create"),
    path("posts/<int:pk>/", views.PostEditView.as_view(), name="post_edit"),
    path("posts/<int:pk>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("menus/", views.MenuListView.as_view(), name="menu_list"),
    path("menus/<int:pk>/delete/", views.MenuDeleteView.as_view(), name="menu_delete"),
]
