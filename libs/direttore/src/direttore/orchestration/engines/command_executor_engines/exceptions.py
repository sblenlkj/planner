from __future__ import annotations


class CommandExecutorError(RuntimeError):
    pass


class UnsupportedCommandExecutionMode(CommandExecutorError):
    pass


class EventDrainCycleLimitExceeded(CommandExecutorError):
    pass


class EventProcessingLimitExceeded(CommandExecutorError):
    pass