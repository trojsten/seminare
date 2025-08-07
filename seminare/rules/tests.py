from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from seminare.problems.models import ProblemSet, Text
from seminare.rules import RuleEngine


class KSPRulesTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("generate_dummy_data", "--force")

    def get_problem_sets(self):
        return (
            ProblemSet.objects.all()
            .select_related("contest")
            .prefetch_related("problems", "enrollment_set", "enrollment_set__user")
        )

    def get_rule_engines(self) -> list[RuleEngine]:
        return [ps.get_rule_engine() for ps in self.get_problem_sets()]

    def test_visible_texts(self):
        for rule_engine in self.get_rule_engines():
            for problem in rule_engine.problem_set.problems.all():
                visible_texts = rule_engine.get_visible_texts(problem)

                now = timezone.now().astimezone(timezone.get_current_timezone())

                if now >= rule_engine.problem_set.start_date:
                    self.assertIn(Text.Type.PROBLEM_STATEMENT, visible_texts)
                else:
                    self.assertNotIn(Text.Type.PROBLEM_STATEMENT, visible_texts)

                if now > rule_engine.problem_set.end_date:
                    self.assertIn(Text.Type.EXAMPLE_SOLUTION, visible_texts)
                else:
                    self.assertNotIn(Text.Type.EXAMPLE_SOLUTION, visible_texts)

    def test_get_effective_submits(self):
        for rule_engine in self.get_rule_engines():
            for problem in rule_engine.problem_set.problems.all():
                for submit_cls in problem.accepted_submit_classes:
                    submits = rule_engine.get_effective_submits(
                        submit_cls, problem
                    ).all()

                    # assert correct problem
                    self.assertTrue(
                        all(submit.problem == problem for submit in submits)
                    )

                    # assert unique enrollment
                    self.assertEqual(
                        submits.values_list("enrollment_id", flat=True)
                        .distinct()
                        .count(),
                        submits.count(),
                    )

                    # assert submits from all enrollments before deadline are present
                    self.assertEqual(
                        submits.count(),
                        submit_cls.objects.filter(
                            problem=problem,
                            created_at__lte=rule_engine.problem_set.end_date,
                        )
                        .order_by("enrollment_id")
                        .distinct("enrollment_id")
                        .count(),
                    )

                    for submit in submits:
                        # assert before deadline
                        self.assertLessEqual(
                            submit.created_at, rule_engine.problem_set.end_date
                        )

                        # assert no better submit exists before deadline
                        self.assertFalse(
                            submits.filter(
                                enrollment=submit.enrollment,
                                score__gt=submit.score,
                                created_at__lte=rule_engine.problem_set.end_date,
                            ).exists()
                        )

    def test_get_enrollments_problems_effective_submits(self):
        for rule_engine in self.get_rule_engines():
            for problem in rule_engine.problem_set.problems.all():
                for submit_cls in problem.accepted_submit_classes:
                    enrollments = rule_engine.problem_set.enrollment_set.all()

                    enrollments = enrollments[: enrollments.count() // 2]

                    submits = rule_engine.get_enrollments_problems_effective_submits(
                        submit_cls, enrollments, [problem]
                    ).all()

                    # assert correct problem
                    self.assertTrue(
                        all(submit.problem == problem for submit in submits)
                    )

                    # assert unique enrollment
                    self.assertEqual(
                        submits.values_list("enrollment_id", flat=True)
                        .distinct()
                        .count(),
                        submits.count(),
                    )

                    # assert only selected enrollments
                    self.assertTrue(
                        all(submit.enrollment in enrollments for submit in submits)
                    )

                    # assert submits from all enrollments before deadline are present
                    self.assertEqual(
                        submits.count(),
                        submit_cls.objects.filter(
                            problem=problem,
                            enrollment__in=enrollments,
                            created_at__lte=rule_engine.problem_set.end_date,
                        )
                        .order_by("enrollment_id")
                        .distinct("enrollment_id")
                        .count(),
                    )

                    for submit in submits:
                        # assert before deadline
                        self.assertLessEqual(
                            submit.created_at, rule_engine.problem_set.end_date
                        )

                        # assert no better submit exists before deadline
                        self.assertFalse(
                            submits.filter(
                                enrollment=submit.enrollment,
                                score__gt=submit.score,
                                created_at__lte=rule_engine.problem_set.end_date,
                            ).exists()
                        )

    def test_get_enrollments(self):
        for rule_engine in self.get_rule_engines():
            enrollments = rule_engine.get_enrollments()

            # assert all enrollments are from the problem set
            self.assertTrue(
                all(
                    enrollment.problem_set == rule_engine.problem_set
                    for enrollment in enrollments
                )
            )
