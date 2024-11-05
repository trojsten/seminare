from django.contrib import admin

from seminare.problemy.models import Problem, ProblemSet, Submit

# Register your models here.

admin.site.register(ProblemSet)
admin.site.register(Problem)
admin.site.register(Submit)
