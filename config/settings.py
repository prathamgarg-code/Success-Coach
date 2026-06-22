import os
from dotenv import load_dotenv
import streamlit as st
load_dotenv()

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL_NAME = "gpt-5.4-mini-2026-03-17"