# TalentScout Hiring Assistant

An intelligent chatbot for initial candidate screening, built using CrewAI, LangChain, and Streamlit.

## Features

- Candidate Information Gathering: Collects name, email, phone, experience, position, and tech stack.
- Technical Question Generation: Generates tailored technical questions based on the candidate's tech stack.
- Structured Data Extraction: Uses Pydantic to ensure all candidate details are extracted reliably.
- Conversational Interface: Provides a smooth screening flow.

## Requirements

- Python 3.10 or higher
- UV (Python package manager)
- OpenRouter API Key

## Setup

1. Install UV if you haven't already.

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   
   uv pip install -r requirements.txt 
   or
   pip install -r requirements.txt
   ```

3. Configure your environment variables in a `.env` file:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   ```

## Running the Application

Start the Streamlit interface:
```bash
uv run streamlit run app.py
```

## Project Structure

- `app.py`: Main Streamlit application.
- `agents.py`: CrewAI agent definitions.
- `tasks.py`: CrewAI task definitions for screening logic.
- `models.py`: Pydantic models for structured output.
- `prompts.py`: System, State, and Technical prompts.
- `llm_config.py`: OpenRouter LLM configuration.
