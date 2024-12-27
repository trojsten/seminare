from django.shortcuts import render


def organizer_demo(request):
    return render(request, "org/base.html")
