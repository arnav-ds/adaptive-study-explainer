#  Adaptive Study Explainer

An AI-powered local learning assistant that explains topics based on user understanding and uploaded documents.

Built using lightweight architecture (no vector databases or embeddings) for fast, offline performance.

---

##  Features

###  Document Understanding
- Upload PDF or Word documents
- Extracts and analyzes content locally
- Generates concise summaries (100–200 words)

###  Adaptive Learning Mode
- AI asks targeted questions before teaching
- Understands user knowledge level and gaps
- Adjusts explanation accordingly

###  Personalized Explanations
- Tailored based on:
  - User level (Beginner / Intermediate / Advanced)
  - User answers
  - Document context

###  Smart Summarization
- Generates short summaries of explanations
- Helps quick revision and understanding

###  Lightweight Memory
- Tracks weak topics based on user responses
- No complex embeddings or vector databases
- Simple and efficient JSON-based storage

---

##  Tech Stack

- Python
- Streamlit
- Ollama (phi3 model)
- PyPDF2 (PDF parsing)
- python-docx (Word parsing)

---

##  How It Works

1. User enters a topic or uploads a document  
2. AI optionally asks diagnostic questions  
3. User responses are analyzed  
4. AI generates:
   - Explanation
   - Summary
5. Weak topics are stored for future adaptation  

---

## How to Run

```bash
pip install -r requirements.txt
ollama run phi3
streamlit run app.py
