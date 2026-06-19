import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from langchain.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SHEET_ID)


def get_student_context(student_id):
    # worksheets
    roster = spreadsheet.worksheet("roster")
    scores = spreadsheet.worksheet("exam_scores")
    attendance = spreadsheet.worksheet("attendance")
    exam_schedule = spreadsheet.worksheet("exam_schedule")

    # fetch all rows
    roster_rows = roster.get_all_records()
    score_rows = scores.get_all_records()
    attendance_rows = attendance.get_all_records()
    exam_rows = exam_schedule.get_all_records()

    # filter by student_id
    student_roster = [
        row for row in roster_rows
        if row["student_id"] == student_id
    ]

    student_scores = [
        row for row in score_rows
        if row["student_id"] == student_id
    ]

    student_attendance = [
        row for row in attendance_rows
        if row["student_id"] == student_id
    ]

    student_exams = [
        row for row in exam_rows
        if row["student_id"] == student_id
    ]

    return {
        "roster": student_roster,
        "scores": student_scores,
        "attendance": student_attendance,
        "upcoming_exams": student_exams
    }



# def student_data_tool(query: str) -> str:
#     """
#     Use this tool when user asks about:
#     marks, scores, attendance, exams, performance, academic progress.
#     """
#     # student_id = st.session_state.student_id
#     import streamlit as st
#     print(st.session_state)
#     student_id = st.session_state.student_id
#     if student_id is None:
#         return "no student logged in. Please login first."
#     data = get_student_context(student_id)

#     if not data["roster"]:
#         return "Student not found."

#     return str(data)