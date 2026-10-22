
from tools.course_catalogue import load_courses


def academic_agent(completed_subjects, keyword="computer science"):
    """
    Academic Agent:
    Finds relevant courses and checks prerequisites.
    """
    courses = load_courses()

    completed = {
        subject.strip().lower()
        for subject in completed_subjects
    }

    # Search course titles and descriptions
    title_column = next(
        (c for c in courses.columns
         if c.strip().lower() in ["title", "course title", "course name"]),
        None
    )

    matches = courses[
        courses["Description"].astype(str).str.contains(
            keyword, case=False, na=False
        )
    ]

    results = []

    for _, row in matches.head(10).iterrows():
        description = str(row["Description"])
        title = str(row[title_column]) if title_column else str(row["Subject"])

        # Extract prerequisite text when available
        prereq_text = ""
        marker = "prerequisite:"
        lower_description = description.lower()

        if marker in lower_description:
            prereq_text = description[
                lower_description.index(marker) + len(marker):
            ].strip()

        results.append({
            "subject": str(row["Subject"]),
            "title": title,
            "description": description,
            "prerequisite_text": prereq_text or "Not specified",
            "credits": str(row.get("Credit Hours", "Unknown")),
            "completed_subjects": sorted(completed)
        })

    return results


if __name__ == "__main__":
    courses = academic_agent(
        completed_subjects=["Python", "Machine Learning"],
        keyword="artificial intelligence"
    )

    print("\nACADEMIC AGENT RESULTS\n")

    for course in courses:
        print("-" * 50)
        print("Department:", course["subject"])
        print("Course:", course["title"])
        print("Credits:", course["credits"])
        print("Prerequisites:", course["prerequisite_text"])
