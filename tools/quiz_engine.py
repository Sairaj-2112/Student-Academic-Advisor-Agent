
import os
import json
import re
import uuid
from collections import defaultdict

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "openai/gpt-oss-20b"
DEFAULT_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 5
API_TIMEOUT = 35

QUIZ_ATTEMPTS = {}


class QuizGenerationError(Exception):
    pass


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json(response_text):

    if not response_text:
        raise QuizGenerationError("Empty response from AI model.")

    response_text = response_text.strip()

    # Remove markdown code fences
    response_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    response_text = re.sub(r"\s*```$", "", response_text)

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Extract JSON object if extra text is present
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start != -1 and end > start:
        try:
            return json.loads(response_text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise QuizGenerationError("AI returned invalid JSON.")


# =========================================================
# QUESTION VALIDATION
# =========================================================

def validate_questions(data, question_count):

    if not isinstance(data, dict):
        raise QuizGenerationError("Invalid quiz response format.")

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise QuizGenerationError("Questions list is missing.")

    if len(questions) != question_count:
        raise QuizGenerationError(
            f"Expected {question_count} questions, received {len(questions)}."
        )

    validated = []
    seen_questions = set()

    for index, question in enumerate(questions):

        if not isinstance(question, dict):
            raise QuizGenerationError("Invalid question structure.")

        question_text = str(question.get("question", "")).strip()
        topic = str(question.get("topic", "General")).strip()
        difficulty = str(question.get("difficulty", "medium")).lower()
        explanation = str(question.get("explanation", "")).strip()

        if len(question_text) < 10:
            raise QuizGenerationError("Question text is too short.")

        normalized = re.sub(r"\W+", "", question_text.lower())

        if normalized in seen_questions:
            raise QuizGenerationError("Duplicate question detected.")

        seen_questions.add(normalized)

        options = question.get("options")

        if not isinstance(options, list) or len(options) != 4:
            raise QuizGenerationError(
                "Every question must have exactly four options."
            )

        clean_options = []
        option_ids = set()
        option_texts = set()

        for option in options:

            if not isinstance(option, dict):
                raise QuizGenerationError("Invalid option structure.")

            option_id = str(option.get("id", "")).strip().upper()
            option_text = str(option.get("text", "")).strip()

            if option_id not in {"A", "B", "C", "D"}:
                raise QuizGenerationError("Option IDs must be A, B, C, D.")

            if not option_text:
                raise QuizGenerationError("An option is empty.")

            if option_id in option_ids:
                raise QuizGenerationError("Duplicate option ID.")

            if option_text.lower() in option_texts:
                raise QuizGenerationError("Duplicate option text.")

            option_ids.add(option_id)
            option_texts.add(option_text.lower())

            clean_options.append({
                "id": option_id,
                "text": option_text
            })

        if option_ids != {"A", "B", "C", "D"}:
            raise QuizGenerationError("All four options are required.")

        correct_answer = str(
            question.get("correct_answer", "")
        ).strip().upper()

        if correct_answer not in {"A", "B", "C", "D"}:
            raise QuizGenerationError("Invalid correct answer.")

        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"

        if not explanation:
            explanation = "Review this concept to strengthen your understanding."

        validated.append({
            "question_id": f"q{index + 1}",
            "question": question_text,
            "topic": topic or "General",
            "difficulty": difficulty,
            "options": clean_options,

            # Never expose these fields in the public quiz response.
            "_correct_answer": correct_answer,
            "_explanation": explanation
        })

    return validated


# =========================================================
# QUIZ GENERATION
# =========================================================

def generate_quiz(
    student_name,
    subject,
    course_description="",
    topics=None,
    question_count=DEFAULT_QUESTION_COUNT
):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise QuizGenerationError(
            "GROQ_API_KEY is missing from the environment."
        )

    student_name = str(student_name or "Student").strip()
    subject = str(subject or "").strip()

    if not subject:
        raise QuizGenerationError("Please provide a subject.")

    question_count = max(
        1,
        min(int(question_count), MAX_QUESTION_COUNT)
    )

    topics = topics or []

    client = Groq(
        api_key=api_key,
        timeout=API_TIMEOUT,
        max_retries=0
    )

    topic_text = ", ".join(map(str, topics[:8])) if topics else "Choose relevant subtopics"

    prompt = f"""
Create exactly {question_count} academic multiple-choice questions.

Subject: {subject}
Course description: {course_description or "General academic subject"}
Topics: {topic_text}
Student: {student_name}

Requirements:
1. Create exactly {question_count} distinct questions.
2. Each question must have exactly four options: A, B, C, D.
3. Only one option must be correct.
4. Use a mixture of easy, medium and hard questions.
5. Test conceptual understanding and practical application.
6. Avoid ambiguous or repeated questions.
7. Provide a short explanation for the correct answer.
8. Do not include answers outside the JSON.

Return ONLY valid JSON in this exact format:

{{
  "questions": [
    {{
      "question": "Question text",
      "topic": "Specific topic",
      "difficulty": "easy",
      "options": [
        {{"id": "A", "text": "Option one"}},
        {{"id": "B", "text": "Option two"}},
        {{"id": "C", "text": "Option three"}},
        {{"id": "D", "text": "Option four"}}
      ],
      "correct_answer": "A",
      "explanation": "Explanation of the correct answer"
    }}
  ]
}}
"""

    last_error = None

    # One normal attempt and one retry if needed
    for attempt in range(2):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an academic assessment generator. "
                            "Return only valid JSON. Generate accurate "
                            "questions and never invent ambiguous answers."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1800
            )

            response_text = response.choices[0].message.content

            data = extract_json(response_text)

            questions = validate_questions(
                data,
                question_count
            )

            attempt_id = str(uuid.uuid4())

            QUIZ_ATTEMPTS[attempt_id] = {
                "student_name": student_name,
                "subject": subject,
                "questions": questions
            }

            # Public response contains no correct answers.
            public_questions = []

            for question in questions:

                public_questions.append({
                    "question_id": question["question_id"],
                    "question": question["question"],
                    "topic": question["topic"],
                    "difficulty": question["difficulty"],
                    "options": question["options"]
                })

            return {
                "status": "success",
                "attempt_id": attempt_id,
                "student_name": student_name,
                "subject": subject,
                "total_questions": len(public_questions),
                "questions": public_questions
            }

        except Exception as error:

            last_error = error

    raise QuizGenerationError(
        f"Could not generate a valid quiz: {last_error}"
    )


