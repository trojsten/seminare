import os
import re
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Generator

import psycopg
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from psycopg.rows import DictRow, dict_row

from seminare.contests.models import Contest
from seminare.legacy.models import OldProblem, OldRound
from seminare.problems.models import Problem, ProblemSet, Text

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

RESULTS_EXPORT_SQL = """
SELECT DISTINCT ON (r.tag) r.id, r.tag, r.round_id, r.serialized_results
  FROM results_results r
  WHERE r.round_id = %s
  ORDER BY r.tag, r.time DESC
"""


class HTMLMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output = []
        self.href_stack = []
        self.math_stack = []
        self.in_pre = False
        self.pre_lang = ""
        self.in_style = False
        self.list_stack = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_dict = {k.lower(): v for k, v in attrs}

        if tag == "style":
            self.in_style = True
            return

        if tag == "pre" and "class" in attr_dict:
            classes = attr_dict["class"].split()
            # pick first class that's not 'sourceCode'
            lang = next((c for c in classes if c.lower() != "sourcecode"), "")
            self.pre_lang = lang.lower()
            fence = "```" + (self.pre_lang if self.pre_lang else "")
            # ensure blank line before block
            self.output.append("\n\n" + fence + "\n")
            self.in_pre = True
            return

        if self.in_style or self.in_pre:
            return

        if tag == "ul":
            self.list_stack.append({"type": "ul"})
            return
        elif tag == "ol":
            self.list_stack.append({"type": "ol", "counter": 1})
            return
        elif tag == "li":
            level = len(self.list_stack)
            indent = "  " * (level - 1) if level > 0 else ""
            top = self.list_stack[-1]
            if top["type"] == "ul":
                prefix = "- "
            else:
                prefix = f"{top['counter']}. "
                top["counter"] += 1
            self.output.append("\n" + indent + prefix)
        elif tag == "img":
            alt = attr_dict.get("alt", "")
            src = attr_dict.get("src", "")
            title = attr_dict.get("title", "")
            title_part = f' "{title}"' if title else ""
            self.output.append(f"![{alt}]({src}{title_part})")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.output.append("\n" + "#" * level + " ")
        elif tag == "p":
            if not self.list_stack:
                self.output.append("\n\n")
        elif tag == "a":
            href = attr_dict.get("href", "")
            self.href_stack.append(href)
            self.output.append("[")
        elif tag == "code":
            self.output.append("`")
        elif tag == "pre":
            lang = attr_dict.get("class", "").replace("language-", "")
            fence = "```" + (lang if lang else "")
            self.output.append("\n\n" + fence + "\n")
        elif (
            tag == "span"
            and "class" in attr_dict
            and "math" in attr_dict["class"].split()
        ):
            stack = "$" if "inline" in attr_dict["class"].split() else "$$"
            self.math_stack.append(stack)
            self.output.append(stack)
        elif tag in ("strong", "b"):
            self.output.append("**")
        elif tag in ("em", "i", "figcaption"):
            self.output.append("*")
        elif tag == "u":
            self.output.append("<u>")
        elif tag == "figure":
            return
        else:
            parts = [tag]
            for k, v in attrs:
                v_escaped = escape(v, quote=True)
                parts.append(f'{k}="{v_escaped}"')
            self.output.append(f"<{' '.join(parts)}>")

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag == "style":
            self.in_style = False
            return

        if tag == "pre" and self.in_pre:
            self.output.append("\n```" + "\n\n")
            self.in_pre = False
            self.pre_lang = ""
            return

        if self.in_pre or self.in_style:
            return

        if tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "li" or tag == "img":
            return
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.output.append("\n\n")
        elif tag == "p":
            self.output.append("\n\n")
        elif tag == "a":
            href = self.href_stack.pop() if self.href_stack else ""
            self.output.append(f"]({href})")
        elif tag == "code":
            self.output.append("`")
        elif tag == "pre":
            self.output.append("\n```" + "\n\n")
        elif tag == "span":
            if self.math_stack:
                self.output.append(self.math_stack.pop())
            else:
                self.output.append("</span>")
        elif tag in ("strong", "b"):
            self.output.append("**")
        elif tag in ("em", "i", "figcaption"):
            self.output.append("*")
        elif tag == "u":
            self.output.append("</u>")
        elif tag == "figure":
            return
        else:
            self.output.append(f"</{tag}>")

    def handle_data(self, data):
        if self.in_style:
            return
        self.output.append(unescape(data))

    def handle_entityref(self, name):
        if self.in_style:
            return
        self.output.append(unescape(f"&{name};"))

    def handle_charref(self, name):
        if self.in_style:
            return
        self.output.append(unescape(f"&#{name};"))

    def handle_comment(self, data):
        return

    def handle_decl(self, decl):
        # self.output.append(f"<!{decl}>")
        return

    def handle_pi(self, data):
        # self.output.append(f"<?{data}>")
        return

    def get_markdown(self):
        text = "".join(self.output).strip()
        # collapse multiple blank lines to max two
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        text = re.sub(r"\$\\\((.+?)\\\)\$", r"$\1$", text, flags=re.DOTALL)
        text = re.sub(r"\$\$\\\[(.+?)\\\]\$\$", r"$$\1$$", text, flags=re.DOTALL)

        return text + "\n"


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

    def migrate_problem_sets(
        self, cur: psycopg.Cursor[DictRow], **options
    ) -> list[ProblemSet]:
        cur.execute(ROUNDS_EXPORT_SQL, (options["legacy_site"],))

        problem_sets: list[ProblemSet] = []

        while row := cur.fetchone():
            rule_engine_options = {}

            if (
                row["second_end_time"]
                or options["rule_engine"] == "seminare.rules.ksp.KSP2025"
            ):
                # it requires at least some date
                rule_engine_options["doprogramovanie_date"] = row[
                    "end_time"
                ].isoformat()

            if row["number"] > 1:
                rule_engine_options["previous_problem_set"] = (
                    f"r{row['year']}{['z', 'l'][row['semester_number'] - 1]}{row['number'] - 1}"
                )

            kwargs = {}

            legacy_path: Path = (
                Path(options["legacy_dir"])
                / "tasks"
                / options["legacy_site"]
                / str(row["year"])
                / str(row["semester_number"])
                / str(row["number"])
            )

            if (path := legacy_path / "zadania" / "zadania.pdf").exists():
                kwargs["statement_pdf"] = File(path.open("rb"), name=path.name)
            if (path := legacy_path / "vzoraky" / "vzoraky.pdf").exists():
                kwargs["solution_pdf"] = File(path.open("rb"), name=path.name)

            problem_set = ProblemSet.objects.create(
                contest=self.contest,
                slug=f"r{row['year']}{['z', 'l'][row['semester_number'] - 1]}{row['number']}",
                name=f"{row['number']}. kolo {row['semester_number']}. časť {row['year']}. ročník {options['legacy_site']}",
                start_date=row["start_time"],
                end_date=row["second_end_time"]
                if row["second_end_time"]
                else row["end_time"],
                is_public=row["visible"],
                is_finalized=True,
                rule_engine=options["rule_engine"],
                rule_engine_options=rule_engine_options,
                **kwargs,
            )

            setattr(problem_set, "legacy_id", row["id"])
            setattr(problem_set, "legacy_path", legacy_path)

            OldRound.objects.create(
                contest=self.contest, old_round_id=row["id"], problem_set=problem_set
            )

            self.stderr.write(problem_set.slug)

            problem_sets.append(problem_set)

        return problem_sets

    def parse_text(self, text: str):
        parser = HTMLMarkdownParser()
        parser.feed(text)
        parser.close()
        text = parser.get_markdown()
        text = re.sub(r"obrazky\/prikl[0-9]\/", "", text)
        return text

    def extract_files(
        self, legacy_path: Path, text: str
    ) -> Generator[Path, None, None]:
        for match in re.finditer(r'(?:(?:src|href)=["\']([^"\']+)["\'])', text):
            file_path = Path(match[1])
            if (
                not file_path.is_absolute()
                and (path := (legacy_path / file_path)).exists()
            ):
                yield path

    def migrate_problems(
        self, problem_set: ProblemSet, cur: psycopg.Cursor[DictRow], **options
    ):
        cur.execute(TASK_EXPORT_SQL, (getattr(problem_set, "legacy_id"),))
        while row := cur.fetchone():
            args = {}
            if row["has_source"]:
                args["judge_namespace"] = self.contest.short_name.lower()
                args["judge_task"] = f"{problem_set.slug}p{row['number']}"

            problem: Problem = problem_set.problems.create(
                name=row["name"],
                number=row["number"],
                problem_set=problem_set,
                file_points=row["description_points"],
                judge_points=row["source_points"]
                if row["has_source"]
                else 0,  # external_submit_link ?
                **args,
            )

            OldProblem.objects.create(
                contest=self.contest, old_problem_id=row["id"], problem=problem
            )

            legacy_path: Path = getattr(problem_set, "legacy_path")

            if (
                path := legacy_path / "zadania" / "html" / f"prikl{problem.number}.html"
            ).exists():
                original_text = path.read_text()
                text = self.parse_text(original_text)
                problem.text_set.create(
                    type=Text.Type.PROBLEM_STATEMENT,
                    text=text,
                    problem=problem,
                )

                root = Path(problem.get_data_root(True))
                root.mkdir(parents=True, exist_ok=True)

                for file in self.extract_files(legacy_path, original_text):
                    default_storage.save(str(root / file.name), file.open("rb"))

            if (
                path := legacy_path / "vzoraky" / "html" / f"prikl{problem.number}.html"
            ).exists():
                original_text = path.read_text()
                text = self.parse_text(original_text)
                problem.text_set.create(
                    type=Text.Type.EXAMPLE_SOLUTION,
                    text=text,
                    problem=problem,
                )

                root = Path(problem.get_data_root(True))
                root.mkdir(parents=True, exist_ok=True)

                for file in self.extract_files(legacy_path, original_text):
                    default_storage.save(str(root / file.name), file.open("rb"))

            self.stderr.write(f"{problem_set.slug}p{row['number']} {row['name']}")

    def get_grade(self, year: int):
        if year > 5:
            return "OLD"
        elif year < -4:
            return "YOUNG"
        elif year <= 0:
            return f"{9 + year}ZS"
        else:
            return f"{year}SS"

    def migrate_results(
        self, problem_set: ProblemSet, cur: psycopg.Cursor[DictRow], **options
    ):
        cur.execute(RESULTS_EXPORT_SQL, (getattr(problem_set, "legacy_id"),))

        while row := cur.fetchone():
            self.stderr.write(f"  results {row['tag']}")

            results = row["serialized_results"]
            assert isinstance(results, dict)

            data = {
                "rows": [],
                "columns": [],
                "_schools": {
                    -1: {
                        "name": "Iná škola",
                        "short_name": "Iná škola",
                        "edu_id": "",
                        "address": "",
                    }
                },
            }

            for col in results["cols"]:
                if col["key"] == "sum":
                    continue

                c = {"link": None, "title": col["name"], "tooltip": None}

                if c["title"] == "P":
                    c["tooltip"] = "Body z predchádzajúceho kola"

                elif "task" in col:
                    c["link"] = f"/kola/{problem_set.slug}/ulohy/{col['name']}/"
                    c["tooltip"] = col["task"]["name"]
                data["columns"].append(c)

            for r in results["rows"]:
                data["rows"].append(
                    {
                        "rank": r["rank"],
                        "ghost": not r["active"],
                        "total": r["cell_list"][-1]["points"],
                        "columns": [
                            {
                                "cell": col["points"],
                                "ghost": not col["active"],
                                "tooltip": f"Program: {col.get('auto_points', '-')}, Popis: {col.get('manual_points', '-')}"
                                if options["legacy_site"] in {"KSP", "PRASK"}
                                else None,
                            }
                            for col in r["cell_list"][:-1]
                        ],
                        "enrollment": {
                            "id": None,
                            "user": {
                                "id": None,  # TODO: maybe set ID for users that are migrated?
                                "email": "",
                                "username": r["user"]["username"],
                                "first_name": r["user"]["name"].split(" ")[0],
                                "last_name": " ".join(r["user"]["name"].split(" ")[1:]),
                            },
                            "grade": self.get_grade(r["user"]["year"]),
                            "school_id": r["user"]["school"]["id"]
                            if r["user"]["school"] is not None
                            else -1,
                        },
                    }
                )

                if r["user"]["school"] is not None:
                    if r["user"]["school"]["id"] not in data["_schools"]:
                        data["_schools"][r["user"]["school"]["id"]] = {
                            "name": r["user"]["school"]["verbose_name"],
                            "short_name": r["user"]["school"]["name"],
                            "edu_id": "",
                            "address": "",
                        }

            problem_set.frozen_results.create(
                table=row["tag"].split("_")[-1].replace("ALL", "all")
                if row["tag"] != "_"
                else "all",
                data=data,
                problem_set=problem_set,
            )

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
            with conn.cursor(row_factory=dict_row) as cur:
                problem_sets = self.migrate_problem_sets(cur, **options)
                for ps in problem_sets:
                    self.migrate_problems(ps, cur, **options)
                    self.migrate_results(ps, cur, **options)
