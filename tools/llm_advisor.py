
import os
import html
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def explain_recommendations(student, courses):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "GROQ_API_KEY is missing. Check your .env file."

    if not courses:
        return "No matching courses were found for these interests."

    # Prepare real course information from the catalogue
    course_details = []

    for course in courses[:5]:
        title = html.unescape(str(course.get("title", "Unknown")))
        code = course.get("course_code", "Not available")
        department = course.get("subject", "Not available")
        credits = course.get("credits", "Not available")
        description = html.unescape(
            str(course.get("description", "No description available"))
        )

        course_details.append(
            f"Title: {title}\n"
            f"Course code: {code}\n"
            f"Department: {department}\n"
            f"Credits: {credits}\n"
            f"Description: {description[:500]}"
        )

    course_text = "\n\n".join(course_details)

    prompt = f"""
You are a careful Student Academic Advisor.

Student interests: {student.get('interests', [])}
Completed subjects: {student.get('completed_subjects', [])}

Available courses from the catalogue:
{course_text}

Instructions:
1. Select the most relevant courses based on the actual titles and descriptions.
2. Explain briefly why each selected course matches the student's interests.
3. Suggest what prerequisites the student should verify.
4. Use only information provided in the catalogue.
5. Never invent course titles, codes, credits, descriptions, or prerequisites.
6. Do not claim the student is eligible for a course.
7. If a course has a vague title or description, clearly say its relevance is uncertain.
8. Give concise, clear advice using simple language.
9. Label your recommendations as preliminary suggestions.
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
                        "You are an academic advisor. "
                        "Give evidence-based advice using only the supplied data. "
                        "Provide a visible final answer."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.2
        )

        message = response.choices[0].message
        answer = message.content

        if answer and answer.strip():
            return answer.strip()

        return (
            "The AI model returned no visible advice. "
            "Please try again."
        )

    except Exception as error:
        print(
            f"[LLM Advisor] Error: "
            f"{type(error).__name__}: {error}"
        )

        return (
            "AI advice could not be generated. "
            "Please check the API configuration and try again."
        )


if __name__ == "__main__":
    from memory.student_memory import load_student
    from agents.recommendation_agent import recommendation_agent

    student = load_student()

    if student:
        courses = recommendation_agent(student["interests"])
        advice = explain_recommendations(student, courses)

        print("\n===== AI ACADEMIC ADVICE =====\n")
        print(advice)
    else:
        print("No saved student profile found.")
