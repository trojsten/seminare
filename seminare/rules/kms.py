from collections import defaultdict
from decimal import Decimal
from typing import Iterable

from django.db.models import F, QuerySet
from django.utils import timezone

from seminare.problems.models import Problem
from seminare.rules import Chip
from seminare.rules.common import (
    LevelRuleEngine,
    LimitedSubmitRuleEngine,
    PreviousProblemSetRuleEngine,
)
from seminare.rules.results import (
    Cell,
    PreviousScoreCell,
    ScoreCell,
    Table,
)
from seminare.rules.scores import Score
from seminare.submits.models import BaseSubmit, FileSubmit
from seminare.users.models import Enrollment, Grade, User


class KMS2025(
    LevelRuleEngine,
    PreviousProblemSetRuleEngine,
    LimitedSubmitRuleEngine,
):
    max_level = 5
    PROBLEMS_IN_LEVEL = [[], range(1, 9), range(2, 9), range(3, 9), range(4, 11), range(5, 11)]
    POINTS_FOR_SUCCESSFUL_LEVEL = [0, 84, 84, 84, 93, 93]  # 0 is just padding, levels start at 1

    def can_submit(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> bool:
        if submit_cls == FileSubmit and timezone.now() > self.doprogramovanie_date:
            return False

        return super().can_submit(submit_cls, problem, enrollment)

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

    def get_enrollments_problems_scores(
        self, enrollments: Iterable[Enrollment], problems: Iterable[Problem]
    ) -> dict[tuple[int, int], Score]:
        user_problem_submits: dict[tuple[int, int], list[BaseSubmit]]
        user_problem_submits = defaultdict(list)

        for type_ in BaseSubmit.get_submit_types():
            submits = self.get_enrollments_problems_effective_submits(
                type_, enrollments, problems
            ).select_related("enrollment")
            for submit in submits:
                key = (submit.enrollment.user_id, submit.problem_id)
                user_problem_submits[key].append(submit)

        output = {}
        for key, submits in user_problem_submits.items():
            output[key] = Score(submits)
        return output

    def get_enrollments(self) -> QuerySet[Enrollment]:
        # TODO: Ignore organizers
        # chceme ich naozaj ignorovat? lebo pouzivato to napr. get_result_table a tam je
        # ich vhodne mat... (Andrej)
        return self.problem_set.enrollment_set.get_queryset()

    def get_result_tables(self) -> dict[str, str]:
        return {f"L{x}": f"Level {x}" for x in range(1, self.max_level + 1)}

    def get_default_result_table(self, user: User | None = None) -> str:
        return "L1"

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        best: list[Decimal] = []
        previous = Decimal(0)
        for score in scores:
            if isinstance(score, PreviousScoreCell):
                previous = score.points
                continue

            if not isinstance(score, ScoreCell):
                continue
            best.append(score.score.points * score.coefficient)

        best.sort(reverse=True)

        return sum(best[:5]) + previous

    def get_coefficient_for_problem(
        self, problem_number: int, enrollment: Enrollment, table: str
    ) -> Decimal:
        if table and problem_number not in self.PROBLEMS_IN_LEVEL[int(table[1])]:
            return Decimal(0)
        return Decimal(1)

    def result_table_is_excluded(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        level = int(table[1:])
        return context["levels"][enrollment.user] > level or super().result_table_is_excluded(table, context, enrollment)

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        return Grade.is_old(enrollment.grade) or super().result_table_is_ghost(
            table, context, enrollment
        )

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

    ### Level stuff

    def should_update_levels(self) -> bool:
        return self.problem_set.slug.endswith("3")

    def get_new_level(
        self, user: "User", current_level: int, tables: dict[str, Table]
    ) -> int:
        for slug, table in tables.items():
            table_level = int(slug[1:])
            for row in table.rows:
                if row.total < self.POINTS_FOR_SUCCESSFUL_LEVEL[table_level]:
                    break
                if row.enrollment.user == user:
                    current_level = max(current_level, table_level + 1)

        # TODO: sustredenia
        return current_level
