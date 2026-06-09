from __future__ import annotations

from agent.llm import LlmMessage, LlmRequest, LlmWorkload
from examples.bootstrap_llm import build_llm_orchestrator


async def main() -> None:
    llm = build_llm_orchestrator()
    response = await llm.complete(
        LlmRequest(
            messages=[
                LlmMessage(role="system", content="Ты краткий технический ассистент."),
                LlmMessage(role="user", content="Ответь одной фразой: API работает?"),
            ]
        ),
        workload=LlmWorkload.INTERACTIVE,
        purpose="manual_smoke_test",
        prompt_template="manual_smoke_test_v1",
    )
    print(response.content)
