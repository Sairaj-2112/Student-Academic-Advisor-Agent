
import json
from pathlib import Path
from datetime import datetime, timezone

FEEDBACK_FILE = Path("memory/student_feedback.json")


def save_feedback(
    student_name,
    recommendation_type,
    recommendation,
    decision,
    comments=""
):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load existing feedback
    if FEEDBACK_FILE.exists():
        try:
            existing_data = json.loads(
                FEEDBACK_FILE.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            existing_data = {}
    else:
        existing_data = {}

    # Preserve old feedback and initialize history
    if "feedback_history" not in existing_data:
        existing_data["feedback_history"] = []

    # Create feedback record
    feedback_record = {
        "student_name": student_name.strip(),
        "recommendation_type": recommendation_type.strip(),
        "recommendation": recommendation.strip(),
        "decision": decision.strip().lower(),
        "comments": comments.strip(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    existing_data["feedback_history"].append(feedback_record)

    # Save JSON
    FEEDBACK_FILE.write_text(
        json.dumps(existing_data, indent=4),
        encoding="utf-8"
    )

    print("\nHuman feedback saved successfully!")

    return feedback_record


def load_feedback(student_name=None):

    if not FEEDBACK_FILE.exists():
        return []

    try:
        data = json.loads(
            FEEDBACK_FILE.read_text(encoding="utf-8")
        )

        feedback_history = data.get("feedback_history", [])

        # Case-insensitive student search
        if student_name:
            feedback_history = [
                item for item in feedback_history
                if item.get("student_name", "").strip().lower()
                == student_name.strip().lower()
            ]

        return feedback_history

    except (json.JSONDecodeError, OSError) as error:
        print(f"Error loading feedback: {error}")
        return []


if __name__ == "__main__":

    print("\n===== HUMAN-AGENT COLLABORATION =====")

    student_name = input("Enter student name: ")

    recommendation_type = input(
        "Recommendation type (Career/Course/Skill): "
    )

    recommendation = input(
        "Enter the AI recommendation: "
    )

    decision = input(
        "Accept / Reject / Revise: "
    ).strip().lower()

    if decision not in ["accept", "reject", "revise"]:
        print("Invalid decision. Please enter Accept, Reject or Revise.")

    else:
        comments = input("Enter your feedback or reason: ")

        save_feedback(
            student_name=student_name,
            recommendation_type=recommendation_type,
            recommendation=recommendation,
            decision=decision,
            comments=comments
        )

        print("\nYour feedback has been recorded.")
