
import os
from dotenv import load_dotenv
from groq import Groq

from tools.knowledge_context import build_knowledge_context

load_dotenv()


def roadmap_agent(profile, career_target=None, skill_analysis=None):
    """
    Universal Roadmap Agent.

    Creates personalized education and career roadmaps
    using student information, skill analysis and local knowledge.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "GROQ_API_KEY is missing."
        }

    # Convert Pydantic profile into a dictionary.
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()

    if not isinstance(profile, dict):
        profile = {}

    career_target = career_target or profile.get("career_goals", [])

    # Retrieve relevant local Knowledge Base information.
    try:
        knowledge_context = build_knowledge_context(
            profile,
            limit=5
        )
    except Exception as error:
        print(f"[Roadmap Knowledge Retrieval] {error}")

        knowledge_context = (
            "Local Knowledge Base is currently unavailable. "
            "Use general reasoning and clearly identify "
            "information that needs verification."
        )

    # Build a compact student profile.
    useful_fields = [
        "name",
        "age",
        "education_level",
        "current_status",
        "subjects",
        "completed_courses",
        "skills",
        "interests",
        "strengths",
        "career_goals",
        "learning_goals",
        "experience",
        "location",
        "preferred_learning_style",
        "additional_information"
    ]

    compact_profile = {
        key: profile.get(key)
        for key in useful_fields
        if profile.get(key) not in [None, "", [], {}]
    }

    prompt = f"""
You are the Universal Academic and Career Roadmap Agent.

Create a realistic, personalized roadmap using the actual
information provided by the user.

USER PROFILE:
{compact_profile}

TARGET CAREER OR GOAL:
{career_target}

SKILL GAP ANALYSIS:
{str(skill_analysis or "Not provided")[:3000]}

RELEVANT LOCAL KNOWLEDGE:
{knowledge_context}

Create the roadmap using these sections:

1. PROFILE AND GOAL UNDERSTANDING
- Briefly explain the user's current position and goal.
- Identify important missing information.

2. IMMEDIATE ACTIONS
- Give the most important actions for the next 7 days.
- Keep the list practical and manageable.

3. SHORT-TERM ROADMAP
- Give milestones for the first 1-3 months where appropriate.

4. MEDIUM-TERM ROADMAP
- Give milestones for months 4-6 where appropriate.

5. LONG-TERM ROADMAP
- Give milestones for months 7-12 or a more suitable timeline.
- Do not force a 12-month plan if it is unnecessary.

6. FLEXIBLE LEARNING SCHEDULE
- Provide a practical learning structure.
- Never assume a fixed number of available study hours.
- If availability is unknown, use flexible task-based milestones.

7. PROJECTS AND PRACTICAL EXPERIENCE
- Suggest relevant projects, exercises, internships,
  work experience or other activities.
- Match difficulty to the user's actual experience.

8. PORTFOLIO AND ACHIEVEMENTS
- Explain how the user can demonstrate progress.
- Adapt this to their education and career stage.

9. PROGRESS TRACKING
- Give measurable and realistic milestones.
- Explain how to review and update progress.

10. ALTERNATIVE PATHWAYS
- Suggest reasonable alternatives if the user's goals change.

11. KNOWLEDGE BASE INSIGHTS
- Use relevant local courses, skills, careers and pathways.
- Explain how each relevant record supports the roadmap.
- Clearly label sample or unverified information.

IMPORTANT RULES:

- Support school students, 10th/12th pass users, diploma
  students, undergraduate and postgraduate students,
  graduates, working professionals and career changers.
- Never assume the user is a college student.
- Adapt recommendations to the actual profile.
- Never invent qualifications, prerequisites, fees,
  admissions requirements, deadlines or institutional facts.
- Do not treat sample Knowledge Base records as official facts.
- Prefer free learning resources and open-source tools.
- Do not assume unlimited money, time or study availability.
- Do not guarantee admission, employment or career success.
- Avoid unnecessary tasks and unrealistic timelines.
- Clearly state when important information needs verification.
- Use simple, actionable language.
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
                        "You are a universal academic and career "
                        "roadmap planning agent. Provide practical, "
                        "flexible, evidence-aware guidance for users "
                        "at every education and career stage."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2600,
            temperature=0.3
        )

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            return {
                "status": "error",
                "message": "Roadmap Agent returned an empty response."
            }

        return {
            "status": "success",
            "roadmap": answer.strip(),
            "knowledge_context": knowledge_context
        }

    except Exception as error:
        print(
            f"[Roadmap Agent] {type(error).__name__}: {error}"
        )

        return {
            "status": "error",
            "message": "Roadmap generation failed."
        }


# ==========================================
# MODULE TEST
# ==========================================

if __name__ == "__main__":

    test_profile = {
        "name": "Test Student",
        "education_level": "Undergraduate",
        "current_status": "Studying Computer Science",
        "completed_courses": ["Python", "Machine Learning"],
        "skills": ["Python", "Power BI"],
        "interests": ["Artificial Intelligence", "Data Science"],
        "career_goals": ["AI Engineer"],
        "learning_goals": ["Improve machine learning skills"],
        "experience": "Beginner"
    }

    print("\n===== ROADMAP AGENT TEST =====")

    result = roadmap_agent(
        profile=test_profile,
        career_target="AI Engineer",
        skill_analysis=(
            "Needs to strengthen SQL, Deep Learning "
            "and model deployment."
        )
    )

    print("\nSTATUS:", result["status"])

    if result["status"] == "success":
        print("\n===== GENERATED ROADMAP =====")
        print(result["roadmap"])

        print("\n===== KNOWLEDGE BASE CONTEXT =====")
        print(result["knowledge_context"])

        print("\nKnowledge context attached successfully.")

    else:
        print("\nERROR:", result["message"])
