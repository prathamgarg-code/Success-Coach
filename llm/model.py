from langchain_openai import ChatOpenAI
from config.settings import MODEL_NAME

def get_llm():
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.5
    )
    return llm

def get_llm_deterministic(temperature: float = 0.0):
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=temperature
    )
    return llm