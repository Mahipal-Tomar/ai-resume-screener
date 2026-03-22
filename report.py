import csv
import io
from datetime import datetime


def to_csv(results: list[dict]) -> bytes:
    """
    Convert a list of screening result dicts into a CSV file (bytes).
    Suitable for st.download_button.
    """
    if not results:
        return b""

    fieldnames = [
        "Rank",
        "Candidate",
        "Score",
        "Verdict",
        "Matched Skills",
        "Missing Skills",
        "Strengths",
        "Red Flags",
        "Summary",
    ]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()

    # sort by score descending before writing
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)

    for rank, r in enumerate(sorted_results, start=1):
        writer.writerow({
            "Rank":           rank,
            "Candidate":      r.get("candidate", "Unknown"),
            "Score":          r.get("score", 0),
            "Verdict":        r.get("verdict", ""),
            "Matched Skills": ", ".join(r.get("matched_skills", [])),
            "Missing Skills": ", ".join(r.get("missing_skills", [])),
            "Strengths":      r.get("strengths", ""),
            "Red Flags":      r.get("red_flags", ""),
            "Summary":        r.get("summary", ""),
        })

    return buf.getvalue().encode("utf-8")


def report_filename() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return f"screening_report_{ts}.csv"
