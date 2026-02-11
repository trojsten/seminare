from decimal import Decimal
from typing import TYPE_CHECKING, Self, Sequence

from seminare.submits.models import BaseSubmit

if TYPE_CHECKING:
    from seminare.problems.models import Problem


class ResultsSerializable:
    def serialize(self) -> dict:
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, data: dict) -> Self:
        raise NotImplementedError()


class Score(ResultsSerializable):
    def __init__(self, submits: Sequence[BaseSubmit], problem: "Problem"):
        self.submits = submits
        self.problem = problem

    @property
    def points(self) -> Decimal:
        total_score = Decimal(0)
        for submit in self.submits:
            if submit.points_visible(self.problem):
                total_score += submit.score
        return total_score

    @property
    def pending(self):
        return any(not submit.points_visible(self.problem) for submit in self.submits)

    @property
    def all_pending(self):
        return all(not submit.points_visible(self.problem) for submit in self.submits)

    @property
    def display(self) -> str:
        if self.all_pending:
            return "?"

        points = self.points
        display_string = f"{self.points:.0f}"
        if not float(points).is_integer():
            display_string = f"{self.points:.1f}"

        if self.pending:
            display_string += "?"

        return display_string

    def serialize(self) -> dict:
        return {
            "submits": [submit.id for submit in self.submits],
            "points": str(self.points),
            "pending": self.pending,
            "display": self.display,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return FrozenScore(
            points=Decimal(data["points"]),
            pending=data["pending"],
            display=data["display"],
        )


class FrozenScore(ResultsSerializable):
    def __init__(
        self,
        points: Decimal,
        pending: bool,
        display: str,
    ):
        self._points = points
        self._pending = pending
        self._display = display

    @property
    def points(self) -> Decimal:
        return self._points

    @property
    def pending(self) -> bool:
        return self._pending

    @property
    def display(self) -> str:
        return self._display
