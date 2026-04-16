# ArchLens - AI Architecture Review Assistant (MVP)

ArchLens is a beginner-friendly Agentic AI mini-project that reviews a repository's high-level architecture and produces a structured markdown report.

It is intentionally scoped for learning:
- Multi-agent orchestration (planner, analyzer, reviewer)
- Tool-calling execution for deterministic repository operations
- Persistent run memory for previous-review recall
- Repository-structure reasoning (not full static analysis)
- Streamlit-first UX, CLI as backup

## Why this demonstrates Agentic AI

This project follows an explicit multi-agent loop:

1. **Plan** - planner agent creates tool sequence.
2. **Observe + Analyze** - analyzer agent calls tools to ingest and extract deterministic metadata.
3. **Recall** - memory store loads previous run summaries when available.
4. **Reason** - reviewer agent synthesizes evidence into strict JSON review output.
5. **Output** - `report_generator.py` renders markdown with recommendations.

## Textual architecture diagram

User Input (repo URL/path + optional focus)  
-> Streamlit `app.py` or `cli.py`  
-> `MultiAgentArchitecturePipeline.run()`  
-> Planner Agent: build tool sequence  
-> Analyzer Agent: tool calls (`load_previous_summary`, `ingest_repository`, `analyze_codebase`, `read_key_file`)  
-> Reviewer Agent: `GeminiClient.generate()` with structured evidence payload  
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
   ├─ agents/
   ├─ memory/
   ├─ tools/
   ├─ multi_agent_pipeline.py
   ├─ code_analyzer.py
   ├─ config.py
   ├─ models.py
   ├─ pipeline_models.py
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

## Documentation pack for demo

Detailed demo artifacts are available under `docs/`:
- `docs/01_Architecture_Document.md`
- `docs/02_Functional_Specification.md`
- `docs/03_Demo_Runbook.md`
- `docs/screenshots/README.md`

## Known limitations and fallback behavior

- Repository-level review only (no deep AST/static analysis).
- Reasoning quality depends on available LLM quota and model access.
- If Gemini quota is unavailable (`429`), the app automatically switches to **mock-learning mode**.
- Mock mode preserves pipeline behavior for learning and demos, but recommendations are illustrative.

## Security notes

- Never commit `.env` with real API keys.
- Use `.env.example` for sharing configuration templates.
- Rotate API keys if they were exposed in screenshots, logs, or chats.
