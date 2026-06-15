from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Generic, Hashable, TypeVar


TState = TypeVar("TState", bound=Hashable)


@dataclass(frozen=True, slots=True)
class StateMachine(Generic[TState]):
    """
    Minimal domain-level state transition checker.

    StateMachine is intentionally small. It does not own an aggregate, does not
    mutate domain objects, does not publish events, and does not execute actions.

    It only answers one domain question:

        Can this state move to that state?

    Typical usage:

        OrderStateMachine = StateMachine[OrderStatus](
            transitions={
                OrderStatus.DRAFT: {
                    OrderStatus.SUBMITTED,
                    OrderStatus.CANCELLED,
                },
                OrderStatus.SUBMITTED: {
                    OrderStatus.RESERVED,
                    OrderStatus.FAILED,
                    OrderStatus.CANCELLED,
                },
            }
        )

        self.status = OrderStateMachine.transition(
            current=self.status,
            target=OrderStatus.SUBMITTED,
        )

    Invalid transitions raise ValueError. The framework intentionally does not
    introduce a custom exception here yet. Domain code can wrap or replace this
    later if it needs domain-specific errors.
    """

    transitions: Mapping[TState, Iterable[TState]]
    _normalized_transitions: dict[TState, frozenset[TState]] = field(
        init=False,
        repr=False,
    )
    _known_states: frozenset[TState] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        normalized_transitions = {
            current: frozenset(targets)
            for current, targets in self.transitions.items()
        }

        known_states: set[TState] = set(normalized_transitions)

        for targets in normalized_transitions.values():
            known_states.update(targets)

        object.__setattr__(
            self,
            "_normalized_transitions",
            normalized_transitions,
        )
        object.__setattr__(
            self,
            "_known_states",
            frozenset(known_states),
        )

    @property
    def known_states(self) -> frozenset[TState]:
        """
        Returns all states known to this machine.

        A state is known if it appears either as a source state or as a target
        state in the transition table.
        """
        return self._known_states

    def allowed_targets(
        self,
        current: TState,
    ) -> frozenset[TState]:
        """
        Returns states that can be reached from the current state.

        If the current state has no outgoing transitions, an empty frozenset is
        returned. This makes terminal states easy to represent: simply omit them
        from the transition table or map them to an empty set.
        """
        return self._normalized_transitions.get(
            current,
            frozenset(),
        )

    def can_transition(
        self,
        current: TState,
        target: TState,
    ) -> bool:
        """
        Returns True if target is allowed from current.

        This method is side-effect free and never raises for normal invalid
        transitions. Use ensure_can_transition(...) when invalid transitions
        should fail loudly.
        """
        return target in self.allowed_targets(current)

    def ensure_can_transition(
        self,
        current: TState,
        target: TState,
    ) -> None:
        """
        Raises ValueError if transition from current to target is not allowed.
        """
        if self.can_transition(current, target):
            return

        allowed_targets = self.allowed_targets(current)

        if not allowed_targets:
            raise ValueError(
                "Invalid state transition. "
                f"State {current!r} has no outgoing transitions. "
                f"Target={target!r}."
            )

        raise ValueError(
            "Invalid state transition. "
            f"Current={current!r}, target={target!r}, "
            f"allowed_targets={sorted(allowed_targets, key=repr)!r}."
        )

    def transition(
        self,
        current: TState,
        target: TState,
    ) -> TState:
        """
        Validates transition and returns target.

        The method does not mutate anything. Domain objects decide themselves
        how to store the returned state.

        Example:

            self.status = OrderStateMachine.transition(
                current=self.status,
                target=OrderStatus.SUBMITTED,
            )
        """
        self.ensure_can_transition(
            current=current,
            target=target,
        )

        return target