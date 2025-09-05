import os
from pathlib import Path

import psycopg
from django.core.management.base import BaseCommand
from psycopg.rows import namedtuple_row

from seminare.contests.models import Contest
from seminare.legacy.models import OldProblem, OldRound
from seminare.problems.models import ProblemSet, Text

ROUNDS_EXPORT_SQL = """
SELECT r.id, r.start_time, r.end_time, r.second_end_time, r.visible, r.number, s.number AS semester_number, s.year
  FROM contests_round r
  JOIN contests_semester s ON r.semester_id = s.id
  JOIN contests_competition c ON s.competition_id = c.id
  WHERE c.name = %s
  ORDER BY start_time
"""

TASK_EXPORT_SQL = """
SELECT t.id, t.name, t.number, t.description_points, t.source_points, t.has_source, t.has_description, t.has_testablezip, t.external_submit_link
  FROM contests_task t
  WHERE t.round_id = %s
"""


class Command(BaseCommand):
    help = "Migrate rounds from legacy site"

    def add_arguments(self, parser):
        parser.add_argument(
            "--legacy-site",
            type=str,
            help="Site name on legacy.",
            required=True,
        )
        parser.add_argument(
            "--legacy-dir",
            type=str,
            help="Path to archiv:/var/www/trojstenweb.",
            required=True,
        )
        parser.add_argument(
            "--contest",
            type=int,
            help="Contest ID on new site.",
            required=True,
        )
        parser.add_argument(
            "--rule-engine",
            type=str,
            help="Rule Engine class path for imported problem sets.",
            required=True,
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear old data.",
        )

    def migrate_problem_sets(self, cur: psycopg.Cursor, **options) -> list[ProblemSet]:
        cur.execute(ROUNDS_EXPORT_SQL, (options["legacy_site"],))

        problem_sets: list[ProblemSet] = []

        while row := cur.fetchone():
            rule_engine_options = {}

            if (
                row.second_end_time
                or options["rule_engine"] == "seminare.rules.ksp.KSP2025"
            ):
                # it requires at least some date
                rule_engine_options["doprogramovanie_date"] = row.end_time.isoformat()

            if row.number > 1:
                rule_engine_options["previous_problem_set"] = (
                    f"r{row.year}{['z', 'l'][row.semester_number - 1]}{row.number - 1}"
                )

            problem_set = ProblemSet.objects.create(
                contest=self.contest,
                slug=f"r{row.year}{['z', 'l'][row.semester_number - 1]}{row.number}",
                name=f"{row.number}. kolo {row.semester_number}. časť {row.year}. ročník {options['legacy_site']}",
                start_date=row.start_time,
                end_date=row.second_end_time if row.second_end_time else row.end_time,
                is_public=row.visible,
                rule_engine=options["rule_engine"],
                rule_engine_options=rule_engine_options,
            )
            setattr(problem_set, "legacy_id", row.id)
            setattr(problem_set, "legacy_number", row.number)
            setattr(problem_set, "legacy_semester_number", row.semester_number)
            setattr(problem_set, "legacy_year", row.year)

            OldRound.objects.create(
                contest=self.contest, old_round_id=row.id, problem_set=problem_set
            )

            self.stderr.write(problem_set.slug)

            problem_sets.append(problem_set)

        return problem_sets

    def migrate_problems(self, problem_set: ProblemSet, cur: psycopg.Cursor, **options):
        cur.execute(TASK_EXPORT_SQL, (getattr(problem_set, "legacy_id"),))
        while row := cur.fetchone():
            args = {}
            if row.has_source:
                args["judge_namespace"] = self.contest.short_name.lower()
                args["judge_task"] = f"{problem_set.slug}p{row.number}"

            problem = problem_set.problems.create(
                name=row.name,
                number=row.number,
                problem_set=problem_set,
                file_points=row.description_points,
                judge_points=row.source_points
                if row.has_source
                else 0,  # external_submit_link ?
                **args,
            )

            OldProblem.objects.create(
                contest=self.contest, old_problem_id=row.id, problem=problem
            )

            legacy_path: Path = (
                Path(options["legacy_dir"])
                / "tasks"
                / options["legacy_site"]
                / str(getattr(problem_set, "legacy_year"))
                / str(getattr(problem_set, "legacy_semester_number"))
                / str(getattr(problem_set, "legacy_number"))
            )

            # TODO: prilohy
            if (
                path := legacy_path / "zadania" / "html" / f"prikl{problem.number}.html"
            ).exists():
                problem.text_set.create(
                    type=Text.Type.PROBLEM_STATEMENT,
                    text=path.read_text(),
                    problem=problem,
                )

            if (
                path := legacy_path / "vzoraky" / "html" / f"prikl{problem.number}.html"
            ).exists():
                problem.text_set.create(
                    type=Text.Type.EXAMPLE_SOLUTION,
                    text=path.read_text(),
                    problem=problem,
                )

            self.stderr.write(f"{problem_set.slug}p{row.number} {row.name}")

    def execute(self, *args, **options):
        if "LEGACY_DB" not in os.environ:
            self.stderr.write(
                self.style.ERROR("Set LEGACY_DB env to connection string.")
            )
            exit(1)

        self.contest = Contest.objects.get(id=options["contest"])

        if options["clear"]:
            ProblemSet.objects.filter(contest=self.contest).delete()

        with psycopg.connect(os.environ["LEGACY_DB"]) as conn:
            with conn.cursor() as cur:
                cur.row_factory = namedtuple_row

                problem_sets = self.migrate_problem_sets(cur, **options)
                for ps in problem_sets:
                    self.migrate_problems(ps, cur, **options)
