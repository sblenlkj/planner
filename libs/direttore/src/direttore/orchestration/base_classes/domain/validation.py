from collections.abc import Callable, Iterator
from typing import Any, Final, Self, TypeAlias, TypeVar, cast


_FIELD_VALIDATOR_ATTR: Final[str] = "__direttore_field_validator__"

T = TypeVar("T")
FieldValidator: TypeAlias = Callable[[Any], Any]


def field_validator(field_name: str) -> Callable[[T], T]:
    if not field_name:
        raise ValueError("field_name must not be empty")

    def decorator(func: T) -> T:
        setattr(func, _FIELD_VALIDATOR_ATTR, field_name)
        return func

    return decorator


class Validatable:
    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> Self:
        self.validate_fields()
        self.validate_invariants()
        return self

    def validate_fields(self) -> Self:
        for field_name, validate_field in self._iter_field_validators():
            if not hasattr(self, field_name):
                raise AttributeError(
                    f"{self.__class__.__name__} has field validator for unknown "
                    f"field '{field_name}'"
                )

            value = getattr(self, field_name)
            validated_value = validate_field(value)
            setattr(self, field_name, validated_value)

        return self

    def validate_invariants(self) -> Self:
        return self

    @classmethod
    def _iter_field_validator_definitions(cls) -> Iterator[tuple[str, str]]:
        validator_definitions: list[tuple[str, str]] = []
        seen: set[str] = set()

        for klass in cls.__mro__:
            for attr_name, attr_value in vars(klass).items():
                field_name = getattr(
                    attr_value,
                    _FIELD_VALIDATOR_ATTR,
                    None,
                )

                if field_name is None:
                    continue

                if attr_name in seen:
                    continue

                seen.add(attr_name)
                validator_definitions.append((attr_name, field_name))

        yield from reversed(validator_definitions)

    def _iter_field_validators(self) -> Iterator[tuple[str, FieldValidator]]:
        for attr_name, field_name in self._iter_field_validator_definitions():
            validate_field = getattr(self, attr_name)
            yield field_name, cast(FieldValidator, validate_field)