from django.utils import timezone

from seminare.problems.models import Problem, Text
from seminare.rules import Chip, LevelRuleEngine
from seminare.users.models import User


class KSPRules(LevelRuleEngine):
    engine_id = "ksp-2025"

    def get_visible_texts(self, problem: "Problem") -> "set[Text.Type]":
        visible = set()
        now = timezone.now()

        if now.date() >= self.problem_set.start_date:
            visible.add(Text.Type.PROBLEM_STATEMENT)

        if now.date() > self.problem_set.end_date:
            visible.add(Text.Type.EXAMPLE_SOLUTION)

        return visible

    def get_chips(self, user: "User") -> dict[Problem, list[Chip]]:
        chips = super().get_chips(user)

        if user.is_authenticated:
            level = self.get_level_for_user(user)

            for problem in self.problem_set.problems.all():
                if level > problem.number:
                    chips[problem].append(
                        Chip.create(
                            message="Nebodovaná",
                            color="amber",
                            help="Za túto úlohu nedostávaš vo svojom leveli body",
                        )
                    )

        return chips
