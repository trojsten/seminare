from dataclasses import dataclass
from decimal import Decimal

from seminare.rules.scores import Score
from seminare.users.models import Enrollment


@dataclass
class ColumnHeader:
    title: str
    link: str | None
    tooltip: str | None


@dataclass
class Cell:
    @property
    def display_cell(self) -> str:
        raise NotImplementedError()

    @property
    def display_tooltip(self) -> str | None:
        return None

    @property
    def ghost(self) -> bool:
        return False


@dataclass
class ScoreCell(Cell):
    score: Score
    coefficient: Decimal

    @property
    def total(self) -> Decimal:
        return self.score.points * self.coefficient

    @property
    def display_cell(self) -> str:
        return self.score.display

    @property
    def display_tooltip(self) -> str | None:
        return (
            f"{self.score.display} (×{self.coefficient})"
            if self.coefficient != 1
            else None
        )

    @property
    def ghost(self):
        return self.coefficient == 0


@dataclass
class PreviousScoreCell(Cell):
    points: Decimal

    @property
    def display_cell(self) -> str:
        display_string = f"{self.points:.0f}"
        if not float(self.points).is_integer():
            display_string = f"{self.points:.1f}"

        return display_string


@dataclass
class TextCell(Cell):
    text: str
    tooltip: str | None

    @property
    def display_cell(self) -> str:
        return self.text

    @property
    def display_tooltip(self) -> str | None:
        return self.tooltip


@dataclass
class Row:
    rank: int | None
    enrollment: Enrollment
    ghost: bool

    columns: list[Cell | None]
    total: Decimal


@dataclass
class Table:
    columns: list[ColumnHeader]
    rows: list[Row]

    def sort(self) -> None:
        self.rows.sort(key=lambda r: -r.total)
        self.rank()

    def rank(self):
        rank = 1
        last_total = -1
        for row in self.rows:
            if row.ghost or row.total == last_total:
                row.rank = None
            else:
                row.rank = rank

            if not row.ghost:
                rank += 1
                last_total = row.total
