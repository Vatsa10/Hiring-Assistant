import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

def get_llm():
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # LiteLLM (used by CrewAI) uses this env var for OpenRouter
    os.environ["OPENROUTER_API_KEY"] = api_key
    
    # IMPORTANT: We MUST NOT have OPENAI_API_KEY set to an OpenRouter key,
    # as LiteLLM might try to use it with the default OpenAI base URL.
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    return LLM(
        model="openrouter/openai/gpt-oss-20b:free",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        # Enable reasoning as requested by the user
        # Note: 'reasoning' parameter in CrewAI LLM is passed to LiteLLM
        # which supports it for specific OpenRouter models.
        extra_headers={
            "HTTP-Referer": "https://github.com/Vatsa10/Hiring-Assistant",
            "X-Title": "TalentScout Hiring Assistant",
        }
    )
