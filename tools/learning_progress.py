
import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


PROGRESS_FILE = Path("memory/learning_progress.json")

VALID_STATUSES = [
    "not_started",
    "in_progress",
    "completed"
]

VALID_TYPES = [
    "course",
    "skill",
    "project"
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load_data():
    """Load saved student learning and assessment data."""
    if not PROGRESS_FILE.exists():
        return {"students": {}}

    try:
        data = json.loads(
            PROGRESS_FILE.read_text(encoding="utf-8")
        )

        if not isinstance(data, dict):
            return {"students": {}}

        if not isinstance(data.get("students"), dict):
            data["students"] = {}

        return data

    except (json.JSONDecodeError, OSError):
        raise RuntimeError(
            "Learning progress file could not be read. "
            "Please check memory/learning_progress.json."
        )


def _save_data(data):
    """Save student data safely using a temporary file."""
    PROGRESS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = PROGRESS_FILE.with_suffix(".tmp")

    temporary_file.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    temporary_file.replace(PROGRESS_FILE)


def _student_record(data, student_name):
    """Get or create a student's record."""
    name = str(student_name or "").strip()

    if not name:
        raise ValueError("Student name is required.")

    student_id = name.lower()

    if student_id not in data["students"]:
        data["students"][student_id] = {
            "student_name": name,
            "items": [],
            "assessments": []
        }

    student = data["students"][student_id]

    student.setdefault("items", [])
    student.setdefault("assessments", [])

    return student


# =========================================================
# LEARNING ITEMS
# =========================================================

def add_learning_item(
    student_name,
    item_name,
    item_type,
    notes=""
):
    """Add a course, skill or project."""

    item_type = str(item_type or "").strip().lower()
    item_name = str(item_name or "").strip()

    if item_type not in VALID_TYPES:
        raise ValueError(
            "Type must be course, skill or project."
        )

    if not item_name:
        raise ValueError("Item name is required.")

    data = _load_data()
    student = _student_record(data, student_name)

    now = _now()

    item = {
        "id": str(uuid4()),
        "item_name": item_name,
        "item_type": item_type,
        "status": "not_started",
        "notes": str(notes or "").strip(),
        "created_at": now,
        "updated_at": now
    }

    student["items"].append(item)

    _save_data(data)

    return item


def update_learning_status(
    student_name,
    item_id,
    new_status,
    notes=None
):
    """Update the status of a learning item."""

    new_status = str(new_status or "").strip().lower()

    if new_status not in VALID_STATUSES:
        raise ValueError(
            "Status must be not_started, in_progress or completed."
        )

    data = _load_data()
    student = data["students"].get(
        str(student_name or "").strip().lower()
    )

    if not student:
        return False

    for item in student.get("items", []):
        if item["id"] == item_id:

            item["status"] = new_status

            if notes is not None:
                item["notes"] = str(notes).strip()

            item["updated_at"] = _now()

            _save_data(data)
            return True

    return False


def get_learning_progress(student_name):
    """Get all learning items for a student."""

    data = _load_data()

    student = data["students"].get(
        str(student_name or "").strip().lower()
    )

    if not student:
        return []

    return student.get("items", [])


def get_progress_summary(student_name):
    """Calculate learning completion statistics."""

    items = get_learning_progress(student_name)

    total = len(items)

    completed = sum(
        1 for item in items
        if item.get("status") == "completed"
    )

    in_progress = sum(
        1 for item in items
        if item.get("status") == "in_progress"
    )

    not_started = sum(
        1 for item in items
        if item.get("status") == "not_started"
    )

    percentage = (
        round(completed / total * 100, 2)
        if total else 0
    )

    return {
        "student_name": student_name,
        "total_items": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "completion_percentage": percentage
    }


# =========================================================
# PERSISTENT QUIZ AND ASSESSMENT HISTORY
# =========================================================

def record_assessment(
    student_name,
    subject,
    quiz_result,
    assessment_type="quiz",
    metadata=None
):
    """
    Save a completed quiz or prerequisite assessment.

    Stores scores, answer review, topic analysis,
    and assessment timestamps.
    """

    if not isinstance(quiz_result, dict):
        raise ValueError("Invalid quiz result.")

    percentage = quiz_result.get("percentage")

    if percentage is None:
        raise ValueError("Assessment percentage is missing.")

    percentage = float(percentage)

    if not 0 <= percentage <= 100:
        raise ValueError("Assessment percentage is invalid.")

    data = _load_data()
    student = _student_record(data, student_name)

    now = _now()

    record = {
        "assessment_id": str(uuid4()),
        "assessment_type": str(assessment_type),
        "subject": str(subject or "General"),
        "total_questions": quiz_result.get("total_questions", 0),
        "correct_answers": quiz_result.get("correct_answers", 0),
        "incorrect_answers": quiz_result.get("incorrect_answers", 0),
        "unanswered_questions": quiz_result.get(
            "unanswered_questions", 0
        ),
        "percentage": percentage,
        "assessment": quiz_result.get("assessment"),
        "readiness_signal": quiz_result.get("readiness_signal"),
        "topic_analysis": quiz_result.get("topic_analysis", []),
        "answer_review": quiz_result.get("answer_review", []),
        "metadata": metadata or {},
        "assessed_at": now
    }

    student["assessments"].append(record)

    _save_data(data)

    return record


def get_assessment_history(student_name):
    """Return all completed assessments for a student."""

    data = _load_data()

    student = data["students"].get(
        str(student_name or "").strip().lower()
    )

    if not student:
        return []

    return student.get("assessments", [])


def get_assessment_summary(student_name):
    """Calculate quiz and assessment statistics."""

    history = get_assessment_history(student_name)

    total = len(history)

    if not total:
        return {
            "student_name": student_name,
            "total_assessments": 0,
            "average_score": 0,
            "best_score": 0,
            "latest_score": None,
            "passed_assessments": 0,
            "needs_practice": 0
        }

    scores = [
        float(item.get("percentage", 0))
        for item in history
    ]

    passed = sum(
        1 for score in scores if score >= 80
    )

    return {
        "student_name": student_name,
        "total_assessments": total,
        "average_score": round(sum(scores) / total, 2),
        "best_score": max(scores),
        "latest_score": scores[-1],
        "passed_assessments": passed,
        "needs_practice": total - passed
    }
