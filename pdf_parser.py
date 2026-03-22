import PyPDF2
import io
import re


def extract_text(file_bytes: bytes) -> str:
    """Read a PDF and return plain text. Returns empty string on failure."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        raw = "\n".join(pages)
        return _clean(raw)
    except Exception:
        return ""


def _clean(text: str) -> str:
    # collapse multiple blank lines, strip weird whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_name(text: str) -> str:
    """
    Very rough heuristic: the candidate's name is usually the first
    non-empty line that looks like 'First Last' (2-4 words, no digits).
    Falls back to 'Unknown' when nothing matches.
    """
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w.replace(".", "").isalpha() for w in words):
            return line
    return "Unknown"
