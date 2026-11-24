
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.coordinator_agent import (
    coordinator_agent,
    universal_coordinator_agent
)
from agents.universal_advisor_agent import universal_advisor_agent
from agents.feedback_agent import feedback_agent
from agents.adaptive_recommendation_agent import (
    adaptive_recommendation_agent
)
from agents.prerequisite_agent import prerequisite_agent
from agents.career_agent import career_agent

from models.student_profile import StudentProfile

from tools.learning_progress import (
    add_learning_item,
    update_learning_status,
    get_learning_progress,
    get_progress_summary,
    record_assessment,
    get_assessment_history,
    get_assessment_summary
)

from tools.knowledge_base import (
    add_knowledge,
    search_knowledge,
    get_all_knowledge,
    get_knowledge_by_id,
    delete_knowledge,
    get_knowledge_statistics
)

from tools.quiz_engine import (
    generate_quiz,
    submit_quiz,
    QuizGenerationError
)

from tools.prerequisite_verification import (
    start_verification,
    get_verification,
    get_prerequisite,
    record_quiz_result,
    get_readiness_report
)


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="Universal AI Academic & Career Advisor",
    description=(
        "AI-powered academic and career guidance using a multi-agent "
        "architecture, persistent quiz history, and adaptive "
        "prerequisite knowledge assessment."
    ),
    version="7.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# REQUEST MODELS
# =========================================================

class StudentRequest(BaseModel):
    name: str = "Student"
    completed_subjects: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


class CareerRequest(BaseModel):
    profile: dict = Field(default_factory=dict)

class FeedbackRevisionRequest(BaseModel):
    student_name: str
    original_recommendation: str


class LearningItemRequest(BaseModel):
    student_name: str
    item_name: str
    item_type: str
    notes: str = ""


class LearningStatusRequest(BaseModel):
    student_name: str
    item_id: str
    new_status: str
    notes: str | None = None


class AdaptiveRecommendationRequest(BaseModel):
    student_name: str
    profile: dict = Field(default_factory=dict)


class KnowledgeRequest(BaseModel):
    category: str
    title: str
    description: str
    institution: str = ""
    education_level: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    related_skills: list[str] = Field(default_factory=list)
    source_name: str = ""
    source_url: str = ""


class PrerequisiteRequest(BaseModel):
    profile: StudentProfile
    academic_results: list[dict] = Field(default_factory=list)


class QuizGenerateRequest(BaseModel):
    student_name: str = "Student"
    subject: str = Field(min_length=1, max_length=120)
    course_description: str = Field(default="", max_length=3000)
    topics: list[str] = Field(default_factory=list)
    question_count: int = Field(default=10, ge=5, le=15)


class QuizSubmitRequest(BaseModel):
    attempt_id: str = Field(min_length=1, max_length=100)
    student_name: str | None = None
    answers: dict[str, str] = Field(default_factory=dict)


# =========================================================
# PREREQUISITE VERIFICATION REQUEST MODELS
# =========================================================

class VerificationStartRequest(BaseModel):
    student_name: str
    target_course_code: str = ""
    target_course_title: str = ""
    requirement_groups: list[list[str]] = Field(
        default_factory=list
    )


class VerificationQuizRequest(BaseModel):
    session_id: str
    prerequisite_code: str
    question_count: int = Field(default=5, ge=5, le=15)


class VerificationSubmitRequest(BaseModel):
    session_id: str
    prerequisite_code: str
    attempt_id: str
    answers: dict[str, str] = Field(default_factory=dict)
    student_name: str | None = None


# =========================================================
# HOME AND HEALTH
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Universal AI Academic & Career Advisor API is running!",
        "version": "7.0.0",
        "status": "active"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is working properly"
    }


# =========================================================
# CAREER ADVISOR

@app.post("/api/career")
def get_career_guidance(request: CareerRequest):
    try:
        result = career_agent(request.profile)

        if result.get("status") != "success":
            raise HTTPException(
                status_code=502,
                detail=result.get(
                    "message",
                    "Career guidance generation failed."
                )
            )

        return result

    except HTTPException:
        raise
    except Exception as error:
        print("[Career Agent Error]", error)
        raise HTTPException(
            status_code=500,
            detail="Could not generate career guidance."
        )

