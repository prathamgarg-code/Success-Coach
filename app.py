import streamlit as st
from agent.chatbot import get_response




if "student_id" not in st.session_state:
    st.session_state.student_id = None

if st.session_state.student_id is None:
    student_id = st.text_input("Enter Student ID")

    if st.button("Login"):
        if student_id:
            st.session_state.student_id = student_id
            st.rerun()

    st.stop()

st.set_page_config(page_title="Student AI Coach")
st.title("Student AI Coach")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def submit():
    text = st.session_state.user_input
    if text:
        response = get_response(text,st.session_state.student_id)
        st.session_state.messages.append(("You", text))
        st.session_state.messages.append(("AI", response))
        st.session_state.user_input = ""

st.text_input("Ask something", key="user_input", on_change=submit)


# Display all previous messages
for sender, message in reversed(st.session_state.messages):
    st.write(f"### {sender}")
    st.write(message)