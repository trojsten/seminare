from django.db.models import Max
from django.shortcuts import redirect, render

from seminare.problemy.models import Problem, ProblemSet, Submit


def home(request):
    return render(request, "home.html")


def problem_list(request):
    problem_set = ProblemSet.objects.first()
    problems = problem_set.problems.all()
    submits = dict()

    for problem in problems:
        highest_submit = Submit.objects.filter(
            problem=problem, user=request.user
        ).aggregate(max_score=Max("score"))["max_score"]
        submits[problem.id] = highest_submit
    context = {"problem_set": problem_set, "problems": problems, "submits": submits}
    return render(request, "problems.html", context=context)


def problem_detail(request, id):
    problem = Problem.objects.filter(id=id).get()
    problems = Problem.objects.filter(problem_set=problem.problem_set)
    problem_submits = Submit.objects.filter(problem=problem, user=request.user)
    submits = dict()
    for p in problems:
        highest_submit = Submit.objects.filter(problem=p, user=request.user).aggregate(
            max_score=Max("score")
        )["max_score"]
        submits[p.id] = highest_submit or 0
    context = {
        "problem": problem,
        "problems": problems,
        "problem_submits": problem_submits,
        "submits": submits,
    }
    return render(request, "problem_detail.html", context=context)


def problem_submit(request, id):
    Submit.objects.create(problem_id=id, user=request.user, score=0)

    return redirect("detail", id=id)
