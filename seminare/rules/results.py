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
    score: Score
    coefficient: Decimal

    @property
    def total(self) -> Decimal:
        return self.score.points * self.coefficient


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
        self.rows.sort(key=lambda r: r.total)
