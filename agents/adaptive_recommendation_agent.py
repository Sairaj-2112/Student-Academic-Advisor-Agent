
import os
import json

from dotenv import load_dotenv
from groq import Groq

from tools.learning_progress import get_learning_progress
from tools.student_feedback import load_feedback


# ==========================================
# CONFIGURATION
# ==========================================

load_dotenv()

MODEL_NAME = "openai/gpt-oss-20b"


# ==========================================
# ADAPTIVE RECOMMENDATION AGENT
# ==========================================

def adaptive_recommendation_agent(student_name, profile=None):
    """
    Generate adaptive learning recommendations using:
    1. Student profile and career goals
    2. Current learning progress
    3. Previous student feedback
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Check your .env file."
        )

    client = Groq(api_key=api_key)

    # --------------------------------------
    # LOAD STUDENT LEARNING PROGRESS
    # --------------------------------------

    progress_items = get_learning_progress(student_name)

    # --------------------------------------
    # LOAD STUDENT FEEDBACK
    # --------------------------------------

    feedback_history = load_feedback(student_name)

    # --------------------------------------
    # PREPARE STUDENT PROFILE
    # --------------------------------------

    if profile is None:
        profile_data = {}

    elif hasattr(profile, "model_dump"):
        profile_data = profile.model_dump()

    elif isinstance(profile, dict):
        profile_data = profile

    else:
        profile_data = {"profile_information": str(profile)}

    # --------------------------------------
    # PREPARE INPUT DATA
    # --------------------------------------

    student_data = {
        "student_name": student_name,
        "profile": profile_data,
        "learning_progress": progress_items,
        "previous_feedback": feedback_history
    }

    student_json = json.dumps(
        student_data,
        indent=4,
        ensure_ascii=False,
        default=str
    )

    # --------------------------------------
    # ADAPTIVE AI PROMPT
    # --------------------------------------

    prompt = f"""
You are an intelligent Adaptive Academic and Career
Recommendation Agent.

Your task is to analyse the student's current situation
and generate personalized, updated recommendations.

STUDENT INFORMATION:

{student_json}

INSTRUCTIONS:

1. Understand the student's education level, interests,
   skills and career goals.

2. Analyse completed, in-progress and not-started
   learning items.

3. Consider previous feedback:
   - Accepted recommendations
   - Rejected recommendations
   - Recommendations the student wants revised

4. Identify missing skills and learning priorities.

5. Recommend the next 5 suitable learning actions.

6. Explain why each recommendation is suitable.

7. Avoid recommending something the student has
   already completed unless revision is useful.

8. Do not assume that an item is completed merely
   because it appears in the student's profile.

9. If progress or feedback information is missing,
   clearly mention that it was not provided.

10. Adapt recommendations to the student's actual
    career goals and education level.

11. Do not invent university admission rules, fees,
    deadlines or eligibility requirements.

RESPONSE FORMAT:

A. STUDENT PROGRESS ANALYSIS

B. SKILL GAPS IDENTIFIED

C. UPDATED TOP 5 RECOMMENDATIONS
For each recommendation include:
- Recommendation name
- Type (Course / Skill / Project)
- Priority (High / Medium / Low)
- Reason
- Expected learning outcome

D. NEXT LEARNING ACTION

E. HOW PREVIOUS FEEDBACK INFLUENCED THE RESULTS

F. SUGGESTED NEXT STEPS

Give practical, clear and student-friendly guidance.
"""

    # --------------------------------------
    # CALL GROQ LLM
    # --------------------------------------

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful, personalized and "
                    "adaptive academic and career advisor."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=2500
    )

    recommendation = response.choices[0].message.content

    # --------------------------------------
    # RETURN RESULTS
    # --------------------------------------

    return {
        "student_name": student_name,
        "progress_items_analysed": len(progress_items),
        "feedback_entries_analysed": len(feedback_history),
        "adaptive_recommendations": recommendation
    }


# ==========================================
# MODULE TEST
# ==========================================

if __name__ == "__main__":

    print("\n===== ADAPTIVE RECOMMENDATION TEST =====")

    result = adaptive_recommendation_agent(
        student_name="sairaj",
        profile={
            "education_level": "Undergraduate",
            "career_goals": ["AI Engineer", "Data Scientist"],
            "skills": ["Python", "Power BI"],
            "interests": ["Artificial Intelligence", "Data Science"]
        }
    )

    print("\n===== ADAPTIVE RECOMMENDATIONS =====")

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )