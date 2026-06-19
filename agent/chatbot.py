from llm.model import get_llm
from utils.prompts import SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from utils.student_tool import get_student_context
from langchain.tools import tool


llm = get_llm()
def create_student_tool(student_id):

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
        data = get_student_context(student_id)
        return str(data[field])

    return student_data_tool


def create_student_agent(student_id):
    student_tool = create_student_tool(student_id)

    agent = create_agent(
        model=llm,
        tools=[student_tool],
        system_prompt="""
You are Student Success AI Coach.

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

2. field="marks"
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

4. field="exams"
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

If the query is a general question that does not require student data,
answer normally without using any tool.

Response style:
- Short
- Clear
- Helpful
- Motivational but practical
"""
    )

    return agent
# agent = create_agent(
#     model=llm,
#     tools=[student_data_tool],
#     system_prompt="""You are Student Success AI Coach.

# Use student_data_tool ONLY when user asks about:
# - marks
# - scores
# - attendance
# - exams
# - academic performance

# For general questions, answer normally.

# When tool data is available:
# - mention exact scores
# - mention attendance
# - mention upcoming exams
# - highlight weak areas
# """
# )

def get_response(user_message: str, agent) -> str:

    # student_tool = create_student_tool(student_id)

#     agent = create_agent(
#         model=llm,
#         tools=[student_tool],
#         system_prompt="""
# You are Student Success AI Coach.

# Use student_data_tool ONLY when user asks about:
# - marks
# - scores
# - attendance
# - exams
# - academic performance

# For general questions, answer normally.
# """
#     )

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": user_message}
        ]
    })

    return response["messages"][-1].content
    