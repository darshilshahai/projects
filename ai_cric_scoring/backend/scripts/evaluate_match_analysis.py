"""Manual OpenAI evaluation for match analysis. Not part of pytest.

Usage from backend/:

    uv run python scripts/evaluate_match_analysis.py

Requires OPENAI_API_KEY. Prints grounded analysis for a few fixture packages.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(BACKEND_ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT / "tests"))

from tests.ai.eval_fixtures import EVAL_FIXTURES  # noqa: E402

from app.ai.prompts.match_analysis_prompt import MatchAnalysisPromptBuilder  # noqa: E402
from app.ai.providers.openai_provider import OpenAIProvider  # noqa: E402
from app.ai.schemas.match_analysis import StructuredMatchAnalysis  # noqa: E402
from app.ai.services.grounding import GroundingValidator  # noqa: E402
from app.core.config import Settings  # noqa: E402


async def main() -> int:
    settings = Settings()
    if not settings.openai_api_key:
        print("OPENAI_API_KEY is not set. Skipping real-provider evaluation.")
        return 0
    provider = OpenAIProvider(settings)
    prompts = MatchAnalysisPromptBuilder()
    validator = GroundingValidator()
    selected = ("defending_win_after_cluster", "chase_through_partnership")
    for name in selected:
        package = EVAL_FIXTURES[name]()
        system, user = prompts.build(package)
        print(f"\n=== {name} ===")
        generation = await provider.generate_structured(
            system_prompt=system,
            user_prompt=user,
            response_model=StructuredMatchAnalysis,
        )
        validator.validate(generation.data, package)
        print(generation.data.headline)
        print(generation.data.summary)
        print(f"tokens in={generation.input_tokens} out={generation.output_tokens} ms={generation.latency_ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
