import random
from datetime import datetime, timedelta
from typing import Iterable

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.utils import timezone

from seminare.contests.models import Contest, RuleData
from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.models import Enrollment, Grade, School, User


class Command(BaseCommand):
    help = "Generate dummy data for testing purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force the command to run.",
        )

    def create_contest(self) -> Contest:
        contest, created = Contest.objects.update_or_create(
            name="Korešpondenčný seminár z programovania",
            short_name="ksp",
            site=Site.objects.get_or_create(
                domain="ksp.localhost:8000", name="ksp.localhost:8000"
            )[0],
        )
        if not created:
            self.stdout.write(
                self.style.WARNING(
                    "Contest already exists, deleting all existing RuleData associated with it"
                )
            )
            RuleData.objects.filter(contest=contest).delete()

        return contest

    def create_users(self, count: int = 300) -> list[User]:
        users: list[User] = []

        first_names = [
            "Adam",
            "Adrián",
            "Anna",
            "Barbora",
            "Daniela",
            "Dominik",
            "Eva",
            "Filip",
            "Gabriel",
            "Jakub",
            "Ján",
            "Katarína",
            "Kristína",
            "Lucia",
            "Lukáš",
            "Marek",
            "Martin",
            "Michal",
            "Mária",
            "Nina",
            "Oliver",
            "Patrícia",
            "Peter",
            "Richard",
            "Samuel",
            "Tomáš",
            "Veronika",
            "Viktória",
            "Zuzana",
            "Šimon",
        ]
        last_names = [
            "Baláž",
            "Bartoš",
            "Bauer",
            "Bielik",
            "Dvořák",
            "Hajduk",
            "Horváth",
            "Hruška",
            "Kiss",
            "Kováč",
            "Kováčik",
            "Kováčová",
            "Krajčír",
            "Kubiš",
            "Kučera",
            "Lukáč",
            "Molnár",
            "Nagy",
            "Novotný",
            "Novák",
            "Pavlík",
            "Ružička",
            "Szabó",
            "Tóth",
            "Varga",
            "Čech",
            "Černák",
            "Černý",
            "Čáp",
            "Šimko",
        ]

        for i in range(count):
            users.append(
                User(
                    username=f"user{i + 1}",
                    first_name=random.choice(first_names),
                    last_name=random.choice(last_names),
                )
            )

        return User.objects.bulk_create(
            users,
            update_conflicts=True,
            unique_fields=["username"],
            update_fields=["first_name", "last_name"],
        )

    def create_schools(self, count: int = 50) -> list[School]:
        schools: list[School] = []

        school_names_1 = [
            ("Gymnázium", "gym"),
            ("Stredná odborná škola", "soš"),
            ("Stredná priemyselná škola", "spš"),
            ("Bilingválne gymnázium", "bg"),
        ]

        school_names_2 = [
            ("A. Bernoláka", "ab"),
            ("E. Bellu", "eb"),
            ("J. A. Komenského", "jak"),
            ("J. C. Hronského", "jch"),
            ("J. Kráľa", "jk"),
            ("J. M. Hurbana", "jmh"),
            ("K. Medveckej", "km"),
            ("L. Novomeského", "ln"),
            ("L. Sáru", "ls"),
            ("M. Kukučína", "mk"),
            ("M. R. Štefánika", "mrs"),
            ("M. Rázusa", "mr"),
            ("P. O. Hviezdoslava", "poh"),
            ("S. Chalupku", "sch"),
            ("T. Vansovej", "tv"),
        ]

        addresses_1 = [
            "Hlavná",
            "Horská",
            "Jabloňová",
            "Jarná",
            "Jasná",
            "Karpatská",
            "Karpatská",
            "Kvetinová",
            "Kvetná",
            "Mierová",
            "Námestie slobody",
            "Slnečná",
            "Trieda SNP",
            "Zimná",
            "Školská",
        ]

        addresses_2 = [
            "Bratislava",
            "Košice",
            "Prešov",
            "Nitra",
            "Trnava",
            "Žilina",
            "Banská Bystrica",
            "Poprad",
            "Martin",
            "Trenčín",
            "Prievidza",
        ]

        for i in range(count):
            choice = (random.choice(school_names_1), random.choice(school_names_2))

            schools.append(
                School(
                    edu_id=f"EDU-{i + 1:03}",
                    name=f"{choice[0][0]} {choice[1][0]}",
                    short_name=f"{choice[0][1]}-{choice[1][1]}",
                    address=f"{random.choice(addresses_1)} {random.randint(1, 100)}, {random.choice(addresses_2)}",
                )
            )

        return School.objects.bulk_create(
            schools,
            update_conflicts=True,
            unique_fields=["edu_id"],
            update_fields=["name", "short_name", "address"],
        )

    def create_problem_sets(
        self, contest: Contest, cast: int, days_ago: int
    ) -> list[ProblemSet]:
        problem_sets: list[ProblemSet] = []

        now = (
            timezone.now()
            .astimezone(timezone.get_current_timezone())
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )
        start = now - timedelta(days=days_ago)
        end = now - timedelta(days=days_ago - 45)
        for kolo in (1, 2):
            slug = f"r0{'z' if cast == 1 else 'l'}{kolo}"

            if old_problem_set := ProblemSet.objects.filter(contest=contest, slug=slug):
                self.stdout.write(
                    self.style.WARNING(
                        f"Old dummy problem set {slug} already exists. Deleting it."
                    )
                )
                old_problem_set.delete()

            options = {
                "doprogramovanie_date": (end - timedelta(days=15)).isoformat(),
            }

            if kolo > 1:
                options["previous_problem_set"] = (
                    f"r0{'z' if cast == 1 else 'l'}{kolo - 1}"
                )

            problem_set = ProblemSet.objects.create(
                contest=contest,
                name=f"{kolo}. kolo {cast}. časť 0. ročník KSP",
                slug=slug,
                start_date=start,
                end_date=end,
                is_public=True,
                rule_engine="seminare.rules.ksp.KSP2025",
                rule_engine_options=options,
            )

            problem_set.problems.bulk_create(
                [
                    Problem(
                        name=f"Úloha {i + 1}",
                        number=i + 1,
                        problem_set=problem_set,
                        file_points=12 if i != 4 else 10,
                        judge_points=8 if i != 4 else 0,
                        text_points=0 if i != 4 else 10,
                    )
                    for i in range(8)
                ]
            )

            problem_sets.append(problem_set)

            start += timedelta(days=45)
            end += timedelta(days=45)

        return problem_sets

    def create_enrollments(
        self,
        users: list[User],
        problem_sets: list[ProblemSet],
        schools: list[School],
        problemset_participate_chance: float = 0.7,
        school_change_chance: float = 0.05,
    ) -> list[Enrollment]:
        enrollments: list[Enrollment] = []

        grades = Grade.choices

        for user in users:
            school = random.choice(schools)
            grade = random.choice(grades)[0]
            for problem_set in problem_sets:
                if random.random() < school_change_chance:
                    school = random.choice(schools)
                if random.random() > problemset_participate_chance:
                    continue

                enrollments.append(
                    Enrollment(
                        user=user,
                        problem_set=problem_set,
                        school=school,
                        grade=grade,
                    )
                )

        return Enrollment.objects.bulk_create(enrollments)

    def create_submits(
        self,
        enrollments: list[Enrollment],
    ) -> list[BaseSubmit]:
        submits: tuple[
            Iterable[FileSubmit], Iterable[JudgeSubmit], Iterable[TextSubmit]
        ] = ([], [], [])

        # disable create_at auto dates
        for field in (FileSubmit, JudgeSubmit, TextSubmit):
            field._meta.get_field("created_at").auto_now_add = False

        try:
            for enrollment in enrollments:
                problems: list[Problem] = enrollment.problem_set.problems.all()

                user_id = int(enrollment.user.username.removeprefix("user"))

                score_coefficient = 1 + ((user_id % 19) - 7) * 0.1

                if random.random() < 0.8:
                    # Most of the users will submit max 5 problems that they can solve
                    level = user_id % 4
                    problems = problems[level : 5 + level]

                for problem in problems:
                    if random.random() < 0.1 / score_coefficient:
                        # most users will not submit anything for some problems
                        continue

                    if (
                        FileSubmit.type in problem.accepted_submit_types
                        and random.random() < 0.3 * score_coefficient
                    ):
                        submits[0].extend(
                            [
                                FileSubmit(
                                    enrollment=enrollment,
                                    problem=problem,
                                    created_at=(
                                        enrollment.problem_set.start_date
                                        + timedelta(
                                            days=random.randint(-2, 60),
                                            seconds=random.randint(0, 60 * 60 * 24),
                                        )
                                    ).astimezone(timezone.get_current_timezone()),
                                    file=f"dummy_files/{enrollment.user.username}/{problem.number}/{i}.txt",
                                    score=min(
                                        random.randint(0, int(problem.file_points))
                                        * score_coefficient
                                        * i
                                        // 2,
                                        int(problem.file_points),
                                    ),
                                    comment="Dummy submit",
                                )
                                for i in range(
                                    random.randint(0, int(8 * score_coefficient))
                                )
                            ]
                        )
                    if (
                        JudgeSubmit.type in problem.accepted_submit_types
                        and random.random() < 0.5 * score_coefficient
                    ):
                        submits[1].extend(
                            [
                                JudgeSubmit(
                                    enrollment=enrollment,
                                    problem=problem,
                                    created_at=(
                                        enrollment.problem_set.start_date
                                        + timedelta(
                                            days=random.randint(-2, 60),
                                            seconds=random.randint(0, 60 * 60 * 24),
                                        )
                                    ).astimezone(timezone.get_current_timezone()),
                                    program=f"dummy_programs/{enrollment.user.username}/{problem.number}/{i}.py",
                                    judge_id=f"dummy-judge-{enrollment.id}-{problem.id}-{i}",
                                    score=min(
                                        random.randint(0, int(problem.judge_points))
                                        * score_coefficient
                                        * i
                                        // 4,
                                        int(problem.judge_points),
                                    ),
                                    comment="Dummy submit",
                                )
                                for i in range(
                                    random.randint(0, int(20 * score_coefficient))
                                )
                            ]
                        )

                    if (
                        TextSubmit.type in problem.accepted_submit_types
                        and random.random() < 0.6 * score_coefficient
                    ):
                        submits[2].extend(
                            [
                                TextSubmit(
                                    enrollment=enrollment,
                                    problem=problem,
                                    created_at=(
                                        enrollment.problem_set.start_date
                                        + timedelta(
                                            days=random.randint(-2, 60),
                                            seconds=random.randint(0, 60 * 60 * 24),
                                        )
                                    ).astimezone(timezone.get_current_timezone()),
                                    value="ipsum",
                                    score=0
                                    if i == 0
                                    else int(problem.text_points)
                                    * random.randint(0, 1),
                                    comment="Dummy submit",
                                )
                                for i in range(
                                    random.randint(0, int(4 * score_coefficient)),
                                    -1,
                                    -1,
                                )
                            ]
                        )

            FileSubmit.objects.bulk_create(submits[0])
            JudgeSubmit.objects.bulk_create(submits[1])
            TextSubmit.objects.bulk_create(submits[2])
        finally:
            # enable create_at auto dates
            for field in (FileSubmit, JudgeSubmit, TextSubmit):
                field._meta.get_field("created_at").auto_now_add = True

        return [*submits[0], *submits[1], *submits[2]]

    def fake_ruledata_times(self, contest: Contest, date: datetime):
        RuleData.objects.filter(
            contest=contest,
            engine="seminare.rules.ksp.KSP2025",
            created_at__gte=timezone.now() - timedelta(minutes=1),
        ).update(created_at=date)

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            self.stdout.write(
                self.style.ERROR("This command should only be run in DEBUG mode.\n")
            )
            self.stdout.write(self.style.NOTICE("Use --force to override.\n"))
            return

        if options["force"]:
            self.stdout.write(self.style.WARNING("Running in forced mode.\n"))

        self.stdout.write("Generating dummy data...\n")

        random.seed(42)

        self.stdout.write("Creating contest...\n")
        contest = self.create_contest()

        self.stdout.write("Creating users...\n")
        users = self.create_users()

        self.stdout.write("Creating schools...\n")
        schools = self.create_schools()

        for cast in (1, 2):
            self.stdout.write(f"Cast {cast}...\n")
            self.stdout.write(" - Creating problem sets...\n")
            problem_sets = self.create_problem_sets(
                contest, cast, (3 - cast) * 2 * 45 - 1
            )

            self.stdout.write(" - Creating enrollments...\n")
            enrollments = self.create_enrollments(users, problem_sets, schools)

            self.stdout.write(" - Creating submits...\n")
            self.create_submits(enrollments)

            self.stdout.write(" - Closing problem sets\n")
            for problem_set in problem_sets:
                problem_set.is_finalized = True
                problem_set.save()

            self.stdout.write(" - Faking RuleData times\n")
            self.fake_ruledata_times(contest, max(ps.end_date for ps in problem_sets))

        self.stdout.write(self.style.SUCCESS("Dummy data generation completed.\n"))
