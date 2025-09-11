from django.http.response import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from seminare.contests.utils import get_current_contest
from seminare.legacy.models import OldProblem, OldRound


def redirect_round(request, *args, **kwargs):
    id = kwargs.get("id")
    if not id:
        return HttpResponsePermanentRedirect(reverse("problem_set_list"))

    contest = get_current_contest(request)
    old_round = get_object_or_404(OldRound, contest=contest, old_round_id=id)
    return HttpResponsePermanentRedirect(
        reverse("problem_set_detail", kwargs={"slug": old_round.problem_set.slug})
    )


def _redirect_problem_or_solution(request, id, solution=False):
    contest = get_current_contest(request)
    old_problem = get_object_or_404(
        OldProblem, contest=contest, old_problem_id=id
    ).problem

    if solution:
        url_name = "problem_solution"
    else:
        url_name = "problem_detail"

    return HttpResponsePermanentRedirect(
        reverse(
            url_name,
            kwargs={
                "problem_set_slug": old_problem.problem_set.slug,
                "number": old_problem.number,
            },
        )
    )


def redirect_problem(request, *args, **kwargs):
    return _redirect_problem_or_solution(request, kwargs.get("id"))


def redirect_solution(request, *args, **kwargs):
    return _redirect_problem_or_solution(request, kwargs.get("id"), True)


def redirect_results(request, id, slug=None, *args, **kwargs):
    contest = get_current_contest(request)

    old_round = get_object_or_404(OldRound, contest=contest, old_round_id=id)

    kwargs = {"slug": old_round.problem_set.slug}

    if slug is not None:
        slug = slug.split("_")[-1]
        kwargs["table"] = {"ALL": "all"}.get(slug, slug)

    return HttpResponsePermanentRedirect(reverse("problem_set_results", kwargs=kwargs))
