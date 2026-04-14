# ArchLens - AI Architecture Review Assistant (MVP)

ArchLens is a beginner-friendly Agentic AI mini-project that reviews a repository's high-level architecture and produces a structured markdown report.

It is intentionally scoped for learning:
- Single agent
- Read-only analysis
- Repository-structure reasoning (not full static analysis)
- Streamlit-first UX, CLI as backup

## Why this demonstrates Agentic AI

This project follows an explicit agent loop:

1. **Observe** - `repo_ingestor.py` gathers deterministic repository facts.
2. **Analyze** - `code_analyzer.py` extracts structural metadata.
3. **Reason** - `architecture_agent.py` sends structured context to the LLM.
4. **Act** - the agent normalizes model output into a strict report contract.
5. **Output** - `report_generator.py` renders markdown with recommendations.

## Textual architecture diagram

User Input (repo URL/path + optional focus)  
-> Streamlit `app.py` or `cli.py`  
-> `ArchitectureAgent.run()`  
-> Observe: `repo_ingestor.ingest_repository()`  
-> Analyze: `code_analyzer.analyze_codebase()`  
-> Reason: `GeminiClient.generate()` with structured prompt  
-> Act: parse + normalize into `ArchitectureReview` model  
-> Output: `report_generator.render_markdown_report()` and save in `output/`

## Project structure

```text
.
├─ app.py
├─ cli.py
├─ requirements.txt
├─ .env.example
├─ README.md
├─ output/
├─ prompts/
│  └─ architecture_review_prompt.md
└─ src/
   ├─ __init__.py
   ├─ architecture_agent.py
   ├─ code_analyzer.py
   ├─ config.py
   ├─ models.py
   ├─ repo_ingestor.py
   ├─ report_generator.py
   └─ llm/
      ├─ __init__.py
      ├─ base.py
      └─ gemini_client.py
      └─ mock_client.py
```

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set `GEMINI_API_KEY`.

## Run (Streamlit - primary)

```bash
streamlit run app.py
```

## Run (CLI - secondary)

```bash
python cli.py "https://github.com/owner/repo" --focus "Look for layering issues"
```

## Quick demo flow

1. Open the Streamlit app.
2. Enter a public GitHub repository URL.
3. Click **Run Architecture Review**.
4. Review sections in the UI and download the generated markdown report.

## Output format

Each report contains:
- Architecture Overview
- Strengths
- Risks / Smells
- Recommendations

Reports are saved as markdown files under `output/`.

## Known limitations and fallback behavior

- Repository-level review only (no deep AST/static analysis).
- Reasoning quality depends on available LLM quota and model access.
- If Gemini quota is unavailable (`429`), the app automatically switches to **mock-learning mode**.
- Mock mode preserves pipeline behavior for learning and demos, but recommendations are illustrative.

## Security notes

- Never commit `.env` with real API keys.
- Use `.env.example` for sharing configuration templates.
- Rotate API keys if they were exposed in screenshots, logs, or chats.
