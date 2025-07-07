from django.utils import timezone

from seminare.problems.models import Problem, Text
from seminare.rules import RuleEngine


class KSPRules(RuleEngine):
    def get_visible_texts(self, problem: "Problem") -> "set[Text.Type]":
        visible = set()
        now = timezone.now()

        if now.date() >= self.problem_set.start_date:
            visible.add(Text.Type.PROBLEM_STATEMENT)

        if now.date() > self.problem_set.end_date:
            visible.add(Text.Type.EXAMPLE_SOLUTION)

        return visible

    pass
