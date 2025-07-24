from datetime import datetime
from importlib import import_module
from typing import TYPE_CHECKING

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
            (self.problem_set.start_date, "Začiatok sady"),
            (self.problem_set.end_date, "Koniec sady"),
        ]


def get_rule_engine_class(path: str) -> type[RuleEngine]:
    module, classname = path.rsplit(".", 1)

    imported = import_module(module)
    class_ = getattr(imported, classname)
    if not issubclass(class_, RuleEngine):
        raise ValueError("Requested class is not a RuleEngine.")
    return class_
