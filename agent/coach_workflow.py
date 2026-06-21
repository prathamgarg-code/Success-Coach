import json

from datetime import datetime
from typing import TypedDict
from llm.model import get_llm_deterministic

from langgraph.graph import StateGraph, END

from utils.student_tool import get_all_signals



llm = get_llm_deterministic()
llm_warm = get_llm_deterministic(temperature=0.3)  # warm up the model to avoid cold start latency
# ── Shared state across all nodes ──────────────────────────────────────────────
class CoachState(TypedDict):
    signals: list[dict]        # raw signals from sheet — set by Node 1
    prioritised: str 
    today_students: list[dict]  # parsed today list for dropdown — set by Node 2          # prioritisation reasoning output — set by Node 2
    plan: str                  # final plan markdown — set by Node 3


# ── Node 1: Signal Fetcher ─────────────────────────────────────────────────────
def fetch_signals(state: CoachState) -> CoachState:
    """Reads all unactioned signals from signal_sheet."""
    print("[Node 1] Fetching signals from Google Sheets...")
    signals = get_all_signals()
    return {**state, "signals": signals}


# ── Node 2: Prioritisation Agent ───────────────────────────────────────────────
PRIORITISE_PROMPT = """
You are a student success coach's assistant.
You have been given a list of student signals — concerns flagged after their AI coaching sessions.
 
Your job is to decide who the coach should meet today and who should be deferred to tomorrow.
 
COACH SCHEDULE:
- Morning slot: 9:00 AM to 1:00 PM (4 students, one per hour: 9am, 10am, 11am, 12pm)
- Afternoon slot: 3:00 PM to 5:00 PM (2 students, one per hour: 3pm, 4pm)
- Total capacity today: 6 students maximum
- Any students beyond capacity are deferred to tomorrow
 
PRIORITISATION RULES:
1. Sort by urgency first: "Today" > "Tomorrow" > "This week"
2. Within same urgency, sort by severity (5 = highest, 1 = lowest)
3. If a student has multiple signals, treat their highest severity signal as their priority
4. Fill morning slots first, then afternoon slots
5. Deferred students must include a clear reason why they didn't make today's plan
 
SESSION TYPE MAPPING:
- disengagement → Retention call
- emotional_distress → Emotional check-in
- exam_anxiety → Exam prep support
- academic_distress → Academic intervention
- deadline_risk → Urgent deadline support
- attendance_risk → Attendance review
 
Return a JSON object with this exact structure:
{
  "today": [
    {
      "student_id": "STU001",
      "time": "9:00 AM",
      "session_type": "Retention call",
      "signal_type": "disengagement",
      "severity": 5,
      "reason": "Student explicitly said they want to leave the program"
    }
  ],
  "tomorrow": [
    {
      "student_id": "STU007",
      "signal_type": "exam_anxiety",
      "severity": 3,
      "reason": "Lower priority than today's critical cases — exam anxiety but not immediate"
    }
  ]
}
 
Return ONLY valid JSON. No explanation, no markdown fences.
"""
 
def prioritise_students(state: CoachState) -> CoachState:
    """LLM reasons over signals and assigns students to time slots."""
    print("[Node 2] Prioritising students...")
 
    signals = state["signals"]
    if not signals:
        empty = {"today": [], "tomorrow": []}
        return {**state, "prioritised": json.dumps(empty), "today_students": []}
 
    signals_text = json.dumps(signals, indent=2)

    messages = [
        ("system", PRIORITISE_PROMPT),
        ("user", f"Here are the signals:\n\n{signals_text}")
]

    response = llm.invoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
 
    # Parse today_students for the dropdown
    try:
        parsed = json.loads(raw)
        today_students = parsed.get("today", [])
    except Exception:
        today_students = []
 
    return {**state, "prioritised": raw, "today_students": today_students}


# ── Node 3: Plan Writer Agent ──────────────────────────────────────────────────
PLAN_PROMPT = """
You are writing a daily coaching plan for a student success coach.
You will receive a prioritised list of students to meet today and those deferred to tomorrow.

Write a clean, structured daily plan in markdown format.

The plan must include:
1. A header with today's date
2. A "Today's Sessions" section — each student as a subsection with:
   - Their assigned time slot
   - Session type (bolded)
   - A plain one-sentence reason why they are there today
3. A "Deferred to Tomorrow" section — a list of students with a brief reason each
4. A short "Coach Notes" section at the bottom with any patterns you notice across the signals

Keep the language direct and practical. This is for the coach's eyes only.
No fluff, no motivational language — just clarity.
"""

def write_plan(state: CoachState) -> CoachState:
    """LLM writes the final markdown plan and saves it to plan.md."""
    print("[Node 3] Writing daily plan...")

    today_str = datetime.now().strftime("%d %B %Y")

    messages = [
    ("system", PLAN_PROMPT),
    (
        "user",
        f"Today's date: {today_str}\n\n"
        f"Prioritised student list:\n{state['prioritised']}"
    )
]

    response = llm_warm.invoke(messages)
    plan = response.content.strip()

    # Save locally as plan.md
    with open("plan.md", "w", encoding="utf-8") as f:
        f.write(plan)
    print("[Node 3] plan.md saved.")

    return {**state, "plan": plan}


# ── Build LangGraph workflow ───────────────────────────────────────────────────
def build_coach_workflow():
    graph = StateGraph(CoachState)

    graph.add_node("fetch_signals", fetch_signals)
    graph.add_node("prioritise_students", prioritise_students)
    graph.add_node("write_plan", write_plan)

    graph.set_entry_point("fetch_signals")
    graph.add_edge("fetch_signals", "prioritise_students")
    graph.add_edge("prioritise_students", "write_plan")
    graph.add_edge("write_plan", END)

    return graph.compile()


# ── Public entry point called from app.py ─────────────────────────────────────
def run_coach_workflow() -> dict:
    """
    Runs the full 3-node LangGraph workflow.
    Returns a dict with:
        - "plan": markdown string for display
        - "today_students": list of dicts for the brief dropdown
    """
    workflow = build_coach_workflow()
    initial_state: CoachState = {
        "signals": [],
        "prioritised": "",
        "today_students": [],
        "plan": ""
    }
    result = workflow.invoke(initial_state)
    return {
        "plan": result["plan"],
        "today_students": result["today_students"]
    }