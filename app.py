import os
# Disable CrewAI telemetry
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
from crewai import Crew, Task
from agents import create_recruiter_agent
from tasks import create_screening_task
from models import CandidateInfo, ScreeningResponse
from database import DatabaseManager
from prompts import TECHNICAL_QUESTION_PROMPT
import json

# Initialize database
db = DatabaseManager()

# Page config
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="💼")

# Initialize session state
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = CandidateInfo().model_dump()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_complete" not in st.session_state:
    st.session_state.is_complete = False

# Cache the agent to prevent re-creation
@st.cache_resource
def get_recruiter_agent():
    return create_recruiter_agent()

# Sidebar
st.sidebar.title("📋 Candidate Profile")
st.sidebar.markdown("Please provide your contact details below.")

with st.sidebar.expander("Existing Candidate?"):
    lookup_email = st.text_input("Enter Email to Load Profile")
    if st.button("Load Data"):
        data, history = db.get_candidate_by_email(lookup_email)
        if data:
            st.session_state.candidate_info = {
                "full_name": data.get("full_name"),
                "email": data.get("email"),
                "phone": data.get("phone"),
                "years_of_experience": data.get("years_of_experience"),
                "desired_positions": data.get("desired_positions"),
                "current_location": data.get("current_location"),
                "tech_stack": data.get("tech_stack"),
                "strongest_areas": data.get("strongest_areas"),
                "preferences": data.get("preferences"),
                "technical_questions": data.get("technical_questions"),
                "current_question_index": data.get("current_question_index", 0)
            }
            st.session_state.is_complete = bool(data.get("is_complete"))
            st.success("Profile Loaded!")
            st.rerun()
        else:
            st.error("No profile found.")

with st.sidebar.form("candidate_form"):
    full_name = st.text_input("Full Name", value=st.session_state.candidate_info.get("full_name") or "")
    email = st.text_input("Email Address", value=st.session_state.candidate_info.get("email") or "")
    phone = st.text_input("Phone Number", value=st.session_state.candidate_info.get("phone") or "")
    
    exp_val = st.session_state.candidate_info.get("years_of_experience")
    years_of_experience = st.number_input("Years of Experience", min_value=0.0, max_value=50.0, value=float(exp_val) if exp_val else 0.0, step=0.5)
    
    desired_positions = st.text_input("Desired Position(s)", value=", ".join(st.session_state.candidate_info.get("desired_positions") or []))
    current_location = st.text_input("Current Location", value=st.session_state.candidate_info.get("current_location") or "")
    
    submit_button = st.form_submit_button("Update Profile")
    
    if submit_button:
        st.session_state.candidate_info.update({
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "years_of_experience": years_of_experience,
            "desired_positions": [p.strip() for p in desired_positions.split(",")] if desired_positions else [],
            "current_location": current_location,
        })
        db.save_candidate(st.session_state.candidate_info, st.session_state.messages, st.session_state.is_complete)
        st.rerun()

# Display progress
if st.session_state.candidate_info.get("tech_stack"):
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Tech Stack:** {', '.join(st.session_state.candidate_info['tech_stack'])}")
    if st.session_state.candidate_info.get("strongest_areas"):
        st.sidebar.markdown(f"**Top Skills:** {', '.join(st.session_state.candidate_info['strongest_areas'])}")
    
    questions = st.session_state.candidate_info.get("technical_questions", [])
    if questions:
        total_q = len(questions)
        curr_q = st.session_state.candidate_info.get("current_question_index", 0)
        st.sidebar.progress(min(curr_q / total_q, 1.0) if total_q > 0 else 0)
        st.sidebar.caption(f"Question {min(curr_q + 1, total_q)} of {total_q}")

if st.session_state.candidate_info.get("preferences"):
    st.sidebar.markdown("---")
    st.sidebar.caption(f"⚙️ **Preferences:** {st.session_state.candidate_info['preferences']}")

