# ArchLens Functional Specification

## 1. Product Summary

ArchLens is a single-agent AI assistant that reviews high-level software architecture from repository structure and outputs a structured architecture review report.

## 2. Target Users

- Developers and architects who need quick architecture health insights.
- Training participants learning Agentic AI design patterns.
- Teams seeking lightweight repository-level architecture review.

## 3. Functional Requirements

### FR-01: Repository Input
- System accepts either:
  - Public GitHub repository URL
  - Local repository path

### FR-02: Repository Ingestion
- System clones (for URL) or reads (for local path) repository in read-only flow.
- System captures bounded file inventory and key files.

### FR-03: Deterministic Metadata Extraction
- System extracts:
  - file count
  - extension distribution
  - inferred languages
  - top-level directories
  - framework/architecture hints

### FR-04: LLM Reasoning
- System sends structured metadata and user focus context to LLM.
- System expects strict JSON response for standardized output sections.

### FR-05: Structured Report Output
- System outputs markdown with:
  - Architecture Overview
  - Strengths
  - Risks / Smells
  - Recommendations
  - Confidence Note

### FR-06: Streamlit Primary UX
- User can provide repository input and optional focus.
- User can run review and view result sections in-app.
- User can download generated markdown report.

### FR-07: CLI Secondary UX
- User can run review from terminal command.
- Output markdown report is saved to configured directory.

### FR-08: Quota-Safe Fallback
- On quota/rate-limit failures from Gemini, system switches to mock-learning mode.
- System still generates a complete structured report for demo continuity.

## 4. Non-Functional Requirements

- **NFR-01 (Usability):** beginner-friendly, clear outputs.
- **NFR-02 (Performance):** bounded scan scope (`MAX_FILES_TO_SCAN`) to avoid heavy scans.
- **NFR-03 (Reliability):** graceful handling of model, key, clone, and permission errors.
- **NFR-04 (Security):** no secret commits; `.env` excluded.
- **NFR-05 (Maintainability):** clear module boundaries and minimal abstractions.

## 5. Inputs and Outputs

### Input
- `repo_input`: URL or local path.
- `user_focus` (optional): natural-language review focus.
- Environment configs from `.env`.

### Output
- In-app rendered architecture review sections.
- Markdown report saved under `output/`.
- Optional downloadable report from Streamlit.

## 6. Acceptance Criteria

1. User can submit a valid repository URL/path and get a report.
2. Report always includes all required sections.
3. App handles common failures with actionable messages.
4. Quota errors do not block demo flow (mock mode fallback works).
5. `.env` is not committed, `.env.example` is present.
