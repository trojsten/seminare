from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from seminare.rules.scores import ResultsSerializable, Score
from seminare.users.models import Enrollment, School, User


@dataclass
class ColumnHeader(ResultsSerializable):
    title: str
    link: str | None
    tooltip: str | None

    def serialize(self) -> dict:
        return {
            "title": self.title,
            "link": self.link,
            "tooltip": self.tooltip,
        }

    @classmethod
    def deserialize(cls, data: dict) -> Self:
        return cls(
            title=data["title"],
            link=data.get("link"),
            tooltip=data.get("tooltip"),
        )


@dataclass
class Cell(ResultsSerializable):
    @property
    def display_cell(self) -> str:
        raise NotImplementedError()

    @property
    def display_tooltip(self) -> str | None:
        return None

    @property
    def ghost(self) -> bool:
        return False

    def serialize(self) -> dict:
        return {
            "display_cell": self.display_cell,
            "display_tooltip": self.display_tooltip,
            "ghost": self.ghost,
        }

    @classmethod
    def deserialize(cls, data: dict):
        return FrozenCell(
            _cell=data["display_cell"],
            _tooltip=data.get("display_tooltip"),
            _ghost=data.get("ghost", False),
        )


@dataclass
class FrozenCell(Cell):
    _cell: str
    _tooltip: str | None
    _ghost: bool

    @property
    def display_cell(self) -> str:
        return self._cell

    @property
    def display_tooltip(self) -> str | None:
        return self._tooltip

    @property
    def ghost(self) -> bool:
        return self._ghost


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
class Table(ResultsSerializable):
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

    def serialize(self) -> dict:
        rows: list[dict] = []
        schools = {}

        for row in self.rows:
            enrollment = row.enrollment
            if row.enrollment.school_id not in schools:
                schools[row.enrollment.school_id] = {
                    "name": enrollment.school.name,
                    "short_name": enrollment.school.short_name,
                    "edu_id": enrollment.school.edu_id,
                    "address": enrollment.school.address,
                }

            rows.append(
                {
                    "rank": row.rank,
                    "enrollment": {
                        "id": enrollment.id,
                        "grade": enrollment.grade,
                        "school_id": enrollment.school_id,
                        "user": {
                            "id": enrollment.user_id,
                            "username": enrollment.user.username,
                            "email": enrollment.user.email,
                            "first_name": enrollment.user.first_name,
                            "last_name": enrollment.user.last_name,
                        },
                    },
                    "ghost": row.ghost,
                    "columns": [
                        col.serialize() if col else None for col in row.columns
                    ],
                    "total": str(row.total),
                }
            )

        return {
            "columns": [col.serialize() for col in self.columns],
            "rows": rows,
            "_schools": schools,
        }

    @classmethod
    def deserialize(cls, data: dict) -> Self:
        rows = []
        schools = {}

        for id, school in data["_schools"].items():
            id = int(id)
            schools[id] = School(
                id=id,
                name=school["name"],
                short_name=school["short_name"],
                edu_id=school["edu_id"],
                address=school["address"],
            )

        for row in data["rows"]:
            rows.append(
                Row(
                    rank=row["rank"],
                    enrollment=Enrollment(
                        id=row["enrollment"]["id"],
                        grade=row["enrollment"]["grade"],
                        school=schools[row["enrollment"]["school_id"]],
                        user=User(
                            id=row["enrollment"]["user"]["id"],
                            username=row["enrollment"]["user"]["username"],
                            email=row["enrollment"]["user"]["email"],
                            first_name=row["enrollment"]["user"]["first_name"],
                            last_name=row["enrollment"]["user"]["last_name"],
                        ),
                    ),
                    ghost=row.get("ghost", False),
                    columns=[
                        Cell.deserialize(col) if col else None for col in row["columns"]
                    ],
                    total=Decimal(row["total"]),
                )
            )

        return cls(
            columns=[ColumnHeader.deserialize(col) for col in data["columns"]],
            rows=rows,
        )
