from collections import defaultdict
from functools import cache

from django.db.models import QuerySet
from django.utils.functional import cached_property

from seminare.problems.models import Problem, ProblemSet
from seminare.rules import Chip, RuleEngine
from seminare.rules.results import (
    Cell,
    ColumnHeader,
    PreviousScoreCell,
    Table,
    TextCell,
)
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.logic.permissions import is_contest_organizer
from seminare.users.models import Enrollment, User


class LevelRuleEngine(RuleEngine):
    default_level: int = 1
    max_level: int

    def get_level_for_users(self, users: "list[User]") -> dict["User", int]:
        """Returns levels for multiple users. If no data is found, returns default level."""
        rule_data = self.get_data_for_users("level", users)

        return defaultdict(
            lambda: self.default_level,
            {d.user: d.data for d in rule_data},
        )

    def get_level_for_user(self, user: "User") -> int:
        """Returns the level for a single user. If no data is found, returns default level."""
        rule_data = self.get_data_for_user("level", user)
        if rule_data is None:
            return self.default_level
        return rule_data.data

    def set_levels_for_users(self, data: dict["User", int]):
        """Sets levels for multiple users. Data is a dict mapping User to level."""
        return self.set_data_for_users(
            "level", {user: min(level, self.max_level) for user, level in data.items()}
        )

    def set_level_for_user(self, user: "User", level: int):
        """Sets level for a single user. Level is an integer."""
        return self.set_data_for_user("level", user, min(level, self.max_level))

    def should_update_levels(self) -> bool:
        """Returns True if levels should be updated on problem set close."""
        raise NotImplementedError()

    def get_new_level(
        self, user: "User", current_level: int, tables: dict[str, Table]
    ) -> int:
        """Returns the new level for a user based on the result tables."""
        raise NotImplementedError()

    def result_table_get_context(
        self, table: str, enrollments: QuerySet[Enrollment, Enrollment], context: dict
    ) -> dict:
        users = list(e.user for e in enrollments)

        context["levels"] = self.get_level_for_users(users)

        return super().result_table_get_context(table, enrollments, context)

    def result_table_get_headers(
        self, table: str, context: dict, **kwargs
    ) -> list[ColumnHeader]:
        headers = [ColumnHeader("Level", None, None)]
        return headers + super().result_table_get_headers(table, context, **kwargs)

    def result_table_get_cells(
        self, table: str, enrollment: Enrollment, context: dict, **kwargs
    ) -> list[Cell | None]:
        levels = context["levels"]
        cells = [TextCell(str(levels[enrollment.user]), None)]
        return cells + super().result_table_get_cells(
            table, enrollment, context, **kwargs
        )

    def close_problemset(self):
        if not self.should_update_levels():
            return

        enrollments = list(
            self.problem_set.enrollment_set.all().prefetch_related("user")
        )
        users = [e.user for e in enrollments]
        levels = self.get_level_for_users(users)

        tables = {
            table: self.get_result_table(table)
            for table in self.get_result_tables().keys()
        }

        new_levels: dict[User, int] = {}

        for user in users:
            if (new_level := self.get_new_level(user, levels[user], tables)) != levels[
                user
            ]:
                new_levels[user] = new_level

        self.set_levels_for_users(new_levels)

        super().close_problemset()


class PreviousProblemSetRuleEngine(RuleEngine):
    previous_problem_set_slug: str | None = None

    @cached_property
    def previous_problem_set(self) -> ProblemSet | None:
        if self.previous_problem_set_slug is None:
            return None

        return ProblemSet.objects.filter(
            contest__id=self.problem_set.contest_id,
            slug=self.previous_problem_set_slug,
        ).first()

    def parse_options(self, options: dict) -> None:
        self.previous_problem_set_slug = options.get("previous_problem_set")

        return super().parse_options(options)

    def result_table_get_context(
        self, table: str, enrollments: QuerySet[Enrollment, Enrollment], context: dict
    ) -> dict:
        if self.previous_problem_set:
            context["previous_problemset_data"] = (
                self.previous_problem_set.get_rule_engine().get_result_table(table)
            )

        return super().result_table_get_context(table, enrollments, context)

    def result_table_get_headers(
        self, table: str, context: dict, **kwargs
    ) -> list[ColumnHeader]:
        headers = super().result_table_get_headers(table, context, **kwargs)

        if self.previous_problem_set:
            headers.insert(
                0,
                ColumnHeader(
                    "P",
                    None,
                    "Body z predchádzajúceho kola",
                ),
            )

        return headers

    def result_table_get_cells(
        self, table: str, enrollment: Enrollment, context: dict, **kwargs
    ) -> list[Cell | None]:
        cells = super().result_table_get_cells(table, enrollment, context, **kwargs)

        if self.previous_problem_set:
            previous_score = next(
                (
                    row
                    for row in context["previous_problemset_data"].rows
                    if row.enrollment.user == enrollment.user
                ),
                None,
            )
            if previous_score is not None:
                cells.insert(0, PreviousScoreCell(previous_score.total))
            else:
                cells.insert(0, None)

        return cells


class LimitedSubmitRuleEngine(RuleEngine):
    max_submissions: dict[type[BaseSubmit], int] = {
        FileSubmit: 5,
        JudgeSubmit: 30,
        TextSubmit: 10,
    }

    def parse_options(self, options: dict) -> None:
        for submit_cls in BaseSubmit.get_submit_types():
            if (key := f"max_{submit_cls.__name__}_submits") in options:
                self.max_submissions[submit_cls] = options[key]

    @cache
    def get_override(self, user: User):
        return self.get_data_for_user("max_submits_override", user)

    @cache
    def get_max_submits(
        self,
        submit_cls: type[BaseSubmit],
        problem: Problem,
        enrollment: Enrollment | None,
    ) -> int:
        """Returns the maximum number of submissions allowed for a problem. -1 for unlimited."""
        if (
            enrollment is not None
            and (rule_data := self.get_override(enrollment.user)) is not None
        ):
            limit = rule_data.data.get(
                f"max_{submit_cls.__name__}_submits_{problem.number}"
            )

            if limit:
                return limit

        return self.max_submissions.get(submit_cls, -1)

    @cache
    def get_submits_count(
        self, submit_cls: type[BaseSubmit], problem: Problem, enrollment: Enrollment
    ) -> int:
        """Returns the number of submits for a given enrollment."""
        return submit_cls.objects.filter(enrollment=enrollment, problem=problem).count()

    def get_submits_chip(
        self,
        submit_cls: type[BaseSubmit],
        problem: "Problem",
        enrollment: Enrollment | None,
    ) -> Chip | None:
        if enrollment is None:
            submits = 0
        else:
            submits = self.get_submits_count(submit_cls, problem, enrollment)

        max_submits = self.get_max_submits(submit_cls, problem, enrollment)
        return Chip(
            f"{submits} / {max_submits}",
            {0: "red", 1: "amber", 2: "amber"}.get(
                max(0, max_submits - submits), "gray"
            ),
            "",
            "Limit odovzdaní. Pre navýšenie napíš na info@trojsten.sk",
        )

    def can_submit(
        self,
        submit_cls: type[BaseSubmit],
        problem: Problem,
        enrollment: Enrollment | None,
    ) -> bool:
        max_submissions = self.get_max_submits(submit_cls, problem, enrollment)
        if max_submissions == -1:
            return True

        if enrollment is not None and is_contest_organizer(
            enrollment.user, self.problem_set.contest
        ):
            return True

        if self.get_submits_count(submit_cls, problem, enrollment) >= max_submissions:
            return False

        return super().can_submit(submit_cls, problem, enrollment)
