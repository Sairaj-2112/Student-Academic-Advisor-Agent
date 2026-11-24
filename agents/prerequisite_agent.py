import re
from itertools import product


# =========================================================
# 1. NORMALIZATION
# =========================================================

def normalize_code(value):
    if not value:
        return ""

    value = str(value).upper().strip()
    value = re.sub(r"\s+", " ", value)

    match = re.search(r"\b([A-Z]{2,6})\s*(\d{3,4})\b", value)

    if match:
        return f"{match.group(1)} {match.group(2)}"

    return value


def normalize_completed(profile):
    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()

    if not isinstance(profile, dict):
        profile = {}

    courses = profile.get("completed_courses", []) or []
    subjects = profile.get("subjects", []) or []

    if isinstance(courses, str):
        courses = [courses]

    if isinstance(subjects, str):
        subjects = [subjects]

    completed = set()

    for course in courses + subjects:
        code = normalize_code(course)

        if code:
            completed.add(code)

    return completed


# =========================================================
# 2. TEXT HELPERS
# =========================================================

def clean_sentence(sentence):
    sentence = re.sub(
        r"^\s*(PREREQUISITES?|COREQUISITES?)\s*:\s*",
        "",
        sentence,
        flags=re.IGNORECASE
    )

    sentence = re.sub(r"\s+", " ", sentence)

    return sentence.strip(" .;")


def sentence_key(sentence):
    return re.sub(
        r"[^A-Z0-9]+",
        " ",
        sentence.upper()
    ).strip()


def split_sentences(text):
    text = str(text or "").strip()

    if not text:
        return []

    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]


# =========================================================
# 3. NO-PREREQUISITE DETECTION
# =========================================================

def has_no_prerequisites(text):
    text = str(text or "").lower().strip()

    patterns = [
        r"\bno prerequisites?\b",
        r"\bprerequisites?\s*:\s*none\b",
        r"\bprerequisites?\s+none\b",
        r"\bno prior coursework required\b",
        r"\bwithout prerequisites?\b"
    ]

    return any(
        re.search(pattern, text)
        for pattern in patterns
    )


# =========================================================
# 4. ELIGIBILITY RESTRICTION DETECTION
# =========================================================

def extract_eligibility_details(text):
    sentences = split_sentences(text)

    eligibility_keywords = [
        "restricted to",
        "only open to",
        "open only to",
        "senior standing",
        "junior standing",
        "graduate standing",
        "undergraduate standing",
        "graduate student status",
        "engineering major",
        "engineering degree program",
        "graduate degree program",
        "consent of instructor",
        "consent of the instructor",
        "consent of department",
        "consent of the department",
        "instructor permission",
        "departmental approval",
        "audition required",
        "successful completion of a qualifying audition"
    ]

    program_patterns = [
        r"restricted to students enrolled in .+",
        r"restricted to students enrolled at .+",
        r"only open to students enrolled in .+",
        r"open only to students enrolled in .+",
        r"students enrolled in .+ curriculum only",
        r"students enrolled in .+ program only",
        r"restricted to students in the .+ program",
        r"restricted to students in .+ curriculum"
    ]

    restrictions = []
    seen = set()
    program_restricted = False

    for sentence in sentences:
        cleaned = clean_sentence(sentence)

        if not cleaned:
            continue

        lower = cleaned.lower()

        if not any(
            keyword in lower
            for keyword in eligibility_keywords
        ):
            continue

        key = sentence_key(cleaned)

        if key not in seen:
            restrictions.append(cleaned)
            seen.add(key)

        if any(
            re.search(pattern, lower)
            for pattern in program_patterns
        ):
            program_restricted = True

    if program_restricted:
        restriction_type = "program"
    elif restrictions:
        restriction_type = "conditional"
    else:
        restriction_type = "none"

    return {
        "eligibility_restrictions": restrictions,
        "restriction_type": restriction_type,
        "program_restricted": program_restricted
    }


# =========================================================
# 5. CONCURRENT ENROLLMENT DETECTION
# =========================================================

