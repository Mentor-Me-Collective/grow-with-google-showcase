import streamlit as st

from src.database import (
    get_appliances,
    create_household,
    add_household_appliance,
)
from src.household_analysis import analyze_household
from src.recommendations import generate_recommendations
from src.historical_tracking import (
    save_household_analysis,
    get_household_history,
)


# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------

st.set_page_config(
    page_title="Household Energy Efficiency Optimizer",
    page_icon="⚡",
    layout="wide",
)


# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------

if "household_id" not in st.session_state:
    st.session_state.household_id = None

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "pending_appliances" not in st.session_state:
    st.session_state.pending_appliances = []


# ------------------------------------------------------------
# Page title
# ------------------------------------------------------------

st.title("Household Energy Efficiency Optimizer")

st.write(
    "Estimate household energy consumption, electricity cost, "
    "carbon footprint, and energy efficiency."
)


# ------------------------------------------------------------
# Household profile
# ------------------------------------------------------------

st.header("1. Household Profile")

housing_type = st.selectbox(
    "Housing type",
    [
        "Apartment",
        "Condo",
        "Studio",
        "Multi-family",
        "Other",
    ],
)

apartment_size_category = st.selectbox(
    "Apartment size",
    [
        "Studio",
        "1BR",
        "2BR",
        "3BR+",
    ],
)

electricity_rate = st.number_input(
    "Electricity rate per kWh",
    min_value=0.0,
    value=0.20,
    step=0.01,
)

carbon_emission_factor = st.number_input(
    "Carbon emission factor (kg CO2e per kWh)",
    min_value=0.0,
    value=0.40,
    step=0.01,
)


# ------------------------------------------------------------
# Appliance selection & staging
# ------------------------------------------------------------

st.header("2. Appliance Information")

appliances = get_appliances()

if not appliances:
    st.error("No appliance reference data was found in the database.")
    st.stop()

appliance_map = {app["appliance_name"]: app for app in appliances}
appliance_names = list(appliance_map.keys())

selected_appliance_name = st.selectbox(
    "Select an appliance",
    appliance_names,
)

quantity = st.number_input(
    "Quantity",
    min_value=1,
    value=1,
    step=1,
)

daily_usage_hours = st.number_input(
    "Daily usage (hours)",
    min_value=0.0,
    max_value=24.0,
    value=1.0,
    step=0.5,
)

# Button to add current appliance to session state list
if st.button("Add Appliance"):
    selected_app = appliance_map[selected_appliance_name]
    st.session_state.pending_appliances.append({
        "appliance_id": selected_app["appliance_id"],
        "appliance_name": selected_app["appliance_name"],
        "quantity": quantity,
        "daily_usage_hours": daily_usage_hours,
    })
    st.success(f"Added {quantity} x {selected_appliance_name} to pending list.")

# Display staged appliances
if st.session_state.pending_appliances:
    st.subheader("Selected Appliances Preview")
    preview_data = [
        {
            "Appliance": item["appliance_name"],
            "Quantity": item["quantity"],
            "Daily Usage (hrs)": item["daily_usage_hours"],
        }
        for item in st.session_state.pending_appliances
    ]
    st.dataframe(preview_data, use_container_width=True)

    if st.button("Clear All Pending Appliances"):
        st.session_state.pending_appliances = []
        st.rerun()


# ------------------------------------------------------------
# Create household and analyze
# ------------------------------------------------------------

st.markdown("---")

if st.button("Create Household & Analyze"):

    if not st.session_state.pending_appliances:
        st.error("Please add at least one appliance before creating a household.")
    else:
        household_id = create_household(
            housing_type=housing_type,
            apartment_size_category=apartment_size_category,
            electricity_rate_per_kwh=electricity_rate,
            carbon_emission_factor=carbon_emission_factor,
        )

        for item in st.session_state.pending_appliances:
            add_household_appliance(
                household_id=household_id,
                appliance_id=item["appliance_id"],
                appliance_quantity=item["quantity"],
                daily_usage_hours=item["daily_usage_hours"],
            )

        # Store household ID so it survives Streamlit reruns
        st.session_state.household_id = household_id

        # Analyze the newly created multi-appliance household
        result = analyze_household(household_id)

        # Store analysis result
        st.session_state.analysis_result = result

        # Clear pending list after submission
        st.session_state.pending_appliances = []

        st.success(
            f"Household {household_id} created and analyzed successfully!"
        )


