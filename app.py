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
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="💼", layout="wide")

# Initialize session state
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = CandidateInfo().model_dump()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_complete" not in st.session_state:
    st.session_state.is_complete = False
if "screening_report" not in st.session_state:
    st.session_state.screening_report = None

# Cache the agent
@st.cache_resource
def get_recruiter_agent():
    return create_recruiter_agent()

# Sidebar
st.sidebar.title("📋 Candidate Profile")

with st.sidebar.expander("Existing Candidate?"):
    lookup_email = st.text_input("Enter Email to Load Profile")
    if st.button("Load Data"):
        data, history = db.get_candidate_by_email(lookup_email)
        if data:
            st.session_state.candidate_info = {k: data.get(k) for k in CandidateInfo.__fields__}
            st.session_state.is_complete = bool(data.get("is_complete"))
            st.session_state.screening_report = data.get("screening_report")
            st.success("Profile Loaded!")
            st.rerun()

with st.sidebar.form("candidate_form"):
    full_name = st.text_input("Full Name", value=st.session_state.candidate_info.get("full_name") or "")
    email = st.text_input("Email", value=st.session_state.candidate_info.get("email") or "")
    phone = st.text_input("Phone", value=st.session_state.candidate_info.get("phone") or "")
    exp_val = st.session_state.candidate_info.get("years_of_experience")
    years_of_experience = st.number_input("Years of Experience", min_value=0.0, max_value=50.0, value=float(exp_val) if exp_val else 0.0, step=0.5)
    desired_positions = st.text_input("Positions", value=", ".join(st.session_state.candidate_info.get("desired_positions") or []))
    current_location = st.text_input("Location", value=st.session_state.candidate_info.get("current_location") or "")
    if st.form_submit_button("Update Info"):
        st.session_state.candidate_info.update({
            "full_name": full_name, "email": email, "phone": phone, "years_of_experience": years_of_experience,
            "desired_positions": [p.strip() for p in desired_positions.split(",")] if desired_positions else [],
            "current_location": current_location,
        })
        db.save_candidate(st.session_state.candidate_info, st.session_state.messages, st.session_state.is_complete, st.session_state.screening_report)
        st.rerun()

# Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 Screening Chat")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Type your response...", disabled=st.session_state.is_complete):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("Analyzing..."):
            agent = get_recruiter_agent()
            extraction_task = create_screening_task(agent, user_input, st.session_state.candidate_info, st.session_state.messages[-10:])
            crew = Crew(agents=[agent], tasks=[extraction_task], verbose=False)
            result = crew.kickoff()
            
            response_obj = result.pydantic if hasattr(result, 'pydantic') and result.pydantic else ScreeningResponse(
                updated_info=CandidateInfo(**st.session_state.candidate_info), response_message=str(result), is_complete=False
            )

            current_info = response_obj.updated_info.model_dump()
            
            # Question generation logic
            if current_info.get('tech_stack') and current_info.get('strongest_areas') and not current_info.get('technical_questions'):
                gen_prompt = TECHNICAL_QUESTION_PROMPT.format(
                    tech_stack=current_info['tech_stack'], strongest_areas=current_info['strongest_areas'],
                    desired_positions=current_info['desired_positions'], experience=current_info['years_of_experience']
                )
                gen_task = Task(description=gen_prompt, expected_output="JSON list of strings", agent=agent)
                gen_result = Crew(agents=[agent], tasks=[gen_task]).kickoff()
                try:
                    questions = json.loads(str(gen_result).replace("```json", "").replace("```", "").strip())
                    if isinstance(questions, list):
                        current_info['technical_questions'] = questions
                        response_obj.response_message += f"\n\n**Question 1:** {questions[0]}"
                except: pass

            st.session_state.candidate_info = current_info
            st.session_state.is_complete = response_obj.is_complete
            st.session_state.screening_report = response_obj.report.model_dump() if response_obj.report else None
            st.session_state.messages.append({"role": "assistant", "content": response_obj.response_message})
            db.save_candidate(st.session_state.candidate_info, st.session_state.messages, st.session_state.is_complete, st.session_state.screening_report)
            st.rerun()

with col2:
    st.subheader("📊 Evaluation Report")
    if st.session_state.screening_report:
        report = st.session_state.screening_report
        st.success("✅ Interaction Complete")
        st.markdown(f"### 📝 Summary\n{report['summary']}")
        
        st.markdown("### 🛠 Technical Assessment")
        for idx, item in enumerate(report['technical_assessment']):
            with st.expander(f"Q{idx+1}: {item.get('question', 'N/A')}"):
                st.write(f"**Answer:** {item.get('answer', 'N/A')}")
                st.write(f"**Evaluation:** {item.get('evaluation', 'N/A')}")
                st.write(f"**Score:** {item.get('correctness_score', 0)}/10")
        
        st.markdown(f"### 🧠 Sentiment Analysis\n{report['sentiment_analysis']}")
        st.info(f"**Final Verdict:** {report['final_verdict']}")
    else:
        st.info("The evaluation report will appear here once the screening is complete.")

if not st.session_state.messages:
    welcome = "Welcome! Fill your details in the sidebar and tell me about your tech stack to start."
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    st.rerun()
