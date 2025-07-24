from datetime import datetime

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from seminare.problems.models import Problem, Text
from seminare.rules import RuleEngine


class KSPRules(RuleEngine):
    doprogramovanie_date: datetime

    def parse_options(self, options: dict) -> None:
        super().parse_options(options)

        if "doprogramovanie_date" not in options:
            raise ValueError("Chýba 'doprogramovanie_date'.")

        date = parse_datetime(options.get("doprogramovanie_date", None))

        if date is None:
            raise ValueError("'doprogramovanie_date' je v neplatnom formáte.")

        date = date.astimezone(timezone.get_current_timezone())

        self.doprogramovanie_date = date

    def get_visible_texts(self, problem: "Problem") -> "set[Text.Type]":
        visible = set()
        now = timezone.now()

        if now >= self.problem_set.start_date:
            visible.add(Text.Type.PROBLEM_STATEMENT)

        if now > self.problem_set.end_date:
            visible.add(Text.Type.EXAMPLE_SOLUTION)

        return visible

    def get_important_dates(self) -> list[tuple[datetime, str]]:
        dates = super().get_important_dates()

        dates.append((self.doprogramovanie_date, "Doprogramovávanie"))

        return dates
