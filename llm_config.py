import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm():
    return ChatOpenAI(
        model="openai/gpt-oss-20b:free",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/Vatsa10/Hiring-Assistant", # Optional but good practice
            "X-Title": "TalentScout Hiring Assistant",
        }
    )
