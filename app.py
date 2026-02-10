import os
# Disable CrewAI telemetry to avoid signal threading issues in Streamlit
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import streamlit as st
from crewai import Crew
from agents import create_recruiter_agent
from tasks import create_screening_task
from models import CandidateInfo, ScreeningResponse
from database import DatabaseManager

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

# Sidebar for Candidate Information
st.sidebar.title("📋 Candidate Profile")
st.sidebar.markdown("Please provide your contact details below.")

# Load from DB functionality
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
                "technical_questions": data.get("technical_questions"),
                "current_question_index": data.get("current_question_index", 0)
            }
            # Only update profile details, do not restore conversation history
            st.session_state.is_complete = bool(data.get("is_complete"))
            st.success("Profile Loaded (excluding chat history)!")
            st.rerun()
        else:
            st.error("No profile found for this email.")

# Form-like inputs in sidebar (Tech Stack removed)
with st.sidebar.form("candidate_form"):
    full_name = st.text_input("Full Name", value=st.session_state.candidate_info.get("full_name") or "")
    email = st.text_input("Email Address", value=st.session_state.candidate_info.get("email") or "")
    phone = st.text_input("Phone Number", value=st.session_state.candidate_info.get("phone") or "")
    
    # Handle numbers carefully
    exp_val = st.session_state.candidate_info.get("years_of_experience")
    years_of_experience = st.number_input("Years of Experience", min_value=0.0, max_value=50.0, value=float(exp_val) if exp_val else 0.0, step=0.5)
    
    desired_positions = st.text_input("Desired Position(s) (comma separated)", value=", ".join(st.session_state.candidate_info.get("desired_positions") or []))
    current_location = st.text_input("Current Location", value=st.session_state.candidate_info.get("current_location") or "")
    
    submit_button = st.form_submit_button("Update Profile")
    
    if submit_button:
        # Update session state with sidebar info
        st.session_state.candidate_info.update({
            "full_name": full_name if full_name else None,
            "email": email if email else None,
            "phone": phone if phone else None,
            "years_of_experience": years_of_experience,
            "desired_positions": [p.strip() for p in desired_positions.split(",")] if desired_positions else [],
            "current_location": current_location if current_location else None,
        })
        # Persist immediately to DB
        db.save_candidate(st.session_state.candidate_info, st.session_state.messages, st.session_state.is_complete)
        
        # Terminal notification
        print(f"\n[INFO] Profile Updated for: {st.session_state.candidate_info.get('full_name')} ({st.session_state.candidate_info.get('email')})")
        
        # Frontend notification
        st.toast("✅ Profile Updated Successfully!")
        st.success("Profile updated and saved!")
        st.rerun()

# Display current progress in sidebar
if st.session_state.candidate_info.get("tech_stack"):
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Tech Stack:** {', '.join(st.session_state.candidate_info['tech_stack'])}")
    if st.session_state.candidate_info.get("technical_questions"):
        total_q = len(st.session_state.candidate_info["technical_questions"])
        curr_q = st.session_state.candidate_info.get("current_question_index", 0)
        st.sidebar.progress(min(curr_q / total_q, 1.0) if total_q > 0 else 0)
        st.sidebar.caption(f"Question {min(curr_q + 1, total_q)} of {total_q}")

st.sidebar.markdown("---")
st.sidebar.caption("🔒 **Data Privacy Notice**")
st.sidebar.caption("Your information is processed for recruitment purposes only and is stored securely in our local database.")

st.title("💼 TalentScout Hiring Assistant")
st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if user_input := st.chat_input("Type your message here...", disabled=st.session_state.is_complete):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process with CrewAI
    with st.spinner("Analyzing response..."):
        agent = create_recruiter_agent()
        task = create_screening_task(
            agent, 
            user_input, 
            st.session_state.candidate_info, 
            st.session_state.messages[-15:] # last 15 messages for better context
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        if hasattr(result, 'pydantic'):
            response_obj = result.pydantic
        else:
            response_obj = ScreeningResponse(
                updated_info=CandidateInfo(**st.session_state.candidate_info),
                response_message=str(result),
                is_complete=False
            )

        # Update state from LLM extraction (sync with sidebar)
        new_info = response_obj.updated_info.model_dump()
        
        # Persistence Logic for questions:
        # If the LLM generated new questions, store them.
        if response_obj.questions_generated:
            new_info['technical_questions'] = response_obj.questions_generated
        else:
            # Preserve existing questions
            new_info['technical_questions'] = st.session_state.candidate_info.get('technical_questions', [])

        st.session_state.candidate_info = new_info
        st.session_state.is_complete = response_obj.is_complete

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response_obj.response_message})
        
        # Persist to DB
        db.save_candidate(st.session_state.candidate_info, st.session_state.messages, st.session_state.is_complete)
        
        with st.chat_message("assistant"):
            st.markdown(response_obj.response_message)

# Welcome message
if not st.session_state.messages:
    welcome_msg = """Welcome to **TalentScout**! 🚀
    
I'm thrilled to assist you with your application journey today. I'm here to learn more about your unique skills and see how they align with our world-class tech teams.

To get us started on the right foot, could you please take a moment to share your basic contact details in the **profile section on the left**? 

Once you've done that, I'm eager to dive into your technical world and hear all about the amazing tools and frameworks you've mastered!"""
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    with st.chat_message("assistant"):
        st.markdown(welcome_msg)
