
import json
from pathlib import Path

FEEDBACK_FILE = Path("memory/student_feedback.json")


def save_feedback(selected_courses, feedback):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "selected_courses": selected_courses,
        "student_feedback": feedback
    }

    FEEDBACK_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )

    print("\nStudent feedback saved successfully!")
    print(json.dumps(data, indent=4))


if __name__ == "__main__":
    print("===== HUMAN-AGENT COLLABORATION =====")

    selected = input(
        "Enter course departments you want to explore (e.g. ABE, BADM): "
    )

    feedback = input(
        "Was the recommendation useful? Why or why not? "
    )

    selected_courses = [
        item.strip().upper()
        for item in selected.split(",")
        if item.strip()
    ]

    save_feedback(selected_courses, feedback)
