import os

import psycopg
import requests
from django.core.management.base import BaseCommand
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
            choices=["fks", "ksp"],
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
            "--clear",
            action="store_true",
            help="Clear old data.",
        )

    def fetch_users(self):
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
            if u["username"] == user["username"]:
                self.stderr.write(
                    self.style.WARNING(f"   - Found by username: {u['username']}")
                )
                self.stderr.write(
                    self.style.WARNING(
                        "     - Is this OK? Please manually check [y/n]: "
                    )
                )
                if input().strip().lower() != "y":
                    return None

                return u
        for u in users:
            if (
                u["first_name"] == user["first_name"]
                and u["last_name"] == user["last_name"]
            ):
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
                if input().strip().lower() != "y":
                    return None
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
            with conn.cursor(row_factory=dict_row) as cur:
                levels = cur.execute(
                    LEVELS_EXPORT_SQL[
                        options["old_contest_name"]
                    ],  # ty:ignore[invalid-argument-type]
                    (options["min_graduation"],),
                ).fetchall()

                failed = False

                for level in levels:
                    user = self.find_user(level, users)
                    if user is None:
                        failed = True

                    level["trojsten_id_user"] = user

                if failed:
                    self.stderr.write(
                        self.style.ERROR("Some users were not found, aborting.")
                    )
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
                        engine=options["rule_engine"],
                        data=level["new_level"],
                    )

                    self.stderr.write(self.style.SUCCESS("   - Done."))