def extract_concurrent_conditions(text):
    text = str(text or "")

    patterns = [
        r"\bconcurrent\s+enrollment\s+in\s+([^.;]+)",
        r"\bconcurrent\s+registration\s+in\s+([^.;]+)",
        r"\bconcurrently\s+enrolled\s+in\s+([^.;]+)"
    ]

    conditions = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:
            value = match.strip()

            value = re.sub(
                r"\s+(is|are)\s+required\s*$",
                "",
                value,
                flags=re.IGNORECASE
            )

            value = re.sub(
                r"\s+for students.*$",
                "",
                value,
                flags=re.IGNORECASE
            )

            value = value.strip(" ,;.")

            if value:
                conditions.append(value)

    # Remove duplicate conditions.
    unique = []
    seen = set()

    for condition in conditions:
        key = sentence_key(condition)

        if key not in seen:
            unique.append(condition)
            seen.add(key)

    return unique


# =========================================================
# 6. EXPRESSION PREPROCESSING
# =========================================================

def preprocess_expression(text):
    text = str(text or "").upper().strip()

    if not text or text == "NOT SPECIFIED":
        return ""

    # Normalize course codes written as "PHIL, 202".
    text = re.sub(
        r"\b([A-Z]{2,6}),\s*(\d{3,4})\b",
        r"\1 \2",
        text
    )

    # Remove prerequisite labels.
    text = re.sub(
        r"\bPREREQUISITES?\s*:\s*",
        "",
        text
    )

    # Special case:
    # "Credit or concurrent registration in TAM 335"
    # means a concurrent registration condition.
    text = re.sub(
        r"\bCREDIT\s+OR\s+CONCURRENT\s+"
        r"(?:ENROLLMENT|REGISTRATION)\s+IN\s+[^.;]+",
        " CONDITION_CONCURRENT ",
        text
    )

    # Concurrent enrollment.
    # Replace only the concurrent phrase, not earlier requirements.
    text = re.sub(
        r"\bCONCURRENT\s+(?:ENROLLMENT|REGISTRATION)\s+IN\s+"
        r"[^.;]+",
        " CONDITION_CONCURRENT ",
        text
    )

    text = re.sub(
        r"\bCONCURRENTLY\s+ENROLLED\s+IN\s+[^.;]+",
        " CONDITION_CONCURRENT ",
        text
    )

    # Instructor consent.
    text = re.sub(
        r"\bCONSENT\s+OF\s+(?:THE\s+)?INSTRUCTOR\b",
        " CONDITION_CONSENT ",
        text
    )

    text = re.sub(
        r"\bINSTRUCTOR\s+APPROVAL\b",
        " CONDITION_CONSENT ",
        text
    )

    # Department consent.
    text = re.sub(
        r"\bCONSENT\s+OF\s+(?:THE\s+)?DEPARTMENT\b",
        " CONDITION_CONSENT ",
        text
    )

    # Equivalency.
    text = re.sub(
        r"\bOR\s+EQUIVALENT\b",
        " OR CONDITION_EQUIVALENT ",
        text
    )

    text = re.sub(
        r"\bEQUIVALENT\b",
        " CONDITION_EQUIVALENT ",
        text
    )

    # "One of A, B, C or D" means A OR B OR C OR D.
    one_of_pattern = re.compile(
        r"\bONE OF\b(.*?)(?=\bAND\b|;|\.|$)"
    )

    def replace_one_of(match):
        group = match.group(1).strip()

        group = group.replace(",", " OR ")

        group = re.sub(
            r"\bOR\s+OR\b",
            "OR",
            group
        )

        group = re.sub(r"\s+", " ", group)

        return "(" + group + ")"

    text = one_of_pattern.sub(
        replace_one_of,
        text
    )

    # Remove a comma immediately before AND.
    text = re.sub(
        r",\s*AND\b",
        " AND ",
        text
    )

    # Semicolons and remaining commas represent AND.
    text = text.replace(";", " AND ")
    text = text.replace(",", " AND ")

    # Remove punctuation.
    text = text.replace(".", " ")

    # Remove descriptive words that are not operators.
    filler_words = [
        "CREDIT",
        "COMPLETED",
        "COMPLETION",
        "PRIOR",
        "COURSEWORK",
        "COURSE",
        "COURSES",
        "REQUIRED",
        "REQUIREMENT",
        "REQUIREMENTS",
        "HAVE",
        "HAS",
        "BEEN",
        "EITHER",
        "THE",
        "A",
        "AN",
        "IS",
        "ARE",
        "MUST",
        "SUCCESSFUL",
        "SATISFACTORY"
    ]

    for word in filler_words:
        text = re.sub(
            r"\b" + word + r"\b",
            " ",
            text
        )

    # -----------------------------------------------------
    # IMPORTANT AND/OR GROUPING FIX
    #
    # "CS 101 OR CS 124, AND MATH 231"
    # becomes:
    # "(CS 101 OR CS 124) AND MATH 231"
    #
    # "CS 101 OR EQUIVALENT AND MATH 257"
    # becomes:
    # "(CS 101 OR CONDITION_EQUIVALENT) AND MATH 257"
    # -----------------------------------------------------

    atom = r"(?:[A-Z]{2,6}\s+\d{3,4}|CONDITION_[A-Z]+)"

    alternative_chain = (
        atom
        + r"(?:\s+OR\s+"
        + atom
        + r")+"
    )

    text = re.sub(
        r"(" + alternative_chain + r")\s+AND\b",
        r"(\1) AND",
        text
    )

    # Clean repeated operators.
    text = re.sub(
        r"\bAND\s+AND\b",
        "AND",
        text
    )

    text = re.sub(
        r"\bOR\s+OR\b",
        "OR",
        text
    )

    # Remove dangling operators.
    text = re.sub(
        r"^\s*(?:AND|OR)\s+",
        "",
        text
    )

    text = re.sub(
        r"\s+(?:AND|OR)\s*$",
        "",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# =========================================================
# 7. TOKENIZER
# =========================================================

def tokenize_expression(text):
    text = preprocess_expression(text)

    if not text:
        return []

    pattern = (
        r"\bAND\b|"
        r"\bOR\b|"
        r"CONDITION_[A-Z]+|"
        r"[()]|"
        r"\b[A-Z]{2,6}\s+\d{3,4}\b"
    )

    tokens = re.findall(pattern, text)

    # Remove dangling operators after filtering out descriptive words.
    while tokens and tokens[0] in ("AND", "OR"):
        tokens.pop(0)

    while tokens and tokens[-1] in ("AND", "OR"):
        tokens.pop()

    return [
        normalize_code(token)
        if re.fullmatch(
            r"[A-Z]{2,6}\s+\d{3,4}",
            token
        )
        else token
        for token in tokens
    ]


# =========================================================
# 8. RECURSIVE DESCENT PARSER
# =========================================================

class PrerequisiteParser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current(self):
        if self.position >= len(self.tokens):
            return None

        return self.tokens[self.position]

    def consume(self):
        token = self.current()
        self.position += 1
        return token

    def parse(self):
        if not self.tokens:
            return None

        result = self.parse_or()

        if self.current() is not None:
            raise ValueError(
                "Unexpected token: " + str(self.current())
            )

        return result

    def parse_or(self):
        left = self.parse_and()

        while self.current() == "OR":
            self.consume()
            right = self.parse_and()
            left = ("OR", left, right)

        return left

    def parse_and(self):
        left = self.parse_atom()

        while self.current() == "AND":
            self.consume()
            right = self.parse_atom()
            left = ("AND", left, right)

        return left

    def parse_atom(self):
        token = self.current()

        if token is None:
            raise ValueError("Unexpected end of expression")

        if token == "(":
            self.consume()

            result = self.parse_or()

            if self.current() != ")":
                raise ValueError("Missing closing parenthesis")

            self.consume()

            return result

        if token in ("AND", "OR", ")"):
            raise ValueError("Invalid expression")

        self.consume()

        if token.startswith("CONDITION_"):
            return ("CONDITION", token, None)

        return ("COURSE", normalize_code(token))


# =========================================================
# 9. REQUIREMENT GROUPS
# =========================================================

def expression_to_groups(expression):
    if expression is None:
        return []

    operator = expression[0]

    if operator == "COURSE":
        return [[("COURSE", expression[1])]]

    if operator == "CONDITION":
        return [[
            ("CONDITION", expression[1], expression[2])
        ]]

    left = expression_to_groups(expression[1])
    right = expression_to_groups(expression[2])

    if operator == "OR":
        return left + right

    if operator == "AND":
        return [
            left_group + right_group
            for left_group, right_group in product(left, right)
        ]

    return []


def parse_requirement_groups(text):
    try:
        tokens = tokenize_expression(text)

        if not tokens:
            return [], True

        parser = PrerequisiteParser(tokens)
        expression = parser.parse()

        return expression_to_groups(expression), False

    except (ValueError, IndexError):
        return [], True


# =========================================================
# 10. PREREQUISITE EVALUATION
# =========================================================

def evaluate_prerequisites(
    completed,
    prerequisite_text,
    description=""
):
    prerequisite_text = str(prerequisite_text or "")
    description = str(description or "")

    combined_text = prerequisite_text + " " + description

    eligibility = extract_eligibility_details(combined_text)

    restrictions = eligibility["eligibility_restrictions"]
    program_restricted = eligibility["program_restricted"]

    concurrent_conditions = extract_concurrent_conditions(
        combined_text
    )

    # Explicitly stated no-prerequisite courses.
    if has_no_prerequisites(prerequisite_text):

        if program_restricted:
            status = "restricted_enrollment"

        elif restrictions or concurrent_conditions:
            status = "needs_verification"

        else:
            status = "not_applicable"

        return {
            "status": status,
            "matched_prerequisites": [],
            "missing_prerequisites": [],
            "requirement_groups": [],
            "eligibility_restrictions": restrictions,
            "restriction_type": eligibility["restriction_type"],
            "program_restricted": program_restricted,
            "concurrent_enrollment_conditions": concurrent_conditions,
            "concurrent_conditions": concurrent_conditions,
            "unresolved_conditions": bool(
                restrictions or concurrent_conditions
            ),
            "explanation": (
                "The course has no academic prerequisites, "
                "but enrollment conditions require confirmation."
                if restrictions or concurrent_conditions
                else "The course explicitly states that it has no prerequisites."
            )
        }

    # Parse academic requirements.
    groups, unresolved = parse_requirement_groups(
        prerequisite_text
    )

    if not groups:

        if program_restricted:
            status = "restricted_enrollment"
            explanation = (
                "This course is restricted to a particular academic "
                "program or curriculum."
            )

        else:
            status = "needs_verification"
            explanation = (
                "Prerequisite information is unavailable or could "
                "not be interpreted reliably."
            )

            if restrictions:
                explanation += (
                    " Student standing or eligibility conditions "
                    "must be confirmed with the institution."
                )

        return {
            "status": status,
            "matched_prerequisites": [],
            "missing_prerequisites": [],
            "requirement_groups": [],
            "eligibility_restrictions": restrictions,
            "restriction_type": eligibility["restriction_type"],
            "program_restricted": program_restricted,
            "concurrent_enrollment_conditions": concurrent_conditions,
            "concurrent_conditions": concurrent_conditions,
            "unresolved_conditions": True,
            "explanation": explanation
        }

    all_matched = []
    all_missing = []

    satisfied_alternative = False
    unknown_alternative = False

    for group in groups:

        courses = [
            item[1]
            for item in group
            if item[0] == "COURSE"
        ]

        conditions = [
            item
            for item in group
            if item[0] == "CONDITION"
        ]

        matched = [
            code
            for code in courses
            if code in completed
        ]

        missing = [
            code
            for code in courses
            if code not in completed
        ]

        all_matched.extend(matched)
        all_missing.extend(missing)

        has_unresolved_condition = bool(conditions)

        if not missing and not has_unresolved_condition:
            satisfied_alternative = True

        elif not missing and has_unresolved_condition:
            unknown_alternative = True

    # Determine academic status.
    if satisfied_alternative:

        if program_restricted:
            status = "restricted_enrollment"
            explanation = (
                "The recorded prerequisites appear satisfied, "
                "but this course is restricted to a particular "
                "academic program or curriculum."
            )

        elif restrictions or concurrent_conditions:
            status = "needs_verification"
            explanation = (
                "The recorded prerequisites appear satisfied, "
                "but additional enrollment conditions require confirmation."
            )

        else:
            status = "prerequisites_met"
            explanation = (
                "At least one complete prerequisite alternative is satisfied."
            )

        missing_output = []

    elif unknown_alternative:

        status = "needs_verification"

        explanation = (
            "Course requirements may be satisfied through an alternative "
            "that requires additional confirmation, such as instructor "
            "consent or concurrent enrollment."
        )

        missing_output = []

    elif all_missing:

        status = "missing_prerequisites"

        explanation = (
            "Some required courses are missing. "
            "Additional eligibility conditions may also require verification."
        )

        missing_output = list(dict.fromkeys(all_missing))

    else:

        status = "needs_verification"

        explanation = (
            "The prerequisite requirements need manual verification."
        )

        missing_output = []

    # Apply explicit program restrictions.
    if program_restricted:

        status = "restricted_enrollment"

        explanation = (
            "This course has an explicit restriction for a particular "
            "academic program or curriculum. Confirm eligibility "
            "with the institution."
        )

    # Conditional restrictions should not override missing academic courses.
    elif restrictions and status == "prerequisites_met":

        status = "needs_verification"

        explanation += (
            " Student standing or other eligibility conditions "
            "must be confirmed with the institution."
        )

    # Explain concurrent conditions.
    if concurrent_conditions:

        explanation += (
            " Concurrent enrollment or registration conditions detected: "
            + "; ".join(concurrent_conditions)
            + "."
        )

        if status == "prerequisites_met":
            status = "needs_verification"

    # Format requirement groups for the API.
    requirement_groups = []

    for group in groups:

        formatted_group = []

        for value in group:
            formatted_group.append(value[1])

        requirement_groups.append(formatted_group)

    return {
        "status": status,
        "matched_prerequisites": list(dict.fromkeys(all_matched)),
        "missing_prerequisites": missing_output,
        "requirement_groups": requirement_groups,
        "eligibility_restrictions": restrictions,
        "restriction_type": eligibility["restriction_type"],
        "program_restricted": program_restricted,
        "concurrent_enrollment_conditions": concurrent_conditions,
        "concurrent_conditions": concurrent_conditions,
        "unresolved_conditions": (
            unresolved
            or bool(restrictions)
            or unknown_alternative
            or bool(concurrent_conditions)
        ),
        "explanation": explanation
    }


# =========================================================
# 11. MAIN PREREQUISITE AGENT
# =========================================================

def prerequisite_agent(profile, academic_results):

    print("\n[Prerequisite Agent] Starting analysis...")

    completed = normalize_completed(profile)

    print(
        "[Prerequisite Agent] Completed courses:",
        sorted(completed)
    )

    if not isinstance(academic_results, list):
        academic_results = []

    analysis = []
    seen_courses = set()

    for course in academic_results:

        if not isinstance(course, dict):
            continue

        title = course.get("title", "Unknown")

        course_code = normalize_code(
            f"{course.get('subject', '')} "
            f"{course.get('course_number', '')}"
        )

        key = course_code or title.lower()

        if key in seen_courses:
            continue

        seen_courses.add(key)

        result = evaluate_prerequisites(
            completed,
            course.get("prerequisite_text", "Not specified"),
            course.get("description", "")
        )

        analysis.append({
            "course": title,
            "course_code": course_code,
            **result
        })

    summary = {
        "total_courses_checked": len(analysis),

        "prerequisites_met": sum(
            item["status"] == "prerequisites_met"
            for item in analysis
        ),

        "missing_prerequisites": sum(
            item["status"] == "missing_prerequisites"
            for item in analysis
        ),

        "needs_verification": sum(
            item["status"] == "needs_verification"
            for item in analysis
        ),

        "restricted_enrollment": sum(
            item["status"] == "restricted_enrollment"
            for item in analysis
        ),

        "not_applicable": sum(
            item["status"] == "not_applicable"
            for item in analysis
        )
    }

    print("[Prerequisite Agent] Summary:", summary)

    return {
        "status": "success",
        "summary": summary,
        "analysis": analysis
    }


# =========================================================
# 12. TEST CASES
# =========================================================

if __name__ == "__main__":

    completed = {"CS 225", "PYTHON"}

    test_cases = [
        (
            "CS 440",
            "CS 225; one of CS 361, STAT 361, ECE 313, "
            "MATH 362, MATH 461, MATH 463, STAT 400 or BIOE 310."
        ),
        (
            "CS 452",
            "(CS 128 or ECE 220) and CS 225 and "
            "(CS 241 or CS 341 or ECE 391)."
        ),
        (
            "ECE 549",
            "ECE 448 or CS 225."
        ),
        (
            "ABE 412",
            "CS 101 or equivalent and MATH 257."
        ),
        (
            "BIOE 210",
            "CS 101 or CS 124, and MATH 231."
        ),
        (
            "BIOE 589",
            "BIOE 588, BIOE 484, BIOE 486, BIOE 580. "
            "Concurrent enrollment in BIOE 489 is required."
        ),
        (
            "BCOG 458",
            "One of PSYC 224, PSYC 248, PHIL 202, "
            "PHIL 270, or consent of instructor."
        ),
        (
            "ABE 459",
            "Credit or concurrent registration in TAM 335."
        )
    ]

    print("\n========== COMPLEX PARSER TESTS ==========")

    for code, text in test_cases:

        result = evaluate_prerequisites(completed, text)

        print("\nCourse:", code)
        print("Text:", text)
        print("Status:", result["status"])
        print("Matched:", result["matched_prerequisites"])
        print("Missing:", result["missing_prerequisites"])
        print("Groups:", result["requirement_groups"])
        print("Restrictions:", result["eligibility_restrictions"])
        print(
            "Concurrent conditions:",
            result["concurrent_enrollment_conditions"]
        )
        print("Explanation:", result["explanation"])

    print("\n========== ELIGIBILITY TESTS ==========")

    eligibility_tests = [
        (
            "BSE 712",
            "Restricted to students enrolled at Carle Illinois College of Medicine."
        ),
        (
            "BIOE 485",
            "Restricted to senior undergraduate or graduate standing "
            "in an engineering degree program or consent of instructor."
        ),
        (
            "BIOE 488",
            "Familiarity with Python. Restricted to senior undergraduate "
            "or graduate standing in an engineering major."
        ),
        (
            "BIOE 489",
            "Restricted to senior undergraduate or graduate standing "
            "and familiarity with machine learning principles."
        ),
        (
            "BIOE 589",
            "Restricted to students enrolled in the Biomedical Image "
            "Computing MS degree program only."
        )
    ]

    for code, text in eligibility_tests:

        result = evaluate_prerequisites(set(), text)

        print("\nCourse:", code)
        print("Status:", result["status"])
        print("Restriction type:", result["restriction_type"])
        print("Program restricted:", result["program_restricted"])
        print("Restrictions:", result["eligibility_restrictions"])

    print("\n========== NO-PREREQUISITE TESTS ==========")

    no_prerequisite_tests = [
        "No prerequisites.",
        "Prerequisites: None.",
        "No prior coursework required."
    ]

    for text in no_prerequisite_tests:

        result = evaluate_prerequisites(set(), text)

        print("\nText:", text)
        print("Status:", result["status"])

    print("\n========== DUPLICATE TEXT TEST ==========")

    duplicate_text = (
        "Graduate student status or consent of instructor. "
        "Prerequisite: Graduate student status or consent of instructor."
    )

    result = evaluate_prerequisites(set(), duplicate_text)

    print("Restrictions:", result["eligibility_restrictions"])

    print("\n========== CONCURRENT REGISTRATION TEST ==========")

    result = evaluate_prerequisites(
        set(),
        "Credit or concurrent registration in TAM 335."
    )

    print("Status:", result["status"])
    print(
        "Concurrent conditions:",
        result["concurrent_enrollment_conditions"]
    )

    result = evaluate_prerequisites(
        set(),
        "Graduate standing in music; concurrent registration "
        "in Symphony Orchestra for students in the Master of Music curriculum."
    )

    print("\nMUSC 510:")
    print("Status:", result["status"])
    print(
        "Concurrent conditions:",
        result["concurrent_enrollment_conditions"]
    )