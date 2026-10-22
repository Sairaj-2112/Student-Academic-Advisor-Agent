
from agents.academic_agent import academic_agent
from agents.recommendation_agent import recommendation_agent
from memory.student_memory import load_student


def coordinator_agent(completed_subjects, interests):
    print("\n[Coordinator] Starting academic analysis...")

    # Normalize completed subjects
    if isinstance(completed_subjects, str):
        completed_subjects = [
            subject.strip()
            for subject in completed_subjects.split(",")
            if subject.strip()
        ]

    # Normalize interests
    if isinstance(interests, str):
        interests = [
            interest.strip()
            for interest in interests.split(",")
            if interest.strip()
        ]

    # Handle empty interests
    if not interests:
        print("[Coordinator] No interests provided.")
        return {
            "academic_results": [],
            "recommendations": []
        }

    # Contact Academic Agent
    print("[Coordinator] Contacting Academic Agent...")

    academic_results = []

    for interest in interests:
        print(f"[Coordinator] Searching for: {interest}")

        result = academic_agent(
            completed_subjects=completed_subjects,
            keyword=interest
        )

        if result:
            if isinstance(result, list):
                academic_results.extend(result)
            else:
                academic_results.append(result)

    # Contact Recommendation Agent
    print("\n[Coordinator] Contacting Recommendation Agent...")

    recommendations = recommendation_agent(interests)

    if recommendations is None:
        recommendations = []

    # Return combined results
    return {
        "academic_results": academic_results,
        "recommendations": recommendations
    }


if __name__ == "__main__":
    student = load_student()

    if student is None:
        print("No saved student data found.")

    else:
        print(f"\nWelcome, {student['name']}!")

        result = coordinator_agent(
            completed_subjects=student["completed_subjects"],
            interests=student["interests"]
        )

        print("\n===== PERSONALIZED ADVISOR REPORT =====")
        print("Completed subjects:", student["completed_subjects"])
        print("Interests:", student["interests"])
        print("Academic results:", len(result["academic_results"]))
        print("Recommended courses:", len(result["recommendations"]))

        # Display the first five recommendations
        for course in result["recommendations"][:5]:
            print("\n" + "-" * 50)
            print("Interest:", course.get("interest", "N/A"))
            print("Title:", course.get("title", "N/A"))
            print("Course code:", course.get("course_code", "N/A"))
            print("Department:", course.get("subject", "N/A"))
            print("Credits:", course.get("credits", "N/A"))

            print(
                "Description:",
                course.get(
                    "description",
                    "No description available"
                )[:200],
                "..."
            )
