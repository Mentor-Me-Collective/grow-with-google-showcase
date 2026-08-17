import os
import pandas as pd
import streamlit as st

# 1. Page Configuration
st.set_page_config(page_title="Biodiversity Planner", page_icon="🌿", layout="wide")

@st.cache_data
def load_datasets():
    """
    Loads data dynamically and caches it in memory so it doesn't
    reload every time the user clicks a button.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_data_path = os.path.join(base_dir, "data", "processed", "plants_app.csv")
    state_data_path = os.path.join(base_dir, "data", "processed", "plant_states.csv")

    plants_df = pd.read_csv(app_data_path)
    states_df = pd.read_csv(state_data_path)
    return plants_df, states_df

def get_recommendations(plants_df, states_df, target_state, sunlight_col, water_col, pollinator_col):
    """Core filtering logic."""
    native_plant_ids = states_df[states_df['native_state'] == target_state]['plant_id'].tolist()

    mask = (
        (plants_df['plant_id'].isin(native_plant_ids)) &
        (plants_df[sunlight_col] == True) &
        (plants_df[water_col] == True) &
        (plants_df[pollinator_col] == True)
    )
    return plants_df[mask]

def main():
    st.title("🌱 Biodiversity & Native Planting Planner 🦋")
    st.write("Discover native plants suitable for your gardening conditions to support local pollinators!")

    # Load data securely
    try:
        plants_df, states_df = load_datasets()
    except FileNotFoundError:
        st.error("❌ Dataset files not found. Ensure 'plants_app.csv' and 'plant_states.csv' are in the 'data/processed/' folder.")
        st.stop()

    # 2. Sidebar for User Inputs
    st.sidebar.header("🌿 Gardening Conditions")

    valid_states = sorted(states_df['native_state'].dropna().unique().tolist())

    sunlight_map = {
        "Full Sun": "supports_full_sun",
        "Part Shade": "supports_part_shade",
        "Shade": "supports_shade"
    }

    water_map = {
        "Low Water": "supports_low_water",
        "Medium Water": "supports_medium_water",
        "High Water": "supports_high_water"
    }

    pollinator_map = {
        "Bee": "supports_bee_observed",
        "Butterfly": "supports_butterfly_observed",
        "Hummingbird": "supports_hummingbird_observed",
        "Moth": "supports_moth_observed",
        "Fly": "supports_fly_observed",
        "Beetle": "supports_beetle_observed",
        "Wasp": "supports_wasp_observed"
    }

    # Streamlit automatically handles validation by restricting input to these dropdowns
    state = st.sidebar.selectbox("📍 Select your State", valid_states)
    sunlight = st.sidebar.selectbox("☀️ Sunlight availability", list(sunlight_map.keys()))
    water = st.sidebar.selectbox("💧 Water availability", list(water_map.keys()))
    pollinator = st.sidebar.selectbox("🦋 Preferred Pollinator", list(pollinator_map.keys()))

    sunlight_col = sunlight_map[sunlight]
    water_col = water_map[water]
    pollinator_col = pollinator_map[pollinator]

    st.write("---")
    st.subheader(f"🔍 Recommendations for {state}")

    # 3. Fetch Results
    results = get_recommendations(plants_df, states_df, state, sunlight_col, water_col, pollinator_col)

    # 4. Rich Data Output Display
    if results.empty:
        st.warning("No exact matches found for these specific conditions. Try adjusting your inputs in the sidebar!")
    else:
        st.success(f"✅ Found {len(results)} recommendation(s)")

        for idx, row in results.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 2.5])

                with col1:
                    # Display the image if the URL exists
                    if pd.notna(row.get('image_url')):
                        st.image(row['image_url'], use_container_width=True)
                        if pd.notna(row.get('image_source')):
                            st.caption(f"Source: {row['image_source']}")
                    else:
                        st.info("No image available")

                with col2:
                    # Display the rich botanical data
                    st.markdown(f"### {row.get('display_name', row.get('common_name', 'Unknown'))}")
                    st.markdown(f"*{row.get('scientific_name', 'Unknown')}* | **Family:** {row.get('plant_family', 'N/A')} | **Type:** {row.get('plant_type', 'N/A')}")
                    st.markdown(f"**Hardiness Zones:** {row.get('zone_min', 'N/A')} to {row.get('zone_max', 'N/A')} | **Maintenance:** {row.get('maintenance', 'N/A')}")
                    st.markdown(f"**Soil:** {row.get('soil_description', 'N/A')} | **Moisture:** {row.get('soil_moisture', 'N/A')} | **pH:** {row.get('soil_ph', 'N/A')}")

                    # Consolidate bloom months into a clean string
                    bloom_months = [m for m in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'] if row.get(f'bloom_{m}') == True]
                    bloom_str = ", ".join([m.title() for m in bloom_months]) if bloom_months else "N/A"

                    st.markdown(f"**Bloom Color:** {row.get('bloom_color', 'N/A')} | **Bloom Season:** {bloom_str}")

                st.write("---")

if __name__ == "__main__":
    main()
