import os
import re
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader


load_dotenv()

DEFAULT_MODEL_NAME = "qwen/qwen3.6-27b"
MAX_RESUME_CHARACTERS = 30000


def get_configured_api_key() -> str:
    """Read the API key from Streamlit Cloud secrets or a local environment variable."""
    try:
        return str(st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", "")))
    except FileNotFoundError:
        return os.getenv("GROQ_API_KEY", "")


def extract_resume_text(pdf_bytes: bytes) -> str:
    """Extract readable text from every page in an uploaded PDF."""
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def build_analysis_prompt(resume_text: str, job_role: str) -> str:
    return f"""
You are an expert resume coach and recruiter. Analyze the resume below for the target job role: {job_role}.

Return a complete report in Markdown with exactly these sections. Keep the entire response under 2100
tokens so that every section is completed. You must finish section 6 before stopping. Explain the
reasoning behind each recommendation, refer to specific resume content when possible, and use up to 4
focused bullets per section.
Use the headings below exactly, in this order. Do not add an introduction, conclusion, or reasoning outside these sections.

## 1. Content Clarity & Impact
Assess clarity, relevance, measurable achievements, action verbs, and keyword alignment. Quote short examples when useful.

## 2. Skills Presentation
Evaluate how technical, soft, and role-specific skills are grouped, prioritized, and supported by evidence.

## 3. Experience Descriptions
Review the strength of each experience description. Identify vague bullets and explain how to make them achievement-focused.

## 4. Specific Recommendations for {job_role}
Give prioritized changes for this role, including missing keywords, projects, evidence, or sections. Be concrete.

## 5. Overall Rating & Checklist
Give an overall score out of 10, then provide a checklist with strengths, high-priority fixes, and ATS/readability checks.

## 6. Refined Resume
Provide a concise improved version of the resume content in a few bullets. Preserve facts from the source and never invent employers, dates, degrees, metrics, or skills. Use placeholders such as [add metric] when information is missing.

Resume text:
---
{resume_text[:MAX_RESUME_CHARACTERS]}
---
""".strip()


def analyze_resume(resume_text: str, job_role: str, api_key: str, model_name: str) -> str:
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured. Add it to a .env file or your environment.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        temperature=0.2,
        max_tokens=2400,
        reasoning_effort="none",
        messages=[
            {
                "role": "system",
                "content": (
                    "Be accurate, constructive, and concise. Do not invent resume facts. "
                    "Return only the final Markdown report; do not include internal reasoning, "
                    "thinking, or <think> tags."
                ),
            },
            {"role": "user", "content": build_analysis_prompt(resume_text, job_role)},
        ],
    )
    analysis = response.choices[0].message.content or "The model returned an empty analysis."
    analysis = re.sub(r"<think>.*?</think>", "", analysis, flags=re.IGNORECASE | re.DOTALL)
    analysis = re.sub(r"<\|思考开始\|>.*?<\|思考结束\|>", "", analysis, flags=re.DOTALL)
    return analysis.strip() or "The model returned an empty analysis."


def main() -> None:
    st.set_page_config(page_title="Resume Analyser", page_icon="📄", layout="wide")

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input(
            "Groq API key",
            value=get_configured_api_key(),
            type="password",
            help="Your key is used only for this session and is not shown in the UI.",
        )
        model_name = st.text_input("Groq model", value=DEFAULT_MODEL_NAME)

    st.title("Resume Analyser")
    st.caption("Upload a resume PDF, choose a target role, and get actionable feedback.")

    with st.form("resume_analysis_form"):
        job_role = st.text_input(
            "Target job role",
            placeholder="For example: Senior Python Developer",
        )
        uploaded_files = st.file_uploader(
            "Upload resume PDF(s)",
            type="pdf",
            accept_multiple_files=True,
            help="Upload text-based PDF resumes. Scanned image PDFs need OCR before analysis.",
        )
        submitted = st.form_submit_button("Analyse Resume", type="primary")

    if not submitted:
        return

    if not job_role.strip():
        st.error("Enter the target job role before analysing.")
        return
    if not uploaded_files:
        st.error("Upload at least one PDF resume.")
        return

    for uploaded_file in uploaded_files:
        with st.expander(uploaded_file.name, expanded=True):
            try:
                resume_text = extract_resume_text(uploaded_file.getvalue())
                if not resume_text:
                    st.warning("No readable text was found. This may be a scanned PDF requiring OCR.")
                    continue

                with st.spinner(f"Analysing {uploaded_file.name}..."):
                    analysis = analyze_resume(
                        resume_text,
                        job_role.strip(),
                        api_key.strip(),
                        model_name.strip() or DEFAULT_MODEL_NAME,
                    )
                st.markdown(analysis)
            except Exception as error:
                st.error(f"Could not analyse {uploaded_file.name}: {error}")


if __name__ == "__main__":
    main()