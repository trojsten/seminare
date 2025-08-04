import random
from datetime import timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.utils import timezone

from seminare.contests.models import Contest
from seminare.problems.models import Problem, ProblemSet
from seminare.submits.models import BaseSubmit, FileSubmit, JudgeSubmit, TextSubmit
from seminare.users.models import Enrollment, School, User


class Command(BaseCommand):
    help = "Generate dummy data for testing purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force the command to run.",
        )

    def create_contest(self) -> Contest:
        return Contest.objects.update_or_create(
            name="Korešpondenčný seminár z programovania",
            short_name="ksp",
            site=Site.objects.get_or_create(
                domain="ksp.localhost", name="ksp.localhost"
            )[0],
        )[0]

    def create_users(self, count: int = 80) -> list[User]:
        users: list[User] = []

        first_names = [
            "Adam",
            "Anna",
            "Eva",
            "Jakub",
            "Ján",
            "Katarína",
            "Lucia",
            "Lukáš",
            "Martin",
            "Michal",
            "Mária",
            "Patrícia",
            "Peter",
            "Tomáš",
            "Veronika",
            "Zuzana",
        ]
        last_names = [
            "Baláž",
            "Bielik",
            "Horváth",
            "Kiss",
            "Kováč",
            "Krajčír",
            "Molnár",
            "Nagy",
            "Novák",
            "Ružička",
            "Szabó",
            "Tóth",
            "Varga",
            "Černák",
            "Šimko",
        ]

        for i in range(count):
            users.append(
                User.objects.update_or_create(
                    username=f"user{i + 1}",
                    defaults={
                        "first_name": random.choice(first_names),
                        "last_name": random.choice(last_names),
                    },
                )[0]
            )

        return users

    def create_schools(self, count: int = 10) -> list[School]:
        schools: list[School] = []

        school_names_1 = [
            ("Gymnázium", "gym"),
            ("Stredná odborná škola", "soš"),
            ("Stredná priemyselná škola", "spš"),
            ("Bilingválne gymnázium", "bg"),
        ]

        school_names_2 = [
            ("A. Bernoláka", "ab"),
            ("M. R. Štefánika", "mrs"),
            ("J. A. Komenského", "jak"),
            ("L. Novomeského", "ln"),
            ("J. C. Hronského", "jch"),
            ("M. Kukučína", "mk"),
            ("E. Bellu", "eb"),
            ("L. Sáru", "ls"),
        ]

        for i in range(count):
            choice = (random.choice(school_names_1), random.choice(school_names_2))

            schools.append(
                School.objects.update_or_create(
                    edu_id=f"EDU-{i + 1:03}",
                    defaults={
                        "name": f"{choice[0][0]} {choice[1][0]}",
                        "short_name": f"{choice[0][1]}-{choice[1][1]}",
                    },
                )[0]
            )

        return schools

    def create_problem_sets(self, contest: Contest) -> list[ProblemSet]:
        problem_sets: list[ProblemSet] = []

        now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = now - timedelta(days=45 * 4 - 1)
        end = now - timedelta(days=45 * 3 - 1)
        for cast in (1, 2):
            for kolo in (1, 2):
                problem_set, created = ProblemSet.objects.update_or_create(
                    contest=contest,
                    name=f"{kolo}. kolo {cast}. časť 0. ročník KSP",
                    defaults={
                        "start_date": start,
                        "end_date": end,
                        "is_public": True,
                        "rule_engine": "seminare.rules.ksp.KSPRules",
                        "rule_engine_options": {
                            "doprogramovanie_date": (
                                end - timedelta(days=15)
                            ).isoformat(),
                        },
                    },
                )

                if created:
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

        grades = Enrollment.Grade.choices

        for user in users:
            school = random.choice(schools)
            grade = random.choice(grades)[0]
            for problem_set in problem_sets:
                if random.random() < school_change_chance:
                    school = random.choice(schools)
                if random.random() > problemset_participate_chance:
                    continue

                enrollments.append(
                    Enrollment.objects.update_or_create(
                        user=user,
                        problem_set=problem_set,
                        defaults={
                            "school": school,
                            "grade": grade,
                        },
                    )[0]
                )

        return enrollments

    def create_submits(
        self,
        enrollments: list[Enrollment],
    ) -> list[BaseSubmit]:
        submits: list[BaseSubmit] = []

        for enrollment in enrollments:
            problems: list[Problem] = enrollment.problem_set.problems.all()

            if random.random() < 0.9:
                # Most of the users will submit max 5 problems that they can solve
                level = random.randint(0, 3)
                problems = problems[level : 5 + level]

            for problem in problems:
                if (
                    FileSubmit.type in problem.accepted_submit_types
                    and random.random() < 0.7
                ):
                    submits.extend(
                        FileSubmit.objects.bulk_create(
                            [
                                FileSubmit(
                                    enrollment=enrollment,
                                    problem=problem,
                                    file=f"dummy_files/{enrollment.user.username}/{problem.number}/{i}.txt",
                                    score=min(
                                        random.randint(0, int(problem.file_points))
                                        * i
                                        // 3,
                                        int(problem.file_points),
                                    ),
                                    comment="Dummy submit",
                                )
                                for i in range(random.randint(0, 10))
                            ]
                        )
                    )
                if (
                    JudgeSubmit.type in problem.accepted_submit_types
                    and random.random() < 0.7
                ):
                    submits.extend(
                        JudgeSubmit.objects.bulk_create(
                            [
                                JudgeSubmit(
                                    enrollment=enrollment,
                                    problem=problem,
                                    program=f"dummy_programs/{enrollment.user.username}/{problem.number}/{i}.py",
                                    judge_id=f"dummy-judge-{enrollment.id}-{problem.id}-{i}",
                                    score=min(
                                        random.randint(0, int(problem.judge_points))
                                        * i
                                        // 3,
                                        int(problem.judge_points),
                                    ),
                                    comment="Dummy submit",
                                )
                                for i in range(random.randint(0, 10))
                            ]
                        )
                    )

                if (
                    TextSubmit.type in problem.accepted_submit_types
                    and random.random() < 0.7
                ):
                    submits.extend(
                        TextSubmit.objects.bulk_create(
                            [
                                TextSubmit(
                                    enrollment=enrollment,
                                    problem=problem,
                                    value="ipsum",
                                    score=0
                                    if i == 0
                                    else int(problem.text_points)
                                    * random.randint(0, 1),
                                    comment="Dummy submit",
                                )
                                for i in range(random.randint(0, 3), -1, -1)
                            ]
                        )
                    )

        return submits

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

        self.stdout.write("Creating problem sets...\n")
        problem_sets = self.create_problem_sets(contest)

        self.stdout.write("Creating enrollments...\n")
        enrollments = self.create_enrollments(users, problem_sets, schools)

        self.stdout.write("Creating submits...\n")
        self.create_submits(enrollments)

        self.stdout.write(self.style.SUCCESS("Dummy data generation completed.\n"))
