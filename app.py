
import gradio as gr

from memory.student_memory import load_student
from agents.coordinator_agent import coordinator_agent
from agents.recommendation_agent import recommendation_agent
from tools.llm_advisor import explain_recommendations
from tools.student_feedback import save_feedback


def advise(name, completed, interests):
    completed_subjects = [
        item.strip() for item in completed.split(",") if item.strip()
    ]
    interest_list = [
        item.strip() for item in interests.split(",") if item.strip()
    ]

    if not interest_list:
        return "Enter at least one interest.", ""

    student = {
        "name": name.strip() or "Student",
        "completed_subjects": completed_subjects,
        "interests": interest_list
    }

    result = coordinator_agent(completed_subjects, interest_list)
    courses = result["recommendations"]

    if not courses:
        return "No matching courses found. Try different interests.", ""

    try:
        advice_text = explain_recommendations(student, courses)
    except Exception as exc:
        advice_text = f"Could not generate AI advice: {exc}"

    course_text = "\n\n".join(
        f"**{course['subject']}** — {course['credits']}\n\n"
        f"{course['description'][:500]}"
        for course in courses[:5]
    )

    return course_text, advice_text


def submit_feedback(selected, feedback):
    if not selected:
        return "Please enter at least one department code."

    selected_courses = [
        item.strip().upper()
        for item in selected.split(",")
        if item.strip()
    ]

    save_feedback(selected_courses, feedback)
    return "Thank you! Your feedback has been saved."


with gr.Blocks(title="Student Academic Advisor") as demo:
    gr.Markdown("# 🎓 Student Academic Advisor")
    gr.Markdown(
        "Explore course matches and receive AI-generated explanations. "
        "Demo data uses the University of Illinois course catalogue."
    )

    with gr.Row():
        name = gr.Textbox(label="Student name", value="Student 1")
        completed = gr.Textbox(
            label="Completed subjects (comma-separated)",
            value="Python, Machine Learning"
        )

    interests = gr.Textbox(
        label="Interests (comma-separated)",
        value="artificial intelligence, machine learning"
    )

    run_button = gr.Button("Get Academic Advice", variant="primary")

    course_output = gr.Markdown(label="Course Matches")
    advice_output = gr.Markdown(label="AI Academic Advice")

    run_button.click(
        fn=advise,
        inputs=[name, completed, interests],
        outputs=[course_output, advice_output]
    )

    gr.Markdown("## Human-Agent Feedback")
    selected = gr.Textbox(
        label="Departments you want to explore",
        placeholder="e.g. ABE, BADM"
    )
    feedback = gr.Textbox(
        label="Was the recommendation useful? Why or why not?"
    )
    feedback_button = gr.Button("Save Feedback")
    feedback_output = gr.Textbox(label="Feedback Status")

    feedback_button.click(
        fn=submit_feedback,
        inputs=[selected, feedback],
        outputs=feedback_output
    )

demo.launch()
