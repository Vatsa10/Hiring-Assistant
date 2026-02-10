import streamlit as st
from crewai import Crew
from agents import create_recruiter_agent
from tasks import create_screening_task
from models import CandidateInfo, ScreeningResponse
import os

# Page config
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="💼")

# Initialize session state
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = CandidateInfo().dict()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_complete" not in st.session_state:
    st.session_state.is_complete = False

# Sidebar for Candidate Information
st.sidebar.title("📋 Candidate Profile")
st.sidebar.markdown("Please provide your details below to proceed with the screening.")

# Form-like inputs in sidebar
with st.sidebar.form("candidate_form"):
    full_name = st.text_input("Full Name", value=st.session_state.candidate_info.get("full_name") or "")
    email = st.text_input("Email Address", value=st.session_state.candidate_info.get("email") or "")
    phone = st.text_input("Phone Number", value=st.session_state.candidate_info.get("phone") or "")
    
    # Handle numbers carefully
    exp_val = st.session_state.candidate_info.get("years_of_experience")
    years_of_experience = st.number_input("Years of Experience", min_value=0.0, max_value=50.0, value=float(exp_val) if exp_val else 0.0, step=0.5)
    
    desired_positions = st.text_input("Desired Position(s) (comma separated)", value=", ".join(st.session_state.candidate_info.get("desired_positions") or []))
    current_location = st.text_input("Current Location", value=st.session_state.candidate_info.get("current_location") or "")
    tech_stack = st.text_input("Tech Stack (comma separated)", value=", ".join(st.session_state.candidate_info.get("tech_stack") or []))
    
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
            "tech_stack": [t.strip() for t in tech_stack.split(",")] if tech_stack else [],
        })
        st.success("Profile updated!")
        st.rerun()

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

    # Exit check
    if any(keyword in user_input.lower() for keyword in ["exit", "quit", "goodbye"]):
        st.session_state.is_complete = True
        response = "Thank you for your time. Goodbye!"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
        st.rerun()

    # Process with CrewAI
    with st.spinner("Analyzing response..."):
        agent = create_recruiter_agent()
        task = create_screening_task(
            agent, 
            user_input, 
            st.session_state.candidate_info, 
            st.session_state.messages[-5:] # last 5 messages for context
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
        st.session_state.candidate_info = response_obj.updated_info.model_dump()
        st.session_state.is_complete = response_obj.is_complete

        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response_obj.response_message})
        with st.chat_message("assistant"):
            st.markdown(response_obj.response_message)
            
            # If technical questions were generated, show them
            if response_obj.questions_generated:
                st.markdown("### Technical Screening Questions")
                for i, q in enumerate(response_obj.questions_generated):
                    st.write(f"{i+1}. {q}")
                st.session_state.is_complete = True

# Welcome message
if not st.session_state.messages:
    welcome_msg = """Hello! I'm the TalentScout Hiring Assistant. 👋
    
I've been designed to help you through our initial screening process. To get started, please fill out your basic details in the **sidebar to the left**. 

Once you've updated your profile, we can move forward with your assessment!"""
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    with st.chat_message("assistant"):
        st.markdown(welcome_msg)
