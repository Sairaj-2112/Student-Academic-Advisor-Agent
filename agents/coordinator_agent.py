
from agents.academic_agent import academic_agent
from agents.recommendation_agent import recommendation_agent

from agents.career_agent import career_agent
from agents.skill_gap_agent import skill_gap_agent
from agents.roadmap_agent import roadmap_agent
from agents.prerequisite_agent import prerequisite_agent

from agents.communication_protocol import send_agent_message

from memory.student_memory import (
    load_student,
    save_student,
    add_student_history
)


# Original coordinator - backward compatibility
def coordinator_agent(completed_subjects, interests):

    print("\n[Coordinator] Starting academic analysis...")

    if isinstance(completed_subjects, str):
        completed_subjects = [
            item.strip()
            for item in completed_subjects.split(",")
            if item.strip()
        ]

    if isinstance(interests, str):
        interests = [
            item.strip()
            for item in interests.split(",")
            if item.strip()
        ]

    if not interests:
        return {
            "academic_results": [],
            "recommendations": []
        }

    academic_results = []

    print("\n[Coordinator] Contacting Academic Agent...")

    for interest in interests:
        try:
            result = academic_agent(
                completed_subjects=completed_subjects,
                keyword=interest
            )

            if result:
                if isinstance(result, list):
                    academic_results.extend(result)
                else:
                    academic_results.append(result)

        except Exception as error:
            print(f"[Coordinator] Academic Agent error: {error}")

    print("\n[Coordinator] Contacting Recommendation Agent...")

    try:
        recommendations = recommendation_agent(interests) or []

    except Exception as error:
        print(f"[Coordinator] Recommendation Agent error: {error}")
        recommendations = []

    return {
        "academic_results": academic_results,
        "recommendations": recommendations
    }


