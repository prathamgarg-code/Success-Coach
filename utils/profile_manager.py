import os
import json
from datetime import datetime
from llm.model import get_llm

PROFILES_DIR = "profiles"

EMPTY_PROFILE_TEMPLATE = {
    "student_id": "",
    "last_updated": "",
    "goals": [],
    "preferences": [],
    "weaknesses": [],
    "habits": [],
    "mental_patterns": [],
    "likings": []
}

UPDATE_PROMPT = """
You are maintaining a long-term student profile.
You will receive the existing profile as JSON and a new conversation transcript.

Your job:
1. Extract any new facts from the conversation that belong to these categories:
   - goals: placement prep, exams, internships, career targets
   - preferences: how they like to learn, what they hate, communication style
   - weaknesses: academic subjects, soft skills, behavioural patterns
   - habits: study routines, physical activities, sleep patterns, daily rituals
   - mental_patterns: stress triggers, motivation patterns, emotional tendencies
   - likings: hobbies, interests, things that help them relax or focus

2. For each new fact, compare it against the existing profile and decide:
   - ADD: if it's a new fact not present at all
   - UPDATE: if it clearly replaces an existing fact (e.g. "used to study at night, now studies in the morning" → update to "studies in the morning")
   - APPEND: if it adds nuance without replacing (e.g. "also likes cricket in addition to football" → keep both)
   - IGNORE: if the fact is already captured or too vague to be useful

3. Return the COMPLETE updated profile as a JSON object with all 6 category arrays updated.
   Each item in an array should be a short, clear string fact.

Rules:
- Never delete facts unless clearly replaced by new information
- Keep facts concise — one fact per string, no long sentences
- Only include facts explicitly mentioned or strongly implied in the conversation
- Do not fabricate or assume facts not present in the transcript
- If nothing new is found, return the existing profile unchanged

Return ONLY a valid JSON object. No explanation, no markdown fences.

Example output:
{
  "goals": ["placement prep", "wants internship by Q3"],
  "preferences": ["likes simple explanations", "hates long answers"],
  "weaknesses": ["statistics", "procrastination"],
  "habits": ["studies in the morning", "yoga helps focus"],
  "mental_patterns": ["gets stressed before exams", "loses motivation mid-week"],
  "likings": ["football reduces stress", "likes cricket"]
}
"""


def load_profile(student_id: str) -> dict:
    """
    Loads the student's profile from disk.
    Returns empty profile template if file doesn't exist yet.
    """
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = os.path.join(PROFILES_DIR, f"{student_id}.json")

    if not os.path.exists(path):
        profile = {**EMPTY_PROFILE_TEMPLATE, "student_id": student_id}
        return profile

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Profile] Failed to load profile for '{student_id}': {e}")
        return {**EMPTY_PROFILE_TEMPLATE, "student_id": student_id}


def save_profile(student_id: str, profile: dict) -> None:
    """Writes the profile dict to profiles/{student_id}.json."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = os.path.join(PROFILES_DIR, f"{student_id}.json")
    try:
        profile["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        print(f"[Profile] Profile saved for '{student_id}'.")
    except Exception as e:
        print(f"[Profile] Failed to save profile for '{student_id}': {e}")


def update_profile(student_id: str, conversation: list[dict]) -> None:
    """
    Called at logout. Extracts new facts from the conversation using LLM,
    merges them with the existing profile, and saves to disk.
    """
    if not conversation:
        return

    try:
        existing_profile = load_profile(student_id)

        # Strip student_id and last_updated — only send the 6 category arrays to LLM
        profile_categories = {
            k: v for k, v in existing_profile.items()
            if k in ("goals", "preferences", "weaknesses", "habits", "mental_patterns", "likings")
        }

        transcript = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in conversation
        )

        messages = [
            {"role": "system", "content": UPDATE_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Existing profile:\n{json.dumps(profile_categories, indent=2)}\n\n"
                    f"New conversation transcript:\n{transcript}"
                )
            }
        ]

        llm = get_llm()
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        updated_categories = json.loads(raw)

        # Merge back with student_id
        updated_profile = {
            "student_id": student_id,
            **updated_categories
        }

        save_profile(student_id, updated_profile)

    except json.JSONDecodeError as e:
        print(f"[Profile] Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        print(f"[Profile] Failed to update profile for '{student_id}': {e}")


def format_profile(profile: dict) -> str:
    """
    Formats the profile dict into a readable string block
    for injection into the agent system prompt or coach brief.
    Returns empty string if profile has no facts yet.
    """
    categories = {
        "goals": "Goals",
        "preferences": "Preferences",
        "weaknesses": "Weaknesses",
        "habits": "Habits",
        "mental_patterns": "Mental patterns",
        "likings": "Likings"
    }

    lines = []
    for key, label in categories.items():
        values = profile.get(key, [])
        if values:
            lines.append(f"- {label}: {', '.join(values)}")

    if not lines:
        return ""

    return "### AUTHORITATIVE Student Profile (always prefer this over episodic memory for profile facts):\n" + "\n".join(lines)