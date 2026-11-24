
from tools.knowledge_base import (
    search_knowledge,
    VALID_CATEGORIES
)


# ==========================================
# EXTRACT PROFILE INFORMATION
# ==========================================

def extract_profile_values(profile):
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()

    if not isinstance(profile, dict):
        profile = {}

    fields = [
        "interests",
        "career_goals",
        "learning_goals",
        "skills",
        "subjects",
        "completed_courses",
        "strengths"
    ]

    values = []

    for field in fields:
        field_values = profile.get(field, [])

        if isinstance(field_values, str):
            field_values = [field_values]

        if isinstance(field_values, list):
            for value in field_values:
                if isinstance(value, str) and value.strip():
                    values.append(value.strip())

    return list(dict.fromkeys(values))


# ==========================================
# RETRIEVE RELEVANT KNOWLEDGE
# ==========================================

def get_relevant_knowledge(profile, limit=8):

    search_terms = extract_profile_values(profile)

    if not search_terms:
        return []

    matched_records = {}

    for term in search_terms:

        for category in VALID_CATEGORIES:

            results = search_knowledge(
                query=term,
                category=category
            )

            for record in results:

                record_id = record.get("id")

                if not record_id:
                    continue

                if record_id not in matched_records:
                    matched_records[record_id] = record

                elif record["match_score"] > matched_records[record_id]["match_score"]:
                    matched_records[record_id] = record

    ranked_records = sorted(
        matched_records.values(),
        key=lambda item: item.get("match_score", 0),
        reverse=True
    )

    return ranked_records[:limit]


# ==========================================
# BUILD KNOWLEDGE CONTEXT FOR AI AGENTS
# ==========================================

def build_knowledge_context(profile, limit=8):

    records = get_relevant_knowledge(
        profile=profile,
        limit=limit
    )

    if not records:
        return (
            "No directly matching records were found in the local "
            "Knowledge Base. Use general reasoning where appropriate, "
            "and do not invent factual requirements or institutional details."
        )

    context = []

    context.append("RELEVANT LOCAL KNOWLEDGE BASE RECORDS:")

    for index, record in enumerate(records, start=1):

        context.append(
            f"""
Record {index}
Category: {record.get('category', 'Not specified')}
Title: {record.get('title', 'Not specified')}
Description: {record.get('description', 'Not specified')}
Institution: {record.get('institution', 'Not specified')}
Education Level: {record.get('education_level', 'Not specified')}
Prerequisites: {', '.join(record.get('prerequisites', []))}
Related Skills: {', '.join(record.get('related_skills', []))}
Source: {record.get('source_name', 'Not specified')}
Source URL: {record.get('source_url', 'Not provided')}
Match Score: {record.get('match_score', 0)}
"""
        )

    context.append(
        """
IMPORTANT:
- Treat these records as supporting information, not guaranteed facts.
- Do not invent missing admission requirements, fees or deadlines.
- Distinguish sample information from verified official information.
- If the local Knowledge Base does not contain an answer, say so.
"""
    )

    return "\n".join(context)


# ==========================================
# MODULE TEST
# ==========================================

if __name__ == "__main__":

    test_profile = {
        "name": "Sairaj",
        "interests": [
            "Artificial Intelligence",
            "Data Science"
        ],
        "skills": [
            "Python",
            "Power BI"
        ],
        "career_goals": [
            "AI Engineer"
        ],
        "completed_courses": [
            "Machine Learning"
        ]
    }

    print("\n===== KNOWLEDGE RETRIEVAL TEST =====")

    print(build_knowledge_context(test_profile))
