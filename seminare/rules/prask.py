from decimal import Decimal
from typing import TYPE_CHECKING, Iterable

from seminare.rules import Chip, RuleEngine
from seminare.rules.common import BestSubmitRuleEngine, PreviousProblemSetRuleEngine
from seminare.rules.results import Cell, PreviousScoreCell, ScoreCell
from seminare.users.models import Enrollment, Grade, User

if TYPE_CHECKING:
    from seminare.problems.models import Problem
    from seminare.users.models import User


class Prask2025(BestSubmitRuleEngine, PreviousProblemSetRuleEngine, RuleEngine):
    problem_types_mappings = {1: "inter", 2: "prog", 3: "prog", 4: "teor", 5: "teor"}

    def parse_options(self, options: dict) -> None:
        """Parses options from problem set."""
        if "problem_types_mappings" in options:
            self.problem_types_mappings = options["problem_types_mappings"]

    # === Contestant frontend ===

    def get_chips(self, user: "User") -> dict["Problem", list[Chip]]:
        chips = super().get_chips(user)

        mapping = {
            "inter": Chip("Interaktívna", "amber", "mdi:interaction-tap"),
            "prog": Chip("Programovacia", "green", "mdi:code-braces"),
            "teor": Chip("Teoretická", "blue", "mdi:head-thinking-outline"),
        }

        for problem in self.problem_set.problems.all():
            if problem.number in self.problem_types_mappings:
                chips[problem] = [mapping[self.problem_types_mappings[problem.number]]]

        return chips

    # === Grading & results ===

    # === Results tables ===

    def get_result_tables(self) -> dict[str, str]:
        return {"all": "Prask"}

    def get_default_result_table(self, user: User | None = None) -> str:
        return "all"

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        total = Decimal(0)
        for score in scores:
            if isinstance(score, PreviousScoreCell):
                total += score.points
                continue

            if not isinstance(score, ScoreCell):
                continue
            total += score.score.points * score.coefficient

        return total

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        return Grade.is_old(enrollment.grade, True) or super().result_table_is_ghost(
            table, context, enrollment
        )
