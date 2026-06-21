import streamlit as st
from agent.chatbot import get_response, create_student_agent
from agent.coach_workflow import run_coach_workflow
from agent.brief_agent import generate_brief
from utils.student_tool import get_student_context
from utils.memory import get_memories, save_memories, save_session_summary
from agent.signal_agent import detect_and_save_signals
from utils.profile_manager import load_profile, format_profile, update_profile

st.set_page_config(page_title="Student AI Coach")

# ── Session state init ─────────────────────────────────────────────────────────
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "student_data" not in st.session_state:
    st.session_state.student_data = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []
if "view" not in st.session_state:
    st.session_state.view = "student"   # "student" | "coach"

# ── Login screen ───────────────────────────────────────────────────────────────
if st.session_state.student_id is None and st.session_state.view == "student":
    st.title("Student AI Coach")
    student_id = st.text_input("Enter Student ID")
    if st.button("Login"):
        if student_id:
            st.session_state.student_id = student_id
            student_data = get_student_context(student_id)        # fetch from Google Sheet at login
            st.session_state.student_data = student_data          # cached for session
            memory_context = get_memories(student_id)
            st.session_state.memory_context = memory_context
            profile = load_profile(student_id)
            st.session_state.profile = profile
            profile_context = format_profile(profile)
            st.session_state.agent = create_student_agent(student_data, memory_context, profile_context)
            st.session_state.agent = create_student_agent(student_data, memory_context)
            st.rerun()

    st.divider()
    if st.button("Switch to Coach View"):
        st.session_state.view = "coach"
        st.rerun()

    st.stop()


# ── Coach View ─────────────────────────────────────────────────────────────────
if st.session_state.view == "coach":
    st.title("Coach Dashboard")

    if st.button("Switch to Student View"):
        st.session_state.view = "student"
        st.rerun()

    st.divider()

    # ── Get Plan ──────────────────────────────────────────────────────────────
    if st.button("Get Plan", type="primary"):
        with st.spinner("Fetching signals → Prioritising students → Writing plan..."):
            result = run_coach_workflow()
            st.session_state.coach_plan = result["plan"]
            st.session_state.today_students = result["today_students"]

    if "coach_plan" in st.session_state and st.session_state.coach_plan:
        st.markdown(st.session_state.coach_plan)
        st.download_button(
            label="Download plan.md",
            data=st.session_state.coach_plan,
            file_name="plan.md",
            mime="text/markdown"
        )

        # ── Pre-Meeting Brief ──────────────────────────────────────────────────
        st.divider()
        st.subheader("Pre-Meeting Brief")

        today_students = st.session_state.get("today_students", [])

        if not today_students:
            st.info("No students scheduled for today.")
        else:
            # Build dropdown options — "9:00 AM — STU001 (Retention call)"
            dropdown_options = [
                f"{s['time']} — {s['student_id']} ({s['session_type']})"
                for s in today_students
            ]
            selected = st.selectbox("Select a student", dropdown_options)

            if st.button("Get Brief", type="primary"):
                # Extract student_id from selected string
                selected_student_id = today_students[dropdown_options.index(selected)]["student_id"]
                with st.spinner(f"Generating brief for {selected_student_id}..."):
                    brief = generate_brief(selected_student_id)
                    st.session_state.coach_brief = brief
                    st.session_state.brief_student_id = selected_student_id

        if "coach_brief" in st.session_state and st.session_state.coach_brief:
            st.divider()
            st.markdown(f"#### Brief — {st.session_state.brief_student_id}")
            st.markdown(st.session_state.coach_brief)

    st.stop()


# ── Student View ───────────────────────────────────────────────────────────────
st.title("Student AI Coach")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Logout"):
        if st.session_state.conversation_log:
            save_memories(
                user_id=st.session_state.student_id,
                conversation=st.session_state.conversation_log
            )
            save_session_summary(st.session_state.student_id, st.session_state.conversation_log)
            detect_and_save_signals(
                student_id=st.session_state.student_id,
                conversation=st.session_state.conversation_log
            )
            update_profile(
                student_id=st.session_state.student_id,
                conversation=st.session_state.conversation_log
            )
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

with col2:
    if st.button("Switch to Coach View"):
        st.session_state.view = "coach"
        st.rerun()

# ── Chat input ─────────────────────────────────────────────────────────────────
def submit():
    text = st.session_state.user_input
    if text:
        relevant_memories = get_memories(st.session_state.student_id, query=text)
        response = get_response(text, st.session_state.agent, relevant_memories)
        st.session_state.messages.append(("You", text))
        st.session_state.messages.append(("AI", response))
        # Update raw log for Mem0 (saved at logout)
        st.session_state.conversation_log.append({"role": "user", "content": text})
        st.session_state.conversation_log.append({"role": "assistant", "content": response})
        st.session_state.user_input = ""

st.text_input("Ask something", key="user_input", on_change=submit)

# ── Display chat history ───────────────────────────────────────────────────────
for sender, message in reversed(st.session_state.messages):
    st.write(f"### {sender}")
    st.write(message)