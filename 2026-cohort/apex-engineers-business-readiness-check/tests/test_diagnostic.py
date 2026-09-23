"""Unit tests for the Business Readiness Check scoring rules."""

import unittest

from diagnostic import (
    NO,
    NOT_APPLICABLE,
    QUESTIONS,
    YES,
    SECURITY_CHECKPOINTS,
    build_context_guidance,
    build_modernization_plan,
    build_readiness_breakdown,
    calculate_risk,
    clean_user_text,
    find_priorities,
    generate_report,
)


class DiagnosticTests(unittest.TestCase):
    def test_all_yes_is_zero_percent_low_risk(self):
        answers = {
            "inventory": YES,
            "payments": YES,
            "customers": YES,
            "booking": YES,
        }
        result = calculate_risk(answers)
        self.assertEqual(result.risk_points, 0)
        self.assertEqual(result.applicable_points, 14)
        self.assertEqual(result.risk_percentage, 0.0)
        self.assertEqual(result.risk_level, "Low")

    def test_all_no_is_one_hundred_percent_critical_risk(self):
        answers = {
            "inventory": NO,
            "payments": NO,
            "customers": NO,
            "booking": NO,
        }
        result = calculate_risk(answers)
        self.assertEqual(result.risk_points, 14)
        self.assertEqual(result.risk_percentage, 100.0)
        self.assertEqual(result.risk_level, "Critical")

    def test_not_applicable_is_removed_from_denominator(self):
        answers = {
            "inventory": NO,
            "payments": YES,
            "customers": NO,
            "booking": NOT_APPLICABLE,
        }
        result = calculate_risk(answers)
        self.assertEqual(result.risk_points, 8)
        self.assertEqual(result.applicable_points, 12)
        self.assertEqual(result.risk_percentage, 66.7)
        self.assertEqual(result.risk_level, "High")

    def test_all_not_applicable_returns_no_score(self):
        answers = {
            "inventory": NOT_APPLICABLE,
            "payments": NOT_APPLICABLE,
            "customers": NOT_APPLICABLE,
            "booking": NOT_APPLICABLE,
        }
        result = calculate_risk(answers)
        self.assertIsNone(result.risk_percentage)
        self.assertEqual(result.risk_level, "Not calculated")

    def test_priorities_are_ordered_by_weight(self):
        answers = {
            "inventory": NO,
            "payments": YES,
            "customers": NO,
            "booking": NO,
        }
        priorities = find_priorities(answers)
        self.assertEqual(
            [key for key, _ in priorities],
            ["inventory", "customers", "booking"],
        )

    def test_recommended_notes_are_distinct_from_diagnostic_explanations(self):
        for question in QUESTIONS.values():
            self.assertNotEqual(question.next_step_note, question.explanation)

    def test_readiness_breakdown_covers_every_answer_state(self):
        answers = {
            "inventory": NO,
            "payments": YES,
            "customers": NO,
            "booking": NOT_APPLICABLE,
        }
        breakdown = build_readiness_breakdown(answers)
        self.assertEqual(
            [area.status for area in breakdown],
            ["Needs attention", "Ready", "Needs attention", "Not applicable"],
        )
        self.assertIn("overselling", breakdown[0].summary)
        self.assertIn("excluded from the score", breakdown[3].summary)

    def test_modernization_plan_is_prioritized_and_actionable(self):
        answers = {
            "inventory": NO,
            "payments": YES,
            "customers": NO,
            "booking": NOT_APPLICABLE,
        }
        plan = build_modernization_plan(answers)
        self.assertEqual([step.key for step in plan], ["inventory", "customers"])
        self.assertIn("re-enter quantities", plan[0].immediate_action)
        self.assertIn("small product set", plan[0].thirty_day_action)
        self.assertIn("stock discrepancies", plan[0].success_measure)
        self.assertEqual(len(plan[0].provider_questions), 3)

    def test_all_ready_answers_need_no_modernization_steps(self):
        answers = {key: YES for key in ("inventory", "payments", "customers", "booking")}
        self.assertEqual(build_modernization_plan(answers), [])

    def test_missing_answer_is_rejected(self):
        answers = {"inventory": YES, "payments": YES, "customers": YES}
        with self.assertRaisesRegex(ValueError, "Missing answers"):
            calculate_risk(answers)

    def test_invalid_answer_is_rejected(self):
        answers = {
            "inventory": "Maybe",
            "payments": YES,
            "customers": YES,
            "booking": YES,
        }
        with self.assertRaisesRegex(ValueError, "Invalid answers"):
            calculate_risk(answers)

    def test_report_matches_result_and_priority(self):
        answers = {
            "inventory": NO,
            "payments": YES,
            "customers": NO,
            "booking": NOT_APPLICABLE,
        }
        result = calculate_risk(answers)
        report = generate_report(answers, result, business_name="Example Store")
        self.assertIn("Overall risk: 66.7% (High)", report)
        self.assertIn(
            "1. Prioritize POS and online inventory synchronization.", report
        )
        self.assertIn(
            "one reliable inventory count that every sales channel uses", report
        )
        self.assertIn("Business name: Example Store", report)
        self.assertIn("Inventory synchronization: Needs attention (No)", report)
        self.assertIn("MODERNIZATION ACTION PLAN", report)
        self.assertIn("NEXT 30 DAYS", report)
        self.assertIn("HOW TO MEASURE PROGRESS", report)
        self.assertIn("QUESTIONS TO ASK PROVIDERS", report)
        self.assertIn(SECURITY_CHECKPOINTS[0], report)
        self.assertIn("not a formal security", report)

    def test_context_guidance_personalizes_without_changing_score(self):
        answers = {
            "inventory": NO,
            "payments": YES,
            "customers": NO,
            "booking": NOT_APPLICABLE,
        }
        before = calculate_risk(answers)
        guidance = build_context_guidance("Spreadsheets", "Every day")
        after = calculate_risk(answers)

        self.assertEqual(before, after)
        self.assertEqual(len(guidance), 2)
        self.assertIn("spreadsheet process", guidance[0])
        self.assertIn("daily duplicate entry", guidance[1])

    def test_report_includes_optional_business_context(self):
        answers = {key: YES for key in ("inventory", "payments", "customers", "booking")}
        result = calculate_risk(answers)
        report = generate_report(
            answers,
            result,
            management_method="Several separate applications",
            manual_copy_frequency="Several times a week",
        )

        self.assertIn("BUSINESS CONTEXT", report)
        self.assertIn("Operations management: Several separate applications", report)
        self.assertIn("Repeated data entry: Several times a week", report)
        self.assertIn("do not affect the score", report)

    def test_optional_report_text_is_normalized_and_limited(self):
        unsafe = "  Example\nStore\t" + "x" * 100
        cleaned = clean_user_text(unsafe, max_length=20)
        self.assertEqual(cleaned, "Example Store xxxxxx")
        self.assertEqual(len(cleaned), 20)


if __name__ == "__main__":
    unittest.main()
