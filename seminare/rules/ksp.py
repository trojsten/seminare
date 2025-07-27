from django.utils import timezone
from django.utils.dateparse import parse_datetime

from seminare.problems.models import Problem, Text
from seminare.rules import Chip, LevelRuleEngine
from seminare.users.models import User


class KSP2025(LevelRuleEngine):
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

        if now >= self.problem_set.start_date:
            visible.add(Text.Type.PROBLEM_STATEMENT)

        if now > self.problem_set.end_date:
            visible.add(Text.Type.EXAMPLE_SOLUTION)

        return visible

    def get_chips(self, user: "User") -> dict[Problem, list[Chip]]:
        chips = super().get_chips(user)

        if user.is_authenticated:
            level = self.get_level_for_user(user)

            for problem in self.problem_set.problems.all():
                if level > problem.number:
                    chips[problem].append(
                        Chip(
                            message="Nebodovaná",
                            color="amber",
                            help="Za túto úlohu nedostávaš vo svojom leveli body",
                        )
                    )

        return chips
