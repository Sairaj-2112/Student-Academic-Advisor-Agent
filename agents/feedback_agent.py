
import os
from groq import Groq
from dotenv import load_dotenv

from tools.student_feedback import load_feedback

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-20b"


def feedback_agent(student_name, original_recommendation):

    # Load the student's feedback
    feedback_history = load_feedback(student_name)

    if not feedback_history:
        return {
            "status": "no_feedback",
            "message": "No feedback found for this student."
        }

    # Select feedback about the relevant recommendation
    relevant_feedback = [
        item for item in feedback_history
        if item.get("decision") in ["reject", "revise"]
    ]

    if not relevant_feedback:
        return {
            "status": "no_revision",
            "message": "No rejected or revision-requested feedback found."
        }

    feedback_text = "\n".join([
        f"Type: {item['recommendation_type']}\n"
        f"Recommendation: {item['recommendation']}\n"
        f"Decision: {item['decision']}\n"
        f"Student comments: {item['comments']}"
        for item in relevant_feedback
    ])

    prompt = f"""
You are a Human-Agent Collaboration Specialist.

Your task is to improve an AI recommendation using student feedback.

ORIGINAL AI RECOMMENDATION:
{original_recommendation}

STUDENT FEEDBACK:
{feedback_text}

INSTRUCTIONS:
1. Understand why the student rejected or wants to revise the recommendation.
2. Respect the student's interests and preferences.
3. Suggest an improved recommendation.
4. Explain what changed and why.
5. Never force the student to accept a recommendation.
6. If information is insufficient, clearly mention what is missing.

Return a clear and structured revised recommendation.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an intelligent academic and career advisor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1500
        )

        revised_advice = response.choices[0].message.content

        return {
            "status": "success",
            "original_recommendation": original_recommendation,
            "student_feedback": relevant_feedback,
            "revised_recommendation": revised_advice
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error)
        }


if __name__ == "__main__":

    result = feedback_agent(
        student_name="Sairaj",
        original_recommendation="AI Engineer"
    )

    print("\n===== AI REVISED RECOMMENDATION =====")
    print(result)
