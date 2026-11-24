
import os
from dotenv import load_dotenv
from groq import Groq

from tools.knowledge_context import build_knowledge_context

load_dotenv()


def skill_gap_agent(profile, career_target=None):
    """Analyzes existing skills against career goals using local knowledge."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "GROQ_API_KEY is missing."
        }

    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()

    if not isinstance(profile, dict):
        profile = {}

    career_target = career_target or profile.get(
        "career_goals", []
    )

    # Retrieve relevant information from the local Knowledge Base.
    try:
        knowledge_context = build_knowledge_context(
            profile,
            limit=8
        )
    except Exception as error:
        print(
            f"[Skill Gap Agent] Knowledge retrieval error: {error}"
        )
        knowledge_context = (
            "Knowledge Base information is currently unavailable. "
            "Use general reasoning without inventing facts."
        )

    prompt = f"""
You are a professional Skill Gap Analysis Agent.

USER PROFILE:
{profile}

TARGET CAREER:
{career_target}

LOCAL KNOWLEDGE BASE INFORMATION:
{knowledge_context}

Prepare a personalized skill analysis:

1. EXISTING SKILLS
List skills explicitly mentioned by the user.

2. IMPORTANT CAREER SKILLS
List important skills commonly required for the target career.

3. POTENTIAL SKILL GAPS
Compare existing skills with important career skills.
Do not assume a skill is missing simply because it was not mentioned.
Label unconfirmed skills as "Not yet specified".

4. LEARNING PRIORITIES
Suggest beginner, intermediate and advanced skills.

5. KNOWLEDGE BASE INSIGHTS
Use relevant courses, skills, prerequisites and pathways
from the local Knowledge Base where available.
Explain how they can help the user.
Clearly identify sample records.

6. FREE LEARNING RESOURCES
Suggest genuinely free resources such as official documentation,
free tutorials and open-source learning materials.
Do not claim paid courses are free.

7. PRACTICAL PROJECTS
Suggest three projects to develop relevant skills.

8. PROGRESS CHECKLIST
Give measurable milestones.

RULES:
- Adapt to the user's education and experience level.
- Do not exaggerate the user's abilities.
- Do not guarantee employment.
- Do not invent prerequisites or institutional requirements.
- Treat sample Knowledge Base records as supporting information,
  not verified facts.
- If information is unavailable, say so.
- Do not assume weekly study hours.
- Use clear, practical language.
"""

    try:
        client = Groq(
            api_key=api_key,
            timeout=60
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a specialized skill gap analysis agent. "
                        "Give realistic, personalized and actionable "
                        "learning guidance using the supplied context."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2200,
            temperature=0.3
        )

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            return {
                "status": "error",
                "message": "Skill Gap Agent returned an empty response."
            }

        return {
            "status": "success",
            "skill_analysis": answer.strip(),
            "knowledge_context": knowledge_context
        }

    except Exception as error:
        print(
            f"[Skill Gap Agent] {type(error).__name__}: {error}"
        )

        return {
            "status": "error",
            "message": "Skill gap analysis failed."
        }


if __name__ == "__main__":

    test_profile = {
        "name": "Sairaj",
        "education_level": "Undergraduate",
        "current_status": "B.Tech Computer Science Student",
        "skills": ["Python", "Power BI"],
        "interests": ["Artificial Intelligence", "Data Science"],
        "career_goals": ["AI Engineer", "Data Scientist"],
        "completed_courses": ["Machine Learning"],
        "experience": "Academic projects and internships"
    }

    print("\n===== SKILL GAP AGENT TEST =====")

    result = skill_gap_agent(test_profile)

    if result["status"] == "success":
        print(result["skill_analysis"])
        print("\nKnowledge context attached successfully.")
    else:
        print(result["message"])
