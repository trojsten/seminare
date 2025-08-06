from django.urls.conf import path

from seminare.legacy.views import redirect_problem, redirect_round, redirect_solution

urlpatterns = [
    path("ulohy/", redirect_round),
    path("ulohy/<int:id>/", redirect_round),
    path("ulohy/zadania/<int:id>/", redirect_problem),
    path("ulohy/risenia/<int:id>/", redirect_solution),
    # TODO: /vysledky/KOLO/*/
]
