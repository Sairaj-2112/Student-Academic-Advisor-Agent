
from tools.course_catalogue import search_courses


def recommendation_agent(interests):
    """Recommend relevant, unique courses for student interests."""

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

    for interest in interests:
        print(f"[Recommendation Agent] Searching for: {interest}")

        try:
            courses = search_courses(interest, limit=5)
        except (FileNotFoundError, ValueError) as error:
            print(f"[Recommendation Agent] Search error: {error}")
            continue

        for course in courses:
            title = course.get("title", "Unknown")
            subject = course.get("subject", "Unknown")
            course_code = course.get("course_code", subject)
            description = course.get("description", "")
            credits = course.get("credits", "Unknown")

            identity = (
                str(course_code).strip().lower(),
                str(title).strip().lower(),
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
            })

    print(
        "[Recommendation Agent] Total unique courses found:",
        len(recommendations),
    )

    return recommendations


if __name__ == "__main__":
    test_interests = [
        "artificial intelligence",
        "machine learning",
        "business",
        "psychology",
        "finance",
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
        print("Description:", course["description"][:250])
