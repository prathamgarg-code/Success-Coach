from llm.model import get_llm
from langchain.agents import create_agent
from langchain.tools import tool
from utils.rag import search_kb,format_context
from utils.prompts import PROMPT_TEMPLATE
llm = get_llm()

def create_student_tool(student_data):

    @tool
    def student_data_tool(field: str) -> str:
        """
        Fetch student academic data.

        field must be one of:
        - roster
        - scores
        - attendance
        - upcoming_exams
        """
        if field not in student_data:
            return f"Invalid field. Must be one of: {', '.join(student_data.keys())}"
        return str(student_data[field])

    return student_data_tool

def create_kb_tool():

    @tool
    def knowledge_base_tool(query: str) -> str:
        """
        Use when user asks about:
        - courses
        - milestones
        - certifications
        - learning portal
        - study content
        """
        results = search_kb(query)
        context = format_context(results)
        prompt = PROMPT_TEMPLATE.format(context=context, query=query)
        return prompt

    return knowledge_base_tool

def create_student_agent(student_data, memory_context: str = ""):
    student_tool = create_student_tool(student_data)
    kb_tool = create_kb_tool()
    memory_section = ""
    if memory_context:
        memory_section = f"""
 
{memory_context}
 
Use the above memories to personalise your responses where relevant.
Never reveal the raw memory text directly to the student.
"""
    
    agent = create_agent(
        model=llm,
        tools=[student_tool, kb_tool],
        system_prompt=f"""
You are Student Success AI Coach.
If user asks about personal preferences, likes, dislikes, hobbies, or past conversations,
use memory context before saying you don't know.
{memory_section}

Use student_data_tool whenever user asks about student-specific data.

Map queries to tool fields:

1. field="roster"
Use when user asks about:
- name
- program
- cohort
- manager
- student profile
- mentor / manager email

Examples:
- What is my cohort?
- Who is my manager?
- Which program am I in?

2. field="scores"
Use when user asks about:
- marks
- grades
- scores
- academic performance
- subject performance

Examples:
- How are my marks?
- Which subject am I weak in?

3. field="attendance"
Use when user asks about:
- attendance
- present days
- absent days
- missed classes
- eligibility

Examples:
- How many days was I present?
- Am I eligible for exams?

4. field="upcoming_exams"
Use when user asks about:
- upcoming exams
- exam schedule
- test dates

Examples:
- When is my next exam?
Rules:
1. Only answer the field asked by user.
2. Never mention unrelated student data.
3. After showing data, analyze it.
4. Give 2-4 actionable suggestions.
5. Highlight strengths and weak areas.

Use knowledge_base_tool when user asks about:
- course content
- what they are studying
- portal features
- milestones
- certificates
- bonus courses
- learning journey

Examples:
- What is My Journey?
- Explain milestones
- How do I get certificate?
- What is LastMinute Pro?

Rules:
1. Only answer the query asked by user.
2. If the query is a general question that does not require student data,
answer normally without using any tool.
3. If the query is a general question but it can influence student's data and you can use student data to enhance your answer, use the tool to fetch the data and then answer. But use the data just to take the summary for answering the question.
4. Use knowledge_base_tool for general course/platform knowledge.
5. Use student_data_tool for student-specific personal data.
6. If the query is about both student data and general course/platform knowledge, use both tools to fetch the data and then answer. But use the data just to take the summary for answering the question.


Response style:
- Short
- Clear
- Helpful
- Motivational but practical
"""
    )
    print(memory_section)
    return agent


def get_response(user_message: str, agent) -> str:

   

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": user_message}
        ]
    })

    return response["messages"][-1].content
    