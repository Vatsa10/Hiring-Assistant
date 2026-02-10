from pydantic import BaseModel, Field
from typing import List, Optional

class CandidateInfo(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    years_of_experience: Optional[float] = Field(None, description="Total years of professional experience")
    desired_positions: Optional[List[str]] = Field(None, description="List of positions the candidate is interested in")
    current_location: Optional[str] = Field(None, description="City and Country")
    tech_stack: Optional[List[str]] = Field(None, description="List of technologies, frameworks, and tools")
    technical_questions: Optional[List[str]] = Field(None, description="The full list of generated technical questions")
    current_question_index: int = Field(0, description="Index of the question currently being asked (0-based)")

class ScreeningResponse(BaseModel):
    updated_info: CandidateInfo = Field(..., description="Extract any new information found in the user response, including updating the current_question_index")
    response_message: str = Field(..., description="The conversational response to the candidate")
    questions_generated: Optional[List[str]] = Field(None, description="Technical questions generated if tech stack is available")
    is_complete: bool = Field(False, description="Set to true if all info is gathered and all questions are answered")
