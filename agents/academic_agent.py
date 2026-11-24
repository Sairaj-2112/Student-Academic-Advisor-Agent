
from tools.course_catalogue import load_courses
from tools.knowledge_context import build_knowledge_context


# ==========================================
# ACADEMIC AGENT
# ==========================================

def academic_agent(completed_subjects, keyword="computer science"):
    """
    Academic Agent:
    1. Searches course titles and descriptions.
    2. Checks completed subjects.
    3. Retrieves relevant local Knowledge Base information.
    """

    courses = load_courses()

    completed = {
        str(subject).strip().lower()
        for subject in completed_subjects
        if str(subject).strip()
    }

    # Identify the actual course name column.
    title_column = next(
        (
            column for column in courses.columns
            if column.strip().lower() in [
                "name",
                "title",
                "course title",
                "course name"
            ]
        ),
        None
    )

    if title_column is None:
        raise ValueError(
            "Course name column not found. Expected a Name or Title column."
        )

    if "Description" not in courses.columns:
        raise ValueError("Description column not found in course catalogue.")

    # Search both course names and descriptions.
    search_text = (
        courses[title_column].fillna("").astype(str)
        + " "
        + courses["Description"].fillna("").astype(str)
    )

    matches = courses[
        search_text.str.contains(
            keyword,
            case=False,
            na=False,
            regex=False
        )
    ]

    results = []
    seen_courses = set()

    for _, row in matches.iterrows():

        title = str(row.get(title_column, "")).strip()
        description = str(row.get("Description", "")).strip()
        department = str(row.get("Subject", "Unknown")).strip()
        course_number = str(row.get("Number", "")).strip()

        # Skip empty course names.
        if not title or title.lower() == "nan":
            continue

        # Avoid duplicate courses from multiple sections.
        course_key = (department, course_number, title)

        if course_key in seen_courses:
            continue

        seen_courses.add(course_key)

        # Extract prerequisite text if available.
        prereq_text = "Not specified"
        lower_description = description.lower()

        marker = "prerequisite:"

        if marker in lower_description:
            prereq_text = description[
                lower_description.index(marker) + len(marker):
            ].strip()

        credits = row.get("Credit Hours", "Unknown")

        results.append({
            "subject": department,
            "course_number": course_number,
            "title": title,
            "description": description,
            "prerequisite_text": prereq_text,
            "credits": str(credits),
            "completed_subjects": sorted(completed)
        })

        if len(results) >= 10:
            break

    return results


# ==========================================
# ACADEMIC KNOWLEDGE RETRIEVAL
# ==========================================

def get_academic_knowledge(completed_subjects, interests):

    profile = {
        "completed_courses": completed_subjects,
        "subjects": completed_subjects,
        "interests": interests
    }

    return build_knowledge_context(profile)


# ==========================================
# MODULE TEST
# ==========================================

if __name__ == "__main__":

    completed = ["Python", "Machine Learning"]
    interests = ["Artificial Intelligence", "Data Science"]

    print("\n===== ACADEMIC AGENT COURSE RESULTS =====")

    courses = academic_agent(
        completed_subjects=completed,
        keyword="artificial intelligence"
    )

    for course in courses:
        print("-" * 50)
        print("Department:", course["subject"])
        print("Course Number:", course["course_number"])
        print("Course:", course["title"])
        print("Credits:", course["credits"])
        print("Prerequisites:", course["prerequisite_text"])

    print("\nTotal unique courses:", len(courses))

    print("\n===== ACADEMIC KNOWLEDGE RETRIEVAL =====")

    knowledge = get_academic_knowledge(
        completed_subjects=completed,
        interests=interests
    )

    print(knowledge)
