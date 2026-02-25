from decimal import Decimal
from typing import Iterable

from django.db.models import QuerySet
from django.utils import timezone

from seminare.problems.models import Problem
from seminare.rules import Chip, RuleEngine
from seminare.rules.common import (
    BestSubmitRuleEngine,
    LevelRuleEngine,
    PreviousProblemSetRuleEngine,
)
from seminare.rules.results import (
    Cell,
    PreviousScoreCell,
    ScoreCell,
    Table,
)
from seminare.submits.models import BaseSubmit
from seminare.users.models import Enrollment, Grade, User


class FKS2026(
    LevelRuleEngine, PreviousProblemSetRuleEngine, BestSubmitRuleEngine, RuleEngine
):
    max_level = 4

    num_rounds = 3

    def parse_options(self, options: dict) -> None:
        super().parse_options(options)

        self.num_rouds = options.get("num_rounds", 3)

        return super().parse_options(options)

    # === Contestant frontend ===

    def get_chips(self, user: "User") -> dict[Problem, list[Chip]]:
        chips = super().get_chips(user)

        if user.is_authenticated:
            level = self.get_level_for_user(user)

            for problem in self.problem_set.problems.all():
                if problem.number < level:
                    chips[problem].append(
                        Chip(
                            message="Nebodovaná",
                            color="amber",
                            help="Za túto úlohu nedostávaš vo svojom leveli body",
                        )
                    )

        return chips

    def can_submit(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> bool:
        if timezone.now() > self.problem_set.end_date:
            return False

        return super().can_submit(submit_cls, problem, enrollment)

    # === Grading & results ===

    # === Results tables ===

    def get_result_tables(self) -> dict[str, str]:
        return {"all": "Spoločná"} | super().get_result_tables()

    def get_default_result_table(self, user: User | None = None) -> str:
        if user is None or not user.is_authenticated:
            return "all"

        return super().get_default_result_table(user)

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        best: list[Decimal] = []
        previous = Decimal(0)
        for score in scores:
            if isinstance(score, PreviousScoreCell):
                previous = score.points
            elif isinstance(score, ScoreCell):
                best.append(score.score.points * score.coefficient)

        best.sort(reverse=True)

        return sum(best[:4]) + previous

    def get_coefficient_for_problem(
        self, problem_number: int, enrollment: Enrollment, table: str, context: dict
    ) -> Decimal:
        if table and table[0] == "L" and problem_number < int(table[1:]):
            return Decimal(0)

        level = context["levels"][enrollment.user_id]
        if problem_number < level:
            return Decimal(0)

        return Decimal(1)

    def get_relevant_problems(self, table: str) -> QuerySet["Problem"]:
        problems = super().get_relevant_problems(table)

        if table[0] == "L":
            level = int(table[1:])

            problems = problems.filter(number__gte=level)

        return problems

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        return Grade.is_old(enrollment.grade) or super().result_table_is_ghost(
            table, context, enrollment
        )

    # === Level stuff ===

    def should_update_levels(self) -> bool:
        return self.problem_set.slug.endswith(str(self.num_rounds))

    def get_new_level(
        self, user: "User", current_level: int, tables: dict[str, Table]
    ) -> int:
        for slug, table in tables.items():
            if not slug.startswith("L"):
                continue

            table_level = int(slug[1:])

            # aspon 60b a v prvej 3 v leveli L => L + 1
            for row in table.rows:
                if (row.rank is not None and row.rank > 3) or row.total < 60:
                    break

                if row.enrollment.user == user:
                    current_level = min(
                        self.max_level, max(current_level, table_level + 1)
                    )
                    break

            # TODO: sustredenia (ak si sa zucastnil a v celkovej vysledkovke mal aspon 42b, tak +1)
        return current_level


class FX2026(PreviousProblemSetRuleEngine, BestSubmitRuleEngine, RuleEngine):
    num_rounds = 2

    def parse_options(self, options: dict) -> None:
        super().parse_options(options)

        self.num_rouds = options.get("num_rounds", 2)

        return super().parse_options(options)

    # === Contestant frontend ===

    def can_submit(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> bool:
        if timezone.now() > self.problem_set.end_date:
            return False

        return super().can_submit(submit_cls, problem, enrollment)

    # === Grading & results ===

    # === Results tables ===

    def get_result_tables(self) -> dict[str, str]:
        return {"all": "Spoločná"}

    def get_default_result_table(self, user: User | None = None) -> str:
        return "all"

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        best: list[Decimal] = []
        previous = Decimal(0)
        for score in scores:
            if isinstance(score, PreviousScoreCell):
                previous = score.points
            elif isinstance(score, ScoreCell):
                best.append(score.score.points * score.coefficient)

        best.sort(reverse=True)

        return sum(best) + previous

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        return Grade.is_old(enrollment.grade) or super().result_table_is_ghost(
            table, context, enrollment
        )


class FKSLegacy(PreviousProblemSetRuleEngine, BestSubmitRuleEngine, RuleEngine):
    def get_result_tables(self) -> dict[str, str]:
        return {"B": "B", "A": "A"}

    def get_default_result_table(self, user: User | None = None) -> str:
        return "B"