# BASIC ACADEMIC RECOMMENDATION
# =========================================================

@app.post("/api/advisor/recommend")
def get_recommendations(request: StudentRequest):
    try:
        result = coordinator_agent(
            completed_subjects=request.completed_subjects,
            interests=request.interests
        )

        return {
            "student_name": request.name,
            "status": "success",
            "result": result
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# UNIVERSAL PROFILE PREVIEW
# =========================================================

@app.post("/api/profile/preview")
def preview_profile(profile: StudentProfile):
    return {
        "status": "success",
        "profile": profile.model_dump()
    }


# =========================================================
# UNIVERSAL AI ADVISOR
# =========================================================

@app.post("/api/advisor/universal")
def universal_advisor(profile: StudentProfile):
    try:
        result = universal_advisor_agent(profile)

        return {
            "status": "success",
            "student_name": profile.name,
            "advice": result
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# MULTI-AGENT ADVISOR
# =========================================================

@app.post("/api/advisor/multi-agent")
def multi_agent_advisor(profile: StudentProfile):
    try:
        result = universal_coordinator_agent(profile)

        return {
            "status": "success",
            "student_name": profile.name,
            "result": result
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# PREREQUISITE ANALYSIS
# =========================================================

@app.post("/api/advisor/prerequisites")
def analyze_prerequisites(request: PrerequisiteRequest):
    try:
        profile = request.profile

        academic_data = coordinator_agent(
            completed_subjects=profile.completed_courses,
            interests=profile.interests
        )

        academic_results = academic_data.get(
            "academic_results", []
        )

        result = prerequisite_agent(
            profile=profile,
            academic_results=academic_results
        )

        return {
            "status": "success",
            "student_name": profile.name,
            "academic_results_count": len(academic_results),
            "recommendations_count": len(
                academic_data.get("recommendations", [])
            ),
            "result": result
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# STANDALONE AI KNOWLEDGE QUIZ
# =========================================================

@app.post("/api/quiz/generate")
def create_quiz(request: QuizGenerateRequest):
    try:
        result = generate_quiz(
            student_name=request.student_name,
            subject=request.subject,
            course_description=request.course_description,
            topics=request.topics,
            question_count=request.question_count
        )

        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except QuizGenerationError as error:
        raise HTTPException(status_code=503, detail=str(error))

    except Exception as error:
        print(
            f"[Quiz Generation Error] "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Quiz generation failed. Please try again."
        )


@app.post("/api/quiz/submit")
def evaluate_quiz(request: QuizSubmitRequest):
    try:
        result = submit_quiz(
            attempt_id=request.attempt_id,
            answers=request.answers,
            student_name=request.student_name
        )

        return result

    except QuizGenerationError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print(
            f"[Quiz Submission Error] "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Quiz submission failed."
        )


# =========================================================
# COURSE-SPECIFIC PREREQUISITE VERIFICATION
# =========================================================

@app.post("/api/prerequisite-verification/start")
def start_prerequisite_verification(
    request: VerificationStartRequest
):
    try:
        result = start_verification(
            student_name=request.student_name,
            target_course_code=request.target_course_code,
            target_course_title=request.target_course_title,
            requirement_groups=request.requirement_groups
        )

        return {
            "status": "success",
            "message": "Prerequisite verification started.",
            "verification": result
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print("[Verification Start Error]", error)

        raise HTTPException(
            status_code=500,
            detail="Could not start prerequisite verification."
        )


# =========================================================
# GET PREREQUISITE VERIFICATION
# =========================================================

@app.get("/api/prerequisite-verification/{session_id}")
def get_prerequisite_verification(session_id: str):
    try:
        return get_verification(session_id)

    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except Exception as error:
        print("[Verification Retrieval Error]", error)

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve verification results."
        )


# =========================================================
# FINAL PREREQUISITE READINESS REPORT
# =========================================================

@app.get("/api/prerequisite-verification/{session_id}/report")
def get_final_readiness_report(session_id: str):
    try:
        report = get_readiness_report(session_id)

        return {
            "status": "success",
            "message": "Final prerequisite readiness report generated.",
            "report": report
        }

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        print("[Readiness Report Error]", error)

        raise HTTPException(
            status_code=500,
            detail="Could not generate readiness report."
        )


# =========================================================
# GENERATE PREREQUISITE QUIZ
# =========================================================

@app.post("/api/prerequisite-verification/quiz")
def generate_prerequisite_quiz(
    request: VerificationQuizRequest
):
    try:
        verification = get_verification(
            request.session_id
        )

        prerequisite = get_prerequisite(
            request.session_id,
            request.prerequisite_code
        )

        if prerequisite["status"] == "passed":
            raise HTTPException(
                status_code=400,
                detail="This prerequisite has already passed."
            )

        result = generate_quiz(
            student_name=verification["student_name"],
            subject=request.prerequisite_code,
            course_description=(
                "Assess the student's knowledge of prerequisite course "
                f"{request.prerequisite_code}. Cover fundamental concepts, "
                "applications, and problem-solving."
            ),
            topics=[],
            question_count=request.question_count
        )

        return {
            "status": "success",
            "session_id": request.session_id,
            "prerequisite_code": request.prerequisite_code,
            "quiz": result
        }

    except HTTPException:
        raise

    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except QuizGenerationError as error:
        raise HTTPException(status_code=503, detail=str(error))

    except Exception as error:
        print("[Prerequisite Quiz Error]", error)

        raise HTTPException(
            status_code=500,
            detail="Could not generate the prerequisite quiz."
        )


# =========================================================
# SUBMIT PREREQUISITE QUIZ
# =========================================================

@app.post("/api/prerequisite-verification/submit")
def submit_prerequisite_quiz(
    request: VerificationSubmitRequest
):
    try:
        verification_before = get_verification(
            request.session_id
        )

        get_prerequisite(
            request.session_id,
            request.prerequisite_code
        )

        quiz_result = submit_quiz(
            attempt_id=request.attempt_id,
            answers=request.answers,
            student_name=request.student_name,
            persist_history=False
        )

        record_assessment(
            student_name=verification_before["student_name"],
            subject=request.prerequisite_code,
            quiz_result=quiz_result,
            assessment_type="prerequisite",
            metadata={
                "session_id": request.session_id,
                "target_course_code": (
                    verification_before["target_course_code"]
                ),
                "target_course_title": (
                    verification_before["target_course_title"]
                ),
                "prerequisite_code": request.prerequisite_code
            }
        )

        verification = record_quiz_result(
            session_id=request.session_id,
            prerequisite_code=request.prerequisite_code,
            quiz_result=quiz_result
        )

        percentage = float(
            quiz_result.get("percentage", 0)
        )

        return {
            "status": "success",
            "quiz_result": quiz_result,
            "verification": verification,
            "readiness_report": verification.get(
                "readiness_report"
            ),
            "message": (
                "Prerequisite passed."
                if percentage >= 80
                else "More practice is recommended."
            )
        }

    except HTTPException:
        raise

    except QuizGenerationError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print("[Prerequisite Submission Error]", error)

        raise HTTPException(
            status_code=500,
            detail="Could not evaluate prerequisite quiz."
        )


# =========================================================
# ASSESSMENT HISTORY
# =========================================================

@app.get("/api/assessments/{student_name}/summary")
def get_student_assessment_summary(student_name: str):
    try:
        return {
            "student_name": student_name,
            "summary": get_assessment_summary(student_name)
        }

    except Exception as error:
        print("[Assessment Summary Error]", error)
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve assessment summary."
        )


@app.get("/api/assessments/{student_name}")
def get_student_assessments(student_name: str):
    try:
        return {
            "student_name": student_name,
            "assessments": get_assessment_history(student_name),
            "summary": get_assessment_summary(student_name)
        }

    except Exception as error:
        print("[Assessment History Error]", error)
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve assessment history."
        )


# =========================================================
# HUMAN FEEDBACK AND REVISION
# =========================================================

@app.post("/api/advisor/revise")
def revise_recommendation(request: FeedbackRevisionRequest):
    try:
        result = feedback_agent(
            student_name=request.student_name,
            original_recommendation=request.original_recommendation
        )

        return {
            "status": "success",
            "student_name": request.student_name,
            "revised_recommendation": result
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# LEARNING PROGRESS: ADD ITEM
# =========================================================

@app.post("/api/progress/add")
def add_progress_item(request: LearningItemRequest):
    try:
        item = add_learning_item(
            student_name=request.student_name,
            item_name=request.item_name,
            item_type=request.item_type,
            notes=request.notes
        )

        return {
            "status": "success",
            "message": "Learning item added successfully!",
            "item": item
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# LEARNING PROGRESS: UPDATE STATUS
# =========================================================

@app.put("/api/progress/update")
def update_progress_item(request: LearningStatusRequest):
    try:
        updated = update_learning_status(
            student_name=request.student_name,
            item_id=request.item_id,
            new_status=request.new_status,
            notes=request.notes
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Student or learning item not found."
            )

        return {
            "status": "success",
            "message": "Learning progress updated successfully!"
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# LEARNING PROGRESS: GET ALL ITEMS
# =========================================================

@app.get("/api/progress/{student_name}")
def get_student_progress(student_name: str):
    try:
        return {
            "student_name": student_name,
            "items": get_learning_progress(student_name),
            "summary": get_progress_summary(student_name)
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# LEARNING PROGRESS: GET SUMMARY
# =========================================================

@app.get("/api/progress/{student_name}/summary")
def get_student_progress_summary(student_name: str):
    try:
        return get_progress_summary(student_name)

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# ADAPTIVE RECOMMENDATION ENGINE
# =========================================================

@app.post("/api/advisor/adaptive")
def get_adaptive_recommendations(
    request: AdaptiveRecommendationRequest
):
    try:
        result = adaptive_recommendation_agent(
            student_name=request.student_name,
            profile=request.profile
        )

        return {
            "status": "success",
            "student_name": request.student_name,
            "result": result
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# KNOWLEDGE BASE: ADD KNOWLEDGE
# =========================================================

@app.post("/api/knowledge/add")
def create_knowledge(request: KnowledgeRequest):
    try:
        record = add_knowledge(
            category=request.category,
            title=request.title,
            description=request.description,
            institution=request.institution,
            education_level=request.education_level,
            prerequisites=request.prerequisites,
            related_skills=request.related_skills,
            source_name=request.source_name,
            source_url=request.source_url
        )

        return {
            "status": "success",
            "message": "Knowledge added successfully!",
            "record": record
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# KNOWLEDGE BASE: SEARCH
# =========================================================

@app.get("/api/knowledge/search")
def search_knowledge_api(
    query: str,
    category: str | None = None
):
    try:
        return {
            "query": query,
            "results": search_knowledge(query, category)
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# =========================================================
# KNOWLEDGE BASE: GET ALL
# =========================================================

@app.get("/api/knowledge/all")
def get_all_knowledge_api(category: str | None = None):
    return {
        "records": get_all_knowledge(category),
        "statistics": get_knowledge_statistics()
    }


# =========================================================
# KNOWLEDGE BASE: STATISTICS
# =========================================================

@app.get("/api/knowledge/statistics")
def knowledge_statistics_api():
    return get_knowledge_statistics()


# =========================================================
# KNOWLEDGE BASE: GET ONE RECORD
# =========================================================

@app.get("/api/knowledge/{record_id}")
def get_knowledge_api(record_id: str):
    record = get_knowledge_by_id(record_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found."
        )

    return record


# =========================================================
# KNOWLEDGE BASE: DELETE RECORD
# =========================================================

@app.delete("/api/knowledge/{record_id}")
def delete_knowledge_api(record_id: str):
    deleted = delete_knowledge(record_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found."
        )

    return {
        "status": "success",
        "message": "Knowledge deleted successfully!"
    }

