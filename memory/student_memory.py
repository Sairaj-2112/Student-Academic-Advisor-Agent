
import json
from pathlib import Path
from datetime import datetime, timezone


MEMORY_FILE = Path("memory/student_data.json")


def _read_memory():
    """Read existing memory and support the old JSON format."""

    if not MEMORY_FILE.exists():
        return {"students": {}}

    try:
        data = json.loads(
            MEMORY_FILE.read_text(encoding="utf-8")
        )

        # Convert old single-student format
        if "students" not in data:
            name = data.get("name", "Student")
            data = {
                "students": {
                    name.strip().lower(): {
                        **data,
                        "history": []
                    }
                }
            }

        return data

    except (json.JSONDecodeError, OSError):
        return {"students": {}}


def _write_memory(data):
    """Save all student memory."""

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    MEMORY_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )


def save_student(
    name,
    completed_subjects,
    interests,
    skills=None,
    career_goals=None,
    learning_goals=None
):
    """Save or update a student's profile."""

    data = _read_memory()

    student_id = name.strip().lower()

    existing = data["students"].get(student_id, {})

    student_data = {
        "name": name,
        "completed_subjects": completed_subjects,
        "interests": interests,
        "skills": skills if skills is not None else existing.get("skills", []),
        "career_goals": career_goals if career_goals is not None else existing.get("career_goals", []),
        "learning_goals": learning_goals if learning_goals is not None else existing.get("learning_goals", []),
        "history": existing.get("history", []),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

    data["students"][student_id] = student_data

    _write_memory(data)

    print("Student memory saved successfully!")

    return student_data


def load_student(name=None):
    """Load a student by name, or the most recently updated student."""

    data = _read_memory()
    students = data["students"]

    if not students:
        return None

    if name:
        return students.get(name.strip().lower())

    # Maintain compatibility with the old load_student() function
    return max(
        students.values(),
        key=lambda student: student.get("last_updated", "")
    )


def load_all_students():
    """Return all saved student profiles."""

    data = _read_memory()
    return list(data["students"].values())


def add_student_history(name, activity_type, details):
    """Save recommendations, feedback and learning progress."""

    data = _read_memory()
    student_id = name.strip().lower()

    if student_id not in data["students"]:
        print("Student profile not found. Save the profile first.")
        return False

    history_record = {
        "activity_type": activity_type,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    data["students"][student_id].setdefault("history", []).append(
        history_record
    )

    data["students"][student_id]["last_updated"] = (
        datetime.now(timezone.utc).isoformat()
    )

    _write_memory(data)

    print("Student history updated successfully!")

    return True


def load_student_history(name):
    """Load the complete history of a student."""

    student = load_student(name)

    if student is None:
        return []

    return student.get("history", [])


if __name__ == "__main__":

    print("===== STUDENT MEMORY SYSTEM =====")

    save_student(
        name="Student 1",
        completed_subjects=["Python", "Machine Learning"],
        interests=["Artificial Intelligence", "Data Science"],
        skills=["Python", "Power BI"],
        career_goals=["AI Engineer"],
        learning_goals=["Deep Learning"]
    )

    student = load_student("Student 1")

    print("\nLoaded Student Profile:")
    print(json.dumps(student, indent=4))

    add_student_history(
        "Student 1",
        "recommendation",
        "AI Engineer and Data Scientist career paths suggested."
    )

    print("\nStudent History:")
    print(json.dumps(load_student_history("Student 1"), indent=4))
