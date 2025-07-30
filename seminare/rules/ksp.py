from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from django.db.models import F, QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from seminare.problems.models import Problem, Text
from seminare.rules import RuleEngine
from seminare.rules.results import Cell, ColumnHeader, Row, Table
from seminare.rules.scores import Score
from seminare.submits.models import BaseSubmit
from seminare.users.models import Enrollment


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

    def get_effective_submits(
        self, submit_cls: type[BaseSubmit], problem: "Problem"
    ) -> QuerySet[BaseSubmit]:
        return (
            submit_cls.objects.filter(
                problem=problem, created_at__lte=self.problem_set.end_date_time
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
        return (
            submit_cls.objects.filter(
                problem__in=problems,
                enrollment__in=enrollments,
                created_at__lte=self.problem_set.end_date_time,
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
        return self.problem_set.enrollment_set.get_queryset()

    def get_result_tables(self):
        return []

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        sum = Decimal(0)
        for score in scores:
            if score is None:
                continue
            sum += score.score.points * score.coefficient
        return sum

    def get_coefficient_for_problem(
        self, problem_number: int, table: str | None = None
    ) -> Decimal:
        return Decimal(1)

    def get_result_table(self, table: str, **kwargs) -> Table:
        problems = self.problem_set.problems.order_by("number").all()
        enrollments = self.get_enrollments().select_related("user", "school")
        scores = self.get_enrollments_problems_scores(enrollments, problems)

        columns = []
        for problem in problems:
            columns.append(ColumnHeader(str(problem.number), None, problem.name))

        rows = []
        for enrollment in enrollments:
            cells: list[Cell | None] = []
            for problem in problems:
                key = (enrollment.user_id, problem.id)
                if key in scores:
                    score = scores[key]
                    coeff = self.get_coefficient_for_problem(problem.number, table)
                    cells.append(Cell(score, coeff))
                else:
                    cells.append(None)

            rows.append(
                Row(
                    rank=None,
                    enrollment=enrollment,
                    ghost=False,
                    columns=cells,
                    total=self.calculate_total(cells),
                )
            )

        table_obj = Table(columns, rows)
        table_obj.sort()
        return table_obj
