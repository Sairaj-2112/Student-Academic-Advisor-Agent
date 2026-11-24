
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

from models.student_profile import StudentProfile

from tools.learning_progress import (
    add_learning_item,
    update_learning_status,
    get_learning_progress,
    get_progress_summary
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


app = FastAPI(
    title="Universal AI Academic & Career Advisor",
    description=(
        "AI-powered academic and career guidance using a multi-agent "
        "architecture and adaptive knowledge assessment."
    ),
    version="4.0.0"
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


# ==========================================
# REQUEST MODELS
# ==========================================

class StudentRequest(BaseModel):
    name: str = "Student"
    completed_subjects: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


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


# ==========================================
# HOME AND HEALTH
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Universal AI Academic & Career Advisor API is running!",
        "version": "4.0.0",
        "status": "active"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is working properly"
    }


# ==========================================
# BASIC ACADEMIC RECOMMENDATION
# ==========================================

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


# ==========================================
# UNIVERSAL PROFILE PREVIEW
# ==========================================

@app.post("/api/profile/preview")
def preview_profile(profile: StudentProfile):
    return {
        "status": "success",
        "profile": profile.model_dump()
    }


# ==========================================
# UNIVERSAL AI ADVISOR
# ==========================================

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


# ==========================================
# MULTI-AGENT ADVISOR
# ==========================================

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


# ==========================================
# PREREQUISITE ANALYSIS
# ==========================================

@app.post("/api/advisor/prerequisites")
def analyze_prerequisites(request: PrerequisiteRequest):
    try:
        profile = request.profile

        academic_data = coordinator_agent(
            completed_subjects=profile.completed_courses,
            interests=profile.interests
        )

        academic_results = academic_data.get("academic_results", [])

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


# ==========================================
# AI-POWERED PREREQUISITE KNOWLEDGE QUIZ
# ==========================================

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
        print(f"[Quiz Generation Error] {type(error).__name__}: {error}")
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

    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print(f"[Quiz Submission Error] {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Quiz submission failed."
        )


# ==========================================
# HUMAN FEEDBACK AND REVISION
# ==========================================

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


# ==========================================
# LEARNING PROGRESS: ADD ITEM
# ==========================================

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


# ==========================================
# LEARNING PROGRESS: UPDATE STATUS
# ==========================================

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


# ==========================================
# LEARNING PROGRESS: GET ALL ITEMS
# ==========================================

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


# ==========================================
# LEARNING PROGRESS: GET SUMMARY
# ==========================================

@app.get("/api/progress/{student_name}/summary")
def get_student_progress_summary(student_name: str):
    try:
        return get_progress_summary(student_name)

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# ==========================================
# ADAPTIVE RECOMMENDATION ENGINE
# ==========================================

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


# ==========================================
# KNOWLEDGE BASE: ADD KNOWLEDGE
# ==========================================

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


# ==========================================
# KNOWLEDGE BASE: SEARCH
# ==========================================

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


# ==========================================
# KNOWLEDGE BASE: GET ALL
# ==========================================

@app.get("/api/knowledge/all")
def get_all_knowledge_api(category: str | None = None):
    return {
        "records": get_all_knowledge(category),
        "statistics": get_knowledge_statistics()
    }


# ==========================================
# KNOWLEDGE BASE: STATISTICS
# ==========================================

@app.get("/api/knowledge/statistics")
def knowledge_statistics_api():
    return get_knowledge_statistics()


# ==========================================
# KNOWLEDGE BASE: GET ONE RECORD
# ==========================================

@app.get("/api/knowledge/{record_id}")
def get_knowledge_api(record_id: str):
    record = get_knowledge_by_id(record_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Knowledge record not found."
        )

    return record


# ==========================================
# KNOWLEDGE BASE: DELETE RECORD
# ==========================================

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
