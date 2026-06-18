import streamlit as st
from agent.chatbot import get_response

st.set_page_config(page_title="Student AI Coach")
st.title("Student AI Coach")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.text_input("Ask something")

if st.button("Send"):
    if user_input:
        response = get_response(user_input)

        # Save conversation
        st.session_state.messages.append(("You", user_input))
        st.session_state.messages.append(("AI", response))

# Display all previous messages
for sender, message in reversed(st.session_state.messages):
    st.write(f"### {sender}")
    st.write(message)