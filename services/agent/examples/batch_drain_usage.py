from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.llm import LlmExecutionScope, LlmWorkload


@dataclass(frozen=True)
class UserGraphBatch:
    user_id: str
    observations: list[dict[str, Any]]
    current_graph: dict[str, Any]


async def drain_graph_update_batch(
    *,
    user_batches: list[UserGraphBatch],
    graph_tools: list[Any],
    llm_orchestrator,
):
    async with llm_orchestrator.session(
        workload=LlmWorkload.GRAPH_UPDATE,
        scope=LlmExecutionScope.BATCH_DRAIN,
        purpose="user_graph_update_batch",
        prompt_template="graph_update_agent_v1",
        max_duration_seconds=600,
        metadata={"items": len(user_batches)},
    ) as session:
        chat_model = session.require_langchain_chat_model()
        agent = build_graph_update_agent(llm=chat_model, tools=graph_tools)

        results = []
        for batch in user_batches:
            results.append(
                await agent.ainvoke(
                    {
                        "user_id": batch.user_id,
                        "observations": batch.observations,
                        "current_graph": batch.current_graph,
                    }
                )
            )
        return results


def build_graph_update_agent(*, llm, tools):
    raise NotImplementedError("Wire your GraphUpdateAgent here")
