# Student Academic Advisor - Project Report

**Project:** Student Academic Advisor — Agentic AI: Advanced Implementation  
**Subject:** Agentic AI  
**Professor:** Dr. Swapnali Karmore  
**Report date:** 24 November 2026

## Team

| Name | Roll No. |
|---|---:|
| Apoorva Shetty | 11 |
| Disharth Patel | 29 |
| Sairaj Patil | 44 |
| Shloka Pai | 47 |

## 1. Project Overview

The Student Academic Advisor is an AI-assisted academic and career guidance system. It combines a course catalogue, a multi-agent Python backend, a Groq language model, persistent student memory, prerequisite verification, generated assessments, learning-progress tracking, and a React web interface.

The project has two related implementations:

- A legacy Gradio interface for direct course exploration and academic advice.
- A newer React and FastAPI application that provides authentication, dashboard navigation, academic recommendations, prerequisite verification, quizzes, career guidance, and progress tracking.

The primary objective is to produce guidance that is personalized, explainable, and grounded in available project data rather than presenting unsupported university or career claims.

## 2. Problem Statement

Students often need help answering questions such as:

- Which courses match completed subjects and personal interests?
- Is a student prepared for a target course?
- What skills are missing for a career goal?
- Which learning activity should be attempted next?
- How can a course recommendation be revised using feedback and progress?

Traditional search tools require students to interpret catalogue rules and compare their own profile manually. This project addresses the problem through coordinated agents and a single web workspace.

## 3. Scope

### Implemented features

- Student login and registration through browser local storage
- Academic course search and recommendation
- Multi-agent academic and career analysis
- Universal student, graduate, and professional profiling
- Course prerequisite parsing and evaluation
- Interactive prerequisite readiness verification
- Generated subject quizzes and prerequisite quizzes
- Student learning-progress tracking
- Assessment-history summaries
- Career guidance and skill-gap analysis
- Adaptive recommendations based on profile, progress, and feedback
- Knowledge-base search and management
- Feedback collection and recommendation revision
- Persistent JSON memory
- REST API with health and operational endpoints

### External boundaries

- The project does not guarantee admission, employment, scholarship eligibility, or course success.
- AI outputs are advisory and may require verification against official institutional sources.
- Authentication is currently browser-based demo storage and is not a production identity system.
- Persistent storage uses JSON files rather than a database.

## 4. System Architecture

```text
React + Vite Frontend
        |
        | HTTP / JSON
        v
FastAPI REST API
        |
        +--> Coordinator Agent
        |      +--> Academic Agent
        |      +--> Recommendation Agent
        |      +--> Prerequisite Agent
        |
        +--> Career Agent
        +--> Skill Gap Agent
        +--> Roadmap Agent
        +--> Universal Advisor Agent
        +--> Adaptive Recommendation Agent
        +--> Feedback Agent
        |
        +--> Groq LLM
        |
        +--> Catalogue, Knowledge, Memory,
             Quiz, and Progress Tools
```

The FastAPI application acts as the integration layer. The React client sends profile and request data to API endpoints, while specialized Python agents perform domain analysis and call the Groq model where natural-language generation is required.

## 5. Technology Stack

| Area | Technology |
|---|---|
| Frontend | React 19, Vite 8, React Markdown |
| Backend | Python, FastAPI |
| Request validation | Pydantic |
| AI model integration | Groq API |
| Source model | openai/gpt-oss-20b |
| HTTP communication | Fetch API and REST |
| Memory | JSON files under `memory/` |
| Legacy interface | Gradio |
| Data | JSON course and knowledge datasets |
| Development platform | Windows, local development server |

## 6. Core Modules

### 6.1 Frontend

The React application provides:

- Login and registration
- Dashboard
- Academic advisor workspace
- Prerequisite verification workspace
- AI assessments
- Career advisor
- Profile and progress view

The main workspace is implemented in `frontend/src/AdvisorWorkspace.jsx`. API calls use `http://127.0.0.1:8000` and handle loading, validation, and error states.

### 6.2 FastAPI application

`api.py` exposes endpoints for:

- Health checks
- Career guidance
- Academic recommendations
- Universal and multi-agent advice
- Prerequisite analysis
- Quiz generation and submission
- Prerequisite-verification sessions
- Learning progress
- Assessment history
- Recommendation revision
- Adaptive recommendations
- Knowledge-base operations

