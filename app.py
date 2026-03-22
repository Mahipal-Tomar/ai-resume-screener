import streamlit as st
import time

from pdf_parser import extract_text, extract_name
from screener import init, screen_resume, generate_interview_questions, summarise_batch
from report import to_csv, report_filename


# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Screener AI",
    page_icon="📋",
    layout="wide",
)

# ── styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: #0d1117; }

    .top-banner {
        background: linear-gradient(135deg, #1a3a6b 0%, #1e40af 100%);
        padding: 1.8rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
    }
    .top-banner h1 { color: #fff; margin: 0; font-size: 1.9rem; }
    .top-banner p  { color: #93c5fd; margin: 0.4rem 0 0; font-size: 0.95rem; }

    .card {
        background: #161b27;
        border: 1px solid #1e2d4a;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }

    .score-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .pill-green  { background: #14532d; color: #4ade80; }
    .pill-blue   { background: #1e3a5f; color: #60a5fa; }
    .pill-yellow { background: #422006; color: #fbbf24; }
    .pill-red    { background: #450a0a; color: #f87171; }

    .tag {
        display: inline-block;
        background: #1e2d4a;
        color: #93c5fd;
        padding: 0.15rem 0.55rem;
        border-radius: 6px;
        font-size: 0.75rem;
        margin: 0.15rem;
    }
    .tag-miss {
        background: #2d1e1e;
        color: #fca5a5;
    }

    .section-title {
        color: #60a5fa;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid #1e2d4a;
        padding-bottom: 0.3rem;
    }

    .stTextArea textarea, .stTextInput input {
        background: #161b27 !important;
        color: #e2e8f0 !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 8px !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1a3a6b, #2563eb) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
    }

    /* progress bar */
    div[data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #2563eb, #60a5fa) !important;
    }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
def verdict_pill(verdict: str) -> str:
    mapping = {
        "Strong Match": "pill-green",
        "Good Match":   "pill-blue",
        "Average Match":"pill-yellow",
        "Weak Match":   "pill-red",
    }
    css = mapping.get(verdict, "pill-yellow")
    return f'<span class="score-pill {css}">{verdict}</span>'


def score_color(score: int) -> str:
    if score >= 75:
        return "#4ade80"
    if score >= 50:
        return "#60a5fa"
    if score >= 30:
        return "#fbbf24"
    return "#f87171"


# ── session defaults ──────────────────────────────────────────────────────────
defaults = {
    "results": [],
    "exec_summary": "",
    "screened": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-banner">
    <h1>📋 AI Resume Screening System</h1>
    <p>Upload multiple resumes · Paste a Job Description · Get AI-ranked candidates instantly</p>
</div>
""", unsafe_allow_html=True)


# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    st.markdown("---")
    shortlist_threshold = st.slider(
        "Shortlist threshold (score ≥)",
        min_value=40, max_value=90, value=60, step=5
    )
    num_interview_qs = st.slider(
        "Interview questions per candidate",
        min_value=2, max_value=5, value=3
    )

    st.markdown("---")
    st.markdown("**📦 Tech Stack**")
    for tag in ["Python", "Groq API", "LLaMA 3", "Streamlit", "NLP", "PyPDF2"]:
        st.markdown(f'<span class="tag">{tag}</span>', unsafe_allow_html=True)


# ── main layout ───────────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="section-title">📄 Job Description</div>', unsafe_allow_html=True)
    jd = st.text_area(
        label="jd",
        label_visibility="collapsed",
        height=260,
        placeholder="Paste the full job description here...\n\nExample:\nRole: AI Engineer\nSkills: Python, ML, NLP, GenAI...",
    )

with right:
    st.markdown('<div class="section-title">📎 Upload Resumes (PDF)</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        label="resumes",
        label_visibility="collapsed",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} resume(s) uploaded")
        for f in uploaded_files:
            st.caption(f"• {f.name}")


st.markdown("<br>", unsafe_allow_html=True)
run_btn = st.button("🚀 Screen All Resumes")


# ── screening logic ───────────────────────────────────────────────────────────
if run_btn:
    if not jd.strip():
        st.error("❌ Please paste the job description.")
    elif not uploaded_files:
        st.error("❌ Please upload at least one resume PDF.")
    else:
        init()
        results = []
        progress = st.progress(0)
        status   = st.empty()

        for i, file in enumerate(uploaded_files):
            status.info(f"🔍 Screening {file.name} ... ({i+1}/{len(uploaded_files)})")
            raw_bytes = file.read()
            text = extract_text(raw_bytes)

            if not text:
                st.warning(f"⚠️ Could not extract text from {file.name} — skipping.")
                continue

            name = extract_name(text)
            try:
                result = screen_resume(text, jd, name)
                result["filename"] = file.name
                results.append(result)
            except Exception as e:
                st.warning(f"⚠️ Error processing {file.name}: {e}")

            progress.progress((i + 1) / len(uploaded_files))
            time.sleep(0.4)   # avoid hammering the API

        status.empty()
        progress.empty()

        if results:
            # sort by score
            results.sort(key=lambda x: x["score"], reverse=True)

            # generate exec summary
            with st.spinner("✍️ Generating executive summary..."):
                try:
                    st.session_state.exec_summary = summarise_batch(results, jd)
                except Exception:
                    st.session_state.exec_summary = ""

            st.session_state.results  = results
            st.session_state.screened = True
            st.rerun()
        else:
            st.error("No resumes could be processed. Check your PDF files.")


# ── results ───────────────────────────────────────────────────────────────────
if st.session_state.screened and st.session_state.results:
    results = st.session_state.results

    st.markdown("---")
    st.markdown("## 📊 Screening Results")

    # ── top metrics ──
    total      = len(results)
    shortlisted = [r for r in results if r["score"] >= shortlist_threshold]
    avg_score  = sum(r["score"] for r in results) // total

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Screened",  total)
    m2.metric("Shortlisted",     len(shortlisted))
    m3.metric("Avg Score",       f"{avg_score}/100")
    m4.metric("Top Score",       f"{results[0]['score']}/100")

    # ── exec summary ──
    if st.session_state.exec_summary:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**🗒️ Executive Summary**")
        st.write(st.session_state.exec_summary)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── download button ──
    csv_bytes = to_csv(results)
    st.download_button(
        label="⬇️ Download Full Report (CSV)",
        data=csv_bytes,
        file_name=report_filename(),
        mime="text/csv",
    )

    st.markdown("---")

    # ── tabs: shortlisted vs all ──
    tab1, tab2 = st.tabs([
        f"✅ Shortlisted ({len(shortlisted)})",
        f"📋 All Candidates ({total})"
    ])

    def render_candidate(r: dict, rank: int, show_questions: bool = False):
        sc = r["score"]
        col_a, col_b = st.columns([3, 1])

        with col_a:
            st.markdown(
                f"**#{rank} — {r['candidate']}**  &nbsp; {verdict_pill(r['verdict'])}",
                unsafe_allow_html=True
            )
            st.caption(f"📁 {r.get('filename', '')}")

        with col_b:
            st.markdown(
                f"<h2 style='color:{score_color(sc)};text-align:right;margin:0'>{sc}</h2>"
                f"<p style='color:#94a3b8;text-align:right;margin:0;font-size:0.75rem'>out of 100</p>",
                unsafe_allow_html=True
            )

        st.progress(sc / 100)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✅ Matched Skills**")
            tags = " ".join(f'<span class="tag">{s}</span>' for s in r.get("matched_skills", []))
            st.markdown(tags or "—", unsafe_allow_html=True)
        with c2:
            st.markdown("**❌ Missing Skills**")
            tags = " ".join(f'<span class="tag tag-miss">{s}</span>' for s in r.get("missing_skills", []))
            st.markdown(tags or "—", unsafe_allow_html=True)

        with st.expander("📝 Detailed Analysis"):
            st.markdown(f"**Strengths:** {r.get('strengths','—')}")
            st.markdown(f"**Red Flags:** {r.get('red_flags','None')}")
            st.markdown(f"**Summary:** {r.get('summary','—')}")

            if show_questions and api_key:
                st.markdown("---")
                st.markdown("**🎯 Suggested Interview Questions**")
                # lazy-load questions only when expander is opened
                key = f"qs_{r['candidate']}"
                if key not in st.session_state:
                    with st.spinner("Generating questions..."):
                        try:
                            init()
                            qs = generate_interview_questions(
                                r.get("summary", ""), jd, num_interview_qs
                            )
                            st.session_state[key] = qs
                        except Exception:
                            st.session_state[key] = []
                for qi, q in enumerate(st.session_state.get(key, []), 1):
                    st.markdown(f"**Q{qi}.** {q}")

        st.markdown("<hr style='border-color:#1e2d4a;margin:0.8rem 0'>", unsafe_allow_html=True)

    with tab1:
        if shortlisted:
            for rank, r in enumerate(shortlisted, 1):
                render_candidate(r, rank, show_questions=True)
        else:
            st.info(f"No candidates scored ≥ {shortlist_threshold}. Lower the threshold in the sidebar.")

    with tab2:
        for rank, r in enumerate(results, 1):
            render_candidate(r, rank, show_questions=False)

    # reset button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Start New Screening"):
        st.session_state.results      = []
        st.session_state.exec_summary = ""
        st.session_state.screened     = False
        # clear any cached interview questions
        for k in list(st.session_state.keys()):
            if k.startswith("qs_"):
                del st.session_state[k]
        st.rerun()
