from llm.model import get_llm
from utils.prompts import SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent
from utils.student_tool import get_student_context
from langchain.tools import tool


llm = get_llm()
def create_student_tool(student_id):

    @tool
    def student_data_tool(query: str) -> str:
        """
        Use when user asks about marks, attendance,
        exams, scores, grades, or academic progress.
        """
        data = get_student_context(student_id)
        return str(data)

    return student_data_tool

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

def get_response(user_message: str, student_id: str):

    student_tool = create_student_tool(student_id)

    agent = create_agent(
        model=llm,
        tools=[student_tool],
        system_prompt="""
You are Student Success AI Coach.

Use student_data_tool ONLY when user asks about:
- marks
- scores
- attendance
- exams
- academic performance

For general questions, answer normally.
"""
    )

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": user_message}
        ]
    })

    return response["messages"][-1].content
    