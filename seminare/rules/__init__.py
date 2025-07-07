from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from seminare.problems.models import ProblemSet


class RuleEngine:
    def __init__(self, problem_set: "ProblemSet") -> None:
        self.problem_set = problem_set


def get_rule_engine_class(path: str) -> type[RuleEngine]:
    module, classname = path.rsplit(".", 1)

    imported = import_module(module)
    class_ = getattr(imported, classname)
    if not issubclass(class_, RuleEngine):
        raise ValueError("Requested class is not a RuleEngine.")
    return class_
