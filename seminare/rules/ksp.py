from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from django.db.models import F, QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from seminare.problems.models import Problem, Text
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
from seminare.submits.models import BaseSubmit
from seminare.users.models import Enrollment, Grade, User


class KSP2025(
    LevelRuleEngine,
    PreviousProblemSetRuleEngine,
    LimitedSubmitRuleEngine,
):
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

    def get_effective_submits(
        self, submit_cls: type[BaseSubmit], problem: "Problem"
    ) -> QuerySet[BaseSubmit]:
        return (
            submit_cls.objects.filter(
                problem=problem, created_at__lte=self.problem_set.end_date
            )
            .order_by("enrollment_id", F("score").desc(nulls_last=True), "-created_at")
            .distinct("enrollment_id")
        )

    def get_enrollments_problems_effective_submits(
        self,
        submit_cls: type[BaseSubmit],
        enrollments: Iterable[Enrollment],
        problems: Iterable[Problem],
    ) -> QuerySet[BaseSubmit]:
        # TODO: doprogramovavanie
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
            output[key] = Score(submits)  # TODO: Extract Score creation
        return output

    def get_enrollments(self) -> QuerySet[Enrollment]:
        # TODO: Ignore organizers
        # chceme ich naozaj ignorovat? lebo pouzivato to napr. get_result_table a tam je
        # ich vhodne mat... (Andrej)
        return self.problem_set.enrollment_set.get_queryset()

    def get_result_tables(self) -> dict[str, str]:
        return {"all": "Spoločná"} | {f"L{x}": f"Level {x}" for x in (1, 2, 3, 4)}

    def get_default_result_table(self, user: User | None = None) -> str:
        return "all"

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
        self, problem_number: int, table: str | None = None
    ) -> Decimal:
        if table and table[0] == "L" and problem_number < int(table[1]):
            return Decimal(0)
        return Decimal(1)

    def result_table_exclude_enrollment(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        level = int(table[1:]) if table.startswith("L") else 0
        return (
            level > 0 and context["levels"][enrollment.user] > level
        ) | super().result_table_exclude_enrollment(table, context, enrollment)

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        return Grade.is_old(enrollment.grade) | super().result_table_is_ghost(
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
