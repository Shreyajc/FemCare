import io
from datetime import datetime

import streamlit as st
from analytics.dashboard import (
    cycle_chart,
    flow_chart,
    get_metrics,
    load_data,
    pain_chart,
    stress_chart,
)

from rag.llm import ask_llm
from rag.retriever import retrieve_context
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
            "📊 Analytics",
            "📁 Dataset Info",
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
            <div class="status-badge">🔍 <b>Embedding:</b> MiniLM</div>
            <div class="status-badge">⚡ <b>Vector DB:</b> FAISS</div>
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


# --- PAGE 3: ANALYTICS ---
elif page == "📊 Analytics":
    st.title("📊 Menstrual Health Analytics")
    st.caption("Aggregated analytics and statistical trends from platform data")
    st.divider()

    st.subheader("📌 General Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", f"{metrics['Total Records']:,}")
    c2.metric("Users", f"{metrics['Unique Users']:,}")
    c3.metric("Average Age", f"{metrics['Average Age']} yrs")
    c4.metric("Average BMI", metrics["Average BMI"])

    st.write("")

    st.subheader("🩺 Clinical Indicators")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Cycle Length", f"{metrics['Average Cycle Length']} days")
    c6.metric("Pain Level", f"{metrics['Average Pain']}/10")
    c7.metric("Stress Level", f"{metrics['Average Stress']}/10")
    c8.metric("PCOS Cases", f"{metrics['PCOS Cases']:,}")

    st.divider()

    st.subheader("📈 Trend Visualizations")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.plotly_chart(cycle_chart(df), use_container_width=True)

    with right:
        with st.container(border=True):
            st.plotly_chart(pain_chart(df), use_container_width=True)

    left2, right2 = st.columns(2)
    with left2:
        with st.container(border=True):
            st.plotly_chart(stress_chart(df), use_container_width=True)

    with right2:
        with st.container(border=True):
            st.plotly_chart(flow_chart(df), use_container_width=True)


# --- PAGE 4: DATASET INFO ---
elif page == "📁 Dataset Info":
    st.title("📁 Dataset Information")
    st.caption("Inspect missing values, features, and record samples.")
    st.divider()

    rows, cols = df.shape

    st.subheader("📊 Dataset Shape")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{rows:,}")
    c2.metric("Columns", cols)
    c3.metric("Missing Values", int(df.isna().sum().sum()))

    st.divider()

    col_df1, col_df2 = st.columns([1, 2])
    with col_df1:
        st.subheader("📋 Columns")
        st.dataframe(
            {"Column Name": df.columns.tolist()}, use_container_width=True
        )

    with col_df2:
        st.subheader("👀 Sample Records")
        st.dataframe(df.head(10), use_container_width=True)


# --- PAGE 5: ABOUT ---
elif page == "ℹ️ About":
    st.title("ℹ️ About FemCare AI")
    st.divider()

    st.markdown(
        """
    ### 🌸 FemCare AI Architecture

    An AI-powered Retrieval-Augmented Generation (RAG) platform designed to provide evidence-based guidance and symptom assessments for menstrual health.

    ---

    ### 🛠️ Key Technology Stack

    | Layer | Technology |
    | :--- | :--- |
    | **LLM Engine** | Llama 3.2 (via Ollama) |
    | **Orchestration** | LangChain / Python |
    | **Vector Database** | FAISS |
    | **Embedding Model** | HuggingFace MiniLM |
    | **UI Framework** | Streamlit |
    | **Visualizations** | Plotly |

    ---

    ### ✨ Core Features
    - **Intelligent Routing:** Automatically routes input to greetings, general chit-chat, RAG retrieval, or clinical symptom analysis.
    - **Clinical Symptom Parser:** Extracts pain scales, sleep hours, stress scores, and risk classifications into metric cards.
    - **Medical Knowledge RAG:** Grounded responses using FAISS vector search context.
    - **Session Transcripts:** Complete chat history saving, renaming, and exporting capability.
    """
    )