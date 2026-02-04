from datetime import datetime
from decimal import Decimal
from typing import Iterable

from django.db.models import F, QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from seminare.problems.models import Problem
from seminare.rules import Chip, RuleEngine
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
from seminare.submits.models import BaseSubmit, FileSubmit
from seminare.users.models import Enrollment, Grade, User


class KSP2025(
    LevelRuleEngine, PreviousProblemSetRuleEngine, LimitedSubmitRuleEngine, RuleEngine
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
                continue

            if not isinstance(score, ScoreCell):
                continue
            best.append(score.score.points * score.coefficient)

        best.sort(reverse=True)

        return sum(best[:5]) + previous

    def get_coefficient_for_problem(
        self, problem_number: int, enrollment: Enrollment, table: str
    ) -> Decimal:
        if table and table[0] == "L" and problem_number < int(table[1]):
            return Decimal(0)
        return Decimal(1)

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
