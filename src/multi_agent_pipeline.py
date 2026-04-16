"""Orchestrator for multi-agent architecture review pipeline."""

from __future__ import annotations

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.config import Settings
from src.llm.base import LLMClient
from src.memory.store import MemoryStore
from src.pipeline_models import PipelineRunResult
from src.tools.repo_tools import build_tool_registry


class MultiAgentArchitecturePipeline:
    """Coordinates memory, tool-calling, and 3 specialized agents."""

    def __init__(self, llm_client: LLMClient, settings: Settings, prompt_path: str) -> None:
        self.llm_client = llm_client
        self.settings = settings
        self.memory_store = MemoryStore(settings.memory_db_path)
        self.tool_registry = build_tool_registry(
            settings=settings,
            load_previous_summary=self.memory_store.load_latest_summary,
        )
        self.planner_agent = PlannerAgent(llm_client=llm_client)
        self.analyzer_agent = AnalyzerAgent()
        self.reviewer_agent = ReviewerAgent(llm_client=llm_client, prompt_path=prompt_path)

    def run(self, repo_input: str, user_focus: str = "") -> PipelineRunResult:
        run_id = self.memory_store.start_run(repo_input=repo_input, user_focus=user_focus)
        previous_summary = self.memory_store.load_latest_summary(repo_input)

        self.memory_store.log_event(
            run_id=run_id,
            agent_name=self.planner_agent.name,
            event_type="start",
            payload={"repo_input": repo_input, "user_focus": user_focus},
        )
        plan = self.planner_agent.plan(
            repo_input=repo_input,
            user_focus=user_focus,
            tool_catalog=self.tool_registry.list_tools(),
            previous_summary=previous_summary,
        )
        self.memory_store.log_event(
            run_id=run_id,
            agent_name=self.planner_agent.name,
            event_type="plan_created",
            payload=plan,
        )

        evidence, tool_calls, previous_memory_used = self.analyzer_agent.run(
            run_id=run_id,
            repo_input=repo_input,
            plan=plan,
            tool_registry=self.tool_registry,
            memory_store=self.memory_store,
        )
        self.memory_store.log_event(
            run_id=run_id,
            agent_name=self.analyzer_agent.name,
            event_type="evidence_collected",
            payload={
                "has_ingestion": bool(evidence.get("ingestion")),
                "has_analysis": bool(evidence.get("analysis")),
                "key_file_excerpt_count": len(evidence.get("key_file_excerpts", [])),
            },
        )

        review = self.reviewer_agent.review(
            evidence=evidence,
            user_focus=user_focus,
            plan=plan,
        )
        self.memory_store.log_event(
            run_id=run_id,
            agent_name=self.reviewer_agent.name,
            event_type="review_created",
            payload={"confidence_note": review.confidence_note},
        )

        self.memory_store.save_artifact(run_id=run_id, key="plan", value=plan)
        self.memory_store.save_artifact(run_id=run_id, key="evidence", value=evidence)
        self.memory_store.save_artifact(run_id=run_id, key="final_review", value=review.to_dict())

        return PipelineRunResult(
            run_id=run_id,
            review=review,
            plan=plan,
            tool_calls=tool_calls,
            previous_memory_used=previous_memory_used,
            model_name=getattr(self.llm_client, "model_name", ""),
        )

