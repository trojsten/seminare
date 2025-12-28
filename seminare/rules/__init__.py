from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import cached_property
from importlib import import_module
from typing import TYPE_CHECKING, Iterable

from django.core.cache import cache
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from seminare.contests.models import RuleData
from seminare.rules.results import Cell, ColumnHeader, Row, ScoreCell, Table
from seminare.rules.scores import Score
from seminare.submits.models import BaseSubmit
from seminare.submits.utils import JSON
from seminare.users.logic.permissions import is_contest_organizer, preload_contest_roles
from seminare.users.models import Enrollment, Grade, User
from seminare.utils import (
    compress_data,
    decompress_data,
)

if TYPE_CHECKING:
    from seminare.problems.models import Problem, ProblemSet, Text
    from seminare.users.models import User


@dataclass
class Chip:
    message: str
    color: str = "gray"
    icon: str = ""
    help: str = ""


class AbstractRuleEngine:
    def __init__(self, problem_set: "ProblemSet") -> None:
        super().__init__()
        self.problem_set = problem_set
        self.parse_options(self.problem_set.rule_engine_options)

    def parse_options(self, options: dict) -> None:
        """Parses options from problem set."""
        pass

    # === Contestant frontend ===

    def get_important_dates(self) -> list[tuple[datetime, str]]:
        """
        Returns a list of important dates for the problem set.
        This is shown to the contestants.
        """
        return []

    def get_visible_texts(self, problem: "Problem") -> "set[Text.Type]":
        """
        Returns types of texts that are currently visible for a given problem.
        If problem is None, we want to know visible texts in general (e.g. for PDF statements).
        """
        raise NotImplementedError()

    def get_chips(self, user: "User") -> dict["Problem", list[Chip]]:
        """
        Returns a mapping Problem -> Chips that is used by problem list to show various
        information chips next to problems.
        Used for showing things like "you will not get any points for this problem, due to your level".
        """
        return defaultdict(list)

    def get_submits_chip(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> Chip | None:
        """
        Returns chip to be displayed in the submit form to the user.
        This is used to notify the user about any errors / warning related to that submit form.
        """
        return None

    def can_submit(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> bool:
        """
        Returns whether the user can create new submit for the given problem.
        """
        return True

    def get_enrollment(self, user: User, create=False) -> Enrollment | None:
        """
        Returns the enrollment for a given user in this problem set, or None if not enrolled.

        If create is True, creates the enrollment if it does not exist.
        """
        raise NotImplementedError()

    # === Grading & results ===

    def get_enrollments_problems_effective_submits(
        self,
        submit_cls: type[BaseSubmit],
        enrollments: Iterable[Enrollment],
        problems: "Iterable[Problem]",
    ) -> QuerySet[BaseSubmit]:
        """
        Returns a QuerySet of submits that are considered accepted for a given enrollments and problems.
        """
        raise NotImplementedError()

    def get_enrollments_problems_scores(
        self, enrollments: Iterable[Enrollment], problems: "Iterable[Problem]"
    ) -> dict[tuple[int, int], Score]:
        """
        Returns a mapping (enrollment_id, problem_id) -> Score for given list of enrollments and problems.
        """
        raise NotImplementedError()

    def get_enrollments(self) -> QuerySet[Enrollment]:
        """
        Returns a QuerySet of enrollments that are considered part of the competition.
        """
        raise NotImplementedError()

    # === Results tables ===

    def get_result_tables(self) -> dict[str, str]:
        """
        Returns a mapping slug -> display_name for all available result tables.
        """
        raise NotImplementedError()

    def get_default_result_table(self, user: User | None = None) -> str:
        """
        Returns the slug of the default result table for user or general default.
        """
        raise NotImplementedError()

    def calculate_total(self, scores: Iterable[Cell | None]) -> Decimal:
        """
        Calculates total score for a set of table Cells.
        """
        raise NotImplementedError()

    def get_coefficient_for_problem(
        self,
        problem_number: int,
        enrollment: Enrollment,
        table: str,
    ) -> Decimal:
        """
        Returns the score coefficient for a given problem in a results table.
        """
        return Decimal(1)

    def result_table_get_context(
        self, table: str, enrollments: QuerySet[Enrollment, Enrollment]
    ) -> dict:
        """
        Returns context for a given result table.
        Context will be passed to result_table_get_headers and result_table_get_cells.
        """
        return {}

    def result_table_get_headers(
        self, table: str, context: dict, **kwargs
    ) -> list[ColumnHeader]:
        """
        Returns the column headers for a given result table.
        """
        return []

    def result_table_get_cells(
        self, table: str, enrollment: Enrollment, context: dict, **kwargs
    ) -> list[Cell | None]:
        """
        Returns the cells of a row for a given result table and enrollment.
        """
        return []

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        """
        Returns whether the enrollment should be marked as ghost in the result table.
        Ghost is a result row that is shown in gray and is hidden by default.
        Ghosts can be seen by organizers and other ghosts.
        """
        return False

    def result_table_is_excluded(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        """
        Returns whether the enrollment should be excluded from a result table.
        Used to hide users from higher levels, etc.
        """
        return False

    def get_result_table(self, table: str, **kwargs) -> Table:
        """
        Returns a result table populated with data.
        """
        raise NotImplementedError()

    def close_problemset(self):
        """
        Called when problem set is marked as closed.
        Should do any house keeping tasks such as freezing the result tables, etc.
        """
        pass


class RuleEngineDataMixin:
    problem_set: "ProblemSet"
    compatible_engines: list[str] = []
    """Other compatible engine IDs that should be fetched with RuleData"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.engine_id = f"{self.__class__.__module__}.{self.__class__.__qualname__}"

    @cached_property
    def data_effective_date(self) -> datetime:
        """
        Returns the effective date for RuleData queries.
        """
        return self.problem_set.start_date

    def get_data_for_users(
        self,
        key: str,
        users: list["User"],
        engines: list[str] | None = None,
    ) -> dict[int, JSON]:
        """
        Returns stored RuleData for given users under key.
        """
        data_objs = RuleData.objects.for_users(
            contest=self.problem_set.contest,
            key=key,
            users=users,
            effective_date=self.data_effective_date,
            engines=engines or [self.engine_id, *self.compatible_engines],
        )

        output = {}
        for obj in data_objs:
            obj: RuleData
            output[obj.user_id] = obj.data
        return output

    def set_data_for_users(self, key: str, data: dict["User", JSON]):
        """
        Stores RuleData for given users under key.
        """
        return RuleData.objects.bulk_create(
            [
                RuleData(
                    contest=self.problem_set.contest,
                    key=key,
                    user=user,
                    engine=self.engine_id,
                    data=data_dict,
                )
                for user, data_dict in data.items()
            ]
        )

    def set_data_for_user(self, key: str, user: "User", data: JSON):
        """
        Stores RuleData for given users under key.
        """
        self.set_data_for_users(key, {user: data})


class RuleEngine(RuleEngineDataMixin, AbstractRuleEngine):
    def get_important_dates(self) -> list[tuple[datetime, str]]:
        return [
            (self.problem_set.start_date, "Začiatok kola"),
            (self.problem_set.end_date, "Koniec kola"),
        ]

    def get_visible_texts(self, problem: "Problem|None") -> "set[Text.Type]":
        from seminare.problems.models import Text

        visible = set()
        now = timezone.now()

        if now >= self.problem_set.start_date:
            visible.add(Text.Type.PROBLEM_STATEMENT)

        if now > self.problem_set.end_date:
            visible.add(Text.Type.EXAMPLE_SOLUTION)

        return visible

    def can_submit(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> bool:
        if (
            self.problem_set.is_public
            and timezone.now() > problem.problem_set.start_date
        ):
            return True

        if enrollment is not None and is_contest_organizer(
            enrollment.user, self.problem_set.contest
        ):
            return True

        return False

    def get_enrollment(self, user: User, create: bool = False) -> Enrollment | None:
        if hasattr(user, f"enrollment_cache_{self.problem_set.slug}"):
            return getattr(user, f"enrollment_cache_{self.problem_set.slug}")

        if create:
            enrollment, _ = Enrollment.objects.get_or_create(
                user=user,
                problem_set=self.problem_set,
                defaults={
                    "grade": user.current_grade if user.current_grade else Grade.OLD,
                    "school": user.current_school,
                },
            )
        else:
            enrollment = Enrollment.objects.filter(
                user=user, problem_set=self.problem_set
            ).first()

        if enrollment is not None:
            setattr(user, f"enrollment_cache_{self.problem_set.slug}", enrollment)

        return enrollment

    def get_enrollments_problems_scores(
        self, enrollments: Iterable[Enrollment], problems: Iterable["Problem"]
    ) -> dict[tuple[int, int], Score]:
        user_problem_submits: dict[tuple[int, int], list[BaseSubmit]]
        user_problem_submits = defaultdict(list)

        for type_ in BaseSubmit.get_submit_types():
            submits = self.get_enrollments_problems_effective_submits(
                type_, enrollments, problems
            ).select_related("enrollment")
            for submit in submits:
                key = (submit.enrollment.user_id, submit.problem_id)
                user_problem_submits[key].append(submit)

        output = {}
        for key, submits in user_problem_submits.items():
            output[key] = Score(submits)
        return output

    def get_enrollments(self) -> QuerySet[Enrollment]:
        return self.problem_set.enrollment_set.get_queryset()

    def result_table_get_context(
        self, table: str, enrollments: QuerySet[Enrollment, Enrollment]
    ) -> dict:
        users = list(e.user for e in enrollments)
        preload_contest_roles(users, self.problem_set.contest)

        context = super().result_table_get_context(table, enrollments)
        context["problems"] = self.problem_set.problems.order_by("number").all()
        context["scores"] = self.get_enrollments_problems_scores(
            enrollments, context["problems"]
        )
        return context

    def result_table_get_headers(
        self, table: str, context: dict, **kwargs
    ) -> list[ColumnHeader]:
        return [
            ColumnHeader(
                str(problem.number),
                reverse("problem_detail", args=[self.problem_set.slug, problem.number]),
                problem.name,
            )
            for problem in context["problems"]
        ]

    def result_table_get_cells(
        self, table: str, enrollment: Enrollment, context: dict, **kwargs
    ) -> list[Cell | None]:
        cells: list[Cell | None] = []

        for problem in context["problems"]:
            if (key := (enrollment.user_id, problem.id)) in context["scores"]:
                score = context["scores"][key]
                coeff = self.get_coefficient_for_problem(
                    problem.number, enrollment, table
                )
                cells.append(ScoreCell(score, coeff))
            else:
                cells.append(None)

        return cells

    def result_table_is_ghost(
        self, table: str, context: dict, enrollment: Enrollment
    ) -> bool:
        # Organizers are ghosts by default.
        return is_contest_organizer(
            enrollment.user,
            self.problem_set.contest,
        )

    def get_result_table(self, table: str, **kwargs) -> Table:
        if self.problem_set.is_finalized:
            frozen_results = self.problem_set.get_frozen_results(table)
            return Table.deserialize(frozen_results)

        key = f"results_table/{self.problem_set.slug}/{table}"
        if key in cache and (data := cache.get(key)) is not None:
            return Table.deserialize(decompress_data(data))

        enrollments = self.get_enrollments().select_related("user", "school")

        context = self.result_table_get_context(table, enrollments)
        columns = self.result_table_get_headers(table, context)

        rows = []
        for enrollment in enrollments:
            if self.result_table_is_excluded(table, context, enrollment):
                continue

            cells: list[Cell | None] = self.result_table_get_cells(
                table, enrollment, context
            )

            rows.append(
                Row(
                    rank=None,
                    enrollment=enrollment,
                    ghost=self.result_table_is_ghost(table, context, enrollment),
                    columns=cells,
                    total=self.calculate_total(cells),
                )
            )

        table_obj = Table(columns, rows)
        table_obj.sort()
        cache.set(key, compress_data(table_obj.serialize()), timeout=60 * 5)
        return table_obj

    def close_problemset(self):
        for table in self.get_result_tables().keys():
            key = f"results_table/{self.problem_set.slug}/{table}"
            cache.delete(key)

            self.problem_set.set_frozen_results(
                table, self.get_result_table(table).serialize()
            )


def get_rule_engine_class(path: str) -> type[RuleEngine]:
    module, classname = path.rsplit(".", 1)

    imported = import_module(module)
    class_ = getattr(imported, classname)
    if not issubclass(class_, RuleEngine):
        raise ValueError("Requested class is not a RuleEngine.")
    return class_
