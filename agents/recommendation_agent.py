
from tools.course_catalogue import search_courses
from tools.knowledge_context import get_relevant_knowledge


# ==========================================
# RECOMMENDATION AGENT
# ==========================================

def recommendation_agent(interests):
    """
    Recommends relevant, unique courses and learning pathways.

    Sources:
    1. Existing course catalogue.
    2. Local Knowledge Base.
    """

    if isinstance(interests, str):
        interests = interests.split(",")

    interests = [
        interest.strip()
        for interest in interests
        if isinstance(interest, str) and interest.strip()
    ]

    if not interests:
        print("[Recommendation Agent] No interests provided.")
        return []

    recommendations = []
    seen_courses = set()

    # ======================================
    # SOURCE 1: EXISTING COURSE CATALOGUE
    # ======================================

    for interest in interests:

        print(
            f"[Recommendation Agent] Searching catalogue for: {interest}"
        )

        try:
            courses = search_courses(interest, limit=5)

        except (FileNotFoundError, ValueError) as error:
            print(
                f"[Recommendation Agent] Catalogue search error: {error}"
            )
            courses = []

        for course in courses:

            title = course.get("title", "Unknown")
            subject = course.get("subject", "Unknown")
            course_code = course.get("course_code", subject)
            description = course.get("description", "")
            credits = course.get("credits", "Unknown")

            identity = (
                str(course_code).strip().lower(),
                str(title).strip().lower()
            )

            if identity in seen_courses:
                continue

            seen_courses.add(identity)

            recommendations.append({
                "interest": interest,
                "title": title,
                "course_code": course_code,
                "subject": subject,
                "description": description,
                "credits": credits,
                "source_type": "course_catalogue"
            })

    print(
        "[Recommendation Agent] Catalogue courses found:",
        len(recommendations)
    )

    # ======================================
    # SOURCE 2: LOCAL KNOWLEDGE BASE
    # ======================================

    profile = {
        "interests": interests,
        "learning_goals": interests
    }

    try:
        knowledge_records = get_relevant_knowledge(
            profile,
            limit=15
        )

        for record in knowledge_records:

            category = record.get("category", "")

            # Only course and pathway records are
            # added to course recommendations.
            if category not in ["course", "pathway"]:
                continue

            title = record.get("title", "Unknown")
            description = record.get("description", "")

            identity = (
                "knowledge_base",
                str(record.get("id", title)).strip().lower()
            )

            if identity in seen_courses:
                continue

            seen_courses.add(identity)

            recommendations.append({
                "interest": ", ".join(interests),
                "title": title,
                "course_code": "Knowledge Base Record",
                "subject": category.title(),
                "description": description,
                "credits": "Not specified",
                "source_type": "knowledge_base",
                "source_name": record.get(
                    "source_name",
                    "Not specified"
                ),
                "prerequisites": record.get(
                    "prerequisites",
                    []
                ),
                "related_skills": record.get(
                    "related_skills",
                    []
                )
            })

    except Exception as error:
        print(
            "[Recommendation Agent] Knowledge retrieval error:",
            error
        )

    print(
        "[Recommendation Agent] Total unique recommendations:",
        len(recommendations)
    )

    return recommendations


# ==========================================
# MODULE TEST
# ==========================================

if __name__ == "__main__":

    test_interests = [
        "artificial intelligence",
        "machine learning",
        "business",
        "psychology",
        "finance"
    ]

    results = recommendation_agent(test_interests)

    print("\n===== RECOMMENDATION AGENT RESULTS =====")

    for course in results:

        print("-" * 50)
        print("Interest:", course["interest"])
        print("Title:", course["title"])
        print("Course code:", course["course_code"])
        print("Department:", course["subject"])
        print("Credits:", course["credits"])
        print("Source:", course["source_type"])
        print("Description:", course["description"][:250])

        if course.get("prerequisites"):
            print("Prerequisites:", course["prerequisites"])

        if course.get("related_skills"):
            print("Related Skills:", course["related_skills"])
