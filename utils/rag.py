import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import streamlit as st
load_dotenv()

# Paths — must match ingest_kb.py
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "knowledge_base"

# Load the existing vectorstore (no re-ingestion)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=st.secrets["OPENAI_API_KEY"]
)

vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)

def search_kb(query: str, k: int = 3) -> list[dict]:
    """
    Search the knowledge base for the most relevant chunks.

    Returns a list of dicts, each with:
        - 'content'  : the text chunk
        - 'source'   : file the chunk came from
        - 'score'    : relevance score (lower = more similar for L2 distance)
    """
    results = vectorstore.similarity_search_with_score(query, k=k)

    if not results:
        return [{"content": "No relevant info found.", "source": None, "score": None}]

    output = []
    for doc, score in results:
        output.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "score": round(score, 4)
        })

    return output


def format_context(results: list[dict]) -> str:
    """Helper — turns search_kb results into a single context string for an LLM prompt."""
    parts = []
    for r in results:
        parts.append(f"[Source: {r['source']} | Score: {r['score']}]\n{r['content']}")
    return "\n\n---\n\n".join(parts)