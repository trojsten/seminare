from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from importlib import import_module
from typing import TYPE_CHECKING, Iterable, TypedDict

from django.db.models import QuerySet

from seminare.contests.models import RuleData
from seminare.rules.results import Cell, Table
from seminare.rules.scores import Score
from seminare.submits.models import BaseSubmit
from seminare.users.models import Enrollment, User

if TYPE_CHECKING:
    from seminare.problems.models import Problem, ProblemSet, Text
    from seminare.users.models import User


class Chip(TypedDict):
    message: str
    color: str
    icon: str
    help: str

    @classmethod  # type: ignore
    def create(cls, message: str, color: str = "gray", icon: str = "", help: str = ""):
        return cls(
            message=message,
            color=color,
            icon=icon,
            help=help,
        )


class RuleEngine:
    engine_id: str = "base"
    """Engine ID for RuleData"""

    compatible_engines: list[str] = []
    """Other compatible engine IDs that should be fetched with RuleData"""

    def __init__(self, problem_set: "ProblemSet") -> None:
        self.problem_set = problem_set
        self.parse_options(self.problem_set.rule_engine_options)

    def parse_options(self, options: dict) -> None:
        pass

    def get_data_for_users(
        self,
        users: list["User"],
        engines: list[str] | None = None,
    ) -> "QuerySet[RuleData]":
        return RuleData.objects.for_users(
            contest=self.problem_set.contest,
            users=users,
            effective_date=self.problem_set.start_date,  # TODO: casti
            engines=engines or [self.engine_id, *self.compatible_engines],
        )

    def get_data_for_user(
        self,
        user: "User",
        engines: list[str] | None = None,
    ) -> "RuleData | None":
        return RuleData.objects.for_user(
            contest=self.problem_set.contest,
            user=user,
            effective_date=self.problem_set.start_date,  # TODO: casti
            engines=engines or [self.engine_id, *self.compatible_engines],
        )

    def set_data_for_user(
        self,
        user: "User",
        data: dict,
    ):
        return RuleData.objects.create(
            contest=self.problem_set.contest,
            user=User,
            engine=self.engine_id,
            data=data,
        )

    def get_visible_texts(self, problem: "Problem") -> "set[Text.Type]":
        raise NotImplementedError()

    def get_important_dates(self) -> list[tuple[datetime, str]]:
        return [
            (self.problem_set.start_date, "Začiatok kola"),
            (self.problem_set.end_date, "Koniec kola"),
        ]

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

    def get_result_table(self, table: str, **kwargs) -> Table:
        """Calculates given result table."""
        raise NotImplementedError()

    def get_aggregated_results(self, table: str, **kwargs) -> Table:
        """Returns the given result table aggregated with previous problem sets."""
        return self.get_result_table(table, **kwargs)

    def get_chips(self, user: "User") -> dict["Problem", list[Chip]]:
        return defaultdict(list)


class LevelRuleEngine(RuleEngine):
    def get_level_for_users(self, users: "list[User]") -> dict["User", int]:
        data = self.get_data_for_users(users)

        return {data.user: data.data.get("level", 0) for data in data}

    def get_level_for_user(self, user: "User") -> int:
        data = self.get_data_for_user(user)
        if data is None:
            return 0
        return data.data.get("level", 0)

    def set_level_for_user(self, user: "User", level: int):
        return self.set_data_for_user(user, {"level": level})


def get_rule_engine_class(path: str) -> type[RuleEngine]:
    module, classname = path.rsplit(".", 1)

    imported = import_module(module)
    class_ = getattr(imported, classname)
    if not issubclass(class_, RuleEngine):
        raise ValueError("Requested class is not a RuleEngine.")
    return class_
