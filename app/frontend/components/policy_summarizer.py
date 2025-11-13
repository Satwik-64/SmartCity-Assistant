# Placeholder for policy_summarizer.py

"""Simple policy summariser that highlights policy points from a document."""

from __future__ import annotations

import html
import io
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import streamlit as st

# Ensure backend packages resolve when executed via ``streamlit run``
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


API_BASE_URL = "http://localhost:8000/api/policy"


def render_policy_summarizer() -> None:
    """Render a minimal interface to extract policy statements from a document."""

    st.header("📋 Policy Summariser")
    st.caption("Upload a policy document or paste its contents to surface the key policy statements.")

    text_source = st.radio(
        "Choose input method",
        options=("Upload document", "Paste text"),
        horizontal=True,
    )

    extracted_text: str | None = None

    if text_source == "Upload document":
        uploaded_file = st.file_uploader(
            "Select a policy document",
            type=["txt", "pdf", "docx"],
            help="Upload .txt, .pdf, or .docx files. PDFs and Word files require optional Python packages.",
        )
        if uploaded_file is not None:
            extracted_text, error = load_text_from_upload(uploaded_file)
            if error:
                st.error(error)
                extracted_text = None
            elif extracted_text:
                word_count = max(len(extracted_text.split()), 1)
                st.success(
                    f"Loaded {Path(uploaded_file.name).suffix.upper()} document with approximately {word_count} words."
                )
    else:
        extracted_text = st.text_area(
            "Paste policy text",
            placeholder="Paste the policy document content here...",
            height=260,
        ).strip() or None

    if st.button("🔍 Identify Policies", use_container_width=True):
        if not extracted_text:
            st.warning("Provide a document or paste text before requesting a summary.")
            return

        with st.spinner("Analyzing policy content..."):
            summary_response = request_policy_summary(extracted_text)

        if summary_response.get("error"):
            st.error(summary_response["error"])
            return

        summary_text = summary_response.get("summary", "")
        if not summary_text:
            st.info("The service did not return any policy summary. Try a longer document.")
            return

        policy_points = extract_policy_points(summary_text)

        st.subheader("Identified Policy Highlights")
        for point in policy_points:
            st.markdown(f"- {html.escape(point)}")

        with st.expander("Full summary text", expanded=False):
            st.write(summary_text)


def request_policy_summary(policy_text: str) -> Dict[str, str]:
    """Send policy text to the backend and return the JSON response."""

    payload = {"text": policy_text, "summary_type": "citizen-friendly"}
    try:
        response = requests.post(
            f"{API_BASE_URL}/summarize",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data: Dict[str, str] = response.json()
    except requests.exceptions.RequestException as exc:
        return {"error": f"Failed to contact the policy service: {exc}"}
    except ValueError:
        return {"error": "Received an invalid response from the policy service."}

    if isinstance(data, dict) and data.get("status") == "success":
        return data

    detail = data.get("detail") if isinstance(data, dict) else "Unexpected response format."
    return {"error": f"Policy service returned an error: {detail}"}


def extract_policy_points(summary_text: str) -> List[str]:
    """Convert a summary paragraph into bullet-ready policy statements."""

    lines = [line.strip("•- \t ") for line in summary_text.splitlines() if line.strip()]
    if lines:
        return lines

    sentences: List[str] = []
    current = []
    for char in summary_text:
        current.append(char)
        if char in {".", "!", "?"}:
            sentence = "".join(current).strip()
            if sentence:
                sentences.append(sentence)
            current = []

    if current:
        sentence = "".join(current).strip()
        if sentence:
            sentences.append(sentence)

    if not sentences:
        return [summary_text.strip()]

    return sentences[:8]


def load_text_from_upload(uploaded_file) -> Tuple[str | None, str | None]:
    """Extract text from an uploaded policy document.

    Returns a tuple of (text, error_message). When extraction succeeds, the
    error message is ``None``. On failure, the text is ``None`` and a human
    readable error is provided.
    """

    file_bytes = uploaded_file.getvalue()
    suffix = Path(uploaded_file.name or "").suffix.lower()

    if suffix == ".txt" or uploaded_file.type == "text/plain":
        for encoding in ("utf-8", "latin-1"):
            try:
                text = file_bytes.decode(encoding)
                return text.strip(), None
            except UnicodeDecodeError:
                continue
        return None, "Unable to decode the text file. Please ensure it is UTF-8 encoded."

    if suffix == ".pdf":
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return None, "PDF support requires the PyPDF2 package. Install it with `pip install PyPDF2`."

        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            return None, "No text could be extracted from the PDF. Ensure it contains selectable text."
        return text, None

    if suffix == ".docx":
        try:
            import docx  # type: ignore
        except ImportError:
            return None, "Word support requires the python-docx package. Install it with `pip install python-docx`."

        document = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join(par.text for par in document.paragraphs).strip()
        if not text:
            return None, "The Word document does not contain readable text."
        return text, None

    return None, "Unsupported file type. Please upload a .txt, .pdf, or .docx file."


if __name__ == "__main__":
    render_policy_summarizer()