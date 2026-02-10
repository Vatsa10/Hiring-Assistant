from crewai import Agent
from llm_config import get_llm
from prompts import SYSTEM_PROMPT

def create_recruiter_agent():
    return Agent(
        role="TalentScout Recruiter",
        goal="Gather candidate information and provide technical questions for screening.",
        backstory=SYSTEM_PROMPT,
        llm=get_llm(),
        allow_delegation=False,
        verbose=True
    )