st.title("💼 TalentScout Hiring Assistant")
st.markdown("---")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CORE CHAT LOGIC ---
if user_input := st.chat_input("Type your message...", disabled=st.session_state.is_complete):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Analyzing..."):
        agent = get_recruiter_agent()
        
        # 1. Update Candidate Info State (Extract info)
        # We run a lightweight extraction task first to see if we need to generate questions
        extraction_task = create_screening_task(
            agent, 
            user_input, 
            st.session_state.candidate_info, 
            st.session_state.messages[-10:] # Give context for personalization
        )
        
        # We use a Crew just for the structured extraction/decision logic
        # Ideally, this should be a direct LLM call for speed, but sticking to Crew structure 
        # while optimizing the "heavy" parts.
        crew = Crew(agents=[agent], tasks=[extraction_task], verbose=False) 
        result = crew.kickoff()
        
        if hasattr(result, 'pydantic') and result.pydantic:
            response_obj = result.pydantic
        else:
            # Fallback
            response_obj = ScreeningResponse(
                updated_info=CandidateInfo(**st.session_state.candidate_info),
                response_message=str(result),
                is_complete=False
            )

        # Update local state with what the agent extracted
        current_info = response_obj.updated_info.model_dump()
        st.session_state.candidate_info = current_info

        # 2. SEPARATE QUESTION GENERATION LOGIC
        # Check if we have stack & strengths but NO questions yet.
        # If so, generate them in a focused single-shot way.
        tech_stack = current_info.get('tech_stack')
        strongest = current_info.get('strongest_areas')
        existing_questions = current_info.get('technical_questions')

        if tech_stack and strongest and not existing_questions:
            # Create a dedicated prompt just for generation (fast)
            gen_prompt = TECHNICAL_QUESTION_PROMPT.format(
                tech_stack=tech_stack,
                strongest_areas=strongest,
                desired_positions=current_info.get('desired_positions'),
                experience=current_info.get('years_of_experience')
            )
            
            # Create a quick "generation task"
            gen_task = Task(
                description=gen_prompt,
                expected_output="JSON list of 3-5 technical questions strings",
                agent=agent
            )
            
            gen_crew = Crew(agents=[agent], tasks=[gen_task], verbose=False)
            gen_result = gen_crew.kickoff()
            
            # Parse list from result
            try:
                # Cleanup potential markdown code blocks
                clean_json = str(gen_result).replace("```json", "").replace("```", "").strip()
                questions = json.loads(clean_json)
                if isinstance(questions, list):
                    current_info['technical_questions'] = questions
                    st.session_state.candidate_info['technical_questions'] = questions
                    print(f"[DEBUG] Generated Questions: {questions}")
            except Exception as e:
                print(f"[ERROR] JSON Parse failed: {e}")

        # 3. IF we have questions, ensure we didn't lose the "next question" message
        # The extraction task might have generated a generic "Thanks" message because it didn't
        # know about the questions we JUST generated above.
        
        questions = current_info.get('technical_questions', [])
        idx = current_info.get('current_question_index', 0)
        
        # If the response doesn't actually contain a question, but we are in the screening phase,
        # we might need to force the question into the response.
        if questions and idx < len(questions):
            current_q = questions[idx]
            # Simple heuristic: if the question isn't in the response, append it.
            if current_q not in response_obj.response_message:
                # If we just generated them, the agent might have said "Thanks for sharing your strengths."
                # We append: "Let's start. Question 1: ..."
                if idx == 0 and "Question 1" not in response_obj.response_message:
                     response_obj.response_message += f"\n\nGreat. Let's begin the technical screening.\n\n**Question 1:** {current_q}"
                elif idx > 0:
                     # For subsequent turns, the agent usually handles it, but this is a safety net
                     pass

        # Final State Update
        st.session_state.is_complete = response_obj.is_complete
        st.session_state.messages.append({"role": "assistant", "content": response_obj.response_message})
        db.save_candidate(st.session_state.candidate_info, st.session_state.messages, st.session_state.is_complete)
        
        with st.chat_message("assistant"):
            st.markdown(response_obj.response_message)

if not st.session_state.messages:
    welcome_msg = "Welcome to **TalentScout**! Please fill in your contact details on the left, then introduce yourself!"
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    with st.chat_message("assistant"):
        st.markdown(welcome_msg)
