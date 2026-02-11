from crewai import Task
from models import ScreeningResponse
from prompts import STATE_PROMPT

def create_screening_task(agent, user_input, current_state_dict, history):
    # Minimal context for chat task
    qs = current_state_dict.get('technical_questions', [])
    ctx = ""
    if qs:
        idx = current_state_dict.get('current_question_index', 0)
        ctx = f"Q_Context: Index={idx}, Total={len(qs)}, List={qs}"

    context = f"""
    History: {history}
    Input: {user_input}
    State: {current_state_dict}
    {ctx}
    {STATE_PROMPT.format(candidate_info=current_state_dict)}
    """

    return Task(
        description=context,
        expected_output="Update state + next message.",
        agent=agent,
        output_pydantic=ScreeningResponse
    )