The application uses CORS configuration for local React origins and Pydantic request models for input validation.

### 6.3 Multi-agent orchestration

The coordinator:

1. Saves or updates the student profile.
2. Runs academic analysis.
3. Identifies matching courses.
4. Performs prerequisite analysis.
5. Transfers findings between agent roles using a communication protocol.
6. Generates career guidance.
7. Calculates skill gaps.
8. Creates a learning roadmap.
9. Combines outputs into a final result.

The system separates academic analysis, career planning, skill-gap detection, prerequisite checking, recommendation, feedback, and universal advising into specialized modules.

### 6.4 Course catalogue

The course catalogue tool loads course data, normalizes text, expands keywords, and searches matching courses. Recommendations are based on interests and completed subjects rather than guessed eligibility.

### 6.5 Prerequisite verification

The prerequisite module performs:

- Requirement parsing
- AND/OR requirement-group creation
- Completed-course comparison
- Prerequisite quiz sessions
- Readiness reporting
- Quiz-based verification of prerequisite knowledge

This is more advanced than simple course-name matching because prerequisite expressions are converted into requirement groups that can be evaluated and assessed.

### 6.6 Quiz engine

The quiz engine:

- Generates 5 to 15 questions
- Supports multiple-choice-style JSON responses
- Validates generated question structure
- Stores attempts
- Records submitted answers
- Produces a score and answer review

The prerequisite verification flow also uses subject-specific quizzes tied to individual requirements.

### 6.7 Learning progress

Learning items can be added, updated, and summarized. Assessment results can be stored with:

- Score
- Maximum score
- Percentage
- Assessment type
- Notes

The progress tool returns summaries that can then be used by the adaptive recommendation agent.

### 6.8 Memory and feedback

JSON-based student memory stores:

- Completed subjects
- Interests
- Skills
- Career goals
- Learning goals
- Activity history
- Last update time

Feedback records can be associated with a student and used to revise or adapt recommendations.

## 7. Agent Roles

| Agent | Responsibility |
|---|---|
| Coordinator | Orchestrates profile, academic, prerequisite, career, skill, and roadmap steps |
| Academic Agent | Uses catalogue data and student interests for academic analysis |
| Recommendation Agent | Generates matching course recommendations |
| Prerequisite Agent | Evaluates eligibility information and requirement groups |
| Career Agent | Generates career paths and career guidance |
| Skill Gap Agent | Identifies missing skills relative to career targets |
| Roadmap Agent | Organizes learning activities into a practical sequence |
| Universal Advisor Agent | Advises users across education and career stages |
| Adaptive Recommendation Agent | Updates recommendations using progress and feedback |
| Feedback Agent | Revises recommendations based on user feedback |

## 8. Key Workflow

### Academic recommendation workflow

1. The student enters completed subjects and interests.
2. The frontend requests basic academic recommendations.
3. The coordinator invokes the academic and recommendation agents.
4. The course catalogue searches matching data.
5. The prerequisite agent evaluates requirement information.
6. The frontend displays course matches and prerequisite status.

### Prerequisite verification workflow

1. The student selects a target course.
2. The system extracts prerequisite requirement groups.
3. A verification session is created.
4. The student takes quizzes for prerequisite courses or topics.
5. Results are recorded against the session.
6. The readiness report indicates readiness, partial readiness, or missing verification.

### Adaptive workflow

1. The system loads the student's profile.
2. It retrieves learning-progress records.
3. It retrieves prior feedback.
4. The adaptive agent creates prioritized recommendations.
5. The UI presents the next learning actions and explains how previous feedback affected the result.

## 9. API Summary

Important endpoint groups include:

| Group | Example endpoints |
|---|---|
| Health | `/api/health` |
| Academic | `/api/advisor/recommend`, `/api/advisor/universal`, `/api/advisor/multi-agent` |
| Prerequisites | `/api/advisor/prerequisites`, `/api/prerequisite-verification/start` |
| Quizzes | `/api/quiz/generate`, `/api/quiz/submit` |
| Career | `/api/career` |
| Progress | `/api/progress/add`, `/api/progress/update`, `/api/progress/{student_name}` |
| Assessment | `/api/assessments/{student_name}/summary` |
| Knowledge | `/api/knowledge/add`, `/api/knowledge/search`, `/api/knowledge/statistics` |
| Feedback | `/api/advisor/revise`, `/api/advisor/adaptive` |

