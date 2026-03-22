import json
from groq import Groq


# one client instance per session is enough
_client = None
MODEL = "llama3-8b-8192"   # fast, free, good at JSON


def init(api_key: str):
    global _client
    _client = Groq(api_key=api_key)


def _call(prompt: str) -> str:
    if _client is None:
        raise RuntimeError("Call init() first.")
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _parse_json(raw: str) -> dict:
    # strip markdown fences if the model added them
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


# ── public API ────────────────────────────────────────────────────────────────

def screen_resume(resume_text: str, jd: str, candidate_name: str) -> dict:
    """
    Send one resume + JD to Gemini and get back a structured evaluation.
    Returns a dict with score, verdict, matched_skills, missing_skills,
    strengths, red_flags, and a short summary.
    """
    prompt = f"""
You are a senior technical recruiter at an AI product company.
Evaluate the resume below against the job description and return ONLY
a JSON object — no explanation, no markdown fences.

Candidate name: {candidate_name}

Job Description:
{jd[:1800]}

Resume:
{resume_text[:2500]}

Return this exact JSON structure:
{{
  "score": <integer 0-100>,
  "verdict": "<Strong Match | Good Match | Average Match | Weak Match>",
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "strengths": "<2 sentences max>",
  "red_flags": "<1 sentence or 'None'>",
  "summary": "<3 sentences — suitability for the role>"
}}
"""
    raw = _call(prompt)
    result = _parse_json(raw)

    # safety: make sure score is an int
    result["score"] = int(result.get("score", 0))
    result["candidate"] = candidate_name
    return result


def generate_interview_questions(resume_text: str, jd: str, n: int = 3) -> list[str]:
    """Return n role-specific interview questions for a shortlisted candidate."""
    prompt = f"""
You are a technical interviewer. Based on the job description and resume
generate exactly {n} interview questions.

Mix: technical + domain-specific + one behavioural.
Keep each question under 25 words.

Job Description: {jd[:800]}
Resume snippet: {resume_text[:800]}

Return ONLY a JSON array of strings. Example:
["Question one?", "Question two?", "Question three?"]
"""
    raw = _call(prompt)
    questions = json.loads(raw.replace("```json", "").replace("```", "").strip())
    return questions[:n]


def summarise_batch(results: list[dict], jd: str) -> str:
    """One-paragraph executive summary for the whole screening batch."""
    scores = [r["score"] for r in results]
    verdicts = [f"{r['candidate']} ({r['score']}/100)" for r in results]
    prompt = f"""
Write a 3-sentence executive summary for an HR manager.
You screened {len(results)} resumes for this role.
Top candidates by score: {', '.join(verdicts[:5])}.
Average score: {sum(scores)//len(scores) if scores else 0}.
Job role context: {jd[:300]}
Keep it professional and concise.
"""
    return _call(prompt)
