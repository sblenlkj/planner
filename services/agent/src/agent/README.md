from agent.settings import LlmModelKind


async def run_main_agent(pool, messages):
    async with pool.acquire(model_kind=LlmModelKind.STRONG) as slot:
        agent = build_main_agent(
            llm=slot.llm,
            tools=main_tools,
        )

        return await agent.ainvoke(
            {
                "messages": messages,
            }
        )