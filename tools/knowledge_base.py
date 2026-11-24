
import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# ==========================================
# KNOWLEDGE BASE CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_FILE = BASE_DIR / "data" / "knowledge_base.json"

VALID_CATEGORIES = [
    "course",
    "career",
    "skill",
    "institution",
    "pathway"
]


# ==========================================
# LOAD KNOWLEDGE BASE
# ==========================================

def load_knowledge_base():
    if not KNOWLEDGE_FILE.exists():
        return {"knowledge": []}

    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {"knowledge": []}

        if not isinstance(data.get("knowledge"), list):
            return {"knowledge": []}

        return data

    except (json.JSONDecodeError, OSError):
        return {"knowledge": []}


# ==========================================
# SAVE KNOWLEDGE BASE
# ==========================================

def save_knowledge_base(data):
    KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


# ==========================================
# ADD KNOWLEDGE
# ==========================================

def add_knowledge(
    category,
    title,
    description,
    institution="",
    education_level="",
    prerequisites=None,
    related_skills=None,
    source_name="",
    source_url=""
):
    category = category.strip().lower()

    if category not in VALID_CATEGORIES:
        raise ValueError(
            "Category must be course, career, skill, institution or pathway."
        )

    if not title.strip() or not description.strip():
        raise ValueError("Title and description are required.")

    data = load_knowledge_base()

    record = {
        "id": str(uuid4()),
        "category": category,
        "title": title.strip(),
        "description": description.strip(),
        "institution": institution.strip(),
        "education_level": education_level.strip(),
        "prerequisites": prerequisites or [],
        "related_skills": related_skills or [],
        "source_name": source_name.strip(),
        "source_url": source_url.strip(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    data["knowledge"].append(record)
    save_knowledge_base(data)

    print("Knowledge added successfully!")
    return record


# ==========================================
# SEARCH KNOWLEDGE
# ==========================================

def search_knowledge(query, category=None):
    if not query or not query.strip():
        return []

    data = load_knowledge_base()
    keywords = query.lower().strip().split()

    results = []

    for record in data["knowledge"]:
        if category and record.get("category") != category.lower():
            continue

        searchable_text = " ".join([
            record.get("title", ""),
            record.get("description", ""),
            record.get("institution", ""),
            record.get("education_level", ""),
            " ".join(record.get("prerequisites", [])),
            " ".join(record.get("related_skills", []))
        ]).lower()

        matched_keywords = sum(
            1 for word in keywords if word in searchable_text
        )

        if matched_keywords > 0:
            result = record.copy()
            result["match_score"] = round(
                matched_keywords / len(keywords), 2
            )
            results.append(result)

    results.sort(
        key=lambda item: item["match_score"],
        reverse=True
    )

    return results


# ==========================================
# GET ALL KNOWLEDGE
# ==========================================

def get_all_knowledge(category=None):
    data = load_knowledge_base()
    records = data["knowledge"]

    if category:
        records = [
            record for record in records
            if record.get("category") == category.lower()
        ]

    return records


# ==========================================
# GET KNOWLEDGE BY ID
# ==========================================

def get_knowledge_by_id(record_id):
    data = load_knowledge_base()

    for record in data["knowledge"]:
        if record.get("id") == record_id:
            return record

    return None


# ==========================================
# DELETE KNOWLEDGE
# ==========================================

def delete_knowledge(record_id):
    data = load_knowledge_base()
    original_count = len(data["knowledge"])

    data["knowledge"] = [
        record for record in data["knowledge"]
        if record.get("id") != record_id
    ]

    if len(data["knowledge"]) == original_count:
        return False

    save_knowledge_base(data)
    return True


# ==========================================
# KNOWLEDGE BASE STATISTICS
# ==========================================

def get_knowledge_statistics():
    records = get_all_knowledge()

    statistics = {
        "total_records": len(records),
        "categories": {}
    }

    for category in VALID_CATEGORIES:
        statistics["categories"][category] = sum(
            1 for record in records
            if record.get("category") == category
        )

    return statistics


# ==========================================
# SAFE MODULE TEST
# ==========================================

if __name__ == "__main__":
    print("===== KNOWLEDGE BASE TEST =====")
    print(json.dumps(
        get_knowledge_statistics(),
        indent=4,
        ensure_ascii=False
    ))
