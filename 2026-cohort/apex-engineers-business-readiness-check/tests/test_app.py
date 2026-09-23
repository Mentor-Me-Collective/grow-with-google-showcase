"""Streamlit walking-skeleton tests for the complete assessment flow."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).parents[1] / "app.py"


def load_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH)).run()
    assert not app.exception
    return app


def test_app_renders_complete_assessment_form():
    app = load_app()
    assert app.title[0].value == "Business Readiness Check"
    assert len(app.radio) == 4
    assert app.button[0].label == "Generate assessment"


def test_golden_path_displays_score_priority_and_download():
    app = load_app()
    answers = ["No", "Yes", "No", "Not applicable"]
    for radio, answer in zip(app.radio, answers):
        radio.set_value(answer)

    app.button[0].click().run()

    assert not app.exception
    assert [metric.value for metric in app.metric] == ["66.7%", "High"]
    assert any(
        heading.value == "Start here: Inventory synchronization"
        for heading in app.subheader
    )
    assert len(app.get("download_button")) == 1


def test_golden_path_displays_breakdown_and_modernization_plan():
    app = load_app()
    answers = ["No", "Yes", "No", "Not applicable"]
    for radio, answer in zip(app.radio, answers):
        radio.set_value(answer)

    app.button[0].click().run()

    assert not app.exception
    subheadings = [heading.value for heading in app.subheader]
    assert "Readiness breakdown" in subheadings
    assert "Your modernization plan" in subheadings

    rendered_markdown = "\n".join(item.value for item in app.markdown)
    assert "Needs attention" in rendered_markdown
    assert "Ready" in rendered_markdown
    assert "Not applicable" in rendered_markdown
    assert "This week" in rendered_markdown
    assert "Next 30 days" in rendered_markdown
    assert "How to measure progress" in rendered_markdown
    assert "highest project-defined weight (5)" in rendered_markdown
    assert "one reliable inventory count that every sales channel uses" in rendered_markdown
    assert rendered_markdown.count(
        "Disconnected inventory systems can cause incorrect stock counts, "
        "overselling, and manual reconciliation."
    ) == 1
    assert "Questions to ask software providers" in [
        item.label for item in app.expander
    ]
    assert "Security checkpoints for any system change" in [
        item.label for item in app.expander
    ]


def test_optional_business_context_personalizes_results_without_changing_score():
    app = load_app()
    app.selectbox[1].set_value("Spreadsheets")
    app.selectbox[2].set_value("Every day")
    answers = ["No", "Yes", "No", "Not applicable"]
    for radio, answer in zip(app.radio, answers):
        radio.set_value(answer)

    app.button[0].click().run()

    assert not app.exception
    assert [metric.value for metric in app.metric] == ["66.7%", "High"]
    assert "Your business context" in [heading.value for heading in app.subheader]
    rendered_markdown = "\n".join(item.value for item in app.markdown)
    assert "spreadsheet process" in rendered_markdown
    assert "daily duplicate entry" in rendered_markdown


def test_each_risk_level_has_a_visible_text_label():
    scenarios = {
        "Low risk": ["Yes", "Yes", "Yes", "No"],
        "Moderate risk": ["Yes", "No", "Yes", "No"],
        "High risk": ["No", "Yes", "No", "Not applicable"],
        "Critical risk": ["No", "No", "No", "No"],
    }

    for expected_label, answers in scenarios.items():
        app = load_app()
        for radio, answer in zip(app.radio, answers):
            radio.set_value(answer)

        app.button[0].click().run()

        assert not app.exception
        assert any(expected_label in item.value for item in app.markdown)


def test_incomplete_assessment_fails_safely():
    app = load_app()
    app.button[0].click().run()

    assert not app.exception
    assert any("Answer every diagnostic question" in item.value for item in app.warning)
    assert not app.metric


def test_all_not_applicable_returns_no_score():
    app = load_app()
    for radio in app.radio:
        radio.set_value("Not applicable")

    app.button[0].click().run()

    assert not app.exception
    assert any("score could not be calculated" in item.value for item in app.warning)
    assert not app.metric
