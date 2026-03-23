import streamlit as st
import ollama
import json
import os
import re
from datetime import datetime
from PyPDF2 import PdfReader
from docx import Document

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Adaptive Study Explainer", layout="centered")
st.title("🧠 Adaptive Study Explainer")

MEMORY_FILE = "user_data.json"

# -------------------------
# SAFE UI STYLE (NO SCROLL BUG)
# -------------------------
st.markdown("""
<style>
.block-container {
    max-width: 850px;
    margin: auto;
}

.card {
    padding: 18px;
    border-radius: 12px;
    background-color: #f9fafb;
    margin-bottom: 20px;
    border: 1px solid #e5e7eb;
    overflow: visible;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# MEMORY (SAFE + MIGRATION)
# -------------------------
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)

                # OLD FORMAT FIX
                if isinstance(data, dict) and "progress" in data:
                    new_data = {}
                    for topic, score in data["progress"].items():
                        new_data[topic] = {
                            "score": score,
                            "last_seen": str(datetime.now()),
                            "history": []
                        }
                    save_memory(new_data)
                    return new_data

                # Ensure valid structure
                for t, v in data.items():
                    if not isinstance(v, dict) or "score" not in v:
                        data[t] = {
                            "score": 50,
                            "last_seen": str(datetime.now()),
                            "history": []
                        }

                return data
        except:
            return {}

    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_memory(topic, score):
    memory = load_memory()

    if topic not in memory:
        memory[topic] = {
            "score": 50,
            "last_seen": str(datetime.now()),
            "history": []
        }

    memory[topic]["score"] = int((memory[topic]["score"] + score) / 2)
    memory[topic]["last_seen"] = str(datetime.now())
    memory[topic]["history"].append(score)

    save_memory(memory)

# -------------------------
# SESSION STATE
# -------------------------
for key in ["stage", "questions", "answers", "explanation", "summary", "doc_summary", "doc_text"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key != "stage" else "input"

# -------------------------
# INPUT
# -------------------------
topic = st.text_input("Enter a topic")
level = st.selectbox("Select your level", ["Beginner", "Intermediate", "Advanced"])
use_questions = st.checkbox("Adaptive Mode")
uploaded_file = st.file_uploader("Upload PDF or Word file", type=["pdf", "docx"])

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
        st.error(f"File error: {e}")

    return text[:5000]

# -------------------------
# SAFE AI CALL
# -------------------------
def safe_chat(prompt):
    try:
        response = ollama.chat(
            model='phi3',
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']
    except Exception:
        st.error("⚠️ Ollama not running. Run: ollama run phi3")
        return "AI unavailable"

# -------------------------
# AI FUNCTIONS
# -------------------------
def generate_doc_summary(text):
    return safe_chat(f"""
Summarize clearly in 5 bullet points:
{text}
""")

def generate_questions(text):
    return safe_chat(f"""
From this content:

{text}

Generate:
1. Conceptual question
2. Application question
3. Edge-case question
""")

def evaluate_understanding(answers):
    result = safe_chat(f"""
Evaluate this answer:

"{answers}"

Return ONLY a number (0-100).
""")

    try:
        match = re.search(r'\d+', result)
        return int(match.group()) if match else 50
    except:
        return 50

def generate_explanation(topic, level, answers, text):
    memory = load_memory()

    weak_topics = []
    for t, v in memory.items():
        if isinstance(v, dict) and v.get("score", 50) < 50:
            weak_topics.append(t)

    return safe_chat(f"""
Teach topic: {topic}

Level: {level}
Weak areas: {weak_topics}
User answers: {answers}

Context:
{text}

Structure:
- Simple explanation
- Key concepts (bullets)
- Example
- Common mistakes
""")

def generate_summary(explanation):
    return safe_chat(f"""
Summarize in 5 bullet points:
{explanation}
""")

# -------------------------
# FLOW
# -------------------------
if st.button("Start Learning"):

    if not topic and not uploaded_file:
        st.warning("Enter a topic or upload a file")
    else:
        if uploaded_file:
            st.session_state.doc_text = extract_text(uploaded_file)
            st.session_state.doc_summary = generate_doc_summary(st.session_state.doc_text)

        if use_questions:
            st.session_state.questions = generate_questions(st.session_state.doc_text)
            st.session_state.stage = "questions"
        else:
            st.session_state.stage = "explain"

# -------------------------
# DOC SUMMARY
# -------------------------
if st.session_state.doc_summary:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📄 Document Summary")
    st.write(st.session_state.doc_summary)
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# QUESTIONS
# -------------------------
if st.session_state.stage == "questions":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("### 🤔 Questions")
    st.write(st.session_state.questions)

    answers = st.text_area("Your answers")

    if st.button("Submit Answers"):
        st.session_state.answers = answers
        st.session_state.stage = "explain"

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# EXPLANATION
# -------------------------
if st.session_state.stage == "explain":

    with st.spinner("Generating explanation..."):

        explanation = generate_explanation(
            topic,
            level,
            st.session_state.answers,
            st.session_state.doc_text
        )

        summary = generate_summary(explanation)

        score = evaluate_understanding(st.session_state.answers)
        update_memory(topic, score)

        st.session_state.explanation = explanation
        st.session_state.summary = summary
        st.session_state.stage = "done"

# -------------------------
# OUTPUT
# -------------------------
if st.session_state.stage == "done":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📘 Explanation")
    st.write(st.session_state.explanation)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⚡ Summary")
    st.write(st.session_state.summary)
    st.markdown('</div>', unsafe_allow_html=True)

    memory = load_memory()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📊 Progress")

    for t, data in memory.items():
        score = data.get("score", 50)
        st.write(f"**{t}** ({score}%)")
        st.progress(score / 100)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🔥 Topic Strength")

    for t, data in memory.items():
        score = data.get("score", 50)

        if score < 40:
            label = "🔴 Weak"
        elif score < 70:
            label = "🟡 Moderate"
        else:
            label = "🟢 Strong"

        st.write(f"{t}: {label} ({score}%)")

    st.markdown('</div>', unsafe_allow_html=True)

    # IMPORTANT: prevents scroll cutoff
    st.write("")
    st.write("")
    st.write("")

    if st.button("Start New"):
        for k in list(st.session_state.keys()):
            st.session_state[k] = "" if k != "stage" else "input"
