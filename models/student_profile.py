
from pydantic import BaseModel, Field
from typing import Optional


class StudentProfile(BaseModel):
    """
    Universal profile for academic and career guidance.
    Suitable for students, graduates and working professionals.
    """

    name: str = "User"

    age: Optional[int] = None

    education_level: str = "Not specified"

    current_status: str = "Not specified"

    subjects: list[str] = Field(default_factory=list)

    completed_courses: list[str] = Field(default_factory=list)

    skills: list[str] = Field(default_factory=list)

    interests: list[str] = Field(default_factory=list)

    strengths: list[str] = Field(default_factory=list)

    career_goals: list[str] = Field(default_factory=list)

    learning_goals: list[str] = Field(default_factory=list)

    experience: str = ""

    location: str = ""

    preferred_learning_style: str = "Not specified"

    additional_information: str = ""
