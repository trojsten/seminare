from django.urls.conf import path

from seminare.legacy.views import (
    redirect_latest_results,
    redirect_problem,
    redirect_results,
    redirect_round,
    redirect_solution,
)

urlpatterns = [
    path("ulohy/", redirect_round),
    path("ulohy/<int:id>/", redirect_round),
    path("ulohy/zadania/<int:id>/", redirect_problem),
    path("ulohy/riesenia/<int:id>/", redirect_solution),
    path("vysledky/", redirect_latest_results),
    path("vysledky/<int:id>/", redirect_results),
    path("vysledky/<int:id>/<str:slug>/", redirect_results),
]