# Universal multi-agent coordinator
def universal_coordinator_agent(profile):

    print("\n========== UNIVERSAL COORDINATOR ==========")

    if hasattr(profile, "model_dump"):
        profile = profile.model_dump()

    if not isinstance(profile, dict):
        profile = {}

    # Extract student information
    completed_subjects = (
        profile.get("completed_courses", [])
        + profile.get("subjects", [])
    )

    interests = profile.get("interests", [])
    student_name = profile.get("name", "User")

    # 1. Save student profile
    print("\n[Coordinator] Saving student profile...")

    save_student(
        name=student_name,
        completed_subjects=completed_subjects,
        interests=interests,
        skills=profile.get("skills", []),
        career_goals=profile.get("career_goals", []),
        learning_goals=profile.get("learning_goals", [])
    )

    communication_log = []

    # 2. Academic analysis
    print("\n[Coordinator] Running Academic Analysis...")

    academic_data = coordinator_agent(
        completed_subjects=completed_subjects,
        interests=interests
    )

    academic_results = academic_data["academic_results"]
    recommendations = academic_data["recommendations"]

    # 3. Prerequisite analysis
    print("\n[Coordinator] Contacting Prerequisite Agent...")

    try:
        prerequisite_result = prerequisite_agent(
            profile=profile,
            academic_results=academic_results
        )

    except Exception as error:
        print(f"[Coordinator] Prerequisite Agent error: {error}")

        prerequisite_result = {
            "status": "error",
            "summary": {},
            "analysis": [],
            "message": str(error)
        }

    print(
        "[Coordinator] Prerequisite analysis status:",
        prerequisite_result.get("status")
    )

    # 4. Academic Agent -> Career Agent
    academic_message = send_agent_message(
        sender="Academic Agent",
        receiver="Career Agent",
        task="Share academic findings",
        message="Academic analysis completed.",
        data={
            "academic_result_count": len(academic_results),
            "recommendation_count": len(recommendations)
        }
    )

    communication_log.append(academic_message)

    # 5. Prerequisite Agent -> Career Agent
    prerequisite_message = send_agent_message(
        sender="Prerequisite Agent",
        receiver="Career Agent",
        task="Share course prerequisite analysis",
        message="Preliminary course prerequisite analysis completed.",
        data={
            "status": prerequisite_result.get("status"),
            "summary": prerequisite_result.get("summary", {})
        }
    )

    communication_log.append(prerequisite_message)

    # 6. Career analysis
    print("\n[Coordinator] Contacting Career Agent...")

    # IMPORTANT:
    # Send only the original profile to avoid excessive
    # prompt size and Groq token-per-minute errors.
    career_profile = profile.copy()

    try:
        career_result = career_agent(career_profile)

    except Exception as error:
        print(f"[Coordinator] Career Agent error: {error}")

        career_result = {
            "status": "error",
            "message": str(error)
        }

    career_guidance = (
        career_result.get("career_guidance", "")
        if career_result.get("status") == "success"
        else ""
    )

    # 7. Career Agent -> Skill Gap Agent
    career_message = send_agent_message(
        sender="Career Agent",
        receiver="Skill Gap Agent",
        task="Share career analysis",
        message=(
            "Career analysis completed."
            if career_result.get("status") == "success"
            else "Career analysis failed or needs retry."
        ),
        data={
            "career_status": career_result.get("status")
        }
    )

    communication_log.append(career_message)

    # 8. Skill gap analysis
    print("\n[Coordinator] Contacting Skill Gap Agent...")

    try:
        skill_result = skill_gap_agent(
            profile=profile,
            career_target=career_guidance
        )

    except Exception as error:
        print(f"[Coordinator] Skill Gap Agent error: {error}")

        skill_result = {
            "status": "error",
            "message": str(error)
        }

    skill_analysis = (
        skill_result.get("skill_analysis", "")
        if skill_result.get("status") == "success"
        else ""
    )

    # 9. Skill Gap Agent -> Roadmap Agent
    skill_message = send_agent_message(
        sender="Skill Gap Agent",
        receiver="Roadmap Agent",
        task="Share skill gap analysis",
        message=(
            "Skill gap analysis completed."
            if skill_result.get("status") == "success"
            else "Skill gap analysis failed or needs retry."
        ),
        data={
            "skill_status": skill_result.get("status")
        }
    )

    communication_log.append(skill_message)

    # 10. Roadmap generation
    print("\n[Coordinator] Contacting Roadmap Agent...")

    try:
        roadmap_result = roadmap_agent(
            profile=profile,
            career_target=career_guidance,
            skill_analysis=skill_analysis
        )

    except Exception as error:
        print(f"[Coordinator] Roadmap Agent error: {error}")

        roadmap_result = {
            "status": "error",
            "message": str(error)
        }

    # 11. Save AI results in student history
    print("\n[Coordinator] Saving AI recommendations to memory...")

    history_details = {
        "academic_result_count": len(academic_results),
        "recommendation_count": len(recommendations),
        "prerequisite_analysis": prerequisite_result,
        "career_guidance": career_guidance,
        "skill_analysis": skill_analysis,
        "roadmap": (
            roadmap_result.get("roadmap", "")
            if roadmap_result.get("status") == "success"
            else ""
        ),
        "agent_status": {
            "prerequisite": prerequisite_result.get("status"),
            "career": career_result.get("status"),
            "skill_gap": skill_result.get("status"),
            "roadmap": roadmap_result.get("status")
        }
    }

    try:
        add_student_history(
            name=student_name,
            activity_type="multi_agent_advisor_report",
            details=history_details
        )

        print("[Coordinator] Student memory updated.")

    except Exception as error:
        print(f"[Coordinator] Memory update error: {error}")

    # 12. Final agent status
    agent_status = {
        "prerequisite": prerequisite_result.get("status"),
        "career": career_result.get("status"),
        "skill_gap": skill_result.get("status"),
        "roadmap": roadmap_result.get("status")
    }

    successful_agents = sum(
        status == "success"
        for status in agent_status.values()
    )

    print("\n========== WORKFLOW SUMMARY ==========")
    print("Successful agents:", successful_agents, "/ 4")

    for agent, status in agent_status.items():
        print(f"{agent}: {status}")

    # 13. Final report
    return {
        "profile": profile,
        "academic_results": academic_results,
        "recommendations": recommendations,
        "prerequisite_analysis": prerequisite_result,
        "career_guidance": career_result,
        "skill_analysis": skill_result,
        "roadmap": roadmap_result,
        "agent_status": agent_status,
        "communication_log": communication_log
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

        print("\n===== ACADEMIC REPORT =====")
        print("Academic results:", len(result["academic_results"]))
        print("Recommendations:", len(result["recommendations"]))
