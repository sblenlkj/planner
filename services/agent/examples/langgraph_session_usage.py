from __future__ import annotations

from typing import Any

from agent.llm import LlmExecutionScope, LlmWorkload


async def run_agent_turn(
    *,
    state: dict[str, Any],
    tools: list[Any],
    llm_orchestrator,
):
    """Skeleton for a LangGraph/LangChain agent run.

    `build_default_assistant_graph` is intentionally not implemented here: keep
    this example focused on the LLM session ownership boundary.
    """

    async with llm_orchestrator.session(
        workload=LlmWorkload.INTERACTIVE,
        scope=LlmExecutionScope.AGENT_RUN,
        purpose="default_assistant_turn",
        prompt_template="default_assistant_agent_v1",
        max_duration_seconds=180,
    ) as session:
        chat_model = session.require_langchain_chat_model()
        graph = build_default_assistant_graph(llm=chat_model, tools=tools)
        return await graph.ainvoke(state)


def build_default_assistant_graph(*, llm, tools):
    raise NotImplementedError("Wire your LangGraph graph here")
