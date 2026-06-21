import os
from urllib import response
from mem0 import MemoryClient
from dotenv import load_dotenv
from llm.model import get_llm
load_dotenv()

client = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))


def get_memories(user_id: str) -> str:
    """
    Fetch all stored memories for a student.
    Returns a formatted context block string, or empty string if none.
    """
    try:
        response = client.search(query="student", filters={"user_id": user_id}, limit=20)
        print(response)
        print(type(response))
        memories = response["results"]
        if not memories:
            return ""
        
        lines = [f"- {m['memory']}" for m in memories]
        print(lines)
        return "### What I remember about this student:\n" + "\n".join(lines)
    except Exception as e:
        print(f"[Memory] Failed to fetch memories: {e}")
        return ""


def save_memories(user_id: str, conversation: list[dict]) -> None:
    """
    Called at session end. Passes the full conversation to Mem0 —
    it automatically extracts and stores only the important facts.

    conversation format:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    try:
        client.add(messages=conversation, user_id=user_id)
        print(f"[Memory] Session saved for user '{user_id}'.")
    except Exception as e:
        print(f"[Memory] Failed to save memories: {e}")


def save_session_summary(student_id: str, conversation: list[dict]) -> None:
    """
    Called at session end alongside save_memories().
    Uses the LLM to generate a structured coach-facing summary of the session,
    then stores it in Mem0 under user_id="coach_{student_id}" — completely
    isolated from the student's factual memory.
    """
    if not conversation:
        return
 
    try:
        # 1. Format conversation into a readable transcript for the LLM
        transcript = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in conversation
        )
 
        # 2. Ask LLM to generate a structured summary
        
        messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a coaching assistant. Given a session transcript between "
                        "a student and an AI coach, write a concise structured summary for "
                        "the human coach. Cover:\n"
                        "- Topics discussed\n"
                        "- Student's struggles or blockers raised\n"
                        "- Suggestions or action items given\n"
                        "- Any progress or wins mentioned\n"
                        "- Overall student mood or tone\n"
                        "Be factual and brief. Use bullet points."
                    )
                },
                {
                    "role": "user",
                    "content": f"Session transcript:\n\n{transcript}"
                }
            ]
        llm = get_llm()
        response = llm.invoke(messages)
        summary = response.content.strip()
        print(summary)
 
        # 3. Store under coach namespace — isolated from student factual memory
        coach_user_id = f"coach_{student_id}"
        client.add(
            messages=[{"role": "user", "content": summary}],
            user_id=coach_user_id
        )
        print(f"[Memory] Session summary saved for coach under '{coach_user_id}'.")
 
    except Exception as e:
        print(f"[Memory] Failed to save session summary: {e}")