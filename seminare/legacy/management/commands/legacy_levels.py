import json
import os
import unicodedata

import psycopg
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from psycopg.rows import dict_row

from seminare.contests.models import Contest, RuleData
from seminare.users.models import User

LEVELS_EXPORT_SQL: dict[str, str] = {
    "ksp": """
SELECT DISTINCT ON (r.user_id) r.id, r.new_level, r.user_id, u.username, u.first_name, u.last_name, u.email FROM rules_ksplevel r
    JOIN people_user u ON u.id = r.user_id
    WHERE u.graduation >= %s
    ORDER BY r.user_id, r.new_level DESC
""",
    "fks": """
SELECT DISTINCT ON (r.user_id) r.id, r.new_level, r.user_id, u.username, u.first_name, u.last_name, u.email FROM rules_fkslevel r
    JOIN people_user u ON u.id = r.user_id
    WHERE u.graduation >= %s
    ORDER BY r.user_id, r.new_level DESC
""",
}


class Command(BaseCommand):
    help = "Migrate rounds from legacy site"

    def add_arguments(self, parser):
        parser.add_argument(
            "--contest",
            type=int,
            help="Contest ID on new site.",
            required=True,
        )
        parser.add_argument(
            "--old-contest-name",
            type=str,
            choices=["fks", "ksp", "kms"],
            help="Contest ID on old site.",
            required=True,
        )
        parser.add_argument(
            "--rule-engine",
            type=str,
            help="Rule Engine class path for create RuleData.",
            required=True,
        )
        parser.add_argument(
            "--min-graduation",
            type=int,
            help="Minimum graduation year user must have to be migrated.",
            required=True,
        )
        parser.add_argument(
            "--levels-json",
            type=str,
            help="Path to JSON with users and levels (KMS).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear old data.",
        )

    def normalized_compare(self, a: str, b: str):
        return (
            "".join(
                c
                for c in unicodedata.normalize("NFD", a)
                if unicodedata.category(c) != "Mn"
            ).lower()
            == "".join(
                c
                for c in unicodedata.normalize("NFD", b)
                if unicodedata.category(c) != "Mn"
            ).lower()
        )

    def fetch_users(self) -> list[dict]:
        response = self.session.get("https://id.trojsten.sk/api/users/")
        response.raise_for_status()
        self.stderr.write(
            self.style.MIGRATE_HEADING("Fetched users from Trojsten ID...")
        )
        return response.json()

    def find_user(self, user: dict, users: list[dict]) -> dict | None:
        self.stderr.write(
            self.style.MIGRATE_HEADING(
                f" - Finding user for {user['first_name']} {user['last_name']} ({user['username']}) {user['email']}..."
            )
        )
        for u in users:
            if u["email"].lower() == user["email"].lower():
                self.stderr.write(
                    self.style.SUCCESS(f"   - Found by email: {u['email']}")
                )
                return u
        for u in users:
            if self.normalized_compare(u["username"], user["username"]):
                self.stderr.write(
                    self.style.WARNING(f"   - Found by username: {u['username']}")
                )
                self.stderr.write(
                    self.style.WARNING(
                        "     - Is this OK? Please manually check [y/n]: "
                    )
                )
                if input().strip().lower() == "y":
                    return u

        for u in users:
            if self.normalized_compare(
                u["first_name"], user["first_name"]
            ) and self.normalized_compare(u["last_name"], user["last_name"]):
                self.stderr.write(
                    self.style.WARNING(
                        f"   - Found by name: {u['first_name']} {u['last_name']}"
                    )
                )
                self.stderr.write(
                    self.style.WARNING(
                        "     - Is this OK? Please manually check [y/n]: "
                    )
                )
                if input().strip().lower() == "y":
                    return u

        self.stderr.write(self.style.ERROR("   - User not found."))
        return None

    def get_or_create_user(self, trojsten_id_user: dict) -> User:
        user, created = User.objects.get_or_create(
            trojsten_id=trojsten_id_user["id"],
            defaults={
                "email": trojsten_id_user["email"],
                "username": trojsten_id_user["username"],
                "first_name": trojsten_id_user["first_name"],
                "last_name": trojsten_id_user["last_name"],
            },
        )
        if created:
            self.stderr.write(
                self.style.MIGRATE_HEADING(
                    f"   - Created new user with Trojsten ID {trojsten_id_user['id']}."
                )
            )
        return user

    def migrate_levels(
        self, conn, levels: list[dict], users: list[dict], rule_engine: str
    ) -> None:
        failed = False

        for level in levels:
            user = self.find_user(level, users)
            if user is None:
                failed = True

            level["trojsten_id_user"] = user

        if failed:
            self.stderr.write(self.style.ERROR("Some users were not found, aborting."))

            data = []
            for level in levels:
                if level["trojsten_id_user"] is None:
                    del level["trojsten_id_user"]
                    del level["new_level"]
                    if "password" not in level:
                        with conn.cursor(row_factory=dict_row) as cur:
                            cur.execute(
                                "SELECT password FROM people_user WHERE id = %s",
                                (level["user_id"],),
                            )
                            row = cur.fetchone()
                            level["password"] = row["password"]
                    data.append(level)

            import json

            self.stdout.write(json.dumps(data, indent=4, ensure_ascii=False))

            self.stderr.write(self.style.ERROR("Some users were not found, aborting."))
            exit(1)

        for level in levels:
            self.stderr.write(
                self.style.MIGRATE_HEADING(
                    f" - Migrating level for {level['first_name']} {level['last_name']} ({level['username']}) {level['email']}..."
                )
            )

            user = self.get_or_create_user(level["trojsten_id_user"])

            RuleData.objects.create(
                contest=self.contest,
                key="level",
                user=user,
                engine=rule_engine,
                data=level["new_level"],
            )

            self.stderr.write(self.style.SUCCESS("   - Done."))

    @transaction.atomic
    def execute(self, *args, **options):
        if "LEGACY_DB" not in os.environ:
            self.stderr.write(
                self.style.ERROR("Set LEGACY_DB env to connection string.")
            )
            exit(1)
        if "TROJSTEN_ID_TOKEN" not in os.environ:
            self.stderr.write(
                self.style.ERROR("Set TROJSTEN_ID_TOKEN env to Trojsten ID token.")
            )
            exit(1)

        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Token {os.environ['TROJSTEN_ID_TOKEN']}"}
        )

        self.contest = Contest.objects.get(id=options["contest"])

        if options["clear"]:
            RuleData.objects.filter(contest=self.contest).delete()

        users = self.fetch_users()

        with psycopg.connect(os.environ["LEGACY_DB"]) as conn:
            if options["old_contest_name"] == "kms":
                if "levels_json" not in options or options["levels_json"] is None:
                    self.stderr.write(
                        self.style.ERROR("For KMS, --levels-json argument is required.")
                    )
                    exit(1)

                with open(options["levels_json"], "r", encoding="utf-8") as f:
                    levels = json.load(f)
            else:
                with conn.cursor(row_factory=dict_row) as cur:
                    levels = cur.execute(
                        LEVELS_EXPORT_SQL[
                            options["old_contest_name"]
                        ],  # ty:ignore[invalid-argument-type]
                        (options["min_graduation"],),
                    ).fetchall()

            self.migrate_levels(conn, levels, users, options["rule_engine"])

            self.stderr.write(self.style.SUCCESS("All done."))
            self.stderr.write(self.style.NOTICE("Please link following accounts:"))
            data = []
            for u in levels:
                data.append(
                    {
                        "id": u["trojsten_id_user"]["id"],
                        "uid": u["user_id"],
                        "extra": {
                            "sub": str(u["user_id"]),
                            "name": f"{u['first_name']} {u['last_name']}",
                            "email": u["email"],
                            "given_name": u["first_name"],
                            "family_name": u["last_name"],
                            "preferred_username": u["username"],
                        },
                    }
                )

            self.stdout.write(json.dumps(data, indent=4, ensure_ascii=False))
