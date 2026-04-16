"""Analyzer agent that executes tool-calling plans."""

from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any

from src.memory.store import MemoryStore
from src.pipeline_models import ToolCallRecord
from src.tools.registry import ToolRegistry


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalyzerAgent:
    """Executes planned tools and builds evidence payload for reviewer."""

    name = "analyzer_agent"

    def run(
        self,
        run_id: str,
        repo_input: str,
        plan: dict[str, Any],
        tool_registry: ToolRegistry,
        memory_store: MemoryStore,
    ) -> tuple[dict[str, Any], list[ToolCallRecord], bool]:
        evidence: dict[str, Any] = {
            "repo_input": repo_input,
            "ingestion": {},
            "analysis": {},
            "key_file_excerpts": [],
            "previous_summary": {},
            "generated_at": _utc_now_iso(),
        }
        tool_calls: list[ToolCallRecord] = []
        previous_memory_used = False

        for item in plan.get("tool_sequence", []):
            if not isinstance(item, dict):
                continue
            tool_name = str(item.get("tool", "")).strip()
            args = item.get("args", {})
            if not isinstance(args, dict):
                args = {}

            if tool_name == "analyze_codebase" and "ingestion" in evidence and evidence["ingestion"]:
                args = {"ingestion": evidence["ingestion"]}

            start = time.perf_counter()
            result = tool_registry.call(name=tool_name, args=args)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            status = "success" if result.ok else "error"

            record = ToolCallRecord(
                agent_name=self.name,
                tool_name=tool_name,
                args=args,
                status=status,
                duration_ms=elapsed_ms,
                error=result.error,
            )
            tool_calls.append(record)
            memory_store.log_event(
                run_id=run_id,
                agent_name=self.name,
                event_type="tool_call",
                payload=record.to_dict(),
            )

            if not result.ok:
                continue

            payload = result.data or {}
            if tool_name == "load_previous_summary":
                previous_memory_used = bool(payload.get("found"))
                evidence["previous_summary"] = payload.get("summary", {})
            elif tool_name == "ingest_repository":
                evidence["ingestion"] = payload.get("ingestion", {})
            elif tool_name == "analyze_codebase":
                evidence["analysis"] = payload.get("analysis", {})
            elif tool_name == "read_key_file":
                evidence["key_file_excerpts"].append(payload)

        ingestion = evidence.get("ingestion", {})
        if ingestion and not evidence["key_file_excerpts"]:
            key_files = ingestion.get("key_files", {})
            repo_path = ingestion.get("repo_path", "")
            for relative_path in list(key_files.keys())[:3]:
                args = {
                    "repo_path": repo_path,
                    "relative_path": relative_path,
                    "max_chars": 1200,
                }
                start = time.perf_counter()
                result = tool_registry.call(name="read_key_file", args=args)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                status = "success" if result.ok else "error"
                record = ToolCallRecord(
                    agent_name=self.name,
                    tool_name="read_key_file",
                    args=args,
                    status=status,
                    duration_ms=elapsed_ms,
                    error=result.error,
                )
                tool_calls.append(record)
                memory_store.log_event(
                    run_id=run_id,
                    agent_name=self.name,
                    event_type="tool_call",
                    payload=record.to_dict(),
                )
                if result.ok:
                    evidence["key_file_excerpts"].append(result.data or {})

        return evidence, tool_calls, previous_memory_used