# =========================================================
# QUIZ SUBMISSION AND SCORING
# =========================================================

def submit_quiz(attempt_id, answers, student_name=None):

    if attempt_id not in QUIZ_ATTEMPTS:
        raise QuizGenerationError(
            "Quiz attempt not found. Please generate a new quiz."
        )

    if not isinstance(answers, dict):
        raise QuizGenerationError("Answers must be a JSON object.")

    attempt = QUIZ_ATTEMPTS[attempt_id]

    if (
        student_name
        and attempt["student_name"].strip().lower()
        != str(student_name).strip().lower()
    ):
        raise QuizGenerationError("Student name does not match this attempt.")

    questions = attempt["questions"]

    total_questions = len(questions)
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0

    topic_results = defaultdict(
        lambda: {"total": 0, "correct": 0}
    )

    difficulty_results = defaultdict(
        lambda: {"total": 0, "correct": 0}
    )

    answer_review = []

    for question in questions:

        question_id = question["question_id"]
        correct_answer = question["_correct_answer"]

        submitted_answer = answers.get(question_id)

        if submitted_answer is None or str(submitted_answer).strip() == "":
            unanswered_count += 1
            status = "unanswered"
            submitted_answer = None

        else:
            submitted_answer = str(submitted_answer).strip().upper()

            if submitted_answer not in {"A", "B", "C", "D"}:
                raise QuizGenerationError(
                    f"Invalid answer for {question_id}."
                )

            if submitted_answer == correct_answer:
                correct_count += 1
                status = "correct"
            else:
                incorrect_count += 1
                status = "incorrect"

        topic = question["topic"]
        difficulty = question["difficulty"]

        topic_results[topic]["total"] += 1
        difficulty_results[difficulty]["total"] += 1

        if status == "correct":
            topic_results[topic]["correct"] += 1
            difficulty_results[difficulty]["correct"] += 1

        answer_review.append({
            "question_id": question_id,
            "question": question["question"],
            "topic": topic,
            "difficulty": difficulty,
            "submitted_answer": submitted_answer,
            "correct_answer": correct_answer,
            "status": status,
            "explanation": question["_explanation"]
        })

    percentage = round(
        (correct_count / total_questions) * 100,
        2
    ) if total_questions else 0

    if percentage >= 80:
        assessment = "Strong Understanding"
        readiness_signal = "strong"

    elif percentage >= 60:
        assessment = "Developing Understanding"
        readiness_signal = "developing"

    else:
        assessment = "Needs More Practice"
        readiness_signal = "needs_practice"

    topic_analysis = []

    for topic, result in topic_results.items():

        score = round(
            result["correct"] / result["total"] * 100,
            2
        )

        topic_analysis.append({
            "topic": topic,
            "total_questions": result["total"],
            "correct_answers": result["correct"],
            "percentage": score,
            "status": (
                "Strong"
                if score >= 80
                else "Developing"
                if score >= 60
                else "Needs Practice"
            )
        })

    difficulty_analysis = []

    for difficulty, result in difficulty_results.items():

        score = round(
            result["correct"] / result["total"] * 100,
            2
        )

        difficulty_analysis.append({
            "difficulty": difficulty,
            "total_questions": result["total"],
            "correct_answers": result["correct"],
            "percentage": score
        })

    # Prevent accidental reuse of the same attempt.
    del QUIZ_ATTEMPTS[attempt_id]

    return {
        "status": "success",
        "student_name": attempt["student_name"],
        "subject": attempt["subject"],
        "total_questions": total_questions,
        "correct_answers": correct_count,
        "incorrect_answers": incorrect_count,
        "unanswered_questions": unanswered_count,
        "percentage": percentage,
        "assessment": assessment,
        "readiness_signal": readiness_signal,
        "topic_analysis": topic_analysis,
        "difficulty_analysis": difficulty_analysis,
        "answer_review": answer_review,
        "important_note": (
            "This is an indicative knowledge assessment based on "
            "quiz responses. It does not prove course completion, "
            "honesty, or formal prerequisite eligibility."
        )
    }
