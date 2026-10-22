
import json
from pathlib import Path

MEMORY_FILE = Path("memory/student_data.json")


def save_student(name, completed_subjects, interests):
    """Save student details for future recommendations."""

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    student_data = {
        "name": name,
        "completed_subjects": completed_subjects,
        "interests": interests
    }

    MEMORY_FILE.write_text(
        json.dumps(student_data, indent=4),
        encoding="utf-8"
    )

    print("Student memory saved successfully!")


def load_student():
    """Load previously saved student details."""

    if not MEMORY_FILE.exists():
        return None

    return json.loads(
        MEMORY_FILE.read_text(encoding="utf-8")
    )


if __name__ == "__main__":
    save_student(
        name="Student 1",
        completed_subjects=["Python", "Machine Learning"],
        interests=["artificial intelligence", "machine learning"]
    )

    student = load_student()
    print("\nLoaded Student Memory:")
    print(json.dumps(student, indent=4))
