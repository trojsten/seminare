from datetime import datetime
from decimal import Decimal
from importlib import import_module
from typing import TYPE_CHECKING, Iterable

from django.db.models import QuerySet

from seminare.rules.results import Cell, Table
from seminare.rules.scores import Score
from seminare.submits.models import BaseSubmit
from seminare.users.models import Enrollment

if TYPE_CHECKING:
    from seminare.problems.models import Problem, ProblemSet, Text


class RuleEngine:
    def __init__(self, problem_set: "ProblemSet") -> None:
        self.problem_set = problem_set
        self.parse_options(self.problem_set.rule_engine_options)

    def parse_options(self, options: dict) -> None:
        pass

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
        problems: Iterable[Problem],
    ) -> QuerySet[BaseSubmit]:
        """Returns a QuerySet of submits that are considered accepted for a given list of enrollments and problems."""
        raise NotImplementedError()

    def get_enrollments_problems_scores(
        self, enrollments: Iterable[Enrollment], problems: Iterable[Problem]
    ) -> dict[tuple[int, int], Score]:
        """Returns a mapping (enrollment_id, problem_id) -> Score for given list of enrollments and problems."""
        raise NotImplementedError()

    def get_enrollments(self) -> QuerySet[Enrollment]:
        """Returns a QuerySet of enrollments that are considered part of the competition."""
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


def get_rule_engine_class(path: str) -> type[RuleEngine]:
    module, classname = path.rsplit(".", 1)

    imported = import_module(module)
    class_ = getattr(imported, classname)
    if not issubclass(class_, RuleEngine):
        raise ValueError("Requested class is not a RuleEngine.")
    return class_
