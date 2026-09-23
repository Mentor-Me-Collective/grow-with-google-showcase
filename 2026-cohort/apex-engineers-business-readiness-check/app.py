"""Streamlit interface for the Apex Engineers Business Readiness Check."""

from pathlib import Path

import streamlit as st

from diagnostic import (
    NOT_APPLICABLE,
    NO,
    MANAGEMENT_METHODS,
    MANUAL_COPY_FREQUENCIES,
    QUESTIONS,
    SECURITY_CHECKPOINTS,
    YES,
    build_context_guidance,
    build_modernization_plan,
    build_readiness_breakdown,
    calculate_risk,
    find_priorities,
    generate_report,
)


st.set_page_config(
    page_title="Business Readiness Check",
    page_icon="BRC",
    layout="centered",
)


def load_styles() -> None:
    """Load the project stylesheet from the application directory."""
    stylesheet = Path(__file__).with_name("styles.css")
    st.markdown(
        f"<style>{stylesheet.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


load_styles()

st.markdown('<div class="brc-brand-line" aria-hidden="true"></div>', unsafe_allow_html=True)
st.title("Business Readiness Check")
st.write(
    "Answer four questions to identify technology gaps and receive a "
    "prioritized modernization plan."
)
st.info(
    "Privacy: This version does not require an account and does not intentionally "
    "store your answers. Do not enter passwords, payment-card details, customer "
    "records, or other sensitive information."
)

with st.form("readiness_assessment"):
    st.subheader("About the business")
    business_name = st.text_input(
        "Business name (optional)",
        max_chars=80,
        help="Use a general or example name if you prefer not to identify the business.",
    )
    business_type = st.selectbox(
        "Business type (optional)",
        [
            "",
            "Retail storefront",
            "E-commerce",
            "Retail and e-commerce",
            "Service-based business",
            "Other",
        ],
        format_func=lambda value: "Select a business type" if not value else value,
    )

    st.subheader("How the business works")
    st.caption(
        "These optional questions help tailor your recommendations. They do not "
        "change the weighted technology risk score."
    )
    management_method = st.selectbox(
        "How do you currently manage orders, inventory, and customer information?",
        ["", *MANAGEMENT_METHODS],
        format_func=lambda value: "Select a management method" if not value else value,
    )
    manual_copy_frequency = st.selectbox(
        "How often do you enter or copy the same information into multiple systems?",
        ["", *MANUAL_COPY_FREQUENCIES],
        format_func=lambda value: "Select a frequency" if not value else value,
    )

    st.subheader("Technology assessment")
    answers: dict[str, str | None] = {}
    for key, question in QUESTIONS.items():
        answers[key] = st.radio(
            question.prompt,
            options=[YES, NO, NOT_APPLICABLE],
            index=None,
            horizontal=True,
            key=f"answer_{key}",
        )

    submitted = st.form_submit_button("Generate assessment", type="primary")

if submitted:
    missing_labels = [
        QUESTIONS[key].label for key, answer in answers.items() if answer is None
    ]
    if missing_labels:
        st.warning("Answer every diagnostic question before generating the result.")
    else:
        completed_answers = {key: str(answer) for key, answer in answers.items()}
        result = calculate_risk(completed_answers)
        priorities = find_priorities(completed_answers)
        breakdown = build_readiness_breakdown(completed_answers)
        action_plan = build_modernization_plan(completed_answers)
        context_guidance = build_context_guidance(
            management_method,
            manual_copy_frequency,
        )

        st.divider()
        with st.container(key="results_panel", border=True):
            st.header("Your results")

            if result.risk_percentage is None:
                st.warning(
                    "A score could not be calculated because every area was marked "
                    "Not applicable. Select at least one applicable area."
                )
            else:
                risk_class = {
                    "Low": "low",
                    "Moderate": "moderate",
                    "High": "high",
                    "Critical": "critical",
                }[result.risk_level]
                st.markdown(
                    f'<div class="brc-risk-badge brc-risk-{risk_class}">'
                    f"{result.risk_level} risk</div>",
                    unsafe_allow_html=True,
                )

                score_column, level_column = st.columns(2)
                score_column.metric(
                    "Technology risk score", f"{result.risk_percentage:.1f}%"
                )
                level_column.metric("Risk level", result.risk_level)

                if priorities:
                    _, highest_priority = priorities[0]
                    st.subheader(f"Start here: {highest_priority.label}")
                    st.write(
                        "This area has the highest project-defined weight "
                        f"({highest_priority.weight}) among the gaps you reported."
                    )
                else:
                    st.success(
                        "No priority gaps were identified from the answers provided."
                    )

            st.subheader("Readiness breakdown")
            st.write(
                "Review what is working, what needs attention, and what was "
                "excluded from your score."
            )
            status_classes = {
                "Ready": "ready",
                "Needs attention": "attention",
                "Not applicable": "not-applicable",
            }
            for area in breakdown:
                with st.container(key=f"area_{area.key}", border=True):
                    label_column, status_column = st.columns([3, 2])
                    label_column.markdown(f"**{area.question.label}**")
                    status_class = status_classes[area.status]
                    status_column.markdown(
                        f'<div class="brc-area-status brc-area-{status_class}">'
                        f"{area.status}</div>",
                        unsafe_allow_html=True,
                    )
                    st.write(area.summary)

            if context_guidance:
                st.subheader("Your business context")
                st.caption(
                    "This guidance reflects your optional operating-process answers "
                    "and does not affect your score."
                )
                for item in context_guidance:
                    st.markdown(f"- {item}")

            st.subheader("Recommended next steps")
            if priorities:
                for index, (_, question) in enumerate(priorities, start=1):
                    st.markdown(f"**{index}. {question.recommendation}**")
                    st.write(question.next_step_note)
            elif result.risk_percentage is None:
                st.write("Complete at least one applicable area to receive recommendations.")
            else:
                st.write("Continue monitoring these areas as the business changes.")

            st.subheader("Your modernization plan")
            if action_plan:
                with st.container(key="action_plan", border=True):
                    st.markdown("#### This week")
                    for index, step in enumerate(action_plan, start=1):
                        st.markdown(f"**{index}. {step.label}**")
                        st.write(step.immediate_action)

                    st.markdown("#### Next 30 days")
                    for index, step in enumerate(action_plan, start=1):
                        st.markdown(f"**{index}. {step.label}**")
                        st.write(step.thirty_day_action)

                    st.markdown("#### How to measure progress")
                    for index, step in enumerate(action_plan, start=1):
                        st.markdown(f"**{index}. {step.label}**")
                        st.write(step.success_measure)
            elif result.risk_percentage is None:
                st.write("Complete at least one applicable area to receive an action plan.")
            else:
                st.success(
                    "No immediate modernization actions were generated because "
                    "no gaps were identified."
                )

            with st.expander("Security checkpoints for any system change"):
                for checkpoint in SECURITY_CHECKPOINTS:
                    st.markdown(f"- {checkpoint}")

            if action_plan:
                with st.expander("Questions to ask software providers"):
                    for step in action_plan:
                        st.markdown(f"**{step.label}**")
                        for provider_question in step.provider_questions:
                            st.markdown(f"- {provider_question}")

            with st.expander("Review all answers"):
                for key, question in QUESTIONS.items():
                    st.write(f"**{question.label}:** {completed_answers[key]}")

            report = generate_report(
                completed_answers,
                result,
                business_name=business_name,
                business_type=business_type,
                management_method=management_method,
                manual_copy_frequency=manual_copy_frequency,
            )
            st.download_button(
                "Download results report",
                data=report,
                file_name="business-readiness-check.txt",
                mime="text/plain",
                on_click="ignore",
            )

            st.caption(
                "This educational tool provides general guidance. It is not a formal "
                "security, financial, compliance, or technology audit."
            )
