from utils.rag import search_kb, format_context

results = search_kb("What is My Journey?")
print(format_context(results))

