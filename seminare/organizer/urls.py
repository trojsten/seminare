from django.urls import path

from seminare.organizer.views import (
    dashboard,
    files,
    grading,
    menu,
    page,
    post,
    problem,
    problemset,
    role,
)

app_name = "org"

urlpatterns = [
    path("", dashboard.ContestDashboardView.as_view(), name="contest_dashboard"),
    path("kola/", problemset.ProblemSetListView.as_view(), name="problemset_list"),
    path(
        "kola/vytvorit/",
        problemset.ProblemSetCreateView.as_view(),
        name="problemset_create",
    ),
    path(
        "kola/<problem_set_slug>/",
        problemset.ProblemSetUpdateView.as_view(),
        name="problemset_update",
    ),
    path(
        "kola/<problem_set_slug>/export",
        problemset.ProblemSetCSVExportView.as_view(),
        name="problemset_csv_export",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/<int:number>/opravovanie/",
        grading.GradingOverviewView.as_view(),
        name="grading_overview",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/<int:number>/opravovanie/zverejnit/",
        grading.GradingPublishView.as_view(),
        name="grading_publish",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/<int:number>/opravovanie/hromadne/",
        grading.BulkGradingView.as_view(),
        name="bulk_grading",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/<int:number>/opravovanie/hromadne/stiahnut/",
        grading.BulkGradingDownloadView.as_view(),
        name="bulk_grading_download",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/<int:number>/opravovanie/<submit_id:submit_id>/",
        grading.GradingSubmitView.as_view(),
        name="grading_submit",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/",
        problem.ProblemListView.as_view(),
        name="problem_list",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/<int:number>/",
        problem.ProblemUpdateView.as_view(),
        name="problem_update",
    ),
    path(
        "kola/<problem_set_slug>/ulohy/vytvorit/",
        problem.ProblemCreateView.as_view(),
        name="problem_create",
    ),
    path("menu/", menu.MenuGroupListView.as_view(), name="menu_group_list"),
    path(
        "menu/<int:pk>/",
        menu.MenuGroupUpdateView.as_view(),
        name="menu_group_update",
    ),
    path(
        "menu/<int:pk>/polozky/",
        menu.MenuItemListView.as_view(),
        name="menu_item_list",
    ),
    path(
        "menu/<int:pk>/polozky/<int:item_pk>/",
        menu.MenuItemUpdateView.as_view(),
        name="menu_item_update",
    ),
    path(
        "menu/<int:pk>/polozky/<int:item_pk>/vymazat/",
        menu.MenuItemDeleteView.as_view(),
        name="menu_item_delete",
    ),
    path(
        "menu/<int:pk>/polozky/vytvorit/",
        menu.MenuItemCreateView.as_view(),
        name="menu_item_create",
    ),
    path(
        "menu/<int:pk>/vymazat/",
        menu.MenuGroupDeleteView.as_view(),
        name="menu_group_delete",
    ),
    path(
        "menu/vytvorit/",
        menu.MenuGroupCreateView.as_view(),
        name="menu_group_create",
    ),
    path("organizatori/", role.RoleListView.as_view(), name="role_list"),
    path(
        "organizatori/<int:pk>/",
        role.RoleUpdateView.as_view(),
        name="role_update",
    ),
    path(
        "organizatori/<int:pk>/vymazat/",
        role.RoleDeleteView.as_view(),
        name="role_delete",
    ),
    path(
        "organizatori/vytvorit/",
        role.RoleCreateView.as_view(),
        name="role_create",
    ),
    path("prispevky/", post.PostListView.as_view(), name="post_list"),
    path("prispevky/<int:pk>/", post.PostUpdateView.as_view(), name="post_update"),
    path(
        "prispevky/<int:pk>/vymazat/", post.PostDeleteView.as_view(), name="post_delete"
    ),
    path("prispevky/vytvorit/", post.PostCreateView.as_view(), name="post_create"),
    path("stranky/", page.PageListView.as_view(), name="page_list"),
    path("stranky/<int:pk>/", page.PageUpdateView.as_view(), name="page_update"),
    path(
        "stranky/<int:pk>/vymazat/", page.PageDeleteView.as_view(), name="page_delete"
    ),
    path("stranky/vytvorit/", page.PageCreateView.as_view(), name="page_create"),
    path(
        "stranky/vytvorit/<path:slug>/",
        page.PageCreateView.as_view(),
        name="page_create",
    ),
    path("subory/", files.FileListView.as_view(), name="file_list"),
    path("subory/vymazat/", files.FileDeleteView.as_view(), name="file_delete"),
    path(
        "subory/novy_priecinok/", files.NewFolderView.as_view(), name="file_new_folder"
    ),
    path("subory/nahrat/", files.FileUploadView.as_view(), name="file_upload"),
]