## 10. Data and Storage

The project stores data in JSON files for:

- Student profiles
- Learning progress
- Quiz attempts
- Prerequisite verification sessions
- Student feedback
- Knowledge records

Example storage files include:

- `memory/student_data.json`
- `memory/learning_progress.json`
- `memory/quiz_attempts.json`
- `memory/prerequisite_verification.json`
- `memory/student_feedback.json`
- `data/knowledge_base.json`

JSON storage is suitable for a prototype but may become inconsistent or inefficient as concurrent users, data volume, and deployment requirements increase.

## 11. Security and Reliability Considerations

The current implementation includes input validation, CORS controls, API error handling, and checks for missing Groq configuration. However, further work is needed for a production-ready deployment:

- Replace local-storage authentication with secure server-side authentication.
- Hash passwords and use secure session or token management.
- Move JSON storage to a relational or document database.
- Restrict CORS origins in production.
- Protect API keys through server-side environment configuration.
- Add rate limiting and usage controls.
- Add request logging and structured monitoring.
- Validate AI output through schemas or post-processing.
- Add automated unit, integration, and end-to-end tests.

## 12. Testing and Evaluation

No formal automated test suite or benchmark results are documented in the repository at this stage. The project should therefore distinguish measured results from proposed evaluation.

### Proposed functional checks

- Verify API health response.
- Confirm recommendation endpoints return course results.
- Confirm prerequisite parsing handles AND and OR expressions.
- Confirm quiz generation returns valid question structure.
- Confirm submitted scores and answer reviews are stored correctly.
- Confirm learning progress updates persist across sessions.
- Confirm adaptive recommendations consider feedback and completed items.

### Proposed quality metrics

- Recommendation relevance, rated by students or subject experts
- Percentage of recommendations supported by catalogue data
- Prerequisite-verification accuracy
- Quiz-generation validity
- API success rate
- Average response time
- Percentage of unsupported or unverifiable statements avoided
- Student satisfaction and usefulness of feedback

These metrics are proposed evaluation targets and should not be presented as measured project results until testing is performed.

## 13. Strengths

- Clear separation of agents and tools
- Practical combination of deterministic catalogue logic and generative AI
- Explicit evidence labels and caution against unsupported claims
- Multiple academic, career, assessment, and progress features
- Persistent local state across different recommendation workflows
- Modern React interface and REST API
- Readiness reporting for prerequisite requirements
- Extensible knowledge-base and agent architecture

## 14. Limitations

- Authentication and authorization are demo-oriented.
- Storage is file-based and not designed for concurrent production use.
- Groq availability and API configuration affect AI-generated features.
- Catalogue completeness determines recommendation quality.
- Prerequisite and assessment results require official course verification.
- No formal test coverage or measured evaluation benchmark is currently provided.
- The legacy Gradio interface and React/FastAPI interface must be maintained separately.
- AI-generated advice can still omit context or overgeneralize if profile data is incomplete.

## 15. Future Enhancements

1. Add a relational database and migration system.
2. Implement secure authentication and role-based authorization.
3. Add automated tests and continuous integration.
4. Add official-source citations for academic requirements.
5. Deploy the frontend and API using separate production environments.
6. Add multilingual support.
7. Improve UI accessibility and mobile responsiveness.
8. Introduce vector search for knowledge-base retrieval.
9. Add human-expert review for high-impact career recommendations.
10. Add analytics dashboards and measurable evaluation reporting.
11. Add real-time notifications for learning milestones.
12. Reconcile the legacy Gradio interface with the main React/FastAPI system.

## 16. Conclusion

The Student Academic Advisor demonstrates a practical agentic-AI architecture for academic and career guidance. It moves beyond a single prompt by coordinating specialized agents for catalog matching, prerequisite analysis, career planning, skill-gap detection, progress tracking, assessment, and feedback.

The implemented system already provides a complete prototype workflow: students create profiles, receive course and career recommendations, complete assessments, and verify prerequisite readiness. Further work should focus on secure authentication, database-backed persistence, formal testing, measurable evaluation, and verified external data sources.

## 17. How to Run

### Backend

```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn api:app --reload
```

The API is available at `http://127.0.0.1:8000`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server will provide the frontend URL, usually `http://localhost:5173`.

Make sure a valid `GROQ_API_KEY` is configured in the environment before using AI-generated features.