# ------------------------------------------------------------
# Retrieve current analysis from session state
# ------------------------------------------------------------

result = st.session_state.analysis_result
household_id = st.session_state.household_id


# ------------------------------------------------------------
# Household analysis
# ------------------------------------------------------------

if result is not None:

    st.header("3. Energy Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Daily Energy",
            f"{result['daily_kwh']:.2f} kWh"
        )

    with col2:
        st.metric(
            "Monthly Energy",
            f"{result['monthly_kwh']:.2f} kWh"
        )

    with col3:
        st.metric(
            "Monthly Cost",
            f"${result['monthly_cost']:.2f}"
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "Carbon Footprint",
            f"{result['monthly_carbon_kg']:.2f} kg CO2e"
        )

    with col5:
        st.metric(
            "Benchmark",
            (
                f"{result['benchmark_kwh_monthly']:.2f} kWh"
                if result["benchmark_kwh_monthly"] is not None
                else "N/A"
            )
        )

    with col6:
        st.metric(
            "Efficiency Score",
            result["efficiency_score"]
        )

    st.write(
        f"**Efficiency:** {result['efficiency_label']}"
    )


    # --------------------------------------------------------
    # Appliance Breakdown
    # --------------------------------------------------------

    st.subheader("Appliance Breakdown")

    appliances_data = result.get("appliances", [])

    if appliances_data:

        table_data = []

        for app in appliances_data:
            qty = app.get("quantity") if "quantity" in app else app.get("appliance_quantity", 1)

            table_data.append({
                "Appliance": app["appliance_name"],
                "Quantity": qty,
                "Daily Usage (hrs)": app["daily_usage_hours"],
                "Daily kWh": f"{app['daily_kwh']:.2f}",
                "Monthly kWh": f"{app['monthly_kwh']:.2f}",
            })

        st.dataframe(
            table_data,
            use_container_width=True
        )

    else:
        st.info("No individual appliance data available.")


    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    st.header("4. Recommendations")

    recommendations = generate_recommendations(result)

    if not recommendations:

        st.info(
            "No specific recommendations for this household."
        )

    else:

        for rec in recommendations:

            if rec["priority"] == "high":

                st.error(
                    f"**{rec['title']}**: {rec['message']}"
                )

            elif rec["priority"] == "medium":

                st.warning(
                    f"**{rec['title']}**: {rec['message']}"
                )

            else:

                st.info(
                    f"**{rec['title']}**: {rec['message']}"
                )


    # --------------------------------------------------------
    # Historical Tracking
    # --------------------------------------------------------

    st.header("5. Historical Tracking")

    st.write(
        "Save this household estimate to track energy consumption "
        "over time."
    )

    if st.button("Save Current Estimate"):

        estimate_id = save_household_analysis(
            household_id
        )

        st.success(
            f"Estimate {estimate_id} saved successfully."
        )


    # --------------------------------------------------------
    # Historical Estimates
    # --------------------------------------------------------

    history = get_household_history(
        household_id
    )

    if history:

        st.subheader("Previous Estimates")

        history_data = []

        for estimate in history:

            history_data.append({
                "Date": estimate["generated_at"],
                "Monthly kWh": f"{estimate['estimated_kwh_monthly']:.2f}",
                "Monthly Cost": f"${estimate['estimated_cost_monthly']:.2f}",
                "% of Benchmark": (
                    f"{estimate['pct_vs_benchmark']:.2f}%"
                    if estimate["pct_vs_benchmark"] is not None
                    else "N/A"
                ),
            })

        st.dataframe(
            history_data,
            use_container_width=True
        )

    else:

        st.info(
            "No historical estimates have been saved yet."
        )
