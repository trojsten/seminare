from django.utils import timezone
from django.utils.dateparse import parse_datetime

from seminare.problems.models import Problem, Text
from seminare.rules import RuleEngine


class KSPRules(RuleEngine):
    def parse_options(self, options: dict) -> None:
        super().parse_options(options)

        if "doprogramovanie_date" not in options:
            raise ValueError("Chýba 'doprogramovanie_date'.")

        self.doprogramovanie_date = parse_datetime(
            options.get("doprogramovanie_date", None)
        )

        if self.doprogramovanie_date is None:
            raise ValueError("'doprogramovanie_date' je v neplatnom formáte.")

    def get_visible_texts(self, problem: "Problem") -> "set[Text.Type]":
        visible = set()
        now = timezone.now()

        if now.date() >= self.problem_set.start_date:
            visible.add(Text.Type.PROBLEM_STATEMENT)

        if now.date() > self.problem_set.end_date:
            visible.add(Text.Type.EXAMPLE_SOLUTION)

        return visible
