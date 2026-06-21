import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from langchain.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SHEET_ID)
print("Service account:", creds.service_account_email)
print("Spreadsheet:", spreadsheet.title)

sheet = spreadsheet.worksheet("signal_sheet")
print("Worksheet:", sheet.title)



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


def append_signal_row(signal: dict) -> None:
    """
    Appends one signal row to the signal_sheet tab.
 
    Expected signal dict keys:
        student_id, signal_type, severity, urgency, reason, timestamp, actioned
    """
    try:
        sheet = spreadsheet.worksheet("signal_sheet")
        row = [
            signal.get("student_id", ""),
            signal.get("signal_type", ""),
            signal.get("severity", ""),
            signal.get("urgency", ""),
            signal.get("reason", ""),
            signal.get("timestamp", ""),
            signal.get("actioned", "FALSE"),
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        print(f"[Sheets] Signal row appended for student '{signal.get('student_id')}'.")
    except Exception as e:
        print(f"[Sheets] Failed to append signal row: {e}")
        
 

