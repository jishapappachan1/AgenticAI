"""CLI entrypoint for ArchLens multi-agent architecture review."""

import argparse

from src.config import get_settings
from src.llm.gemini_client import GeminiClient
from src.llm.mock_client import MockLLMClient
from src.multi_agent_pipeline import MultiAgentArchitecturePipeline
from src.report_generator import render_markdown_report, save_markdown_report


def _is_quota_error(message: str) -> bool:
    lowered = message.lower()
    return "quota" in lowered or "429" in lowered or "rate limit" in lowered


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ArchLens - Multi-Agent Architecture Review Assistant"
    )
    parser.add_argument("repo", help="Repository URL or local path")
    parser.add_argument("--focus", default="", help="Optional focus note for the review")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save markdown report",
    )
    args = parser.parse_args()

    settings = get_settings()
    try:
        llm_client = GeminiClient(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
        )
        pipeline = MultiAgentArchitecturePipeline(
            llm_client=llm_client,
            settings=settings,
            prompt_path="prompts/architecture_review_prompt.md",
        )
        pipeline_result = pipeline.run(repo_input=args.repo, user_focus=args.focus)
        review = pipeline_result.review
        markdown = render_markdown_report(review, args.repo)
        saved_path = save_markdown_report(
            markdown=markdown,
            output_dir=args.output_dir,
            repo_name=review.context["repo_summary"]["repo_name"],
        )
    except Exception as exc:
        if _is_quota_error(str(exc)):
            print("Gemini quota unavailable; switching to mock-learning mode.")
            llm_client = MockLLMClient()
            pipeline = MultiAgentArchitecturePipeline(
                llm_client=llm_client,
                settings=settings,
                prompt_path="prompts/architecture_review_prompt.md",
            )
            pipeline_result = pipeline.run(repo_input=args.repo, user_focus=args.focus)
            review = pipeline_result.review
            markdown = render_markdown_report(review, args.repo)
            saved_path = save_markdown_report(
                markdown=markdown,
                output_dir=args.output_dir,
                repo_name=review.context["repo_summary"]["repo_name"],
            )
        else:
            print(f"Review failed: {exc}")
            print("Tip: verify GEMINI_API_KEY and use GEMINI_MODEL=gemini-2.0-flash in .env")
            raise SystemExit(1) from exc

    print("Architecture review completed.")
    print(f"Model used: {getattr(llm_client, 'model_name', settings.gemini_model)}")
    print(f"Run ID: {pipeline_result.run_id}")
    print(f"Tool calls executed: {len(pipeline_result.tool_calls)}")
    print(f"Previous memory used: {pipeline_result.previous_memory_used}")
    print(f"Report saved to: {saved_path}")


if __name__ == "__main__":
    main()
