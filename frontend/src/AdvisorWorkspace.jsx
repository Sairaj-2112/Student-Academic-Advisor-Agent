
import { useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = "http://127.0.0.1:8000";

// =====================================================
// API HELPERS
// =====================================================

async function apiRequest(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail || "The request failed.")
    );
  }

  return data;
}

function getQuizResult(data) {
  const candidates = [
    data,
    data?.quiz_result,
    data?.result,
    data?.result?.quiz_result,
    data?.result?.result
  ];

  return (
    candidates.find(
      item =>
        item &&
        typeof item === "object" &&
        (
          Array.isArray(item.answer_review) ||
          item.percentage !== undefined ||
          item.correct_answers !== undefined
        )
    ) || data
  );
}

function formatLabel(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, letter => letter.toUpperCase());
}

function isAnswerCorrect(item) {
  const status = String(item.status || "").toLowerCase();

  if (status === "correct" || status === "passed") return true;
  if (status === "incorrect" || status === "wrong") return false;

  return (
    String(item.submitted_answer ?? "").trim().toUpperCase() ===
    String(item.correct_answer ?? "").trim().toUpperCase()
  );
}

function renderList(items) {
  if (!Array.isArray(items) || !items.length) return null;

  return (
    <ul>
      {items.map((item, index) => (
        <li key={index}>
          {typeof item === "string" ? item : JSON.stringify(item)}
        </li>
      ))}
    </ul>
  );
}

// =====================================================
// ANSWER REVIEW
// =====================================================

function AnswerReview({ result, quiz }) {
  const reviews =
    result?.answer_review ||
    result?.result?.answer_review ||
    result?.quiz_result?.answer_review ||
    [];

  if (!Array.isArray(reviews) || !reviews.length) {
    return (
      <div style={styles.notice}>
        Question-by-question review was not returned by the backend.
      </div>
    );
  }

  const questionMap = Object.fromEntries(
    (quiz?.questions || []).map(question => [
      String(question.question_id),
      question
    ])
  );

  return (
    <div>
      <h3>Question-by-Question Review</h3>

      {reviews.map((item, index) => {
        const correct = isAnswerCorrect(item);
        const question = questionMap[String(item.question_id)] || {};

        return (
          <div
            key={item.question_id || index}
            style={{
              ...styles.card,
              border: `2px solid ${correct ? "#16a34a" : "#dc2626"}`
            }}
          >
            <h4>
              Question {index + 1} â€” {correct ? "Correct" : "Incorrect"}
            </h4>

            <p>{item.question || question.question || "Question unavailable"}</p>
            <p><strong>Your answer:</strong> {item.submitted_answer || "Not answered"}</p>
            <p><strong>Correct answer:</strong> {item.correct_answer || "Not available"}</p>
            <p><strong>Explanation:</strong> {item.explanation || "No explanation available."}</p>
          </div>
        );
      })}
    </div>
  );
}

// =====================================================
// MAIN WORKSPACE
// =====================================================

