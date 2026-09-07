# AI Resume Analyser

A simple Streamlit application that extracts text from uploaded resume PDFs and uses the Groq-hosted `qwen/qwen3.6-27b` model to review each resume against a target job role.

## Features

- Upload one or more text-based PDF resumes.
- Enter the job role the candidate is targeting.
- Receive feedback for:
  1. Content Clarity & Impact
  2. Skills Presentation
  3. Experience Descriptions
  4. Specific Recommendations for the job role
  5. Overall Rating & Checklist
  6. Refined Resume
- Keeps the application code in one file: `main.py`.

## Architecture

```text
Browser
  -> Streamlit UI in main.py
  -> PDF text extraction with pypdf
  -> Prompt construction with resume text + job role
  -> Groq API using qwen/qwen3.6-27b
  -> Markdown analysis displayed in Streamlit
```

The API key is read from `GROQ_API_KEY`. It is never entered into the prompt or shown in the UI.

## Workflow

1. The user enters a target job role.
2. The user uploads one or more PDF resumes.
3. When **Analyse resume** is pressed, `pypdf` extracts text locally from each PDF.
4. The app sends the extracted text and job role to the Groq model.
5. The model returns a six-part Markdown report for each resume.
6. Each report is shown in its own expandable result area.

## Setup

### 1. Create and activate the virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in an Administrator PowerShell or use Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure the Groq API key

Copy `.env.example` to `.env` and replace the placeholder with a Groq API key:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```text
GROQ_API_KEY=your_actual_groq_api_key
```

Do not commit `.env`.

### 4. Start the app

```powershell
streamlit run main.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## Deploy on Streamlit Community Cloud

1. Push this project to a GitHub repository. Keep `.env` out of Git; it is already listed in `.gitignore`.
2. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. Select **Create app**, choose the repository and branch, and set the main file to `main.py`.
4. Open **Advanced settings**, choose Python 3.11 or newer, and add this secret:

```toml
GROQ_API_KEY = "your_actual_groq_api_key"
```

5. Deploy the app. Streamlit Cloud installs the packages from `requirements.txt` automatically.

The deployed app reads `GROQ_API_KEY` from Streamlit Secrets. For local development, it continues to read the
same value from `.env` or the sidebar field.

## Notes

- This version supports text-based PDFs. Scanned image PDFs need OCR first.
- Resume text is limited before it is sent to the model to keep requests manageable.
- Check Groq's current model availability and free-tier limits if the requested model is unavailable for your account.