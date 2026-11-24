
import os
import json

from dotenv import load_dotenv
from groq import Groq

from tools.knowledge_context import build_knowledge_context


load_dotenv()


# ==========================================
# CAREER GUIDANCE AGENT
# ==========================================

def career_agent(profile):
    """
    Analyzes a user's profile and suggests suitable career paths.
    Uses Groq LLM and the local Knowledge Base.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "GROQ_API_KEY is missing."
        }

    # Convert Pydantic profile into dictionary
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()

    if not isinstance(profile, dict):
        profile = {}

    # Keep only useful profile fields to reduce token usage
    profile_fields = [
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
        key: profile[key]
        for key in profile_fields
        if key in profile and profile[key] not in [None, "", []]
    }

    profile_text = json.dumps(
        compact_profile,
        ensure_ascii=False,
        default=str
    )

    # ======================================
    # RETRIEVE SMALLER KNOWLEDGE CONTEXT
    # ======================================

    try:
        knowledge_context = build_knowledge_context(
            profile,
            limit=3
        )

        # Prevent excessively large retrieved descriptions
        knowledge_context = knowledge_context[:3500]

    except Exception as error:
        print(f"[Career Agent] Knowledge retrieval error: {error}")

        knowledge_context = (
            "No local Knowledge Base information is available. "
            "Use general career knowledge responsibly."
        )

    # ======================================
    # BUILD SHORTER PROMPT
    # ======================================

    prompt = f"""
Analyze this user's profile and provide personalized career guidance.

USER PROFILE:
{profile_text}

LOCAL KNOWLEDGE:
{knowledge_context}

Cover these areas:

1. Five suitable career options.
2. Why each career may suit the user.
3. Typical responsibilities.
4. Important skills required.
5. Alternative career pathways.
6. One practical first step for each career.

RULES:
- Support all education and career stages.
- Consider the user's actual education, skills, interests and goals.
- Do not assume missing skills are weaknesses.
- Use local records only as supporting information.
- Clearly identify sample records; do not present them as verified facts.
- Do not invent admission requirements, fees or deadlines.
- Do not guarantee employment or salary.
- Use simple, practical language.
- Mention uncertainty when information is insufficient.
- Use general career knowledge when local records are unavailable.
"""

    # ======================================
    # GENERATE CAREER GUIDANCE
    # ======================================

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
                        "You are a professional career advisor. "
                        "Give realistic, personalized and practical "
                        "career guidance."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            return {
                "status": "error",
                "message": "Career Agent returned an empty response."
            }

        return {
            "status": "success",
            "career_guidance": answer.strip(),
            "knowledge_context": knowledge_context
        }

    except Exception as error:
        error_text = str(error)

        print(
            f"[Career Agent] {type(error).__name__}: {error_text}"
        )

        if "rate_limit" in error_text.lower() or "tokens per minute" in error_text.lower():
            message = (
                "Groq token limit reached. Please wait before "
                "trying again, or reduce the request size."
            )
        else:
            message = "Career guidance generation failed."

        return {
            "status": "error",
            "message": message
        }


# ==========================================
# MODULE TEST
# ==========================================

if __name__ == "__main__":

    test_profile = {
        "name": "Sairaj",
        "education_level": "Undergraduate",
        "current_status": "B.Tech Computer Science Student",
        "skills": ["Python", "Power BI"],
        "interests": ["Artificial Intelligence", "Data Science"],
        "career_goals": ["AI Engineer", "Data Scientist"],
        "completed_courses": ["Python", "Machine Learning"]
    }

    print("\n===== CAREER AGENT TEST =====")

    result = career_agent(test_profile)

    if result["status"] == "success":
        print("\n===== CAREER GUIDANCE =====")
        print(result["career_guidance"])

        print("\n===== KNOWLEDGE RETRIEVAL STATUS =====")
        print("Knowledge context attached successfully.")

    else:
        print("\nCAREER AGENT ERROR:")
        print(result["message"])
