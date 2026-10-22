
import re
import html
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/course-catalog.csv")


SYNONYMS = {
    "ai": ["artificial intelligence"],
    "artificial intelligence": ["ai"],

    "ml": ["machine learning"],
    "machine learning": [
        "ml",
        "predictive modelling",
        "predictive modeling",
    ],

    "ca": ["computer architecture"],
    "computer architecture": [
        "ca",
        "computer organization",
        "computer organisation",
        "processor architecture",
        "instruction set architecture",
    ],

    "data analytics": [
        "data analysis",
        "data science",
        "data mining",
    ],
    "business": [
        "business analytics",
        "business administration",
        "entrepreneurship",
    ],
    "psychology": [
        "cognition",
        "human behavior",
        "human behaviour",
    ],
    "finance": [
        "financial analysis",
        "personal finance",
        "investments",
    ],
    "cybersecurity": [
        "cyber security",
        "information security",
        "computer security",
        "network security",
        "security and privacy",
        "information assurance",
    ],
    "programming": [
        "software development",
        "computer programming",
    ],
    "design": [
        "user experience",
        "visual design",
        "graphic design",
    ],
    "agriculture": [
        "agricultural",
        "agricultural science",
        "crop science",
        "food systems",
    ],
}


GENERIC_PHRASES = [
    "topics vary",
    "topic varies",
    "topics to be announced",
    "content varies",
    "special topics",
    "new and developing areas",
]


def normalize_text(value):
    """Normalize text for consistent keyword comparisons."""
    if value is None or pd.isna(value):
        return ""

    value = html.unescape(str(value))
    return re.sub(r"\s+", " ", value.strip().lower())


def contains_term(text, term):
    """Match a whole word or phrase."""
    text = normalize_text(text)
    term = normalize_text(term)

    if not text or not term:
        return False

    pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    return re.search(pattern, text) is not None


def load_courses():
    """Load and clean the university course catalogue."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Course catalogue not found: {DATA_PATH.resolve()}"
        )

    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    required_columns = ["Subject", "Description"]
    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required catalogue columns: {missing}"
        )

    df = df.dropna(subset=["Subject"]).copy()

    for column in df.select_dtypes(include=["object", "str"]).columns:
        df[column] = df[column].map(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

    identity_columns = [
        column for column in [
            "Year",
            "Term",
            "Subject",
            "Number",
            "Name",
            "Section Title",
            "Description",
            "Credit Hours",
        ]
        if column in df.columns
    ]

    if identity_columns:
        df = df.drop_duplicates(subset=identity_columns)

    return df.reset_index(drop=True)


def expand_keyword(keyword):
    """Expand a keyword using defined synonyms."""
    keyword = normalize_text(keyword)

    if not keyword:
        return []

    terms = [keyword]

    for phrase, aliases in SYNONYMS.items():
        if keyword == phrase or keyword in aliases:
            terms.append(phrase)
            terms.extend(aliases)

    return list(dict.fromkeys(terms))


def search_courses(keyword, limit=10):
    """
    Search and rank courses by relevance.

    Official course names receive the highest weight.
    Generic courses are filtered when their title does not
    directly match the search term.
    """
    if not isinstance(keyword, str) or not keyword.strip():
        return []

    if limit <= 0:
        return []

    df = load_courses()
    original_keyword = normalize_text(keyword)
    terms = expand_keyword(original_keyword)

    ranked_courses = []

    for _, row in df.iterrows():
        subject = normalize_text(row.get("Subject", ""))
        number = normalize_text(row.get("Number", ""))
        name = normalize_text(row.get("Name", ""))
        section_title = normalize_text(
            row.get("Section Title", "")
        )
        description = normalize_text(
            row.get("Description", "")
        )

        title = name or section_title or "Untitled course"

        score = 0
        title_match = False
        exact_name_match = False

        # Score matches using all defined terms.
        for term in terms:
            if contains_term(name, term):
                score += 12
                title_match = True

            if contains_term(section_title, term):
                score += 8
                title_match = True

            if contains_term(description, term):
                score += 2

        # Give the original search phrase extra weight.
        if contains_term(name, original_keyword):
            score += 8
            exact_name_match = True

        if contains_term(section_title, original_keyword):
            score += 5

        if contains_term(description, original_keyword):
            score += 2

        # Detect vague descriptions.
        description_is_generic = any(
            contains_term(description, phrase)
            for phrase in GENERIC_PHRASES
        )

        if description_is_generic:
            score -= 5

            # Generic descriptions alone are not enough.
            if not title_match:
                continue

            # A generic course must have a direct match in
            # its official name, not only a section title.
            if not exact_name_match:
                continue

        # Require a reasonable minimum relevance score.
        if score < 5:
            continue

        course_code = (
            f"{row['Subject']} {row['Number']}"
            if pd.notna(row.get("Number")) and number
            else str(row["Subject"])
        )

        course = {
            "title": html.unescape(str(title)).strip(),
            "subject": str(row["Subject"]).strip(),
            "course_code": course_code.strip(),
            "description": html.unescape(
                str(row.get("Description", ""))
            ).strip(),
            "credits": str(
                row.get("Credit Hours", "Unknown")
            ),
        }

        identity = (
            normalize_text(course["course_code"]),
            normalize_text(course["title"]),
            normalize_text(course["description"]),
        )

        ranked_courses.append((score, identity, course))

    # Highest scores first.
    ranked_courses.sort(
        key=lambda item: (-item[0], item[2]["title"].lower())
    )

    results = []
    seen = set()

    for score, identity, course in ranked_courses:
        if identity in seen:
            continue

        seen.add(identity)
        results.append(course)

        if len(results) >= limit:
            break

    return results


if __name__ == "__main__":
    test_interests = [
        "artificial intelligence",
        "machine learning",
        "computer architecture",
        "CA",
        "cybersecurity",
        "business",
        "psychology",
        "finance",
        "agriculture",
        "design",
    ]

    for interest in test_interests:
        print("\n" + "=" * 55)
        print("Interest:", interest)

        try:
            courses = search_courses(interest, limit=5)

            if not courses:
                print("No sufficiently relevant courses found.")
                continue

            for course in courses:
                print("-" * 40)
                print("Title:", course["title"])
                print("Course code:", course["course_code"])
                print("Department:", course["subject"])
                print("Credits:", course["credits"])
                print("Description:", course["description"][:180])

        except (FileNotFoundError, ValueError) as error:
            print("Catalogue error:", error)
