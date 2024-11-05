from django.shortcuts import render


def problem_list(request):
    return render(request, "problems.html")


def problem_detail(request, id):
    return render(request, "problem_detail.html")
