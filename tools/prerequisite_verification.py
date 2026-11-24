
import json
import re
import uuid

from pathlib import Path
from datetime import datetime, timezone
from threading import RLock


# =========================================================
# CONFIGURATION
# =========================================================

PASS_THRESHOLD = 80

SESSIONS_FILE = Path("memory/prerequisite_verification.json")

SESSIONS = {}
LOCK = RLock()


# =========================================================
# PERSISTENCE
# =========================================================

def _load_sessions():
    if not SESSIONS_FILE.exists():
        return {}

    try:
        data = json.loads(
            SESSIONS_FILE.read_text(encoding="utf-8")
        )
        return data if isinstance(data, dict) else {}

    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(
            "Could not read prerequisite verification history."
        ) from error


def _save_sessions():
    SESSIONS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = SESSIONS_FILE.with_suffix(".tmp")

    temporary_file.write_text(
        json.dumps(
            SESSIONS,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    temporary_file.replace(SESSIONS_FILE)


SESSIONS = _load_sessions()


# =========================================================
# UTILITIES
# =========================================================

def _now():
    return datetime.now(timezone.utc).isoformat()


def _clean_code(value):
    if not value:
        return ""

    value = str(value).upper().strip()
    value = re.sub(r"\s+", " ", value)

    if value.startswith("CONDITION_"):
        return ""

    return value


def _get_groups(requirement_groups):
    """
    Inner lists mean AND.
    Separate lists mean OR.

    Example:
    [["CS101", "MATH101"], ["CS102"]]

    Means:
    (CS101 AND MATH101) OR CS102
    """

    if not isinstance(requirement_groups, list):
        return []

    groups = []

    for group in requirement_groups:
        if isinstance(group, str):
            values = [group]
        elif isinstance(group, (list, tuple, set)):
            values = list(group)
        else:
            continue

        cleaned = []

        for value in values:
            code = _clean_code(value)

            if code and code not in cleaned:
                cleaned.append(code)

        if cleaned:
            groups.append(cleaned)

    return groups


def _build_prerequisite_records(groups):
    records = {}

    for group in groups:
        for code in group:
            if code not in records:
                records[code] = {
                    "course_code": code,
                    "status": "not_started",
                    "latest_score": None,
                    "best_score": None,
                    "attempt_count": 0,
                    "attempts": [],
                    "weak_topics": [],
                    "last_assessed_at": None
                }

    return records


def _copy_data(data):
    return json.loads(
        json.dumps(data, ensure_ascii=False)
    )


# =========================================================
# READINESS REPORT GENERATOR
# =========================================================

def _build_readiness_report(session):
    prerequisites = session.get("prerequisites", {})
    groups = session.get("requirement_groups", [])

    prerequisite_details = []
    practice_recommendations = []

    for code, record in prerequisites.items():

        score = record.get("latest_score")
        best_score = record.get("best_score")
        status = record.get("status", "not_started")

        if status == "passed":
            decision = "passed"
        elif status == "needs_practice":
            decision = "needs_practice"
        else:
            decision = "not_started"

        prerequisite_details.append({
            "course_code": code,
            "status": decision,
            "latest_score": score,
            "best_score": best_score,
            "attempt_count": record.get("attempt_count", 0),
            "weak_topics": record.get("weak_topics", []),
            "last_assessed_at": record.get("last_assessed_at")
        })

        if decision == "not_started":
            practice_recommendations.append({
                "prerequisite_code": code,
                "priority": "high",
                "recommendation": (
                    f"Complete the prerequisite quiz for {code}."
                )
            })

        elif decision == "needs_practice":
            weak_topics = record.get("weak_topics", [])

            if weak_topics:
                recommendation = (
                    "Revise these weak topics: "
                    + ", ".join(weak_topics)
                    + ". Then attempt the quiz again."
                )
            else:
                recommendation = (
                    "Revise the prerequisite material and retake the quiz."
                )

            practice_recommendations.append({
                "prerequisite_code": code,
                "priority": "high",
                "recommendation": recommendation
            })

    # Evaluate each AND/OR prerequisite group.
    group_results = []

    for index, group in enumerate(groups):

        passed_codes = [
            code for code in group
            if prerequisites.get(code, {}).get("status") == "passed"
        ]

        missing_codes = [
            code for code in group
            if prerequisites.get(code, {}).get("status") != "passed"
        ]

        group_passed = len(missing_codes) == 0

        group_percentage = (
            round(len(passed_codes) / len(group) * 100, 2)
            if group else 0
        )

        group_results.append({
            "group_number": index + 1,
            "prerequisites": group,
            "passed_prerequisites": passed_codes,
            "remaining_prerequisites": missing_codes,
            "completed_count": len(passed_codes),
            "total_count": len(group),
            "completion_percentage": group_percentage,
            "status": "passed" if group_passed else "incomplete",
            "passed": group_passed
        })

    # A student needs to complete only one alternative group.
    ready_groups = [
        group for group in group_results
        if group["passed"]
    ]

    overall_ready = len(ready_groups) > 0

    if overall_ready:
        overall_status = "ready"
        final_decision = "Prerequisite requirements satisfied."
        explanation = (
            "The student has successfully passed at least one "
            "complete prerequisite group."
        )

    else:
        any_passed = any(
            item["status"] == "passed"
            for item in prerequisite_details
        )

        if any_passed:
            overall_status = "partially_ready"
            final_decision = "More preparation required."
            explanation = (
                "Some prerequisites have been passed, but no complete "
                "prerequisite group has been satisfied."
            )
        else:
            overall_status = "not_ready"
            final_decision = "Prerequisite requirements not yet satisfied."
            explanation = (
                "The student has not completed a full prerequisite group."
            )

    total = len(prerequisites)

    passed = sum(
        1 for item in prerequisite_details
        if item["status"] == "passed"
    )

    assessed = sum(
        1 for item in prerequisite_details
        if item["latest_score"] is not None
    )

    # Group completion is more meaningful when OR alternatives exist.
    overall_progress = max(
        (
            item["completion_percentage"]
            for item in group_results
        ),
        default=0
    )

    return {
        "student_name": session.get("student_name"),
        "target_course_code": session.get("target_course_code"),
        "target_course_title": session.get("target_course_title"),
        "session_id": session.get("session_id"),
        "generated_at": _now(),
        "pass_threshold": PASS_THRESHOLD,
        "overall_status": overall_status,
        "final_decision": final_decision,
        "explanation": explanation,
        "assessment_ready": overall_ready,
        "total_prerequisites": total,
        "assessed_prerequisites": assessed,
        "passed_prerequisites": passed,
        "remaining_prerequisites": total - passed,
        "overall_progress_percentage": overall_progress,
        "prerequisite_details": prerequisite_details,
        "group_results": group_results,
        "practice_recommendations": practice_recommendations,
        "ready_groups": [
            item["group_number"] for item in ready_groups
        ]
    }


# =========================================================
# START VERIFICATION
# =========================================================

def start_verification(
    student_name,
    target_course_code,
    target_course_title,
    requirement_groups
):

    student_name = str(student_name or "").strip()
    target_course_code = _clean_code(target_course_code)
    target_course_title = str(target_course_title or "").strip()

    groups = _get_groups(requirement_groups)

    if not student_name:
        raise ValueError("Student name is required.")

    if not target_course_code:
        raise ValueError("Target course code is required.")

    if not groups:
        raise ValueError(
            "No valid prerequisite groups were provided."
        )

    session_id = str(uuid.uuid4())

    session = {
        "session_id": session_id,
        "student_name": student_name,
        "target_course_code": target_course_code,
        "target_course_title": target_course_title,
        "requirement_groups": groups,
        "prerequisites": _build_prerequisite_records(groups),
        "created_at": _now(),
        "updated_at": _now()
    }

    with LOCK:
        SESSIONS[session_id] = session

        session["readiness_report"] = (
            _build_readiness_report(session)
        )

        _save_sessions()

    return get_verification(session_id)


# =========================================================
# GET VERIFICATION STATUS
# =========================================================

def get_verification(session_id):

    with LOCK:
        if session_id not in SESSIONS:
            raise KeyError("Verification session not found.")

        session = _copy_data(SESSIONS[session_id])

    report = _build_readiness_report(session)

    session["readiness_report"] = report
    session["group_results"] = report["group_results"]
    session["overall_status"] = report["overall_status"]
    session["assessment_ready"] = report["assessment_ready"]
    session["total_prerequisites"] = report["total_prerequisites"]
    session["passed_prerequisites"] = report["passed_prerequisites"]
    session["remaining_prerequisites"] = report["remaining_prerequisites"]

    return session


# =========================================================
# GET ONE PREREQUISITE
# =========================================================

def get_prerequisite(session_id, prerequisite_code):

    prerequisite_code = _clean_code(prerequisite_code)

    verification = get_verification(session_id)
    prerequisites = verification["prerequisites"]

    if prerequisite_code not in prerequisites:
        raise KeyError(
            f"{prerequisite_code} is not part of this verification."
        )

    return prerequisites[prerequisite_code]


# =========================================================
# RECORD QUIZ RESULT
# =========================================================

def record_quiz_result(
    session_id,
    prerequisite_code,
    quiz_result
):

    prerequisite_code = _clean_code(prerequisite_code)

    if not isinstance(quiz_result, dict):
        raise ValueError("Quiz result must be a dictionary.")

    try:
        score = float(quiz_result.get("percentage"))
    except (TypeError, ValueError):
        raise ValueError(
            "Quiz result does not contain a valid percentage."
        )

    if score < 0 or score > 100:
        raise ValueError(
            "Quiz percentage must be between 0 and 100."
        )

    assessed_at = _now()
    passed = score >= PASS_THRESHOLD

    topic_analysis = quiz_result.get("topic_analysis", [])
    weak_topics = []

    if isinstance(topic_analysis, list):
        for topic in topic_analysis:

            if not isinstance(topic, dict):
                continue

            try:
                topic_score = float(topic.get("percentage", 0))
            except (TypeError, ValueError):
                continue

            if topic_score < PASS_THRESHOLD:
                weak_topics.append(
                    topic.get("topic", "Unknown")
                )

    with LOCK:

        if session_id not in SESSIONS:
            raise KeyError("Verification session not found.")

        session = SESSIONS[session_id]
        prerequisites = session["prerequisites"]

        if prerequisite_code not in prerequisites:
            raise KeyError(
                f"{prerequisite_code} is not part of this verification."
            )

        record = prerequisites[prerequisite_code]

        previous_best = record.get("best_score")

        record["latest_score"] = score

        if previous_best is None:
            record["best_score"] = score
        else:
            record["best_score"] = max(
                float(previous_best),
                score
            )

        record["attempt_count"] += 1

        record["status"] = (
            "passed" if passed else "needs_practice"
        )

        record["weak_topics"] = weak_topics
        record["last_assessed_at"] = assessed_at

        record["attempts"].append({
            "attempt_number": record["attempt_count"],
            "score": score,
            "passed": passed,
            "assessed_at": assessed_at,
            "weak_topics": weak_topics
        })

        session["updated_at"] = assessed_at

        # Save the newly generated readiness report.
        session["readiness_report"] = (
            _build_readiness_report(session)
        )

        _save_sessions()

    return get_verification(session_id)


# =========================================================
# GET FINAL READINESS REPORT
# =========================================================

def get_readiness_report(session_id):

    verification = get_verification(session_id)

    return verification["readiness_report"]


# =========================================================
# LIST ALL VERIFICATION SESSIONS
# =========================================================

def list_sessions():

    with LOCK:
        sessions = _copy_data(SESSIONS)

    results = []

    for session_id, session in sessions.items():

        report = _build_readiness_report(session)

        results.append({
            "session_id": session_id,
            "student_name": session.get("student_name"),
            "target_course_code": session.get("target_course_code"),
            "target_course_title": session.get("target_course_title"),
            "total_prerequisites": report["total_prerequisites"],
            "passed_prerequisites": report["passed_prerequisites"],
            "remaining_prerequisites": report["remaining_prerequisites"],
            "overall_status": report["overall_status"],
            "assessment_ready": report["assessment_ready"],
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at")
        })

    return results
