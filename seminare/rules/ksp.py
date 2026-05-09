from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional

from django.db.models import F, Q, QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from seminare.problems.models import Problem
from seminare.rules import Chip, RuleEngine, Score
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
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit
from seminare.users.models import Enrollment, Grade, User


class KSP2025(LevelRuleEngine, PreviousProblemSetRuleEngine, RuleEngine):
    max_level = 4

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

        return super().parse_options(options)

    def get_important_dates(self) -> list[tuple[datetime, str]]:
        dates = super().get_important_dates()

        dates.append((self.doprogramovanie_date, "Doprogramovávanie"))

        return dates

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
        filters: Optional[Q] = None,
    ) -> QuerySet[BaseSubmit]:
        if filters is None:
            filters = Q(created_at__lte=self.doprogramovanie_date) | Q(
                late_accepted=True
            )

        return (
            submit_cls.objects.filter(
                problem__in=problems,
                enrollment__in=enrollments,
            )
            .filter(filters)
            .order_by(
                "enrollment_id",
                "problem_id",
                F("score").desc(nulls_last=True),
                "-created_at",
            )
            .distinct("enrollment_id", "problem_id")
        )

    def get_enrollments_problems_scores(
        self, enrollments: Iterable[Enrollment], problems: Iterable["Problem"]
    ) -> dict[tuple[int, int], Score]:
        user_problem_submits: dict[tuple[int, int], list[BaseSubmit]]
        user_problem_submits = defaultdict(list)

        best_judge_scores: dict[tuple[int, int], Decimal]
        best_judge_scores = defaultdict(lambda: Decimal(0))

        for type_ in BaseSubmit.get_submit_types():
            if not any(
                type_ in problem.accepted_submit_classes for problem in problems
            ):
                continue

            submits = self.get_enrollments_problems_effective_submits(
                type_, enrollments, problems
            ).select_related("enrollment")
            for submit in submits:
                key = (submit.enrollment.user_id, submit.problem_id)
                user_problem_submits[key].append(submit)
                if type_ == JudgeSubmit:
                    best_judge_scores[key] = max(best_judge_scores[key], submit.score)

        doprogramovanie_submits = self.get_enrollments_problems_effective_submits(
            JudgeSubmit,
            enrollments,
            problems,
            filters=Q(
                created_at__gt=self.doprogramovanie_date,
                late_accepted=False,
                created_at__lte=self.problem_set.end_date,
            ),
        ).select_related("enrollment")
        for submit in doprogramovanie_submits:
            key = (submit.enrollment.user_id, submit.problem_id)

            new_score = (submit.score - best_judge_scores[key]) * Decimal(0.5)
            submit.score = new_score if new_score > 0 else Decimal(0)

            user_problem_submits[key].append(submit)

        output = {}
        for key, submits in user_problem_submits.items():
            problem: "Problem" = next(
                problem for problem in problems if problem.id == key[1]
            )
            output[key] = Score(submits, problem)
        return output

    def get_result_tables(self) -> dict[str, str]:
        return {"all": "Spoločná"} | super().get_result_tables()

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

        return sum(best[:5]) + previous

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
        return self.problem_set.slug.endswith("2")

    def get_new_level(
        self, user: "User", current_level: int, tables: dict[str, Table]
    ) -> int:
        for slug, table in tables.items():
            if not slug.startswith("L"):
                continue

            # aspon 150b a top 5 v leveli L => L + 1
            last_rank = 0
            for row in table.rows:
                if row.rank is not None:
                    last_rank = row.rank
                    if last_rank > 5:
                        break

                if row.enrollment.user == user:
                    if row.total >= 150:
                        current_level = max(current_level, int(slug[1:]) + 1)

            # TODO: sustredenia
        return current_level
