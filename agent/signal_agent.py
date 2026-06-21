import json
from datetime import datetime
from urllib import response
from llm.model import get_llm_deterministic
from dotenv import load_dotenv
import os

from utils.student_tool import append_signal_row

load_dotenv()

llm = get_llm_deterministic()

SIGNAL_PROMPT = """
You are a student success coach reviewing a conversation between a student and an AI coach.
Your job is to detect any concerning signals that a human coach should be aware of.
 
Scan for these signal types:
- exam_anxiety: stress, panic, can't sleep, overwhelmed before an exam
- attendance_risk: missing classes, planning to skip, low attendance mentioned
- academic_distress: failing, not understanding content, thinking of giving up academically
- deadline_risk: exam or submission very soon and student is unprepared
- disengagement: thinking of quitting the program, stopped caring, lost motivation entirely
- emotional_distress: burnout, anxiety, depression, feeling hopeless, personal crisis
 
For each signal found, return a JSON object with:
- signal_type: one of the types above (snake_case)
- severity: integer 1 to 5 (1 = minor concern, 5 = critical)
- urgency: one of "Today", "Tomorrow", "This week"
- reason: one clear sentence explaining what the student said that triggered this signal
 
==================================================
SEVERITY RULES
==================================================
1 - Very minor, passing concern, no immediate action needed
2 - Worth noting, monitor over time
3 - Moderate concern, coach should follow up soon
4 - Serious concern, needs attention within a day or two
5 - Critical, student at immediate risk of dropping out, harming themselves, or a crisis situation
 
==================================================
URGENCY RULES - FOLLOW THESE STRICTLY
==================================================
These are NOT suggestions. Apply them exactly:
 
"Today" - MUST be used when ANY of these are true:
  - severity is 4 or 5
  - Student explicitly says they want to quit or leave the program
  - Student mentions a crisis happening right now (emotional breakdown, etc.)
  - Student expresses hopelessness or complete loss of motivation
  - Student is failing and has an important exam or deadline within the next 2 days
  - Student mentions severe burnout or mental health struggles impacting their ability to continue
  - Attendance risk with an important upcoming exam or deadline and low attendance
 
"Tomorrow" - use when:
  - severity is 3
  - Issue is serious but not immediate
 
"This week" - use when:
  - severity is 1 or 2
  - Issue is a pattern or slow-building concern with no immediate trigger
 
A severity 5 signal ALWAYS gets urgency "Today". No exceptions.
A student saying they want to leave the course is ALWAYS severity 5 and urgency "Today".
 
==================================================
 
Return ONLY a valid JSON array. No explanation, no markdown, no preamble.
If nothing concerning is found, return an empty array: []
 
Example:
[
  {
    "signal_type": "disengagement",
    "severity": 5,
    "urgency": "Today",
    "reason": "Student explicitly said they want to leave the course and see no point in continuing."
  }
]
"""


def detect_and_save_signals(student_id: str, conversation: list[dict]) -> None:
    """
    Runs after session ends. Passes the full conversation to GPT-4o,
    detects concerning signals, and writes each one as a row in signal_sheet.

    Args:
        student_id: the logged-in student's ID
        conversation: list of {"role": ..., "content": ...} dicts
    """
    if not conversation:
        return

    try:
        # 1. Format transcript
        transcript = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in conversation
        )

        # 2. Call GPT-4o to detect signals
        response = llm.invoke([
            ("system", SIGNAL_PROMPT),
            ("human", f"Session transcript:\n\n{transcript}")
        ])

        raw = response.content.strip()

        # 3. Parse JSON response
        # Strip markdown fences if model wraps in ```json ... ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        signals = json.loads(raw.strip())

        if not signals:
            print(f"[Signal Agent] No signals detected for '{student_id}'.")
            return

        # 4. Write one row per signal to signal_sheet
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        for signal in signals:
            append_signal_row({
                "student_id": student_id,
                "signal_type": signal.get("signal_type", "unknown"),
                "severity": signal.get("severity", 1),
                "urgency": signal.get("urgency", "This week"),
                "reason": signal.get("reason", ""),
                "timestamp": timestamp,
                "actioned": "FALSE"
            })

        print(f"[Signal Agent] {len(signals)} signal(s) saved for '{student_id}'.")

    except json.JSONDecodeError as e:
        print(f"[Signal Agent] Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        print(f"[Signal Agent] Error: {e}")

