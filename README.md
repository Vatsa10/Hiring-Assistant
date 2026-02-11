# TalentScout Hiring Assistant

This project is an **Internship Assignment** for [PGAGI](https://pgagi.in/).

An intelligent, high-speed Hiring Assistant chatbot developed for **TalentScout**, a recruitment agency specializing in technology placements. The assistant streamlines the initial screening process by gathering candidate information, performing technical assessments, and generating detailed evaluation reports.

---

## Key Features

### High-Performance Interaction
- **Ultra-Low Latency**: Powered by **Gemini 2.0 Flash Lite**, achieving response times under **3 seconds**.
- **Efficiency Optimized**: Refined prompts and decoupled task execution for maximum responsiveness.

### Intelligent Screening & Personalization
- **Profile Gathering**: Automatically collects Name, Email, Phone, Experience, Positions, and Location.
- **Personalized Responses**: Adapts conversational tone and depth based on user history and explicit preferences (e.g., "explain simply").
- **Dynamic Technical Assessment**: Generates **5 tailored technical questions** based on the candidate's specific tech stack and strongest areas.

### Advanced Evaluation & Sentiment Analysis
- **Comprehensive Report**: Side-by-side comparison of candidate answers against technical standards.
- **Sentiment Analysis**: Gauges candidate emotions, confidence, and engagement throughout the conversation.
- **Object Scoring**: Accurate, LLM-driven scoring (0-10) for each technical response.
- **Final Verdict**: Provides a clear "Hire/No-Hire" recommendation based on combined performance metrics.

### Modern User Interface
- **Dual-Pane Dashboard**: Interactive screening chat on the left, with a real-time Evaluation Report dashboard on the right.
- **Sidebar Integration**: Easy profile updates and visual progress tracking.
- **SQLite Persistence**: Local storage for candidate profiles, chat history, and evaluation reports.

---

## Project Design Standards

### Technical Proficiency
- **Core Functionalities**: Correct implementation of the hiring assistant including automated information gathering and technical screening.
- **LLM Integration**: Effective use of Gemini 2.0 Flash Lite tailored specifically for recruitment screening and evaluation.
- **Code Quality**: Designed for efficiency, responsiveness, and clear architectural separation of concerns.

### Problem-Solving and Critical Thinking
- **Prompt Engineering**: Designed high-efficiency prompts for accurate data extraction and relevant technical question generation.
- **Context Management**: Implemented creative solutions to maintain conversation flow and state persistence across multiple turns.
- **Data Handling**: Standardized technical assessment with structured reporting and sentiment analysis.

### User Interface and Experience
- **Interactive Experience**: Developed a clean, intuitive, and responsive dual-pane interface tailored for a recruitment context.
- **User Flow**: Optimized for ease of interaction, providing clear feedback on screening progress and final results.

---

## Requirements

- Python 3.10 or higher
- [UV](https://github.com/astral-sh/uv) (Recommended Python package manager)
- **Google AI Studio API Key** (for Gemini Flash Lite)
- OpenRouter API Key (Optional fallback/legacy support)

---

## Setup

1. **Install UV** if you haven't already.

2. **Initialize Environment**:
   ```powershell
   uv venv
   or 
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```powershell
   uv pip install -r requirements.txt
   ```

4. **Configure API Keys**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_google_ai_studio_key_here
   OPENROUTER_API_KEY=your_openrouter_key_here
   ```

---

## Running the Application

Launch the Streamlit interface:
```powershell
uv run streamlit run app.py
```
*Note: The application will automatically open a browser window at `http://localhost:8501`.*

---

## Project Structure

- `app.py`: Main Streamlit application with dual-pane layout.
- `database.py`: SQLite Database Manager for persistent storage.
- `agents.py`: CrewAI agent configuration (Cached for speed).
- `tasks.py`: Structured task definitions for screening and evaluation.
- `models.py`: Pydantic schemas for Candidate Profiles, Screening Responses, and Reports.
- `prompts.py`: Ultra-compressed, high-efficiency prompts for Gemini.
- `llm_config.py`: Configuration for the Gemini 2.0 Flash Lite model.

---

**Developed by Vatsa Joshi**
