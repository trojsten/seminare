from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from importlib import import_module
from typing import TYPE_CHECKING, Iterable

from django.core.cache import cache
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from seminare.contests.models import RuleData
from seminare.rules.results import Cell, ColumnHeader, Row, ScoreCell, Table
from seminare.rules.scores import Score
from seminare.submits.models import BaseSubmit
from seminare.submits.utils import JSON
from seminare.users.logic.permissions import is_contest_organizer, preload_contest_roles
from seminare.users.models import Enrollment, User
from seminare.utils import (
    compress_data,
    decompress_data,
)

if TYPE_CHECKING:
    from seminare.problems.models import Problem, ProblemSet, Text
    from seminare.users.models import User


@dataclass
class Chip:
    message: str
    color: str = "gray"
    icon: str = ""
    help: str = ""


class RuleEngine:
    engine_id: str
    """Engine ID for RuleData"""

    compatible_engines: list[str] = []
    """Other compatible engine IDs that should be fetched with RuleData"""

    def __init__(self, problem_set: "ProblemSet") -> None:
        self.problem_set = problem_set
        self.engine_id = f"{self.__class__.__module__}.{self.__class__.__qualname__}"

        self.parse_options(self.problem_set.rule_engine_options)

    def parse_options(self, options: dict) -> None:
        """Parses options from problem set."""
        pass

    def get_data_for_users(
        self,
        key: str,
        users: list["User"],
        engines: list[str] | None = None,
    ) -> "QuerySet[RuleData]":
        """Returns RuleData for multiple users."""
        return RuleData.objects.for_users(
            contest=self.problem_set.contest,
            key=key,
            users=users,
            effective_date=self.problem_set.start_date,  # TODO: casti
            engines=engines or [self.engine_id, *self.compatible_engines],
        )

    def get_data_for_user(
        self,
        key: str,
        user: "User",
        engines: list[str] | None = None,
    ) -> "RuleData | None":
        """Returns RuleData for a single user."""
        return RuleData.objects.for_user(
            contest=self.problem_set.contest,
            key=key,
            user=user,
            effective_date=self.problem_set.start_date,  # TODO: casti
            engines=engines or [self.engine_id, *self.compatible_engines],
        )

    def set_data_for_users(self, key: str, data: dict["User", JSON]):
        """Sets data for multiple users. Data is a dict mapping User to dict of data."""
        return RuleData.objects.bulk_create(
            [
                RuleData(
                    contest=self.problem_set.contest,
                    key=key,
                    user=user,
                    engine=self.engine_id,
                    data=data_dict,
                )
                for user, data_dict in data.items()
            ]
        )

    def set_data_for_user(
        self,
        key: str,
        user: "User",
        data: JSON,
    ):
        """Sets data for a single user. Data is a dict of data."""
        return self.set_data_for_users(key, {user: data})

    def get_visible_texts(self, problem: "Problem|None") -> "set[Text.Type]":
        """
        Returns types of texts that are currently visible for a given problem.
        If problem is None, we want to know visible texts in general (e.g. PDF statements).
        """
        raise NotImplementedError()

    def get_important_dates(self) -> list[tuple[datetime, str]]:
        return [
            (self.problem_set.start_date, "Začiatok kola"),
            (self.problem_set.end_date, "Koniec kola"),
        ]

    def get_submits_chip(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> Chip | None:
        """Returns chip to be displayed next to submits for user."""
        return None

    def can_submit(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> bool:
        """Returns True if the user can submit solution to the problem."""
        if (
            self.problem_set.is_public
            and timezone.now() > problem.problem_set.start_date
        ):
            return True

        if enrollment is not None and is_contest_organizer(
            enrollment.user, self.problem_set.contest
        ):
            return True

        return False

    def get_effective_submits(
        self, submit_cls: type[BaseSubmit], problem: "Problem"
    ) -> QuerySet[BaseSubmit]:
        """Returns a QuerySet of submits that are considered accepted."""
        raise NotImplementedError()

    def get_enrollments_problems_effective_submits(
        self,
        submit_cls: type[BaseSubmit],
        enrollments: Iterable[Enrollment],
        problems: "Iterable[Problem]",
    ) -> QuerySet[BaseSubmit]:
        """Returns a QuerySet of submits that are considered accepted for a given list of enrollments and problems."""
        raise NotImplementedError()

    def get_enrollments_problems_scores(
        self, enrollments: Iterable[Enrollment], problems: "Iterable[Problem]"
    ) -> dict[tuple[int, int], Score]:
        """Returns a mapping (enrollment_id, problem_id) -> Score for given list of enrollments and problems."""
        raise NotImplementedError()

    def get_enrollments(self) -> QuerySet[Enrollment]:
        """Returns a QuerySet of enrollments that are considered part of the competition."""
        raise NotImplementedError()

    def get_result_tables(self) -> dict[str, str]:
        """Returns a dict (slug: display_name) for all result tables."""
        raise NotImplementedError()

    def get_default_result_table(self, user: User | None = None) -> str:
        """Returns the slug of the default result table for user."""
        raise NotImplementedError()

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        """Calculates total score for a set of table Cells."""
        raise NotImplementedError()

    def get_coefficient_for_problem(
        self, problem_number: int, table: str | None = None
    ) -> Decimal:
        """Returns the score coefficient for a given problem in a results table."""
        # TODO: Also pass User or UserData.
        raise NotImplementedError()

    def result_table_get_context(
        self, table: str, enrollments: QuerySet[Enrollment, Enrollment], context: dict
    ) -> dict:
        """
        Precomputes context for a given result table.
        Context will be passed to result_table_get_headers and result_table_get_cells.
        """
        users = list(e.user for e in enrollments)
        preload_contest_roles(users, self.problem_set.contest)

        context["problems"] = self.problem_set.problems.order_by("number").all()
        context["scores"] = self.get_enrollments_problems_scores(
            enrollments, context["problems"]
        )
        return context

    def result_table_get_headers(
        self, table: str, context: dict, **kwargs
    ) -> list[ColumnHeader]:
        """Returns the column headers for a given result table."""
        return [
            ColumnHeader(
                str(problem.number),
                reverse("problem_detail", args=[self.problem_set.slug, problem.number]),
                problem.name,
            )
            for problem in context["problems"]
        ]

    def result_table_get_cells(
        self, table: str, enrollment: Enrollment, context: dict, **kwargs
    ) -> list[Cell | None]:
        """Returns the row cells for a given result table and enrollment."""
        cells: list[Cell | None] = []

        for problem in context["problems"]:
            if (key := (enrollment.user_id, problem.id)) in context["scores"]:
                score = context["scores"][key]
                coeff = self.get_coefficient_for_problem(problem.number, table)
                cells.append(ScoreCell(score, coeff))
            else:
                cells.append(None)

        return cells

    def result_table_exclude_enrollment(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        """Returns True if the enrollment should be excluded from the result table."""
        return False

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        """Returns True if the enrollment should be marked as ghost in the result table."""
        return is_contest_organizer(
            enrollment.user,
            self.problem_set.contest,
        )

    def get_result_table(self, table: str, **kwargs) -> Table:
        """Calculates given result table."""

        if self.problem_set.is_finalized:
            frozen_results = self.problem_set.get_frozen_results(table)
            return Table.deserialize(frozen_results)

        key = f"results_table/{self.problem_set.slug}/{table}"
        if key in cache and (data := cache.get(key)) is not None:
            return Table.deserialize(decompress_data(data))

        enrollments = self.get_enrollments().select_related("user", "school")

        context = self.result_table_get_context(table, enrollments, {})
        columns = self.result_table_get_headers(table, context)

        rows = []
        for enrollment in enrollments:
            if self.result_table_exclude_enrollment(table, context, enrollment):
                continue

            cells: list[Cell | None] = self.result_table_get_cells(
                table, enrollment, context
            )

            rows.append(
                Row(
                    rank=None,
                    enrollment=enrollment,
                    ghost=self.result_table_is_ghost(table, context, enrollment),
                    columns=cells,
                    total=self.calculate_total(cells),
                )
            )

        table_obj = Table(columns, rows)
        table_obj.sort()
        cache.set(key, compress_data(table_obj.serialize()), timeout=60 * 5)
        return table_obj

    def get_chips(self, user: "User") -> dict["Problem", list[Chip]]:
        return defaultdict(list)

    def close_problemset(self):
        """Callback to be called when problemset is marked as closed."""

        for table in self.get_result_tables().keys():
            key = f"results_table/{self.problem_set.slug}/{table}"
            cache.delete(key)

            self.problem_set.set_frozen_results(
                table, self.get_result_table(table).serialize()
            )


def get_rule_engine_class(path: str) -> type[RuleEngine]:
    module, classname = path.rsplit(".", 1)

    imported = import_module(module)
    class_ = getattr(imported, classname)
    if not issubclass(class_, RuleEngine):
        raise ValueError("Requested class is not a RuleEngine.")
    return class_
