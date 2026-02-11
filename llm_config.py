import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

def get_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    return LLM(
        model="gemini/gemini-flash-lite-latest", 
        api_key=api_key,
        temperature=0.2 # Lower temperature for faster, deterministic answers
    )
