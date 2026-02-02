from decimal import Decimal
from typing import Iterable

from django.db.models import F, QuerySet

from seminare.problems.models import Problem
from seminare.rules import Chip, RuleEngine
from seminare.rules.common import (
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


class KMS2026(LevelRuleEngine, PreviousProblemSetRuleEngine, RuleEngine):
    max_level = 5

    # === KMS helpers ===

    KMS_POINTS_FOR_SUCCESSFUL_LEVEL: list[int] = [0, 84, 84, 84, 94, 94]

    KMS_LEVEL_BOUNDARIES: dict[int, tuple[int, int]] = {
        1: (1, 8),
        2: (2, 8),
        3: (3, 8),
        4: (4, 10),
        5: (5, 10),
    }

    def kms_can_solve_problem(
        self, problem_number: int, level: int, strict=False
    ) -> bool:
        boundary = self.KMS_LEVEL_BOUNDARIES.get(level, (-1, -1))

        if problem_number >= boundary[0] and (
            not strict or problem_number <= boundary[1]
        ):
            return True

        return False

    # === Contestant frontend ===

    def get_chips(self, user: "User") -> dict[Problem, list[Chip]]:
        chips = super().get_chips(user)

        if user.is_authenticated:
            level = self.get_level_for_user(user)

            for problem in self.problem_set.problems.all():
                if not self.kms_can_solve_problem(problem.number, level):
                    chips[problem].append(
                        Chip(
                            message="Nebodovaná",
                            color="amber",
                            help="Za túto úlohu nedostávaš vo svojom leveli body",
                        )
                    )

        return chips

    # === Grading & results ===

    def get_enrollments_problems_effective_submits(
        self,
        submit_cls: type[BaseSubmit],
        enrollments: Iterable[Enrollment],
        problems: Iterable[Problem],
    ) -> QuerySet[BaseSubmit]:
        return (
            submit_cls.objects.filter(
                problem__in=problems,
                enrollment__in=enrollments,
                created_at__lte=self.problem_set.end_date,
            )
            .order_by(
                "enrollment_id",
                "problem_id",
                F("score").desc(nulls_last=True),
                "-created_at",
            )
            .distinct("enrollment_id", "problem_id")
        )

    # === Results tables ===

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        best: list[Decimal] = []
        previous = Decimal(0)
        for score in scores:
            if isinstance(score, PreviousScoreCell):
                previous = score.points
            elif isinstance(score, ScoreCell):
                best.append(score.score.points * score.coefficient)

        best.sort(reverse=True)

        return sum(best[:5]) + previous

    def get_coefficient_for_problem(
        self, problem_number: int, enrollment: Enrollment, table: str
    ) -> Decimal:
        if (
            table
            and table[0] == "L"
            and not self.kms_can_solve_problem(problem_number, int(table[1:]), True)
        ):
            return Decimal(0)

        return Decimal(1)

    def get_relevant_problems(self, table: str) -> QuerySet["Problem"]:
        problems = super().get_relevant_problems(table)

        if table[0] == "L":
            level = int(table[1:])
            boundary = self.KMS_LEVEL_BOUNDARIES.get(level, (-1, -1))

            problems = problems.filter(number__range=boundary)

        return problems

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        return Grade.is_old(enrollment.grade) or super().result_table_is_ghost(
            table, context, enrollment
        )

    # === Level stuff ===

    def should_update_levels(self) -> bool:
        return self.problem_set.slug.endswith("3")

    def get_new_level(
        self, user: "User", current_level: int, tables: dict[str, Table]
    ) -> int:
        for slug, table in tables.items():
            if not slug.startswith("L"):
                continue

            table_level = int(slug[1:])

            # aspon 80% leveli L => L + 1
            for row in table.rows:
                if row.total < self.KMS_POINTS_FOR_SUCCESSFUL_LEVEL[table_level]:
                    break
                if row.enrollment.user == user:
                    current_level = min(
                        self.max_level, max(current_level, table_level + 1)
                    )
                    break

            # TODO: sustredenia (ak si sa zucastnil, tak +1)
        return current_level


class KMSLegacy(PreviousProblemSetRuleEngine, RuleEngine):
    def get_enrollments_problems_effective_submits(
        self,
        submit_cls: type[BaseSubmit],
        enrollments: Iterable[Enrollment],
        problems: Iterable[Problem],
    ) -> QuerySet[BaseSubmit]:
        return (
            submit_cls.objects.filter(
                problem__in=problems,
                enrollment__in=enrollments,
                created_at__lte=self.problem_set.end_date,
            )
            .order_by(
                "enrollment_id",
                "problem_id",
                F("score").desc(nulls_last=True),
                "-created_at",
            )
            .distinct("enrollment_id", "problem_id")
        )

    def get_result_tables(self) -> dict[str, str]:
        return {"alfa": "Alfa", "beta": "Beta"}

    def get_default_result_table(self, user: User | None = None) -> str:
        return "alfa"
