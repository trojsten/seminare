from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from importlib import import_module
from typing import TYPE_CHECKING, Iterable

from django.db.models import QuerySet

from seminare.contests.models import RuleData
from seminare.rules.results import Cell, Table
from seminare.rules.scores import Score
from seminare.submits.models import BaseSubmit
from seminare.users.models import Enrollment, User

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
        users: list["User"],
        engines: list[str] | None = None,
    ) -> "QuerySet[RuleData]":
        """Returns RuleData for multiple users."""
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
        """Returns RuleData for a single user."""
        return RuleData.objects.for_user(
            contest=self.problem_set.contest,
            user=user,
            effective_date=self.problem_set.start_date,  # TODO: casti
            engines=engines or [self.engine_id, *self.compatible_engines],
        )

    def set_data_for_users(self, data: dict["User", dict]):
        """Sets data for multiple users. Data is a dict mapping User to dict of data."""
        return RuleData.objects.bulk_create(
            [
                RuleData(
                    contest=self.problem_set.contest,
                    user=user,
                    engine=self.engine_id,
                    data=data_dict,
                )
                for user, data_dict in data.items()
            ]
        )

    def set_data_for_user(
        self,
        user: "User",
        data: dict,
    ):
        """Sets data for a single user. Data is a dict of data."""
        return self.set_data_for_users({user: data})

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

    def close_problemset(self):
        """Callback to be called when problemset is marked as closed."""
        # TODO: actually call it
        # TODO: freeze results
        pass


class LevelRuleEngine(RuleEngine):
    default_level: int = 1
    max_level: int

    def get_level_for_users(self, users: "list[User]") -> dict["User", int]:
        """Returns levels for multiple users. If no data is found, returns default level."""
        data = self.get_data_for_users(users)

        return defaultdict(
            lambda: self.default_level,
            {data.user: data.data.get("level", self.default_level) for data in data},
        )

    def get_level_for_user(self, user: "User") -> int:
        """Returns the level for a single user. If no data is found, returns default level."""
        data = self.get_data_for_user(user)
        if data is None:
            return self.default_level
        return data.data.get("level", self.default_level)

    def set_levels_for_users(self, data: dict["User", int]):
        """Sets levels for multiple users. Data is a dict mapping User to level."""
        return self.set_data_for_users(
            {
                user: {"level": min(level, self.max_level)}
                for user, level in data.items()
            }
        )

    def set_level_for_user(self, user: "User", level: int):
        """Sets level for a single user. Level is an integer."""
        return self.set_data_for_user(user, {"level": min(level, self.max_level)})

    def should_update_levels(self) -> bool:
        """Returns True if levels should be updated on problem set close."""
        raise NotImplementedError()

    def get_new_level(
        self, user: "User", current_level: int, tables: dict[str, Table]
    ) -> int:
        """Returns the new level for a user based on the result tables."""
        raise NotImplementedError()

    def close_problemset(self):
        if not self.should_update_levels():
            return

        enrollments = list(
            self.problem_set.enrollment_set.all().prefetch_related("user")
        )
        users = [e.user for e in enrollments]
        levels = self.get_level_for_users(users)

        tables = {
            table: self.get_result_table(table)
            for table in self.get_result_tables().keys()
        }

        for user in users:
            levels[user] = self.get_new_level(user, levels[user], tables)

        self.set_levels_for_users(levels)

        super().close_problemset()


def get_rule_engine_class(path: str) -> type[RuleEngine]:
    module, classname = path.rsplit(".", 1)

    imported = import_module(module)
    class_ = getattr(imported, classname)
    if not issubclass(class_, RuleEngine):
        raise ValueError("Requested class is not a RuleEngine.")
    return class_
