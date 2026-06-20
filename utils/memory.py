import os
from mem0 import MemoryClient
from dotenv import load_dotenv

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