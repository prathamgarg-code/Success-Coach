from llm.model import get_llm
from utils.prompts import SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

llm = get_llm()

def get_response(user_message: str):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    response = llm.invoke(messages)

    return response.content