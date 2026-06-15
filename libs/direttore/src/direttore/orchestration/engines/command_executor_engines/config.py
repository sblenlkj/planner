from __future__ import annotations

from dataclasses import dataclass

from direttore.orchestration.base_types.command_handler import CommandHandlerExecutionMode


@dataclass(frozen=True, slots=True)
class ExecutionEngineConfig:
    execution_mode: CommandHandlerExecutionMode = CommandHandlerExecutionMode.IN_TRANSACTION
    max_processed_events: int = 100
    max_drain_cycles: int = 100