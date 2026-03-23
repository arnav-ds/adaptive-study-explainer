import streamlit as st
import ollama
import json
import os
from PyPDF2 import PdfReader
from docx import Document

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Adaptive Study Explainer", layout="centered")

st.title(" Adaptive Study Explainer")

MEMORY_FILE = "user_data.json"

# -------------------------
# MEMORY FUNCTIONS
# -------------------------

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_memory(topic, answers):
    if not topic or topic.strip() == "":
        return  # don't store empty topics

    memory = load_memory()
    weak_topics = memory.get("weak_topics", [])

    answers_lower = answers.lower()

    weak_signals = ["don't", "dont", "hard", "confusing", "difficult", "not sure"]

    if any(word in answers_lower for word in weak_signals):
        if topic not in weak_topics:
            weak_topics.append(topic)

    memory["weak_topics"] = weak_topics

    save_memory(memory)
# -------------------------
# SESSION STATE
# -------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "input"

if "questions" not in st.session_state:
    st.session_state.questions = ""

if "answers" not in st.session_state:
    st.session_state.answers = ""

if "explanation" not in st.session_state:
    st.session_state.explanation = ""

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "doc_summary" not in st.session_state:
    st.session_state.doc_summary = ""

# -------------------------
# INPUT
# -------------------------
topic = st.text_input("Enter a topic")

level = st.selectbox(
    "Select your level",
    ["Beginner", "Intermediate", "Advanced"]
)

use_questions = st.checkbox("Let AI ask me questions first (adaptive mode)")

uploaded_file = st.file_uploader(
    "Upload PDF or Word file",
    type=["pdf", "docx"]
)

# -------------------------
# FILE PROCESSING
# -------------------------
def extract_text(file):
    text = ""
    try:
        if file.name.endswith(".pdf"):
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif file.name.endswith(".docx"):
            doc = Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return text

# -------------------------
# AI FUNCTIONS
# -------------------------

def generate_doc_summary(text):
    prompt = f"Summarize this in 100-200 words:\n{text[:4000]}"
    return ollama.chat(model='phi3', messages=[{"role": "user", "content": prompt}])['message']['content']


def generate_questions(context_text):
    prompt = f"""
    Based on this content:

    {context_text[:3000]}

    Generate 3 short, specific learning questions.
    """
    return ollama.chat(model='phi3', messages=[{"role": "user", "content": prompt}])['message']['content']


def generate_explanation(topic, level, answers, context_text):
    memory = load_memory()

    weak_topics = memory.get("weak_topics", [])

    prompt = f"""
    Teach: {topic}

    User level: {level}

    Known weak topics:
    {weak_topics}

    User answers:
    {answers}

    Context:
    {context_text[:3000]}

    Instructions:
    - Focus more if topic is in weak_topics
    - Adapt to user answers
    - Keep it simple and structured
    - Use examples
    """

    return ollama.chat(model='phi3', messages=[{"role": "user", "content": prompt}])['message']['content']


def generate_summary(explanation):
    prompt = f"Summarize in 100-150 words:\n{explanation}"
    return ollama.chat(model='phi3', messages=[{"role": "user", "content": prompt}])['message']['content']

# -------------------------
# FLOW
# -------------------------

if st.button("Start Learning"):

    if topic or uploaded_file:

        context_text = ""

        if uploaded_file:
            context_text = extract_text(uploaded_file)
            st.session_state.doc_summary = generate_doc_summary(context_text)

        if use_questions:
            st.session_state.questions = generate_questions(context_text)
            st.session_state.stage = "questions"
        else:
            st.session_state.stage = "explain"

# -------------------------
# SHOW SUMMARY
# -------------------------
if st.session_state.doc_summary:
    st.markdown("### 📄 Document Summary")
    st.write(st.session_state.doc_summary)

# -------------------------
# QUESTIONS
# -------------------------
if st.session_state.stage == "questions":
    st.markdown("### 🤔 Answer these:")

    st.write(st.session_state.questions)

    user_answers = st.text_area("Your answers")

    if st.button("Submit Answers"):
        st.session_state.answers = user_answers

        # UPDATE MEMORY HERE
        update_memory(topic, user_answers)

        st.session_state.stage = "explain"

# -------------------------
# EXPLANATION
# -------------------------
if st.session_state.stage == "explain":

    context_text = ""
    if uploaded_file:
        context_text = extract_text(uploaded_file)

    explanation = generate_explanation(
        topic,
        level,
        st.session_state.answers,
        context_text
    )

    summary = generate_summary(explanation)

    st.session_state.explanation = explanation
    st.session_state.summary = summary
    st.session_state.stage = "done"

# -------------------------
# OUTPUT
# -------------------------
if st.session_state.stage == "done":

    st.markdown("### 📘 Explanation")
    st.write(st.session_state.explanation)

    st.markdown("### ⚡ Summary")
    st.write(st.session_state.summary)

    st.markdown("### 🧠 Your Learning Profile")
    st.json(load_memory())

    if st.button("Start New"):
        st.session_state.stage = "input"
        st.session_state.answers = ""
        st.session_state.questions = ""
        st.session_state.explanation = ""
        st.session_state.summary = ""
        st.session_state.doc_summary = ""