"""Streamlit UI for the ArchLens multi-agent architecture review assistant."""

import streamlit as st

from src.config import get_settings
from src.llm.gemini_client import GeminiClient
from src.llm.mock_client import MockLLMClient
from src.multi_agent_pipeline import MultiAgentArchitecturePipeline
from src.report_generator import render_markdown_report, save_markdown_report


st.set_page_config(page_title="ArchLens", page_icon=":mag:", layout="wide")
st.title("ArchLens - AI Architecture Review Assistant")
st.caption("Multi-agent pipeline: Planner -> Analyzer (tools) -> Reviewer")

repo_input = st.text_input(
    "Repository URL or local path",
    placeholder="https://github.com/owner/repo or C:/projects/my-repo",
)
focus = st.text_area(
    "Optional focus area",
    placeholder="Example: Please focus on layering and deployment readiness.",
)

run_clicked = st.button("Run Architecture Review", type="primary")


def _is_quota_error(message: str) -> bool:
    lowered = message.lower()
    return "quota" in lowered or "429" in lowered or "rate limit" in lowered

if run_clicked:
    if not repo_input.strip():
        st.error("Please provide a repository URL or local path.")
        st.stop()

    settings = get_settings()
    try:
        with st.spinner("Running agentic architecture review..."):
            llm_client = GeminiClient(
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model,
            )
            pipeline = MultiAgentArchitecturePipeline(
                llm_client=llm_client,
                settings=settings,
                prompt_path="prompts/architecture_review_prompt.md",
            )
            pipeline_result = pipeline.run(repo_input=repo_input.strip(), user_focus=focus.strip())
            review = pipeline_result.review
    except Exception as exc:
        if _is_quota_error(str(exc)):
            st.warning(
                "Gemini quota is unavailable for this key/project. "
                "Running in mock-learning mode so you can continue practicing the agentic flow."
            )
            with st.spinner("Running mock architecture review..."):
                llm_client = MockLLMClient()
                pipeline = MultiAgentArchitecturePipeline(
                    llm_client=llm_client,
                    settings=settings,
                    prompt_path="prompts/architecture_review_prompt.md",
                )
                pipeline_result = pipeline.run(
                    repo_input=repo_input.strip(),
                    user_focus=focus.strip(),
                )
                review = pipeline_result.review
        else:
            st.error(f"Review failed: {exc}")
            st.info(
                "Tips: verify GEMINI_API_KEY, set GEMINI_MODEL in .env (for most keys, "
                "`gemini-2.0-flash` works), and if cloning fails check repository URL and local folder permissions."
            )
            st.stop()

    markdown_report = render_markdown_report(review, repo_input.strip())
    saved_path = save_markdown_report(
        markdown_report,
        "output",
        review.context["repo_summary"]["repo_name"],
    )

    st.success("Review completed.")
    st.write(f"Saved report: `{saved_path}`")
    st.caption(f"Model used: `{getattr(llm_client, 'model_name', settings.gemini_model)}`")
    st.caption(f"Run ID: `{pipeline_result.run_id}`")
    st.caption(
        "Tool calls: "
        f"`{len(pipeline_result.tool_calls)}` | Previous memory used: "
        f"`{pipeline_result.previous_memory_used}`"
    )

    st.subheader("Execution Plan")
    st.markdown("\n".join(f"- {step}" for step in pipeline_result.plan.get("steps", [])))

    st.subheader("Tool Call Trace")
    if pipeline_result.tool_calls:
        tool_rows = [
            {
                "agent": call.agent_name,
                "tool": call.tool_name,
                "status": call.status,
                "duration_ms": call.duration_ms,
                "error": call.error,
            }
            for call in pipeline_result.tool_calls
        ]
        st.dataframe(tool_rows, use_container_width=True)
    else:
        st.info("No tool calls were captured.")

    st.subheader("Architecture Overview")
    st.write(review.architecture_overview)

    st.subheader("Strengths")
    st.markdown("\n".join(f"- {item}" for item in review.strengths) or "- None identified.")

    st.subheader("Risks / Smells")
    st.markdown("\n".join(f"- {item}" for item in review.risks_smells) or "- None identified.")

    st.subheader("Recommendations")
    st.markdown("\n".join(f"- {item}" for item in review.recommendations) or "- None identified.")

    st.subheader("Confidence Note")
    st.write(review.confidence_note or "Moderate confidence.")

    st.download_button(
        label="Download Markdown Report",
        data=markdown_report,
        file_name="architecture_review_report.md",
        mime="text/markdown",
    )
