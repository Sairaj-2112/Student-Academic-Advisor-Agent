
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


def _load_data():
    """Load saved learning progress."""
    if not PROGRESS_FILE.exists():
        return {"students": {}}

    try:
        return json.loads(
            PROGRESS_FILE.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return {"students": {}}


def _save_data(data):
    """Save learning progress."""
    PROGRESS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    PROGRESS_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )


def add_learning_item(
    student_name,
    item_name,
    item_type,
    notes=""
):
    """Add a course, skill or project to a student's plan."""

    if item_type.lower() not in VALID_TYPES:
        raise ValueError(
            "Type must be course, skill or project."
        )

    if not student_name.strip() or not item_name.strip():
        raise ValueError(
            "Student name and item name are required."
        )

    data = _load_data()
    student_id = student_name.strip().lower()

    if student_id not in data["students"]:
        data["students"][student_id] = {
            "student_name": student_name.strip(),
            "items": []
        }

    now = datetime.now(timezone.utc).isoformat()

    item = {
        "id": str(uuid4()),
        "item_name": item_name.strip(),
        "item_type": item_type.lower(),
        "status": "not_started",
        "notes": notes.strip(),
        "created_at": now,
        "updated_at": now
    }

    data["students"][student_id]["items"].append(item)
    _save_data(data)

    print("Learning item added successfully!")
    return item


def update_learning_status(
    student_name,
    item_id,
    new_status,
    notes=None
):
    """Update the status of a learning item."""

    new_status = new_status.lower()

    if new_status not in VALID_STATUSES:
        raise ValueError(
            "Status must be not_started, in_progress or completed."
        )

    data = _load_data()
    student_id = student_name.strip().lower()

    student = data["students"].get(student_id)

    if not student:
        print("Student not found.")
        return False

    for item in student["items"]:
        if item["id"] == item_id:
            item["status"] = new_status

            if notes is not None:
                item["notes"] = notes.strip()

            item["updated_at"] = (
                datetime.now(timezone.utc).isoformat()
            )

            _save_data(data)
            print("Learning progress updated successfully!")
            return True

    print("Learning item not found.")
    return False


def get_learning_progress(student_name):
    """Get all learning items for a student."""

    data = _load_data()
    student_id = student_name.strip().lower()

    student = data["students"].get(student_id)

    if not student:
        return []

    return student["items"]


def get_progress_summary(student_name):
    """Calculate a student's learning progress."""

    items = get_learning_progress(student_name)

    total = len(items)

    completed = sum(
        1 for item in items
        if item["status"] == "completed"
    )

    in_progress = sum(
        1 for item in items
        if item["status"] == "in_progress"
    )

    not_started = sum(
        1 for item in items
        if item["status"] == "not_started"
    )

    percentage = (
        round((completed / total) * 100, 2)
        if total > 0 else 0
    )

    return {
        "student_name": student_name,
        "total_items": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "completion_percentage": percentage
    }


if __name__ == "__main__":

    print("===== LEARNING PROGRESS TRACKER =====")

    item = add_learning_item(
        student_name="Test Student",
        item_name="Python Programming",
        item_type="skill",
        notes="Learn Python fundamentals"
    )

    update_learning_status(
        student_name="Test Student",
        item_id=item["id"],
        new_status="in_progress"
    )

    print("\nLearning Items:")
    print(
        json.dumps(
            get_learning_progress("Test Student"),
            indent=4
        )
    )

    print("\nProgress Summary:")
    print(
        json.dumps(
            get_progress_summary("Test Student"),
            indent=4
        )
    )

