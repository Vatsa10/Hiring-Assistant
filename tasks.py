from crewai import Task
from models import ScreeningResponse
from prompts import STATE_PROMPT, TECHNICAL_QUESTION_PROMPT

def create_screening_task(agent, user_input, current_state_dict, history):
    # Determine missing fields for the prompt
    missing_fields = [k for k, v in current_state_dict.items() if v is None or v == []]
    
    # Context prompt includes history and current state
    context = f"""
    Conversation History:
    {history}
    
    Current User Input: {user_input}
    
    {STATE_PROMPT.format(candidate_info=current_state_dict, missing_info=missing_fields)}
    """
    
    # If tech stack is available and questions are missing, add question generation instruction
    if current_state_dict.get('tech_stack') and not current_state_dict.get('technical_questions'):
        context += f"\n\n{TECHNICAL_QUESTION_PROMPT.format(tech_stack=current_state_dict['tech_stack'], experience=current_state_dict.get('years_of_experience', 'not specified'))}"

    return Task(
        description=context,
        expected_output="An updated Screening Response object with the candidate's info and the next message to show them.",
        agent=agent,
        output_pydantic=ScreeningResponse
    )
