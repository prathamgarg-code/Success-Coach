from langchain_openai import ChatOpenAI
from config.settings import MODEL_NAME

def get_llm():
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.5
    )
    return llm

def get_llm_deterministic():
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.0
    )
    return llm