function AdvisorWorkspace({ student, section = "academic" }) {

  // PROFILE
  const [name, setName] = useState(student?.name || "");
  const [subjects, setSubjects] = useState("");
  const [interests, setInterests] = useState("");
  // CAREER ADVISOR
  const [careerSkills, setCareerSkills] = useState("");
  const [careerGoals, setCareerGoals] = useState("");
  const [careerEducation, setCareerEducation] = useState("Undergraduate");
  const [careerStatus, setCareerStatus] = useState("Currently studying");
  const [careerLocation, setCareerLocation] = useState("");
  const [careerExperience, setCareerExperience] = useState("");
  const [careerGuidance, setCareerGuidance] = useState("");
  const [careerLoading, setCareerLoading] = useState(false);
  const [careerError, setCareerError] = useState("");

  // ACADEMIC ADVISOR
  const [results, setResults] = useState(null);
  const [prerequisiteResults, setPrerequisiteResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // PREREQUISITE VERIFICATION
  const [selectedTargetIndex, setSelectedTargetIndex] = useState("");
  const [verificationSession, setVerificationSession] = useState(null);
  const [readinessReport, setReadinessReport] = useState(null);
  const [readinessReportLoading, setReadinessReportLoading] = useState(false);
  const [verificationLoading, setVerificationLoading] = useState(false);
  const [verificationError, setVerificationError] = useState("");

  const [activePrerequisite, setActivePrerequisite] = useState("");
  const [prerequisiteQuiz, setPrerequisiteQuiz] = useState(null);
  const [prerequisiteAnswers, setPrerequisiteAnswers] = useState({});
  const [prerequisiteQuizResult, setPrerequisiteQuizResult] = useState(null);
  const [prerequisiteQuizLoading, setPrerequisiteQuizLoading] = useState(false);

  // GENERAL ASSESSMENT
  const [quizSubject, setQuizSubject] = useState("");
  const [standaloneQuiz, setStandaloneQuiz] = useState(null);
  const [standaloneAnswers, setStandaloneAnswers] = useState({});
  const [standaloneResult, setStandaloneResult] = useState(null);
  const [standaloneLoading, setStandaloneLoading] = useState(false);
  const [standaloneError, setStandaloneError] = useState("");
  // CAREER ADVISOR

  const completedCourses = subjects
    .split(",")
    .map(item => item.trim())
    .filter(Boolean);

  const studentInterests = interests
    .split(",")
    .map(item => item.trim())
    .filter(Boolean);

  const analysis = prerequisiteResults?.analysis || [];

  const selectedTarget =
    selectedTargetIndex !== ""
      ? analysis[Number(selectedTargetIndex)]
      : null;

  // =====================================================
  // GENERATE ACADEMIC ADVICE
  // =====================================================

  const generateAdvice = async event => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResults(null);
    setPrerequisiteResults(null);
    setVerificationSession(null);
    setReadinessReport(null);
    setSelectedTargetIndex("");
    setVerificationError("");
    setPrerequisiteQuiz(null);
    setPrerequisiteQuizResult(null);

    try {
      const academicData = await apiRequest(
        `${API_URL}/api/advisor/recommend`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            completed_subjects: completedCourses,
            interests: studentInterests
          })
        }
      );

      const advisorResult = academicData.result || academicData;
      const academicResults = advisorResult.academic_results || [];

      setResults({
        ...advisorResult,
        student_name: academicData.student_name || name,
        academic_results: academicResults,
        recommendations: advisorResult.recommendations || []
      });

      const profile = {
        name,
        education_level: "Undergraduate",
        current_status: "Studying",
        completed_courses: completedCourses,
        interests: studentInterests
      };

      const prerequisiteData = await apiRequest(
        `${API_URL}/api/advisor/prerequisites`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            profile,
            academic_results: academicResults
          })
        }
      );

      const report = prerequisiteData.result || {};
      setPrerequisiteResults(report);

      const firstIndex = (report.analysis || []).findIndex(
        item =>
          Array.isArray(item.requirement_groups) &&
          item.requirement_groups.length > 0
      );

      if (firstIndex >= 0) {
        setSelectedTargetIndex(String(firstIndex));
      }
    } catch (err) {
      setError(err.message || "Unable to generate academic advice.");
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // READINESS REPORT
  // =====================================================

  const loadReadinessReport = async sessionId => {
    if (!sessionId) return;

    setReadinessReportLoading(true);

    try {
      const data = await apiRequest(
        `${API_URL}/api/prerequisite-verification/${sessionId}/report`
      );

      setReadinessReport(data.report || data);
    } catch (err) {
      console.error("Readiness report error:", err);
      setVerificationError(
        "The readiness report could not be refreshed. Please try again."
      );
    } finally {
      setReadinessReportLoading(false);
    }
  };

  // =====================================================
  // START VERIFICATION
  // =====================================================

  const startVerification = async () => {
    if (!selectedTarget) {
      setVerificationError("Please select a target course.");
      return;
    }

    const groups = selectedTarget.requirement_groups || [];

    if (!groups.length) {
      setVerificationError("No prerequisite groups are available.");
      return;
    }

    setVerificationLoading(true);
    setVerificationError("");
    setVerificationSession(null);
    setReadinessReport(null);
    setPrerequisiteQuiz(null);
    setPrerequisiteQuizResult(null);

    try {
      const data = await apiRequest(
        `${API_URL}/api/prerequisite-verification/start`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            student_name: name || "Student",
            target_course_code: selectedTarget.course_code || "",
            target_course_title:
              selectedTarget.course ||
              selectedTarget.title ||
              "Selected Course",
            requirement_groups: groups
          })
        }
      );

      const verification = data.verification || data.result || data;

      setVerificationSession(verification);
      await loadReadinessReport(verification.session_id);
    } catch (err) {
      setVerificationError(err.message || "Unable to start verification.");
    } finally {
      setVerificationLoading(false);
    }
  };

  // =====================================================
  // GENERATE PREREQUISITE QUIZ
  // =====================================================

  const generatePrerequisiteQuiz = async courseCode => {
    if (!verificationSession) return;

    setPrerequisiteQuizLoading(true);
    setVerificationError("");
    setPrerequisiteQuiz(null);
    setPrerequisiteQuizResult(null);
    setPrerequisiteAnswers({});
    setActivePrerequisite(courseCode);

    try {
      const data = await apiRequest(
        `${API_URL}/api/prerequisite-verification/quiz`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: verificationSession.session_id,
            prerequisite_code: courseCode,
            question_count: 5
          })
        }
      );

      if (!data.quiz?.questions?.length) {
        throw new Error("The AI did not return any quiz questions.");
      }

      setPrerequisiteQuiz(data.quiz);
    } catch (err) {
      setVerificationError(err.message || "Unable to generate prerequisite quiz.");
    } finally {
      setPrerequisiteQuizLoading(false);
    }
  };

  // =====================================================
  // SUBMIT PREREQUISITE QUIZ
  // =====================================================

  const submitPrerequisiteQuiz = async () => {
    if (!prerequisiteQuiz || !verificationSession) return;

    setPrerequisiteQuizLoading(true);
    setVerificationError("");

    try {
      const data = await apiRequest(
        `${API_URL}/api/prerequisite-verification/submit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: verificationSession.session_id,
            prerequisite_code: activePrerequisite,
            attempt_id: prerequisiteQuiz.attempt_id,
            student_name: verificationSession.student_name || name,
            answers: prerequisiteAnswers
          })
        }
      );

      const quizResult = getQuizResult(data.quiz_result || data);
      setPrerequisiteQuizResult(quizResult);

      if (data.verification) {
        const updated = data.verification.verification || data.verification;
        setVerificationSession(updated);
      } else {
        try {
          const updated = await apiRequest(
            `${API_URL}/api/prerequisite-verification/${verificationSession.session_id}`
          );
          setVerificationSession(updated.verification || updated);
        } catch (refreshError) {
          console.error("Session refresh error:", refreshError);
        }
      }

      await loadReadinessReport(verificationSession.session_id);
      setPrerequisiteQuiz(null);
    } catch (err) {
      setVerificationError(err.message || "Unable to submit prerequisite quiz.");
    } finally {
      setPrerequisiteQuizLoading(false);
    }
  };

  // =====================================================
  // GENERAL QUIZ
  // =====================================================

  const generateStandaloneQuiz = async () => {
    if (!quizSubject.trim()) {
      setStandaloneError("Please enter a subject.");
      return;
    }

    setStandaloneLoading(true);
    setStandaloneError("");
    setStandaloneQuiz(null);
    setStandaloneResult(null);
    setStandaloneAnswers({});

    try {
      const data = await apiRequest(
        `${API_URL}/api/quiz/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            student_name: name || "Student",
            subject: quizSubject.trim(),
            question_count: 5
          })
        }
      );

      const quiz = data.quiz || data.result || data;

      if (!quiz.questions?.length) {
        throw new Error("No quiz questions were returned.");
      }

      setStandaloneQuiz(quiz);
    } catch (err) {
      setStandaloneError(err.message || "Unable to generate quiz.");
    } finally {
      setStandaloneLoading(false);
    }
  };

  const submitStandaloneQuiz = async () => {
    if (!standaloneQuiz) return;

    setStandaloneLoading(true);
    setStandaloneError("");

    try {
      const data = await apiRequest(
        `${API_URL}/api/quiz/submit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            attempt_id: standaloneQuiz.attempt_id,
            student_name: name || "Student",
            answers: standaloneAnswers
          })
        }
      );

      setStandaloneResult(getQuizResult(data));
      setStandaloneQuiz(null);
    } catch (err) {
      setStandaloneError(err.message || "Unable to submit quiz.");
    } finally {
      setStandaloneLoading(false);
    }
  };

  // =====================================================
  // REUSABLE QUIZ QUESTIONS
  // =====================================================

  const renderQuizQuestions = (
    quizData,
    selectedAnswers,
    answerHandler
  ) => (
    <div>
      {quizData.questions.map((question, index) => (
        <div key={question.question_id} style={styles.card}>
          <p>
            <strong>{index + 1}. {question.question}</strong>
          </p>

          <p style={styles.muted}>
            Topic: {question.topic || "General"} | Difficulty:{" "}
            {formatLabel(question.difficulty || "Not specified")}
          </p>

          {(question.options || []).map(option => (
            <label
              key={option.id}
              style={{
                ...styles.option,
                borderColor:
                  selectedAnswers[question.question_id] === option.id
                    ? "#2563eb"
                    : "#e5e7eb"
              }}
            >
              <input
                type="radio"
                name={question.question_id}
                checked={selectedAnswers[question.question_id] === option.id}
                onChange={() =>
                  answerHandler(question.question_id, option.id)
                }
              />

              <span>
                <strong>{option.id}.</strong> {option.text}
              </span>
            </label>
          ))}
        </div>
      ))}
    </div>
  );

  // =====================================================
  // READINESS DASHBOARD
  // =====================================================

  const renderReadinessDashboard = () => {
    if (!readinessReport) return null;

    const report = readinessReport;
    const isReady = Boolean(report.assessment_ready);
    const progress = Math.max(
      0,
      Math.min(100, Number(report.overall_progress_percentage || 0))
    );

    return (
      <div style={styles.card}>
        <div style={styles.flexBetween}>
          <h2>Final Prerequisite Readiness Report</h2>

          <button
            type="button"
            onClick={() =>
              loadReadinessReport(verificationSession?.session_id)
            }
            disabled={readinessReportLoading}
          >
            {readinessReportLoading ? "Refreshing..." : "Refresh Report"}
          </button>
        </div>

        <div style={styles.notice}>
          <h2>{isReady ? "Prerequisite Assessment Ready" : "Not Yet Ready"}</h2>
          <h3>{report.final_decision || "Decision unavailable"}</h3>
          <p>{report.explanation || "Complete the required assessments."}</p>
          <strong>Overall Status: {formatLabel(report.overall_status)}</strong>
        </div>

        <h3>Overall Progress: {progress}%</h3>

        <div style={styles.progressTrack}>
          <div
            style={{
              ...styles.progressFill,
              width: `${progress}%`
            }}
          />
        </div>

        <div style={styles.stats}>
          {[
            ["Total", report.total_prerequisites],
            ["Assessed", report.assessed_prerequisites],
            ["Passed", report.passed_prerequisites],
            ["Remaining", report.remaining_prerequisites]
          ].map(([label, value]) => (
            <div key={label} style={styles.stat}>
              <h2>{value ?? 0}</h2>
              <p>{label}</p>
            </div>
          ))}
        </div>

        <h3>Prerequisite-wise Results</h3>

        {(report.prerequisite_details || []).map((item, index) => (
          <div key={item.course_code || index} style={styles.card}>
            <h3>{item.course_code}</h3>
            <p>Status: {formatLabel(item.status)}</p>
            <p>Latest Score: {item.latest_score ?? "Not assessed"}</p>
            <p>Best Score: {item.best_score ?? "Not assessed"}</p>
            <p>Attempts: {item.attempt_count ?? 0}</p>

            {item.weak_topics?.length > 0 && (
              <div style={styles.notice}>
                <strong>Topics to improve:</strong>
                {renderList(item.weak_topics)}
              </div>
            )}
          </div>
        ))}

        <h3>Alternative Requirement Groups</h3>
        <p>
          AND logic applies within a group. OR logic applies between
          alternative groups.
        </p>

        {(report.group_results || []).map((group, index) => (
          <div key={index} style={styles.notice}>
            <strong>Option {group.group_number || index + 1}</strong>
            <p>Requirements: {(group.prerequisites || []).join(" AND ")}</p>
            <p>Passed: {(group.passed_prerequisites || []).join(", ") || "None"}</p>
            <p>Remaining: {(group.remaining_prerequisites || []).join(", ") || "None"}</p>
            <p>Progress: {group.completion_percentage ?? 0}%</p>
          </div>
        ))}

        <h3>Practice Recommendations</h3>

        {(report.practice_recommendations || []).length ? (
          <ul>
            {report.practice_recommendations.map((item, index) => (
              <li key={index}>
                <strong>{item.prerequisite_code || "Practice"}:</strong>{" "}
                {item.recommendation || JSON.stringify(item)}
              </li>
            ))}
          </ul>
        ) : (
          <p>No additional recommendations.</p>
        )}

        <div style={styles.notice}>
          <strong>Assessment Threshold: {report.pass_threshold ?? 80}%</strong>
          <p>
            This report measures knowledge demonstrated through prerequisite
            quizzes. It does not certify official course completion or
            university enrollment eligibility.
          </p>
        </div>
      </div>
    );
  };

  // =====================================================
  // SECTION 1: ACADEMIC ADVISOR
  // =====================================================

  const AcademicSection = (
    <div>
      <div style={styles.heading}>
        <h1>Academic Advisor</h1>
        <p>Discover relevant courses and understand your academic eligibility.</p>
      </div>

      <form onSubmit={generateAdvice} style={styles.form}>
        <h2>Student Information</h2>

        <label>Student Name</label>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Enter your name"
          required
          style={styles.input}
        />

        <label>Completed Subjects / Courses</label>
        <input
          value={subjects}
          onChange={e => setSubjects(e.target.value)}
          placeholder="Python, Data Structures, Mathematics"
          style={styles.input}
        />

        <label>Your Interests</label>
        <input
          value={interests}
          onChange={e => setInterests(e.target.value)}
          placeholder="Artificial Intelligence, Data Science"
          required
          style={styles.input}
        />

        <button type="submit" disabled={loading}>
          {loading ? "Analyzing Profile..." : "Generate Academic Advice"}
        </button>
      </form>

      {loading && <div style={styles.notice}>Analyzing your profile...</div>}
      {error && <div style={styles.error}>{error}</div>}

      {results && (
        <div style={styles.section}>
          <h2>Academic Advisor Report</h2>
          <h3>Welcome, {results.student_name || name}!</h3>

          <div style={styles.stats}>
            <div style={styles.stat}>
              <h2>{results.academic_results?.length ?? 0}</h2>
              <p>Academic Results</p>
            </div>

            <div style={styles.stat}>
              <h2>{results.recommendations?.length ?? 0}</h2>
              <p>Recommendations</p>
            </div>

            <div style={styles.stat}>
              <h2>{analysis.length}</h2>
              <p>Prerequisite Checks</p>
            </div>
          </div>

          <h2>Recommended Courses</h2>

          {(results.recommendations || []).map((course, index) => (
            <div key={index} style={styles.card}>
              <h3>{course.title || "Untitled Course"}</h3>
              <p><strong>Course Code:</strong> {course.course_code || "Not available"}</p>
              <p><strong>Department:</strong> {course.subject || "Not available"}</p>
              <p><strong>Credits:</strong> {course.credits ?? "Not available"}</p>
              <p>{course.description || "No description available."}</p>
            </div>
          ))}

          <h2>Academic Search Results</h2>

          {(results.academic_results || []).map((course, index) => (
            <div key={index} style={styles.card}>
              <h3>{course.title || "Untitled Course"}</h3>
              <p><strong>Course Code:</strong> {course.course_code || `${course.subject || ""} ${course.course_number || ""}`}</p>
              <p><strong>Department:</strong> {course.subject || "Not available"}</p>
              <p><strong>Credits:</strong> {course.credits ?? "Not available"}</p>
              <p><strong>Prerequisites:</strong> {course.prerequisite_text || "Not specified"}</p>
              <p>{course.description || "No description available."}</p>
            </div>
          ))}

          <h2>Prerequisite & Eligibility Analysis</h2>

          {prerequisiteResults?.summary && (
            <div style={styles.notice}>
              <h3>Analysis Summary</h3>
              {typeof prerequisiteResults.summary === "object"
                ? Object.entries(prerequisiteResults.summary).map(([key, value]) => (
                    <p key={key}>
                      <strong>{formatLabel(key)}:</strong> {String(value)}
                    </p>
                  ))
                : <p>{prerequisiteResults.summary}</p>}
            </div>
          )}

          {analysis.map((item, index) => (
            <div key={index} style={styles.card}>
              <h3>{item.title || item.course_name || item.course || `Course ${index + 1}`}</h3>
              <p><strong>Course Code:</strong> {item.course_code || "Not available"}</p>
              <p><strong>Status:</strong> {formatLabel(item.status || "needs_verification")}</p>

              {item.explanation && <p>{item.explanation}</p>}

              {item.missing_prerequisites?.length > 0 && (
                <div style={styles.error}>
                  <strong>Missing Requirements:</strong>
                  {renderList(item.missing_prerequisites)}
                </div>
              )}

              {item.matched_prerequisites?.length > 0 && (
                <div style={styles.success}>
                  <strong>Matched Requirements:</strong>
                  {renderList(item.matched_prerequisites)}
                </div>
              )}

              {item.requirement_groups?.length > 0 && (
                <div style={styles.notice}>
                  <strong>Prerequisite Alternatives:</strong>
                  {item.requirement_groups.map((group, i) => (
                    <p key={i}>
                      Option {i + 1}: {Array.isArray(group) ? group.join(" AND ") : String(group)}
                    </p>
                  ))}
                </div>
              )}

              {item.eligibility_restrictions?.length > 0 && (
                <div style={styles.notice}>
                  <strong>Enrollment Restrictions:</strong>
                  {renderList(item.eligibility_restrictions)}
                </div>
              )}

              {item.concurrent_conditions?.length > 0 && (
                <div style={styles.notice}>
                  <strong>Concurrent Enrollment Conditions:</strong>
                  {renderList(item.concurrent_conditions)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // =====================================================
  // SECTION 2: PREREQUISITE VERIFICATION
  // =====================================================

  const PrerequisiteSection = (
    <div>
      <div style={styles.heading}>
        <h1>Prerequisite Verification</h1>
        <p>Test your knowledge of prerequisite subjects before taking a target course.</p>
      </div>

      {!prerequisiteResults && (
        <div style={styles.notice}>
          Generate Academic Advice first in the Academic Advisor section.
          Your course prerequisite analysis will appear here.
        </div>
      )}

      {prerequisiteResults && (
        <>
          <div style={styles.form}>
            <label>Select Target Course</label>

            <select
              value={selectedTargetIndex}
              onChange={e => {
                setSelectedTargetIndex(e.target.value);
                setVerificationSession(null);
                setReadinessReport(null);
                setPrerequisiteQuiz(null);
                setPrerequisiteQuizResult(null);
                setActivePrerequisite("");
                setVerificationError("");
              }}
              style={styles.input}
            >
              <option value="">Choose a course</option>

              {analysis.map((item, index) => (
                <option key={index} value={String(index)}>
                  {item.course_code || "Course"} - {item.course || item.title || `Course ${index + 1}`}
                </option>
              ))}
            </select>

            {selectedTarget && (
              <div style={styles.notice}>
                <h3>{selectedTarget.course_code} {selectedTarget.course || selectedTarget.title}</h3>
                <strong>Requirement Alternatives</strong>
                {(selectedTarget.requirement_groups || []).map((group, index) => (
                  <p key={index}>
                    Option {index + 1}: {Array.isArray(group) ? group.join(" AND ") : String(group)}
                  </p>
                ))}
              </div>
            )}

            <button
              type="button"
              onClick={startVerification}
              disabled={
                verificationLoading ||
                !selectedTarget ||
                !selectedTarget.requirement_groups?.length
              }
            >
              {verificationLoading ? "Starting Verification..." : "Start Prerequisite Verification"}
            </button>
          </div>

          {verificationError && <div style={styles.error}>{verificationError}</div>}

          {verificationSession && (
            <div style={styles.section}>
              <h2>Prerequisite Verification Dashboard</h2>

              <p><strong>Student:</strong> {verificationSession.student_name}</p>
              <p>
                <strong>Target Course:</strong>{" "}
                {verificationSession.target_course_code}{" "}
                {verificationSession.target_course_title}
              </p>

              <div style={styles.stats}>
                <div style={styles.stat}>
                  <h2>{verificationSession.total_prerequisites ?? 0}</h2>
                  <p>Total Prerequisites</p>
                </div>

                <div style={styles.stat}>
                  <h2>{verificationSession.passed_prerequisites ?? 0}</h2>
                  <p>Passed</p>
                </div>

                <div style={styles.stat}>
                  <h2>{verificationSession.remaining_prerequisites ?? 0}</h2>
                  <p>Not Yet Passed</p>
                </div>
              </div>

              <div style={styles.notice}>
                <h3>Overall Status: {formatLabel(verificationSession.overall_status)}</h3>
                Every prerequisite in one group must pass. Alternative groups use OR logic.
              </div>

              {renderReadinessDashboard()}

              {readinessReportLoading && (
                <div style={styles.notice}>Updating readiness report...</div>
              )}

              <h3>Individual Prerequisite Assessments</h3>

              {Object.entries(verificationSession.prerequisites || {}).map(([code, record]) => (
                <div key={code} style={styles.card}>
                  <h3>{code}</h3>
                  <p><strong>Status:</strong> {formatLabel(record.status)}</p>
                  <p><strong>Latest Score:</strong> {record.latest_score == null ? "Not assessed" : `${record.latest_score}%`}</p>
                  <p><strong>Best Score:</strong> {record.best_score == null ? "Not assessed" : `${record.best_score}%`}</p>
                  <p><strong>Attempts:</strong> {record.attempt_count ?? 0}</p>

                  {record.weak_topics?.length > 0 && (
                    <div style={styles.error}>
                      <strong>Topics needing improvement:</strong>
                      {renderList(record.weak_topics)}
                    </div>
                  )}

                  {record.attempts?.length > 0 && (
                    <div style={styles.notice}>
                      <strong>Attempt History</strong>
                      {record.attempts.map(attempt => (
                        <p key={attempt.attempt_number}>
                          Attempt {attempt.attempt_number}: {attempt.score}% â€”{" "}
                          {attempt.passed ? "Passed" : "Needs practice"}
                        </p>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => generatePrerequisiteQuiz(code)}
                    disabled={prerequisiteQuizLoading || record.status === "passed"}
                  >
                    {record.status === "passed"
                      ? "Prerequisite Passed"
                      : record.attempt_count > 0
                        ? "Retake Prerequisite Quiz"
                        : "Start Individual Quiz"}
                  </button>
                </div>
              ))}

              <h3>Alternative Requirement Evaluation</h3>

              {(verificationSession.group_results || []).map((group, index) => (
                <div key={index} style={styles.notice}>
                  <strong>Option {index + 1}:</strong>{" "}
                  {(group.requirements || []).join(" AND ")}
                  <p>
                    Status: {group.passed ? "All requirements passed" : "Requirements still pending"}
                  </p>
                </div>
              ))}

              {verificationSession.assessment_ready && (
                <div style={styles.success}>
                  <h3>Assessment Readiness Achieved</h3>
                  At least one complete prerequisite alternative group has been passed.
                </div>
              )}
            </div>
          )}

          {prerequisiteQuizLoading && (
            <div style={styles.notice}>Generating or evaluating your prerequisite quiz...</div>
          )}

          {prerequisiteQuiz && (
            <div style={styles.card}>
              <h2>{activePrerequisite} Knowledge Assessment</h2>
              <p>Answer these questions to demonstrate your understanding.</p>

              {renderQuizQuestions(
                prerequisiteQuiz,
                prerequisiteAnswers,
                (questionId, optionId) =>
                  setPrerequisiteAnswers(previous => ({
                    ...previous,
                    [questionId]: optionId
                  }))
              )}

              <p>
                Answered: {Object.keys(prerequisiteAnswers).length} /{" "}
                {prerequisiteQuiz.questions.length}
              </p>

              <button
                type="button"
                onClick={submitPrerequisiteQuiz}
                disabled={prerequisiteQuizLoading}
              >
                Submit Prerequisite Assessment
              </button>
            </div>
          )}

          {prerequisiteQuizResult && (
            <div style={styles.card}>
              <h2>Prerequisite Assessment Result</h2>
              <h3>{activePrerequisite}</h3>

              <div style={styles.stats}>
                <div style={styles.stat}>
                  <h2>{prerequisiteQuizResult.percentage ?? 0}%</h2>
                  <p>Score</p>
                </div>

                <div style={styles.stat}>
                  <h2>{prerequisiteQuizResult.correct_answers ?? 0}</h2>
                  <p>Correct Answers</p>
                </div>

                <div style={styles.stat}>
                  <h2>{prerequisiteQuizResult.incorrect_answers ?? 0}</h2>
                  <p>Incorrect Answers</p>
                </div>
              </div>

              <h3>Topic-wise Analysis</h3>

              {(prerequisiteQuizResult.topic_analysis || []).map((topic, index) => (
                <div key={index} style={styles.notice}>
                  <strong>{topic.topic}</strong>
                  <p>
                    Score: {topic.correct_answers}/{topic.total_questions} ({topic.percentage}%)
                  </p>
                  <p>Assessment: {formatLabel(topic.status || topic.interpretation || "Not available")}</p>
                </div>
              ))}

              <AnswerReview result={prerequisiteQuizResult} />

              <button
                type="button"
                onClick={() => setPrerequisiteQuizResult(null)}
              >
                Back to Verification Dashboard
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );

  // =====================================================
  // SECTION 3: AI ASSESSMENTS
  // =====================================================

  const AssessmentSection = (
    <div>
      <div style={styles.heading}>
        <h1>AI Assessments</h1>
        <p>Generate subject-wise AI quizzes and evaluate your knowledge.</p>
      </div>

      <div style={styles.form}>
        <label>Subject to Assess</label>

        <input
          value={quizSubject}
          onChange={e => setQuizSubject(e.target.value)}
          placeholder="Python, Data Structures, Mathematics"
          style={styles.input}
        />

        <button
          type="button"
          onClick={generateStandaloneQuiz}
          disabled={standaloneLoading}
        >
          {standaloneLoading ? "Generating..." : "Generate General Quiz"}
        </button>
      </div>

      {standaloneError && <div style={styles.error}>{standaloneError}</div>}

      {standaloneLoading && (
        <div style={styles.notice}>Generating or evaluating your quiz...</div>
      )}

      {standaloneQuiz && (
        <div style={styles.card}>
          <h2>{standaloneQuiz.subject || quizSubject} Knowledge Assessment</h2>

          {renderQuizQuestions(
            standaloneQuiz,
            standaloneAnswers,
            (questionId, optionId) =>
              setStandaloneAnswers(previous => ({
                ...previous,
                [questionId]: optionId
              }))
          )}

          <p>
            Answered: {Object.keys(standaloneAnswers).length} /{" "}
            {standaloneQuiz.questions.length}
          </p>

          <button
            type="button"
            onClick={submitStandaloneQuiz}
            disabled={standaloneLoading}
          >
            Submit General Quiz
          </button>
        </div>
      )}

      {standaloneResult && (
        <div style={styles.card}>
          <h2>General Knowledge Assessment Result</h2>

          <h3>
            {standaloneResult.percentage ?? 0}% â€”{" "}
            {formatLabel(standaloneResult.assessment || "Completed")}
          </h3>

          <div style={styles.stats}>
            <div style={styles.stat}>
              <h2>{standaloneResult.correct_answers ?? 0}</h2>
              <p>Correct Answers</p>
            </div>

            <div style={styles.stat}>
              <h2>{standaloneResult.incorrect_answers ?? 0}</h2>
              <p>Incorrect Answers</p>
            </div>
          </div>

          <p>
            <strong>Readiness Signal:</strong>{" "}
            {formatLabel(standaloneResult.readiness_signal || "Not available")}
          </p>

          <AnswerReview result={standaloneResult} />

          <button
            type="button"
            onClick={() => setStandaloneResult(null)}
          >
            Close Result
          </button>
        </div>
      )}
    </div>
  );

  // =====================================================
    // =====================================================
  // GENERATE PERSONALIZED CAREER GUIDANCE
  // =====================================================

  const generateCareerGuidance = async event => {
    event.preventDefault();

    setCareerLoading(true);
    setCareerError("");
    setCareerGuidance("");

    const profile = {
      name: name || student?.name || "Student",
      education_level: careerEducation,
      current_status: careerStatus,
      completed_courses: completedCourses,
      skills: careerSkills.split(",").map(item => item.trim()).filter(Boolean),
      interests: studentInterests,
      career_goals: careerGoals.split(",").map(item => item.trim()).filter(Boolean),
      experience: careerExperience.split(",").map(item => item.trim()).filter(Boolean),
      location: careerLocation
    };

    try {
      const data = await apiRequest(`${API_URL}/api/career`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile })
      });

      setCareerGuidance(
        data.career_guidance ||
        data.guidance ||
        data.message ||
        "The career agent did not return guidance."
      );
    } catch (err) {
      setCareerError(err.message || "Unable to generate career guidance.");
    } finally {
      setCareerLoading(false);
    }
  };
// SECTION 4: CAREER ADVISOR
  // =====================================================


  const CareerSection = (
    <div>
      <div style={styles.heading}>
        <h1>AI Career Advisor</h1>
        <p>Discover suitable career paths using your profile, skills, interests and goals.</p>
      </div>

      <form onSubmit={generateCareerGuidance} style={styles.form}>
        <h2>Your Career Profile</h2>

        <label>Student Name</label>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Enter your name"
          style={styles.input}
        />

        <label>Education Level</label>
        <select
          value={careerEducation}
          onChange={e => setCareerEducation(e.target.value)}
          style={styles.input}
        >
          <option>School</option>
          <option>Undergraduate</option>
          <option>Postgraduate</option>
          <option>Graduate</option>
          <option>Other</option>
        </select>

        <label>Current Status</label>
        <select
          value={careerStatus}
          onChange={e => setCareerStatus(e.target.value)}
          style={styles.input}
        >
          <option>Currently studying</option>
          <option>Recently graduated</option>
          <option>Working professional</option>
          <option>Looking for employment</option>
          <option>Career transition</option>
        </select>

        <label>Completed Courses / Subjects</label>
        <input
          value={subjects}
          onChange={e => setSubjects(e.target.value)}
          placeholder="Python, Machine Learning, Mathematics"
          style={styles.input}
        />

        <label>Your Skills (comma separated)</label>
        <input
          value={careerSkills}
          onChange={e => setCareerSkills(e.target.value)}
          placeholder="Python, Power BI, SQL, Communication"
          style={styles.input}
        />

        <label>Your Interests</label>
        <input
          value={interests}
          onChange={e => setInterests(e.target.value)}
          placeholder="Artificial Intelligence, Data Science"
          style={styles.input}
        />

        <label>Career Goals (comma separated)</label>
        <input
          value={careerGoals}
          onChange={e => setCareerGoals(e.target.value)}
          placeholder="AI Engineer, Data Scientist"
          style={styles.input}
        />

        <label>Location</label>
        <input
          value={careerLocation}
          onChange={e => setCareerLocation(e.target.value)}
          placeholder="Pune, India"
          style={styles.input}
        />

        <label>Experience (comma separated)</label>
        <input
          value={careerExperience}
          onChange={e => setCareerExperience(e.target.value)}
          placeholder="Frontend internship, Academic projects"
          style={styles.input}
        />

        <button type="submit" disabled={careerLoading}>
          {careerLoading ? "AI is analyzing your profile..." : "Generate AI Career Guidance"}
        </button>
      </form>

      {careerLoading && (
        <div style={styles.notice}>
          Your Career Agent is analyzing your profile and preparing recommendations...
        </div>
      )}

      {careerError && (
        <div style={styles.error}>
          <strong>Career Guidance Error</strong>
          <p>{careerError}</p>
        </div>
      )}

      {careerGuidance && (
  <div style={styles.card} className="career-report">
    <h2>Personalized AI Career Guidance</h2>

    <div className="career-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {careerGuidance}
      </ReactMarkdown>
    </div>

    <button
      type="button"
      onClick={() => setCareerGuidance("")}
      style={{ marginTop: "20px" }}
    >
      Generate Another Report
    </button>
  </div>
)}

      <div style={styles.notice}>
        <strong>How it works:</strong>
        <p>
          Your profile is sent to the existing Python Career Agent.
          It uses your skills, interests and goals to generate career suggestions.
        </p>
      </div>
    </div>
  );

  // =====================================================
  // SECTION 5: PROFILE & PROGRESS
  // =====================================================

  const ProgressSection = (
    <div>
      <div style={styles.heading}>
        <h1>Profile & Progress</h1>
        <p>Review the student information and learning activity in this workspace.</p>
      </div>

      <div style={styles.card}>
        <h2>Student Profile</h2>
        <p><strong>Name:</strong> {name || student?.name || "Not provided"}</p>
        <p><strong>Email:</strong> {student?.email || "Not available"}</p>
        <p><strong>Completed Subjects:</strong> {subjects || "Not entered"}</p>
        <p><strong>Interests:</strong> {interests || "Not entered"}</p>
      </div>

      <div style={styles.stats}>
        <div style={styles.stat}>
          <h2>{results?.academic_results?.length ?? 0}</h2>
          <p>Academic Results</p>
        </div>

        <div style={styles.stat}>
          <h2>{results?.recommendations?.length ?? 0}</h2>
          <p>Recommendations</p>
        </div>

        <div style={styles.stat}>
          <h2>{analysis.length}</h2>
          <p>Prerequisite Checks</p>
        </div>

        <div style={styles.stat}>
          <h2>{readinessReport?.passed_prerequisites ?? 0}</h2>
          <p>Prerequisites Passed</p>
        </div>
      </div>

      <div style={styles.notice}>
        Your assessment and prerequisite activity is displayed here when it is available
        in the current workspace. This section does not claim to retrieve additional
        progress data from a separate backend endpoint.
      </div>
    </div>
  );

  // =====================================================
  // DISPLAY SELECTED SECTION
  // =====================================================

  return (
    <div style={styles.page}>
      {section === "academic" && AcademicSection}
      {section === "prerequisite" && PrerequisiteSection}
      {section === "assessments" && AssessmentSection}
      {section === "career" && CareerSection}
      {section === "progress" && ProgressSection}
    </div>
  );
}

export default AdvisorWorkspace;

// =====================================================
// STYLES
// =====================================================

const styles = {
  page: {
    maxWidth: "1100px",
    margin: "20px auto",
    padding: "20px",
    fontFamily: "Arial, sans-serif",
    color: "#1f2937"
  },

  heading: {
    padding: "22px",
    background: "#eff6ff",
    borderRadius: "12px",
    marginBottom: "22px"
  },

  form: {
    padding: "22px",
    border: "1px solid #ddd",
    borderRadius: "12px",
    marginBottom: "22px",
    background: "#fff"
  },

  input: {
    display: "block",
    width: "100%",
    padding: "12px",
    margin: "10px 0 20px",
    boxSizing: "border-box",
    border: "1px solid #ccc",
    borderRadius: "6px"
  },

  card: {
    border: "1px solid #ddd",
    borderRadius: "10px",
    padding: "18px",
    margin: "15px 0",
    background: "#fff"
  },

  section: {
    marginTop: "25px"
  },

  stats: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: "14px",
    margin: "20px 0"
  },

  stat: {
    textAlign: "center",
    background: "#eff6ff",
    padding: "15px",
    borderRadius: "10px"
  },

  flexBetween: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
    flexWrap: "wrap"
  },

  option: {
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
    padding: "12px",
    margin: "8px 0",
    border: "1px solid #e5e7eb",
    borderRadius: "7px",
    cursor: "pointer"
  },

  notice: {
    background: "#eff6ff",
    padding: "15px",
    borderRadius: "8px",
    margin: "15px 0"
  },

  error: {
    background: "#fee2e2",
    color: "#991b1b",
    padding: "15px",
    borderRadius: "8px",
    margin: "15px 0"
  },

  success: {
    background: "#dcfce7",
    color: "#166534",
    padding: "15px",
    borderRadius: "8px",
    margin: "15px 0"
  },

  muted: {
    color: "#6b7280",
    fontSize: "13px"
  },

  progressTrack: {
    height: "14px",
    width: "100%",
    background: "#e5e7eb",
    borderRadius: "20px",
    overflow: "hidden"
  },

  progressFill: {
    height: "100%",
    background: "#2563eb",
    borderRadius: "20px",
    transition: "width 0.3s ease"
  }
};






