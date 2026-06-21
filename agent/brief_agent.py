import os
from llm.model import get_llm_deterministic
from dotenv import load_dotenv

from utils.memory import get_memories, get_session_summaries
from utils.student_tool import get_student_context
from utils.profile_manager import load_profile, format_profile

load_dotenv()

BRIEF_PROMPT = """
You are preparing a pre-meeting brief for a student success coach.
The coach is about to meet this student and needs a focused, practical summary.

You will receive:
1. Live academic data — current scores, attendance, upcoming exams
2. Long-term profile — stable facts about this student (goals, preferences, weaknesses, habits, mental patterns, likings)
3. Episodic memory — recent facts extracted from AI coaching sessions
4. Past session summaries — what was discussed in previous sessions

Write a brief covering exactly these four sections:

## Current Academic Situation
Summarise their academic standing right now — scores, attendance, any upcoming exams.
Be specific with numbers if available. Flag anything concerning.

## What Has Changed Since Last Session
Based on session summaries, what is new or different? Any progress made or new issues raised?
If no previous sessions exist, state that this appears to be an early interaction.

## Open Concerns
List any unresolved struggles, patterns, or blockers from the profile, memory, and past sessions.
These are things the coach should actively address today.

## Conversation Starters for Today
Give exactly 3 specific, natural opening questions or prompts the coach can use.
These should feel personal and reference what you know about the student — not generic.
Draw from their goals, habits, and known stress patterns where possible.

Keep each section concise. This is a quick brief, not a report.
Coach has 2 minutes to read this before the meeting.
"""


def generate_brief(student_id: str) -> str:
    """
    Generates a focused pre-meeting brief for the coach about a specific student.
    Pulls from live sheet data, long-term profile, episodic memory, and session summaries.
    """
    print(f"[Brief Agent] Generating brief for '{student_id}'...")

    # 1. Live academic data from Google Sheets
    try:
        student_data = get_student_context(student_id)
        academic_context = f"Live academic data:\n{student_data}"
    except Exception as e:
        academic_context = f"Could not fetch academic data: {e}"

    # 2. Long-term profile from disk
    profile = load_profile(student_id)
    profile_context = format_profile(profile)
    if not profile_context:
        profile_context = "Long-term profile: No profile data stored yet for this student."

    # 3. Episodic memory from Mem0 — recent facts from AI sessions
    episodic_memory = get_memories(student_id, query="student goals struggles patterns performance")
    if not episodic_memory:
        episodic_memory = "Episodic memory: No recent session memories found."

    # 4. Past session summaries stored under coach_{student_id}
    session_summaries = get_session_summaries(student_id)
    if not session_summaries:
        session_summaries = "Past session summaries: No previous sessions found."

    full_context = "\n\n".join([
        academic_context,
        profile_context,
        episodic_memory,
        session_summaries
    ])

    messages = [
        {"role": "system", "content": BRIEF_PROMPT},
        {"role": "user", "content": f"Student ID: {student_id}\n\n{full_context}"}
    ]

    llm = get_llm_deterministic(temperature=0.3)
    response = llm.invoke(messages)
    brief = response.content.strip()

    print(f"[Brief Agent] Brief generated for '{student_id}'.")
    return brief