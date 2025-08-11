from decimal import Decimal
from typing import Sequence

from seminare.submits.models import BaseSubmit


class Score:
    def __init__(self, submits: Sequence[BaseSubmit]):
        self.submits = submits

    @property
    def points(self) -> Decimal:
        total_score = Decimal(0)
        for submit in self.submits:
            if submit.score:
                total_score += submit.score
        return total_score

    @property
    def pending(self):
        return any(submit.score is None for submit in self.submits)

    @property
    def display(self) -> str:
        points = self.points
        display_string = f"{self.points:.0f}"
        if not float(points).is_integer():
            display_string = f"{self.points:.1f}"

        if self.pending:
            display_string += "?"

        return display_string
