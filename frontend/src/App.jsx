
import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

async function apiRequest(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "The request failed. Please try again."
    );
  }

  return data;
}

function App() {
  const [name, setName] = useState("");
  const [subjects, setSubjects] = useState("");
  const [interests, setInterests] = useState("");

  const [results, setResults] = useState(null);
  const [prerequisiteResults, setPrerequisiteResults] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Quiz states
  const [quizSubject, setQuizSubject] = useState("");
  const [quizCount, setQuizCount] = useState(5);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizError, setQuizError] = useState("");

  const completedCourses = subjects
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const studentInterests = interests
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  // ==========================================
  // GENERATE ACADEMIC ADVICE
  // ==========================================

  const generateAdvice = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResults(null);
    setPrerequisiteResults(null);

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
      const recommendations = advisorResult.recommendations || [];

      setResults({
        ...advisorResult,
        student_name: academicData.student_name || name,
        academic_results: academicResults,
        recommendations
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

      setPrerequisiteResults(prerequisiteData.result || {});

      if (!quizSubject && completedCourses.length > 0) {
        setQuizSubject(completedCourses[0]);
      }
    } catch (err) {
      setError(err.message || "Unable to generate academic advice.");
    } finally {
      setLoading(false);
    }
  };

  // ==========================================
  // GENERATE AI KNOWLEDGE ASSESSMENT
  // ==========================================

  const generateQuiz = async () => {
    if (!quizSubject.trim()) {
      setQuizError("Please enter a subject to assess.");
      return;
    }

    setQuizLoading(true);
    setQuizError("");
    setQuiz(null);
    setQuizResult(null);
    setAnswers({});

    try {
      const data = await apiRequest(`${API_URL}/api/quiz/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_name: name || "Student",
          subject: quizSubject.trim(),
          question_count: Number(quizCount)
        })
      });

      if (!data.questions || data.questions.length === 0) {
        throw new Error("The AI did not return any questions. Please try again.");
      }

      setQuiz(data);
    } catch (err) {
      setQuizError(err.message || "Unable to generate quiz.");
    } finally {
      setQuizLoading(false);
    }
  };

  // ==========================================
  // SELECT ANSWER
  // ==========================================

  const selectAnswer = (questionId, optionId) => {
    setAnswers((previous) => ({
      ...previous,
      [questionId]: optionId
    }));
  };

  // ==========================================
  // SUBMIT QUIZ
  // ==========================================

  const submitQuiz = async () => {
    if (!quiz) return;

    setQuizLoading(true);
    setQuizError("");

    try {
      const data = await apiRequest(`${API_URL}/api/quiz/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attempt_id: quiz.attempt_id,
          student_name: name || "Student",
          answers
        })
      });

      setQuizResult(data);
      setQuiz(null);
    } catch (err) {
      setQuizError(err.message || "Unable to submit quiz.");
    } finally {
      setQuizLoading(false);
    }
  };

  // ==========================================
  // FORMAT HELPERS
  // ==========================================

  const formatLabel = (value) => {
    return String(value ?? "")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  };

  const getStatusStyle = (status) => {
    const styles = {
      prerequisites_met: {
        background: "#dcfce7",
        color: "#166534"
      },
      missing_prerequisites: {
        background: "#fee2e2",
        color: "#991b1b"
      },
      needs_verification: {
        background: "#fef3c7",
        color: "#92400e"
      },
      restricted_enrollment: {
        background: "#ede9fe",
        color: "#5b21b6"
      },
      not_applicable: {
        background: "#dbeafe",
        color: "#1e40af"
      }
    };

    return styles[String(status || "").toLowerCase()] || {
      background: "#e5e7eb",
      color: "#374151"
    };
  };

  const renderList = (items) => {
    if (!Array.isArray(items) || items.length === 0) return null;

    return (
      <ul style={{ paddingLeft: "22px", marginTop: "8px" }}>
        {items.map((item, index) => (
          <li key={index} style={{ marginBottom: "5px" }}>
            {typeof item === "string" ? item : JSON.stringify(item)}
          </li>
        ))}
      </ul>
    );
  };

  // Backend returns difficulty_analysis as a list.
  // This helper also supports an object response for compatibility.
  const getDifficultyEntries = (analysis) => {
    if (Array.isArray(analysis)) {
      return analysis.map((item) => [
        item.difficulty || "Unknown",
        item
      ]);
    }

    if (analysis && typeof analysis === "object") {
      return Object.entries(analysis);
    }

    return [];
  };

  // ==========================================
  // UI
  // ==========================================

  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <h1>Universal AI Academic & Career Advisor</h1>
        <p>
          AI-powered academic planning, course recommendations,
          prerequisite analysis and knowledge assessment.
        </p>
      </header>

      {/* STUDENT PROFILE */}

      <form onSubmit={generateAdvice} style={formStyle}>
        <h2>Student Information</h2>

        <label>Student Name</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter your name"
          required
          style={inputStyle}
        />

        <label>Completed Subjects / Courses</label>
        <input
          value={subjects}
          onChange={(e) => setSubjects(e.target.value)}
          placeholder="Python, Data Structures, Mathematics"
          style={inputStyle}
        />

        <label>Your Interests</label>
        <input
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
          placeholder="Artificial Intelligence, Data Science"
          required
          style={inputStyle}
        />

        <button type="submit" disabled={loading} style={buttonStyle}>
          {loading ? "Analyzing Profile..." : "Generate Academic Advice"}
        </button>
      </form>

      {loading && (
        <div style={loadingStyle}>
          Analyzing your academic profile and checking prerequisites...
        </div>
      )}

      {error && <div style={errorStyle}>{error}</div>}

      {/* ACADEMIC REPORT */}

      {results && (
        <section style={sectionStyle}>
          <h2>Academic Advisor Report</h2>
          <h3>Welcome, {results.student_name || name}!</h3>

          <div style={statsContainer}>
            <div style={statCard}>
              <h2>{results.academic_results?.length ?? 0}</h2>
              <p>Academic Results</p>
            </div>

            <div style={statCard}>
              <h2>{results.recommendations?.length ?? 0}</h2>
              <p>Course Recommendations</p>
            </div>

            <div style={statCard}>
              <h2>{prerequisiteResults?.analysis?.length ?? 0}</h2>
              <p>Prerequisite Checks</p>
            </div>
          </div>

          <h2>Recommended Courses</h2>

          {results.recommendations?.length > 0 ? (
            results.recommendations.map((course, index) => (
              <div
                key={`${course.course_code || course.title}-${index}`}
                style={cardStyle}
              >
                <h3>{course.title || "Untitled Course"}</h3>
                <p>
                  <strong>Course Code:</strong>{" "}
                  {course.course_code || "Not available"}
                </p>
                <p>
                  <strong>Department:</strong>{" "}
                  {course.subject || "Not available"}
                </p>
                <p>
                  <strong>Credits:</strong>{" "}
                  {course.credits ?? "Not available"}
                </p>
                <p>
                  <strong>Interest:</strong>{" "}
                  {course.interest || "Not specified"}
                </p>
                <p>{course.description || "No description available."}</p>
              </div>
            ))
          ) : (
            <p>No course recommendations found.</p>
          )}

          <h2>Academic Search Results</h2>

          {results.academic_results?.length > 0 ? (
            results.academic_results.map((course, index) => (
              <div
                key={`${course.course_code || course.title}-${index}`}
                style={cardStyle}
              >
                <h3>{course.title || "Untitled Course"}</h3>
                <p>
                  <strong>Course Code:</strong>{" "}
                  {course.course_code ||
                    `${course.subject || ""} ${course.course_number || ""}`}
                </p>
                <p>
                  <strong>Department:</strong>{" "}
                  {course.subject || "Not available"}
                </p>
                <p>
                  <strong>Credits:</strong>{" "}
                  {course.credits ?? "Not available"}
                </p>
                <p>
                  <strong>Prerequisites:</strong>{" "}
                  {course.prerequisite_text || "Not specified"}
                </p>
                <p>{course.description || "No description available."}</p>
              </div>
            ))
          ) : (
            <p>No academic search results found.</p>
          )}

          <hr style={dividerStyle} />

          {/* PREREQUISITE REPORT */}

          <h2>Prerequisite & Eligibility Analysis</h2>
          <p>
            The Prerequisite Agent compares your completed subjects with
            course requirements and identifies additional conditions.
          </p>

          {prerequisiteResults && (
            <>
              {prerequisiteResults.summary && (
                <div style={summaryStyle}>
                  <h3>Analysis Summary</h3>
                  {typeof prerequisiteResults.summary === "object"
                    ? Object.entries(prerequisiteResults.summary).map(
                        ([key, value]) => (
                          <p key={key}>
                            <strong>{formatLabel(key)}:</strong>{" "}
                            {String(value)}
                          </p>
                        )
                      )
                    : <p>{prerequisiteResults.summary}</p>}
                </div>
              )}

              <h3>Individual Course Eligibility</h3>

              {prerequisiteResults.analysis?.length > 0 ? (
                prerequisiteResults.analysis.map((item, index) => {
                  const status = item.status || "needs_verification";

                  return (
                    <div key={index} style={cardStyle}>
                      <h3>
                        {item.title ||
                          item.course_name ||
                          item.course ||
                          `Course ${index + 1}`}
                      </h3>

                      {item.course_code && (
                        <p>
                          <strong>Course Code:</strong> {item.course_code}
                        </p>
                      )}

                      <p>
                        <strong>Status:</strong>{" "}
                        <span
                          style={{
                            ...getStatusStyle(status),
                            padding: "6px 10px",
                            borderRadius: "6px",
                            fontWeight: "bold"
                          }}
                        >
                          {formatLabel(status)}
                        </span>
                      </p>

                      {item.prerequisite_text && (
                        <p>
                          <strong>Prerequisites:</strong>{" "}
                          {item.prerequisite_text}
                        </p>
                      )}

                      {item.explanation && (
                        <p>
                          <strong>Explanation:</strong> {item.explanation}
                        </p>
                      )}

                      {item.missing_prerequisites?.length > 0 && (
                        <div style={missingStyle}>
                          <strong>Missing Requirements:</strong>
                          {renderList(item.missing_prerequisites)}
                        </div>
                      )}

                      {item.matched_prerequisites?.length > 0 && (
                        <div style={matchedStyle}>
                          <strong>Matched Requirements:</strong>
                          {renderList(item.matched_prerequisites)}
                        </div>
                      )}

                      {item.requirement_groups?.length > 0 && (
                        <div style={infoStyle}>
                          <strong>Prerequisite Alternatives:</strong>
                          {item.requirement_groups.map((group, i) => (
                            <p key={i}>
                              Option {i + 1}:{" "}
                              {Array.isArray(group)
                                ? group.join(" AND ")
                                : String(group)}
                            </p>
                          ))}
                        </div>
                      )}

                      {item.eligibility_restrictions?.length > 0 && (
                        <div style={restrictionStyle}>
                          <strong>Enrollment Restrictions:</strong>
                          {renderList(item.eligibility_restrictions)}
                          <p>Confirm these conditions with your institution.</p>
                        </div>
                      )}

                      {item.concurrent_conditions?.length > 0 && (
                        <div style={verificationStyle}>
                          <strong>Concurrent Enrollment Conditions:</strong>
                          {renderList(item.concurrent_conditions)}
                          <p>
                            You may need to take these courses at the same time.
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <p>No individual prerequisite analysis records were returned.</p>
              )}

              {prerequisiteResults.important_note && (
                <div style={noticeStyle}>
                  <strong>Important:</strong>{" "}
                  {prerequisiteResults.important_note}
                </div>
              )}
            </>
          )}
        </section>
      )}

      {/* ======================================
          KNOWLEDGE VERIFICATION QUIZ
      ====================================== */}

      <section style={sectionStyle}>
        <div style={quizHeaderStyle}>
          <h2>Prerequisite Knowledge Verification</h2>
          <p>
            Test your understanding of a subject you have previously studied.
            Questions are generated dynamically using AI.
          </p>
        </div>

        <div style={formStyle}>
          <label>Subject to Assess</label>
          <input
            value={quizSubject}
            onChange={(e) => setQuizSubject(e.target.value)}
            placeholder="Example: Python, Data Structures, Mathematics"
            style={inputStyle}
          />

          <label>Number of Questions</label>
          <select
            value={quizCount}
            onChange={(e) => setQuizCount(Number(e.target.value))}
            style={inputStyle}
          >
            <option value={5}>5 Questions</option>
          </select>

          <button
            type="button"
            onClick={generateQuiz}
            disabled={quizLoading || !quizSubject.trim()}
            style={buttonStyle}
          >
            {quizLoading ? "Generating Quiz..." : "Generate AI Quiz"}
          </button>
        </div>

        {quizError && <div style={errorStyle}>{quizError}</div>}

        {/* QUIZ QUESTIONS */}

        {quiz && (
          <div style={cardStyle}>
            <h2>{quiz.subject} Knowledge Assessment</h2>
            <p>
              Student: {quiz.student_name || name || "Student"} | Questions:{" "}
              {quiz.questions.length}
            </p>
            <p>
              Select one answer for each question. Unanswered questions
              will be counted separately.
            </p>

            {quiz.questions.map((question, index) => (
              <div key={question.question_id} style={questionStyle}>
                <p style={{ fontWeight: "bold" }}>
                  {index + 1}. {question.question}
                </p>

                <p style={mutedStyle}>
                  Topic: {question.topic} | Difficulty:{" "}
                  {formatLabel(question.difficulty)}
                </p>

                {question.options.map((option) => (
                  <label
                    key={option.id}
                    style={{
                      ...optionStyle,
                      borderColor:
                        answers[question.question_id] === option.id
                          ? "#2563eb"
                          : "#e5e7eb",
                      background:
                        answers[question.question_id] === option.id
                          ? "#eff6ff"
                          : "#ffffff"
                    }}
                  >
                    <input
                      type="radio"
                      name={question.question_id}
                      value={option.id}
                      checked={answers[question.question_id] === option.id}
                      onChange={() =>
                        selectAnswer(question.question_id, option.id)
                      }
                    />
                    <span>
                      <strong>{option.id}.</strong> {option.text}
                    </span>
                  </label>
                ))}
              </div>
            ))}

            <p>
              Answered: {Object.keys(answers).length} / {quiz.questions.length}
            </p>

            <button
              type="button"
              onClick={submitQuiz}
              disabled={quizLoading}
              style={submitButtonStyle}
            >
              {quizLoading ? "Evaluating..." : "Submit Quiz & View Assessment"}
            </button>
          </div>
        )}

        {/* QUIZ RESULT */}

        {quizResult && (
          <div style={cardStyle}>
            <h2>Knowledge Assessment Report</h2>
            <h3>{quizResult.subject}</h3>
            <p>Student: {quizResult.student_name}</p>

            <div style={statsContainer}>
              <div style={statCard}>
                <h2>{quizResult.percentage}%</h2>
                <p>Overall Score</p>
              </div>

              <div style={statCard}>
                <h2>{quizResult.correct_answers}</h2>
                <p>Correct Answers</p>
              </div>

              <div style={statCard}>
                <h2>{quizResult.incorrect_answers}</h2>
                <p>Incorrect Answers</p>
              </div>

              <div style={statCard}>
                <h2>{quizResult.unanswered_questions}</h2>
                <p>Unanswered</p>
              </div>
            </div>

            <div style={summaryStyle}>
              <h3>{quizResult.assessment}</h3>
              <p>
                <strong>Readiness signal:</strong>{" "}
                {formatLabel(quizResult.readiness_signal)}
              </p>
              <p>
                This result reflects performance on this quiz, not formal
                course completion or institutional eligibility.
              </p>
            </div>

            {/* TOPIC-WISE ANALYSIS */}

            <h3>Topic-wise Knowledge Analysis</h3>

            {quizResult.topic_analysis?.length > 0 ? (
              quizResult.topic_analysis.map((topic, index) => (
                <div key={index} style={cardStyle}>
                  <h4>{topic.topic}</h4>
                  <p>
                    Score: {topic.correct_answers}/{topic.total_questions} (
                    {topic.percentage}%)
                  </p>
                  <p>
                    <strong>Assessment:</strong>{" "}
                    {formatLabel(topic.status || topic.interpretation || "Not available")}
                  </p>
                </div>
              ))
            ) : (
              <p>No topic analysis available.</p>
            )}

            {/* DIFFICULTY ANALYSIS */}

            <h3>Difficulty Analysis</h3>

            {getDifficultyEntries(quizResult.difficulty_analysis).length > 0 ? (
              getDifficultyEntries(quizResult.difficulty_analysis).map(
                ([difficulty, stats], index) => (
                  <div key={index} style={cardStyle}>
                    <strong>{formatLabel(difficulty)}</strong>
                    <p>
                      {stats.correct_answers}/{stats.total_questions} correct
                      {stats.percentage !== null &&
                      stats.percentage !== undefined
                        ? ` (${stats.percentage}%)`
                        : ""}
                    </p>
                  </div>
                )
              )
            ) : (
              <p>No difficulty analysis available.</p>
            )}

            {/* ANSWER REVIEW */}

            <h3>Answer Review</h3>

            {quizResult.answer_review?.length > 0 ? (
              quizResult.answer_review.map((answer, index) => (
                <div key={answer.question_id || index} style={cardStyle}>
                  <h4>
                    Question {index + 1} —{" "}
                    <span
                      style={{
                        color:
                          answer.status === "correct"
                            ? "#15803d"
                            : answer.status === "incorrect"
                              ? "#b91c1c"
                              : "#92400e"
                      }}
                    >
                      {formatLabel(answer.status)}
                    </span>
                  </h4>

                  <p>{answer.question}</p>

                  <p>
                    <strong>Topic:</strong> {answer.topic || "Not available"}
                  </p>

                  <p>
                    <strong>Your answer:</strong>{" "}
                    {answer.submitted_answer || answer.selected_option || "Not answered"}
                  </p>

                  <p>
                    <strong>Correct answer:</strong>{" "}
                    {answer.correct_answer || answer.correct_option || "Not available"}
                  </p>

                  <p>
                    <strong>Explanation:</strong>{" "}
                    {answer.explanation || "No explanation available."}
                  </p>
                </div>
              ))
            ) : (
              <p>No answer review available.</p>
            )}

            <div style={noticeStyle}>
              <strong>Assessment limitation:</strong>{" "}
              {quizResult.important_note ||
                "This quiz is an additional knowledge signal. It does not prove course completion, honesty, or institutional eligibility."}
            </div>

            <button
              type="button"
              onClick={() => {
                setQuizResult(null);
                setAnswers({});
                setQuizError("");
              }}
              style={buttonStyle}
            >
              Start Another Assessment
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

// ==========================================
// STYLES
// ==========================================

const pageStyle = {
  maxWidth: "1100px",
  margin: "30px auto",
  padding: "20px",
  fontFamily: "Arial, sans-serif",
  color: "#1f2937"
};

const headerStyle = {
  textAlign: "center",
  padding: "25px",
  background: "#eff6ff",
  borderRadius: "12px",
  marginBottom: "25px"
};

const formStyle = {
  padding: "25px",
  border: "1px solid #ddd",
  borderRadius: "12px",
  marginBottom: "25px",
  background: "#ffffff"
};

const inputStyle = {
  display: "block",
  width: "100%",
  padding: "12px",
  margin: "10px 0 20px",
  boxSizing: "border-box",
  border: "1px solid #ccc",
  borderRadius: "6px"
};

const buttonStyle = {
  padding: "13px 20px",
  background: "#2563eb",
  color: "white",
  border: "none",
  borderRadius: "6px",
  cursor: "pointer",
  fontWeight: "bold"
};

const submitButtonStyle = {
  ...buttonStyle,
  background: "#15803d",
  marginTop: "15px"
};

const sectionStyle = {
  marginTop: "30px"
};

const cardStyle = {
  border: "1px solid #ddd",
  borderRadius: "10px",
  padding: "18px",
  margin: "15px 0",
  background: "#ffffff"
};

const statsContainer = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
  gap: "15px",
  margin: "20px 0"
};

const statCard = {
  textAlign: "center",
  background: "#eff6ff",
  padding: "15px",
  borderRadius: "10px"
};

const errorStyle = {
  color: "#991b1b",
  background: "#fee2e2",
  padding: "15px",
  borderRadius: "8px",
  margin: "15px 0"
};

const loadingStyle = {
  background: "#eff6ff",
  color: "#1e40af",
  padding: "15px",
  borderRadius: "8px",
  margin: "15px 0",
  textAlign: "center"
};

const summaryStyle = {
  background: "#f3f4f6",
  padding: "15px",
  borderRadius: "10px",
  margin: "15px 0"
};

const missingStyle = {
  background: "#fef2f2",
  padding: "12px",
  borderRadius: "8px",
  marginTop: "12px"
};

const matchedStyle = {
  background: "#f0fdf4",
  padding: "12px",
  borderRadius: "8px",
  marginTop: "12px"
};

const restrictionStyle = {
  background: "#f5f3ff",
  color: "#5b21b6",
  padding: "12px",
  borderRadius: "8px",
  marginTop: "12px"
};

const verificationStyle = {
  background: "#fffbeb",
  color: "#92400e",
  padding: "12px",
  borderRadius: "8px",
  marginTop: "12px"
};

const infoStyle = {
  background: "#eff6ff",
  padding: "12px",
  borderRadius: "8px",
  marginTop: "12px"
};

const noticeStyle = {
  background: "#fef3c7",
  color: "#92400e",
  padding: "15px",
  borderRadius: "8px",
  marginTop: "15px"
};

const dividerStyle = {
  margin: "35px 0",
  border: "none",
  borderTop: "1px solid #ddd"
};

const quizHeaderStyle = {
  background: "#eff6ff",
  padding: "20px",
  borderRadius: "10px",
  marginBottom: "20px"
};

const questionStyle = {
  padding: "18px 0",
  borderBottom: "1px solid #e5e7eb"
};

const mutedStyle = {
  color: "#6b7280",
  fontSize: "13px"
};

const optionStyle = {
  display: "flex",
  alignItems: "flex-start",
  gap: "10px",
  padding: "12px",
  margin: "8px 0",
  border: "1px solid #e5e7eb",
  borderRadius: "7px",
  cursor: "pointer"
};

export default App;
