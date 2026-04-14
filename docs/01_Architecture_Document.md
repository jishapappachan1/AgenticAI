# ArchLens Architecture Document

## 1. Purpose

This document describes the architecture of **ArchLens**, a beginner-friendly single-agent AI assistant that reviews repository architecture and generates a structured markdown report.

Primary goals:
- Ingest a GitHub or local repository.
- Extract deterministic structural metadata.
- Run architecture reasoning through an LLM (with fallback).
- Generate a readable architecture review report.

## 2. Scope and Constraints

- MVP-only implementation.
- Single-agent workflow.
- Read-only repository analysis.
- No deep AST parsing.
- Prioritize clarity and explainability.

## 3. High-Level Architecture

ArchLens follows a staged agentic loop:

1. **Observe**: read repository shape and key files.
2. **Analyze**: produce deterministic architecture signals.
3. **Reason**: pass structured payload to LLM.
4. **Act**: normalize model output to strict report schema.
5. **Output**: render and save markdown report.

## 4. Component View

### 4.1 Entry Interfaces
- `app.py` (Streamlit): primary interface for demos and interactive use.
- `cli.py` (CLI): secondary interface for scriptable runs.

### 4.2 Core Pipeline
- `src/repo_ingestor.py`
  - Clones/opens repository.
  - Collects bounded file inventory and key file signals.
  - Handles clone-path conflicts and Windows permission fallbacks.

- `src/code_analyzer.py`
  - Builds deterministic metadata (extensions, languages, directories, hints).
  - Avoids expensive deep parsing.

- `src/architecture_agent.py`
  - Orchestrates Observe -> Analyze -> Reason -> Act.
  - Builds structured JSON-like prompt payload.
  - Parses LLM output into strict review model.

- `src/report_generator.py`
  - Renders standardized markdown report.
  - Persists report to `output/`.

### 4.3 LLM Layer
- `src/llm/base.py`: provider abstraction.
- `src/llm/gemini_client.py`: Gemini implementation with model fallback logic.
- `src/llm/mock_client.py`: quota-safe fallback for learning/demo continuity.

## 5. Data Flow (Textual Diagram)

User Input (repo URL/path + optional focus)
-> Streamlit/CLI interface
-> `ArchitectureAgent.run()`
-> `ingest_repository()` [Observe]
-> `analyze_codebase()` [Analyze]
-> `LLMClient.generate()` [Reason]
-> parse/normalize output [Act]
-> `render_markdown_report()` + `save_markdown_report()` [Output]

## 6. Key Design Decisions

- Deterministic preprocessing before LLM reasoning to improve grounding.
- Structured payloads and strict JSON output contract for predictability.
- Single-agent orchestration for explainability and reduced complexity.
- Mock fallback path to avoid demo failure under API quota constraints.

## 7. Error Handling Strategy

- Missing/invalid key: surfaced in UI with actionable hints.
- Model unavailability: model resolution fallback attempts supported models.
- Clone path conflicts: unique clone folder generation.
- Windows clone permission issues: fallback clone location in OS temp.
- Quota/rate-limit errors (`429`): automatic switch to mock-learning mode.

## 8. Security and Compliance Notes

- `.env` is git-ignored.
- `.env.example` is provided for safe sharing.
- No write operations are performed on analyzed repositories.
- No automated PR/code modification actions are executed.

## 9. Operational Considerations

- Runtime dependencies are Python + Streamlit + GitPython + Gemini SDK.
- Reports are generated as markdown and easy to archive/share.
- Deterministic stage can be used standalone for low/no-LLM environments.
