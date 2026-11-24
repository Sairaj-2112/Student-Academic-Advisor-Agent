
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def universal_advisor_agent(profile, academic_results=None, recommendations=None):
    """
    Generates general academic and career guidance
    using the user's complete profile.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "GROQ_API_KEY is missing. Check your .env file."
        }

    academic_results = academic_results or []
    recommendations = recommendations or []

    # Convert the profile into a dictionary if necessary
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()

    prompt = f"""
You are an experienced Universal Academic and Career Advisor.

Your responsibility is to guide people at ANY stage of education or career.

You can advise:
- School students
- 10th and 12th pass students
- Diploma students
- Undergraduate students
- Postgraduate students
- Graduates
- Working professionals
- Career changers

USER PROFILE:
{profile}

AVAILABLE ACADEMIC RESULTS:
{academic_results[:10]}

AVAILABLE COURSE RECOMMENDATIONS:
{recommendations[:10]}

Prepare a personalized report with these sections:

1. PROFILE UNDERSTANDING
Summarize the user's current situation.

2. ACADEMIC GUIDANCE
Suggest relevant education options and learning directions.

3. CAREER POSSIBILITIES
Suggest suitable career paths and explain why they may fit.

4. SKILL GAP ANALYSIS
Identify important skills the user may need to develop.
Do not assume the user lacks a skill unless the profile supports it.

5. LEARNING ROADMAP
Provide practical steps in a sensible sequence.

6. ALTERNATIVE PATHWAYS
Suggest alternatives if the user's preferred path is unsuitable.

7. NEXT ACTIONS
Give three practical actions the user can start taking.

IMPORTANT RULES:
- Personalize advice using the supplied profile.
- Do not restrict guidance to the supplied university catalogue.
- General career and learning suggestions are allowed.
- Never invent university admission requirements, fees, deadlines,
  course prerequisites, scholarships or eligibility rules.
- Clearly label information that requires official verification.
- Do not guarantee admission, employment or career success.
- If information is missing, mention the uncertainty.
- Use simple, supportive and practical language.
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
                        "You are a responsible universal academic "
                        "and career advisor. Give personalized, "
                        "realistic and clearly explained guidance."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2500,
            temperature=0.3
        )

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            return {
                "status": "error",
                "message": "The AI model returned an empty response."
            }

        return {
            "status": "success",
            "advice": answer.strip()
        }

    except Exception as error:
        print(
            f"[Universal Advisor] "
            f"{type(error).__name__}: {error}"
        )

        return {
            "status": "error",
            "message": "AI guidance could not be generated. "
                       "Check your API configuration and try again."
        }
