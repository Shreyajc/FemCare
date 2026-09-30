import io
from datetime import datetime

import streamlit as st
import pandas as pd
from pathlib import Path
from analytics.dashboard import (
    cycle_chart,
    flow_chart,
    get_metrics,
    load_data,
    pain_chart,
    stress_chart,
)

from scripts.api_overpass_search import find_healthcare

from analytics.eda import (
    get_dataset_overview,
    get_missing_summary,
    get_numeric_summary,
    get_category_distribution,
    get_pain_relationship,
    get_lifestyle_analysis,
    get_weather_correlation,
    get_state_analysis,
    get_correlation_matrix,
    get_pain_correlations,
    get_fusion_feature_groups,
)

from rag.llm import ask_llm
from rag.phase2_retriever import retrieve_context
from router import route
from utils.chat_history import (
    delete_chat,
    get_chat_info,
    get_history,
    load_chat,
    rename_chat,
    save_chat,
)
from utils.clinical_engine import analyze

from utils.nutrition import (
    load_recipes,
    filter_recipes,
    load_usda_foods,
    get_usda_food_names,
    get_food_record,
    format_nutrient,
)

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM CSS STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FemCare AI",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for modern cards, typography, and status elements
st.markdown(
    """
    <style>
    /* Global Container Adjustments */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 95%;
    }

    /* Sidebar Background & Borders */
    [data-testid="stSidebar"] {
        background-color: #faf5f8;
        border-right: 1px solid #f0deea;
    }

    /* Custom Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #f2dbe8;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-card-label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #d53f8c;
        margin-top: 4px;
    }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        background-color: #fff5f7;
        color: #b83280;
        border: 1px solid #fed7e2;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 8px;
        width: 100%;
    }

    /* Hero Banner Header */
    .hero-container {
        background: linear-gradient(135deg, #fff5f7 0%, #fed7e2 100%);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        border: 1px solid #fbb6ce;
    }
    .hero-title {
        color: #97266d;
        font-weight: 800;
        margin-bottom: 6px;
        font-size: 2rem;
    }
    .hero-subtitle {
        color: #702459;
        font-size: 1.05rem;
        margin: 0;
    }

    /* Section Card Wrappers */
    .card-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. DATA LOADING & METRICS
# -----------------------------------------------------------------------------
df = load_data()
metrics = get_metrics(df)

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & SYSTEM STATUS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌸 FemCare AI")
    st.caption("AI-Powered Menstrual Health Assistant")

    st.divider()

    page = st.radio(
    "Navigation",
    [
        "💬 Chat",
        "🕒 History",
        "📊 EDA & Analytics",
        "🔗 Data Fusion",
        "🗃️ Complete Dataset",
        "🏥 Healthcare Finder",
        "🍎 Nutrition Guide",
        "ℹ️ About",
    ],
    label_visibility="collapsed",
)

    st.divider()

    st.markdown("### ⚙️ System Status")
    st.markdown(
        """
        <div>
            <div class="status-badge">🤖 <b>LLM:</b> Llama 3.2</div>
            <div class="status-badge">🔍 <b>Vectorizer:</b> TF-IDF</div>
            <div class="status-badge">⚡ <b>Knowledge Base:</b> Fused Index</div>
            <div class="status-badge">📚 <b>RAG:</b> Enabled</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# 4. PAGE ROUTING & UI LAYOUT
# -----------------------------------------------------------------------------

# --- PAGE 1: CHAT ---
if page == "💬 Chat":
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🌸 FemCare AI Assistant</div>
            <p class="hero-subtitle">
                Ask questions about menstrual cycles, PCOS, pain management, hormonal health, and wellness.
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = datetime.now().strftime(
            "Chat_%d-%m-%Y_%H-%M-%S"
        )

    def generate_chat_text(messages):
        text = []
        text.append("FemCare AI Conversation")
        text.append("=" * 40)
        text.append(f"Generated: {datetime.now()}")
        text.append("")

        for msg in messages:
            role = msg["role"].capitalize()
            text.append(f"{role}:")
            text.append(msg["content"])
            text.append("-" * 40)

        return "\n".join(text)

    # Collapsible / Expressive Guide Card
    with st.expander("💬 **How to interact with FemCare AI**", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown(
                """
                **Ask General Knowledge Questions:**
                - *What is PCOS?*
                - *Why do menstrual cramps happen?*
                - *How does stress affect periods?*
                """
            )
        with col_g2:
            st.markdown(
                """
                **Describe Symptoms for Analysis:**
                ```text
                Pain: 6/10 | Stress: 4/10 | Sleep: 5 hours | Flow: Heavy | PCOS: Yes
                ```
                *Or as text:* "My pain is 6/10, stress is 4/10, I slept 5 hours and my flow is heavy. What can you infer?"
                """
            )

    st.write("")

    # Chat Actions Header Bar
    c_act1, c_act2, _ = st.columns([1, 1, 2])
    with c_act1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = datetime.now().strftime(
                "Chat_%d-%m-%Y_%H-%M-%S"
            )
            st.rerun()

    with c_act2:
        if st.session_state.messages:
            chat_text = generate_chat_text(st.session_state.messages)
            st.download_button(
                label="📥 Download Chat",
                data=chat_text,
                file_name=f"FemCare_Chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.divider()

    # Chat Input Box
    question = st.chat_input("Ask anything about menstrual health...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})

        assessment = None
        context = ""

        with st.spinner("Analyzing and retrieving context..."):
            intent = route(question)

            if intent == "greeting":
                answer = """
👋 Hello! I'm **FemCare AI**.

I'm your AI-powered menstrual health assistant.

I can help you with:

• 🌸 PCOS
• 🩸 Menstrual Health
• 😖 Pain Analysis
• 😴 Sleep & Stress
• 📊 Symptom Assessment

Example:

"My pain is 6/10, stress is 4/10, I slept 5 hours and my flow is heavy. What can you infer?"
"""

            elif intent == "conversation":
                answer = """
You're welcome! 😊

Feel free to ask me anything related to menstrual health, PCOS, hormones, periods, pain, stress or sleep.
"""

            elif intent == "clinical":
                assessment = analyze(question)
                answer = ask_llm(
                    question=question,
                    clinical_report=assessment["report"],
                    context="",
                    mode="clinical",
                )

            else:
                context = retrieve_context(question)
                answer = ask_llm(
                    question=question, context=context, mode="knowledge"
                )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "context": context,
                "assessment": assessment,
            }
        )
        save_chat(
            st.session_state.messages, st.session_state.conversation_id
        )
        st.rerun()

    # Display Chat History Messages
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "🌸"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                assessment = msg.get("assessment")
                if assessment:
                    if any(
                        [
                            assessment["pain"],
                            assessment["stress"],
                            assessment["sleep"],
                            assessment["flow"],
                            assessment["pcos"],
                        ]
                    ):
                        st.divider()
                        st.markdown("### 📋 Health Assessment Overview")

                        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)

                        with mc1:
                            val = assessment["pain"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Pain</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc2:
                            val = assessment["stress"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Stress</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc3:
                            val = assessment["sleep"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Sleep</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc4:
                            val = assessment["flow"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Flow</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc5:
                            val = "Yes" if assessment["pcos"] else "No"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">PCOS</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc6:
                            val = str(assessment["risk"])
                            st.markdown(
                                f"""<div class="metric-card" style="border-color: #fbb6ce;">
                                    <div class="metric-card-label">Risk</div>
                                    <div class="metric-card-value" style="color: #e53e3e;">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                if msg.get("context"):
                    with st.expander("📚 Medical Knowledge Used"):
                        st.info(msg["context"])


# --- PAGE 2: HISTORY ---
elif page == "🕒 History":
    st.title("🕒 Conversation History")
    st.caption("Review, edit, or delete past session transcripts.")
    st.divider()

    history = get_history()

    if not history:
        st.info("No saved conversations found.")
    else:
        chat_map = {}
        for file in history:
            info = get_chat_info(file)
            display = f"{info['title']}    ({info['created_at']})"
            chat_map[display] = file

        selected_display = st.selectbox(
            "Select a conversation", list(chat_map.keys())
        )
        selected_file = chat_map[selected_display]
        info = get_chat_info(selected_file)

        st.markdown(f"## 📝 {info['title']}")
        st.caption(f"Created: {info['created_at']}")
        st.divider()

        # Action Buttons Layout
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input(
                "Rename Conversation", value=info["title"]
            )
            if st.button("💾 Save Title", use_container_width=True):
                rename_chat(selected_file, new_title)
                st.success("Conversation renamed.")
                st.rerun()

        with col2:
            st.write("")
            st.write("")
            if st.button(
                "🗑️ Delete Conversation",
                type="primary",
                use_container_width=True,
            ):
                delete_chat(selected_file)
                st.success("Conversation deleted.")
                st.rerun()

        st.divider()

        # Show Messages Transcript
        messages = load_chat(selected_file)
        for msg in messages:
            avatar = "👤" if msg["role"] == "user" else "🌸"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])


# --- PAGE 3: EDA & ANALYTICS ---

elif page == "📊 EDA & Analytics":

    st.title("📊 FemCare EDA & Analytics")
    st.caption(
        "Exploratory Data Analysis of the final fused menstrual-health dataset"
    )

    eda_df = df

    overview = get_dataset_overview(eda_df)

    # ============================================================
    # OVERVIEW
    # ============================================================

    st.subheader("📌 Dataset Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Records",
        f"{overview['records']:,}"
    )

    c2.metric(
        "Users",
        f"{overview['users']:,}"
    )

    c3.metric(
        "States",
        overview["states"]
    )

    c4.metric(
        "Features",
        overview["features"]
    )

    st.divider()

    # ============================================================
    # EXISTING BASIC ANALYTICS
    # ============================================================

    st.subheader("📈 Menstrual Health Trends")

    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            cycle_chart(eda_df),
            use_container_width=True
        )

    with right:
        st.plotly_chart(
            pain_chart(eda_df),
            use_container_width=True
        )

    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            stress_chart(eda_df),
            use_container_width=True
        )

    with right:
        st.plotly_chart(
            flow_chart(eda_df),
            use_container_width=True
        )

    st.divider()

    # ============================================================
    # PAIN ANALYSIS
    # ============================================================

    st.subheader("🩸 Pain Level Analysis")

    pain_features = [
        "stress_score_cycle",
        "sleep_hours_cycle",
        "mood_score",
        "energy_level",
        "concentration_score",
        "work_hours_lost",
        "overall_health_score",
    ]

    selected_feature = st.selectbox(
        "Analyze pain against:",
        pain_features,
    )

    relationship = get_pain_relationship(
        eda_df,
        selected_feature
    )

    if not relationship.empty:

        import plotly.express as px

        y_column = relationship.columns[1]

        fig = px.bar(
            relationship,
            x="pain_level",
            y=y_column,
            title=(
                f"Average {selected_feature.replace('_', ' ').title()} "
                "by Pain Level"
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # ============================================================
    # PAIN CORRELATIONS
    # ============================================================

    st.subheader("🔗 Correlation With Pain")

    pain_corr = get_pain_correlations(
        eda_df
    )

    pain_corr_display = (
        pain_corr
        .drop("pain_level", errors="ignore")
        .sort_values(
            ascending=False
        )
        .reset_index()
    )

    pain_corr_display.columns = [
        "Feature",
        "Correlation"
    ]

    st.dataframe(
        pain_corr_display,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Correlation indicates statistical association, "
        "not causation."
    )

    st.divider()

    # ============================================================
    # CORRELATION HEATMAP
    # ============================================================

    st.subheader("🔥 Feature Correlation Heatmap")

    correlation_matrix = get_correlation_matrix(
        eda_df
    )

    import plotly.express as px

    fig = px.imshow(
        correlation_matrix,
        text_auto=".2f",
        aspect="auto",
        title="Correlation Matrix"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # ============================================================
    # WEATHER ANALYSIS
    # ============================================================


    st.subheader("🌦️ Environmental Feature Analysis")

    weather_features = [
        "temperature_mean",
        "humidity_mean",
        "precipitation",
        "wind_speed_mean"
    ]

    # Check which weather columns actually exist
    available_weather_features = [
        col for col in weather_features
        if col in eda_df.columns
    ]

    if not available_weather_features:

        st.warning(
            "No environmental/weather features are available "
            "in the current dataset."
        )

    else:

        # Calculate correlations directly from the fused dataset

        weather_results = []

        for feature in available_weather_features:

            correlation = eda_df[
                [feature, "pain_level"]
            ].corr().loc[
                feature,
                "pain_level"
            ]

            weather_results.append({
                "feature": feature,
                "correlation_with_pain": round(
                    correlation,
                    4
                )
            })

        weather_corr = pd.DataFrame(
            weather_results
        )

        # Display table

        st.dataframe(
            weather_corr,
            use_container_width=True,
            hide_index=True
        )

        # Display chart

        import plotly.express as px

        fig = px.bar(
            weather_corr,
            x="feature",
            y="correlation_with_pain",
            title="Weather Feature Correlation With Pain"
        )

        fig.update_layout(
            xaxis_title="Weather Feature",
            yaxis_title="Correlation with Pain"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # Interpretation

        st.info(
            "Correlation measures the strength and direction of a "
            "linear relationship between each weather feature and "
            "pain level. Correlation does not imply causation."
        )

        # LIFESTYLE ANALYSIS

        st.subheader("🏃 Lifestyle Analysis")

        lifestyle = get_lifestyle_analysis(
            eda_df
        )

        if not lifestyle.empty:

            st.dataframe(
                lifestyle,
                use_container_width=True,
                hide_index=True,
            )

            fig = px.bar(
                lifestyle,
                x="exercise_frequency",
                y="average_pain",
                title="Average Pain by Exercise Frequency"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.divider()

        # STATE ANALYSIS

        st.subheader("🇺🇸 State-Level Analysis")

        state_data = get_state_analysis(
            eda_df
        )

        selected_state = st.selectbox(
            "Select a state:",
            sorted(
                state_data["state"].unique()
            )
        )

        selected_state_data = state_data[
            state_data["state"]
            == selected_state
        ]

        st.dataframe(
            selected_state_data,
            use_container_width=True,
            hide_index=True,
        )

# --- PAGE 4: DATA FUSION  ---

elif page == "🔗 Data Fusion":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🔗 FemCare Data Fusion</div>
            <p class="hero-subtitle">
                Integration of menstrual, demographic, public-health,
                environmental and nutritional data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "External APIs are collected separately and stored locally. "
        "The application reads the processed datasets rather than repeatedly "
        "calling external services."
    )

    # FUSION PIPELINE

    st.subheader("🔄 Fusion Pipeline")

    pipeline = pd.DataFrame({
        "Stage": [
            "Base Menstrual Dataset",
            "Census ACS",
            "CDC PLACES",
            "Open-Meteo",
            "USDA FoodData Central",
            "OpenStreetMap / Overpass",
            "Final Fusion",
            "Final Cleaning",
        ],
        "Purpose": [
            "Primary menstrual-cycle records",
            "Population and demographic context",
            "Public-health indicators",
            "Weather and environmental context",
            "Nutrition reference data",
            "Healthcare accessibility reference",
            "Combine contextual features",
            "Prepare ML-ready dataset",
        ],
        "Status": [
            "✓ Complete",
            "✓ Complete",
            "✓ Complete",
            "✓ Complete",
            "✓ Complete",
            "✓ Implemented",
            "✓ Complete",
            "✓ Complete",
        ],
    })

    st.dataframe(
        pipeline,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # FINAL DATASET

    final_path = Path(
        "data/api_fusion/final/femcare_final_cleaned.csv"
    )

    if final_path.exists():

        @st.cache_data
        def load_final_fusion(path):
            return pd.read_csv(path)

        fusion_df = load_final_fusion(final_path)

        rows, cols = fusion_df.shape

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Final Records", f"{rows:,}")
        c2.metric("Final Features", cols)
        c3.metric("Users", f"{fusion_df['user_id'].nunique():,}")
        c4.metric("States", fusion_df["state"].nunique())

        st.divider()

        st.subheader("📊 Final Dataset Composition")

        category_counts = {
            "Menstrual / Clinical": 34,
            "Census ACS": 8,
            "CDC PLACES": 7,
            "Open-Meteo": 6,
        }

        fusion_summary = pd.DataFrame(
            {
                "Source": list(category_counts.keys()),
                "Features": list(category_counts.values()),
            }
        )

        st.bar_chart(
            fusion_summary.set_index("Source")
        )

        st.divider()

        st.subheader("👀 Final Fused Dataset Preview")

        st.dataframe(
            fusion_df.head(20),
            use_container_width=True,
            height=500,
        )

        st.download_button(
            "📥 Download Final Fused Dataset",
            data=fusion_df.to_csv(index=False).encode("utf-8"),
            file_name="femcare_final_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:
        st.error(
            "Final fused dataset not found."
        )

# --- PAGE 5: COMPLETE DATASET ---

elif page == "🗃️ Complete Dataset":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">📋 Complete FemCare Dataset</div>
            <p class="hero-subtitle">
                Explore the cleaned and fully fused menstrual-health dataset.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dataset_path = Path(
        "data/api_fusion/final/femcare_final_cleaned.csv"
    )

    if not dataset_path.exists():
        st.error(f"Dataset not found: {dataset_path}")
        st.stop()

    @st.cache_data
    def load_complete_dataset(path):
        return pd.read_csv(path)

    complete_df = load_complete_dataset(dataset_path)

    # OVERVIEW

    rows, cols = complete_df.shape
    users = complete_df["user_id"].nunique()
    states = complete_df["state"].nunique()
    missing = int(complete_df.isna().sum().sum())

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Records", f"{rows:,}")
    c2.metric("Users", f"{users:,}")
    c3.metric("States", states)
    c4.metric("Columns", cols)

    st.divider()

    # DATA QUALITY

    st.subheader("🔎 Data Quality")

    missing_df = (
        complete_df.isna()
        .sum()
        .reset_index()
    )

    missing_df.columns = ["Feature", "Missing"]

    missing_df["Percentage"] = (
        missing_df["Missing"] / len(complete_df) * 100
    ).round(2)

    missing_df = missing_df[
        missing_df["Missing"] > 0
    ].sort_values(
        "Missing",
        ascending=False
    )

    if missing_df.empty:
        st.success("✓ No missing values found.")
    else:
        st.dataframe(
            missing_df,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # FILTERS

    st.subheader("🔍 Explore Dataset")

    f1, f2, f3 = st.columns(3)

    with f1:
        state_options = ["All States"] + sorted(
            complete_df["state"].dropna().unique().tolist()
        )

        selected_state = st.selectbox(
            "State",
            state_options,
            key="dataset_state_filter",
        )

    with f2:
        selected_pain = st.selectbox(
            "Pain Level",
            ["All"] + list(range(1, 11)),
            key="dataset_pain_filter",
        )

    with f3:
        selected_pcos = st.selectbox(
            "PCOS Diagnosed",
            ["All", "Yes", "No"],
            key="dataset_pcos_filter",
        )

    filtered_df = complete_df.copy()

    if selected_state != "All States":
        filtered_df = filtered_df[
            filtered_df["state"] == selected_state
        ]

    if selected_pain != "All":
        filtered_df = filtered_df[
            filtered_df["pain_level"] == selected_pain
        ]

    if selected_pcos != "All":
        pcos_value = 1 if selected_pcos == "Yes" else 0

        filtered_df = filtered_df[
            filtered_df["pcos_diagnosed"] == pcos_value
        ]

    st.caption(
        f"Showing {len(filtered_df):,} of {len(complete_df):,} records."
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=600,
    )

    # DOWNLOAD

    st.divider()

    st.download_button(
        "📥 Download Complete Dataset",
        data=complete_df.to_csv(index=False).encode("utf-8"),
        file_name="femcare_final_cleaned.csv",
        mime="text/csv",
        use_container_width=True,
    )

# --- PAGE 6: HEALTHCARE FINDER ---

elif page == "🏥 Healthcare Finder":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🏥 FemCare Healthcare Finder</div>
            <p class="hero-subtitle">
                Find nearby hospitals, clinics, doctors, gynecologists and
                pharmacies across the United States using OpenStreetMap data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Healthcare facilities are retrieved dynamically from OpenStreetMap. "
        "Availability and facility information may change over time."
    )

    # U.S. STATES

    us_states = [
        "Alabama",
        "Alaska",
        "Arizona",
        "Arkansas",
        "California",
        "Colorado",
        "Connecticut",
        "Delaware",
        "Florida",
        "Georgia",
        "Hawaii",
        "Idaho",
        "Illinois",
        "Indiana",
        "Iowa",
        "Kansas",
        "Kentucky",
        "Louisiana",
        "Maine",
        "Maryland",
        "Massachusetts",
        "Michigan",
        "Minnesota",
        "Mississippi",
        "Missouri",
        "Montana",
        "Nebraska",
        "Nevada",
        "New Hampshire",
        "New Jersey",
        "New Mexico",
        "New York",
        "North Carolina",
        "North Dakota",
        "Ohio",
        "Oklahoma",
        "Oregon",
        "Pennsylvania",
        "Rhode Island",
        "South Carolina",
        "South Dakota",
        "Tennessee",
        "Texas",
        "Utah",
        "Vermont",
        "Virginia",
        "Washington",
        "West Virginia",
        "Wisconsin",
        "Wyoming",
    ]

    # LOCATION INPUT

    col1, col2 = st.columns(2)

    with col1:
        state = st.selectbox(
            "Select State",
            us_states,
            index=20,  # Massachusetts
            key="healthcare_state",
        )

    with col2:
        city = st.text_input(
            "📍 Enter City / Locality",
            value="Boston",
            placeholder="Example: Boston",
            key="healthcare_city",
        )

    # SEARCH RADIUS

    radius = 12
    st.caption(
        f"Searching healthcare facilities near {city}, {state}."
    )

    # SEARCH BUTTON

    if st.button(
        "🔎 Find Healthcare Facilities",
        use_container_width=True,
    ):

        if not city.strip():

            st.warning(
                "Please enter a city or locality before searching."
            )

        else:

            with st.spinner(
                f"Searching healthcare facilities near "
                f"{city}, {state}..."
            ):

                search_result = find_healthcare(
                    city=city.strip(),
                    state=state,
                    radius_km=radius,
                )

                if not search_result["success"]:

                    if search_result["error"] == "location":

                        st.error(
                            f"Could not verify {city}, {state}. "
                            "Please check the city name."
                        )

                    elif search_result["error"] == "overpass":

                        st.error(
                            "The OpenStreetMap healthcare service is "
                            "temporarily unavailable. Please try again."
                        )

                    facilities = []

                else:
                    facilities = search_result["facilities"]

            # NO RESULTS

            if search_result["success"] and not facilities:

                st.warning(
                    f"No healthcare facilities were found near "
                    f"{city}, {state}."
                )

            elif search_result["success"] and facilities:

                st.success(
                    f"Found {len(facilities)} healthcare facilities "
                    f"near {city}, {state}."
                )

            # RESULTS

            if search_result["success"] and not facilities:

                st.warning(
                    f"No healthcare facilities were found near "
                    f"{city}, {state}."
                )

            elif search_result["success"] and facilities:
                # Show the healthcare search results.

                # ========================================================
                # HEALTHCARE RESULTS
                # ========================================================

                st.success(
                    f"Found {len(facilities)} healthcare facilities "
                    f"near {city}, {state}."
                )

                st.markdown(
                    "## 🏥 Healthcare Facilities"
                )

                st.caption(
                    "Healthcare information is retrieved from "
                    "OpenStreetMap. Address, phone number and website "
                    "availability depends on the information mapped for "
                    "each facility."
                )

                # --------------------------------------------------------
                # DATAFRAME
                # --------------------------------------------------------

                facilities_df = pd.DataFrame(
                    facilities
                )

                expected_columns = [
                    "name",
                    "type",
                    "address",
                    "phone",
                    "website",
                    "latitude",
                    "longitude",
                ]

                for column in expected_columns:

                    if column not in facilities_df.columns:
                        facilities_df[column] = ""

                # Clean empty values

                facilities_df["address"] = (
                    facilities_df["address"]
                    .fillna("")
                    .replace("", "Address not available")
                )

                facilities_df["phone"] = (
                    facilities_df["phone"]
                    .fillna("")
                    .replace("", "Not available")
                )

                facilities_df["website"] = (
                    facilities_df["website"]
                    .fillna("")
                    .replace("", "Not available")
                )

                # --------------------------------------------------------
                # FILTERS
                # --------------------------------------------------------

                st.markdown(
                    "### 🔎 Find a Facility"
                )

                filter_col1, filter_col2 = st.columns(
                    [1, 2]
                )

                with filter_col1:

                    facility_types = [
                        "All",
                        "Hospital",
                        "Clinic",
                        "Doctor",
                        "Gynecologist / OB-GYN",
                        "Pharmacy",
                        "Specialist",
                    ]

                    selected_type = st.selectbox(
                        "Facility type",
                        facility_types,
                        key="healthcare_type_filter",
                    )

                with filter_col2:

                    search_name = st.text_input(
                        "Search by facility name",
                        placeholder="e.g. hospital, clinic, pharmacy...",
                        key="healthcare_name_search",
                    )

                # --------------------------------------------------------
                # APPLY TYPE FILTER
                # --------------------------------------------------------

                filtered_df = facilities_df.copy()

                if selected_type != "All":

                    filtered_df = filtered_df[
                        filtered_df["type"] == selected_type
                    ]

                # --------------------------------------------------------
                # APPLY NAME SEARCH
                # --------------------------------------------------------

                if search_name.strip():

                    search_text = search_name.strip()

                    filtered_df = filtered_df[
                        filtered_df["name"]
                        .str.contains(
                            search_text,
                            case=False,
                            na=False,
                        )
                    ]

                st.caption(
                    f"Showing {len(filtered_df)} "
                    f"of {len(facilities_df)} facilities."
                )

                # --------------------------------------------------------
                # QUICK COUNTS
                # --------------------------------------------------------

                hospitals = int(
                    (
                        facilities_df["type"]
                        == "Hospital"
                    ).sum()
                )

                clinics = int(
                    (
                        facilities_df["type"]
                        == "Clinic"
                    ).sum()
                )

                doctors = int(
                    (
                        facilities_df["type"]
                        == "Doctor"
                    ).sum()
                )

                gynecologists = int(
                    (
                        facilities_df["type"]
                        == "Gynecologist / OB-GYN"
                    ).sum()
                )

                pharmacies = int(
                    (
                        facilities_df["type"]
                        == "Pharmacy"
                    ).sum()
                )

                count1, count2, count3, count4, count5 = st.columns(5)

                with count1:
                    st.metric(
                        "Hospitals",
                        hospitals,
                    )

                with count2:
                    st.metric(
                        "Clinics",
                        clinics,
                    )

                with count3:
                    st.metric(
                        "Doctors",
                        doctors,
                    )

                with count4:
                    st.metric(
                        "Gynecologists",
                        gynecologists,
                    )

                with count5:
                    st.metric(
                        "Pharmacies",
                        pharmacies,
                    )

                st.markdown("---")

                # ========================================================
                # FACILITY DIRECTORY
                # ========================================================

                st.markdown(
                    "### 📋 Facility Directory"
                )

                if filtered_df.empty:

                    st.info(
                        "No facilities match your selected filter."
                    )

                else:

                    directory_df = filtered_df[
                        [
                            "name",
                            "type",
                            "address",
                            "phone",
                            "website",
                        ]
                    ].copy()

                    directory_df.columns = [
                        "Facility Name",
                        "Type",
                        "Address",
                        "Phone",
                        "Website",
                    ]

                    st.dataframe(
                        directory_df,
                        use_container_width=True,
                        hide_index=True,
                        height=500,
                    )

                # ========================================================
                # MAP
                # ========================================================

                st.markdown(
                    "### 📍 Facility Map"
                )

                map_df = filtered_df[
                    [
                        "latitude",
                        "longitude",
                        "name",
                        "type",
                    ]
                ].copy()

                map_df = map_df.dropna(
                    subset=[
                        "latitude",
                        "longitude",
                    ]
                )

                if not map_df.empty:

                    st.map(
                        map_df,
                        latitude="latitude",
                        longitude="longitude",
                        size=40,
                    )

                else:

                    st.info(
                        "Location coordinates are not available "
                        "for the filtered facilities."
                    )

                # ========================================================
                # FACILITY DETAILS
                # ========================================================

                st.markdown(
                    "### 🏥 Facility Details"
                )

                if not filtered_df.empty:

                    for _, facility in filtered_df.iterrows():

                        name = facility["name"]
                        facility_type = facility["type"]
                        address = facility["address"]
                        phone = facility["phone"]
                        website = facility["website"]

                        latitude = facility["latitude"]
                        longitude = facility["longitude"]

                        with st.expander(
                            f"🏥 {name}  ·  {facility_type}"
                        ):

                            detail_col1, detail_col2 = st.columns(
                                [3, 1]
                            )

                            with detail_col1:

                                st.markdown(
                                    f"**Type:** {facility_type}"
                                )

                                st.markdown(
                                    f"**Address:** {address}"
                                )

                                st.markdown(
                                    f"**Phone:** {phone}"
                                )

                                if website != "Not available":

                                    st.markdown(
                                        f"**Website:** "
                                        f"[Open website]({website})"
                                    )

                                else:

                                    st.markdown(
                                        "**Website:** Not available"
                                    )

                            with detail_col2:

                                if (
                                    pd.notna(latitude)
                                    and pd.notna(longitude)
                                ):

                                    maps_url = (
                                        "https://www.google.com/maps/search/"
                                        f"?api=1&query={latitude},{longitude}"
                                    )

                                    st.link_button(
                                        "📍 Open in Maps",
                                        maps_url,
                                        use_container_width=True,
                                    )

        st.divider()

#--- PAGE 7: NUTRITION GUIDE ---

elif page == "🍎 Nutrition Guide":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🍎 FemCare Nutrition Guide</div>
            <p class="hero-subtitle">
                Explore nutritious foods, healthy recipes and simple meal ideas
                designed around menstrual-health wellness.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Nutrition suggestions are for general wellness and educational purposes. "
        "They are not individualized medical or dietary prescriptions."
    )

    recipes = load_recipes()

    # -------------------------------------------------------------------------
    # 1. NUTRITION FOCUS
    # -------------------------------------------------------------------------

    st.subheader("🥗 Find a Healthy Recipe")

    nutrition_focus = st.selectbox(
        "Nutrition Focus",
        [
            "All",
            "Iron",
            "Protein",
            "Calcium",
            "Fiber",
            "Energy",
            "B12",
        ],
        key="nutrition_focus",
    )

    filtered = filter_recipes(
        recipes,
        nutrition_focus=nutrition_focus,
    )

    st.caption(
        f"Showing {len(filtered)} matching recipes."
    )

    # -------------------------------------------------------------------------
    # 2. RECIPE CARDS
    # -------------------------------------------------------------------------

    st.divider()
    st.subheader("🍳 Healthy Recipes")

    if not filtered:

        st.warning(
            "No recipes match all the selected filters. "
            "Try changing one of the selections."
        )

    else:

        for start in range(0, len(filtered), 3):

            row = filtered[start:start + 3]

            cols = st.columns(3)

            for col, recipe in zip(cols, row):

                with col:

                    with st.container(border=True):

                        st.markdown(
                            f"### 🍽️ {recipe['name']}"
                        )

                        st.caption(
                            f"{recipe['meal_type']} • "
                            f"{recipe['diet']} • "
                            f"⏱️ {recipe['prep_time']} min"
                        )

                        st.markdown(
                            "**Nutrition focus:** "
                            + ", ".join(recipe["nutrition_focus"])
                        )

                        st.markdown(
                            "**Ingredients:** "
                            + ", ".join(recipe["ingredients"])
                        )

                        with st.expander("View Recipe"):

                            st.markdown(
                                "**Instructions**"
                            )

                            for step_number, step in enumerate(
                                recipe["instructions"],
                                start=1,
                            ):

                                st.write(
                                    f"{step_number}. {step}"
                                )


    # =============================================================================
    # 3. FOOD EXPLORER
    # =============================================================================

    st.divider()

    st.subheader("🔬 Food Explorer")

    st.write(
        "Explore nutrient information collected from USDA FoodData Central. "
        "Values are provided per 100 g of food."
    )

    usda_df = load_usda_foods()

    if usda_df.empty:

        st.warning(
            "USDA nutrition data is not available."
        )

    else:

        food_names = get_usda_food_names(usda_df)

        if not food_names:

            st.warning(
                "No foods are available in the USDA nutrition dataset."
            )

        else:

            selected_food = st.selectbox(
                "Select a food",
                food_names,
                key="usda_food_selector",
            )

            food = get_food_record(
                usda_df,
                selected_food,
            )

            if food is not None:

                st.markdown(
                    f"### 🍽️ {food['food_name']}"
                )

                st.caption(
                    f"USDA FoodData Central • "
                    f"Data type: {food['data_type']} • "
                    f"FDC ID: {int(food['fdc_id'])}"
                )

                st.markdown(
                    "**Nutrition values per 100 g**"
                )

                # -----------------------------------------------------------------
                # ROW 1
                # -----------------------------------------------------------------

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.metric(
                        "Energy",
                        format_nutrient(
                            food["energy_kcal_100g"],
                            "kcal",
                        ),
                    )

                with c2:
                    st.metric(
                        "Protein",
                        format_nutrient(
                            food["protein_g_100g"],
                            "g",
                        ),
                    )

                with c3:
                    st.metric(
                        "Carbohydrates",
                        format_nutrient(
                            food["carbohydrates_g_100g"],
                            "g",
                        ),
                    )

                with c4:
                    st.metric(
                        "Fat",
                        format_nutrient(
                            food["fat_g_100g"],
                            "g",
                        ),
                    )

                # -----------------------------------------------------------------
                # ROW 2
                # -----------------------------------------------------------------

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.metric(
                        "Iron",
                        format_nutrient(
                            food["iron_mg_100g"],
                            "mg",
                        ),
                    )

                with c2:
                    st.metric(
                        "Magnesium",
                        format_nutrient(
                            food["magnesium_mg_100g"],
                            "mg",
                        ),
                    )

                with c3:
                    st.metric(
                        "Calcium",
                        format_nutrient(
                            food["calcium_mg_100g"],
                            "mg",
                        ),
                    )

                with c4:
                    st.metric(
                        "Fiber",
                        format_nutrient(
                            food["fiber_g_100g"],
                            "g",
                        ),
                    )

                # -----------------------------------------------------------------
                # ROW 3
                # -----------------------------------------------------------------

                c1, c2 = st.columns(2)

                with c1:
                    st.metric(
                        "Vitamin B6",
                        format_nutrient(
                            food["vitamin_b6_mg_100g"],
                            "mg",
                        ),
                    )

                with c2:
                    st.metric(
                        "Vitamin B12",
                        format_nutrient(
                            food["vitamin_b12_ug_100g"],
                            "µg",
                        ),
                    )

                st.caption(
                    "Nutrition values represent the selected USDA food record "
                    "and are reported per 100 g. Missing USDA values are shown "
                    "as 'Not available'."
                )

# --- PAGE 8: ABOUT ---

elif page == "ℹ️ About":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🌸 About FemCare AI</div>
            <p class="hero-subtitle">
                AI-powered menstrual health assistance, analytics and
                contextual health intelligence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🎯 Project Objective")

    st.write(
        """
        FemCare AI is an AI-powered menstrual health platform designed to
        provide menstrual-health information, symptom analysis, statistical
        insights and contextual healthcare information through a unified
        interface.
        """
    )

    st.divider()

    st.subheader("🧠 AI Architecture")

    architecture = pd.DataFrame({
        "Component": [
            "User Interface",
            "Intent Router",
            "Clinical Engine",
            "RAG Retriever",
            "Embedding Model",
            "Vector Database",
            "LLM",
            "Analytics",
            "Data Fusion",
        ],
        "Technology": [
            "Streamlit",
            "Python",
            "Python",
            "LangChain / Retriever",
            "MiniLM",
            "FAISS",
            "Llama 3.2 via Ollama",
            "Pandas / Plotly",
            "Python / Pandas",
        ],
    })

    st.dataframe(
        architecture,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("📊 Data Sources")

    st.markdown(
        """
        - 🩸 Menstrual health dataset
        - 🏛️ Census ACS
        - 🏥 CDC PLACES
        - 🌦️ Open-Meteo
        - 🥗 USDA FoodData Central
        - 🗺️ OpenStreetMap / Overpass
        """
    )

    st.divider()

    st.subheader("⚠️ Important Disclaimer")

    st.warning(
        "FemCare AI is an educational and analytical system. "
        "It does not replace professional medical diagnosis, treatment "
        "or consultation with a qualified healthcare professional."
    )

    st.divider()

    st.subheader("🚀 Future Scope")

    st.markdown(
        """
        - Machine-learning based prediction
        - Personalized health insights
        - Multilingual support
        - Voice interaction
        - Healthcare appointment integration
        - Expanded healthcare accessibility data
        """
    )
