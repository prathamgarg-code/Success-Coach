import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

# Paths
DOCUMENTS_DIR = "./documents"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "knowledge_base"

def ingest():
    # 1. Load all .md files from the documents folder
    loader = DirectoryLoader(
        DOCUMENTS_DIR,
        glob="**/*.md", #loads all .md files in the current directory and subdirectories
        loader_cls=UnstructuredMarkdownLoader, #specialised reader for markdown files
        show_progress=True #display progress bar while loading files
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} document(s).")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,        # small overlap so chunks don't lose context at boundaries
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks.")

    # 3. Embed and store in ChromaDB
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME
    )

    print(f"Done. {len(chunks)} chunks stored in ChromaDB at '{CHROMA_DIR}'.")

if __name__ == "__main__":
    ingest()