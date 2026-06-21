import streamlit as st
from agent.chatbot import get_response,create_student_agent
from utils.student_tool import get_student_context
from utils.memory import get_memories, save_memories, save_session_summary


if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "student_data" not in st.session_state:
    st.session_state.student_data = None
if "messages" not in st.session_state:
    st.session_state.messages = []
# Raw conversation log for Mem0 — built up turn by turn, saved on logout
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []

if st.session_state.student_id is None:
    student_id = st.text_input("Enter Student ID")

    if st.button("Login"):
        if student_id:
            st.session_state.student_id = student_id
            student_data = get_student_context(student_id) #get student datat from google sheet at login
            st.session_state.student_data = student_data #data is cached for the session
            # 2. Fetch past memories from Mem0 cloud
            memory_context = get_memories(student_id)
            st.session_state.memory_context = memory_context

            st.session_state.agent = create_student_agent(student_data,memory_context) #agent is created with tools and memory context
            st.rerun()

    st.stop()

st.set_page_config(page_title="Student AI Coach")
st.title("Student AI Coach")

if st.button("Logout"):
    if st.session_state.conversation_log:
        save_memories(
            user_id=st.session_state.student_id,
            conversation=st.session_state.conversation_log
        )
        save_session_summary(st.session_state.student_id, st.session_state.conversation_log)
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def submit():
    text = st.session_state.user_input
    if text:
        response = get_response(text, st.session_state.agent)
        st.session_state.messages.append(("You", text))
        st.session_state.messages.append(("AI", response))
         # Update raw log for Mem0 (saved at logout)
        st.session_state.conversation_log.append({"role": "user", "content": text})
        st.session_state.conversation_log.append({"role": "assistant", "content": response})

        st.session_state.user_input = ""

st.text_input("Ask something", key="user_input", on_change=submit)


# Display all previous messages
for sender, message in reversed(st.session_state.messages):
    st.write(f"### {sender}")
    st.write(message)