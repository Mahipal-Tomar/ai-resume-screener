# 📋 AI Resume Screening System

An end-to-end AI-powered recruitment tool that screens multiple resumes against a Job Description, ranks candidates by match score, flags missing skills, generates interview questions for shortlisted candidates, and exports a full report as CSV.

Built with Python, Google Gemini 1.5 Flash, and Streamlit.

---

## Features

- Bulk PDF resume upload (screen 10+ resumes at once)
- JD-based AI scoring out of 100
- Matched skills and missing skills detection
- Auto-shortlisting above a configurable score threshold
- AI-generated interview questions for shortlisted candidates
- Executive summary for HR managers
- One-click CSV report download
- Clean, responsive dark-mode UI

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| AI / LLM | Google Gemini 1.5 Flash API |
| NLP | Prompt-based text analysis, keyword extraction |
| PDF Parsing | PyPDF2 |
| UI | Streamlit |
| Data Export | CSV via Python stdlib |

---

## Project Structure

```
ai_resume_screener/
├── app.py          # Streamlit UI and app flow
├── screener.py     # Gemini API calls and AI logic
├── pdf_parser.py   # PDF text extraction and name detection
├── report.py       # CSV report generation
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/ai-resume-screener.git
cd ai-resume-screener
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Gemini API key
Go to https://aistudio.google.com/apikey, sign in with Google, and create a key. No credit card needed.

### 4. Run
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## How to Use

1. Paste your API key in the sidebar
2. Set the shortlist threshold (default 60/100)
3. Paste the job description
4. Upload one or more resume PDFs
5. Click **Screen All Resumes**
6. View ranked results, matched/missing skills, interview questions
7. Download the CSV report

---

## Resume Bullet Points (for your resume)

```
AI Resume Screening System          Python, Gemini API, Streamlit, NLP, PyPDF2
• Built end-to-end AI recruitment tool that screens bulk PDF resumes against
  a JD using Google Gemini 1.5 Flash — scoring candidates 0-100 with matched
  skills, missing skills, and auto-shortlisting.
• Implemented NLP-based keyword extraction, interview question generation for
  shortlisted candidates, and one-click CSV report export for HR managers.
• Deployed on Streamlit Cloud with multi-file upload, configurable thresholds,
  and executive summary generation — covering GenAI, automation, and APIs.
```

---

## License

MIT
