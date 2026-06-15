from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar, overload


TValue = TypeVar("TValue")
TOwner = TypeVar("TOwner")


class LazyAttribute(Generic[TOwner, TValue]):
    def __init__(
        self,
        factory: Callable[[TOwner], TValue],
        *,
        name: str | None = None,
    ) -> None:
        self._factory = factory
        self._explicit_name = name
        self._storage_name: str | None = None

    def __set_name__(self, owner: type[TOwner], name: str) -> None:
        self._storage_name = self._explicit_name or f"_{name}"

    @property
    def storage_name(self) -> str:
        if self._storage_name is None:
            raise RuntimeError("LazyAttribute storage name is not initialized.")

        return self._storage_name

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[TOwner],
    ) -> LazyAttribute[TOwner, TValue]:
        ...

    @overload
    def __get__(
        self,
        instance: TOwner,
        owner: type[TOwner],
    ) -> TValue:
        ...

    def __get__(
        self,
        instance: TOwner | None,
        owner: type[TOwner],
    ) -> TValue | LazyAttribute[TOwner, TValue]:
        if instance is None:
            return self

        storage_name = self.storage_name

        if storage_name not in instance.__dict__:
            instance.__dict__[storage_name] = self._factory(instance)

        return instance.__dict__[storage_name]

    def __set__(self, instance: TOwner, value: TValue) -> None:
        instance.__dict__[self.storage_name] = value

    def __delete__(self, instance: TOwner) -> None:
        instance.__dict__.pop(self.storage_name, None)


class LazyAttributeOwner:
    def iter_initialized_lazy_attributes(self) -> Iterable[Any]:
        for descriptor in self._iter_lazy_descriptors():
            storage_name = descriptor.storage_name

            if storage_name in self.__dict__:
                yield self.__dict__[storage_name]

    @classmethod
    def _iter_lazy_descriptors(cls) -> Iterable[LazyAttribute[Any, Any]]:
        for klass in reversed(cls.__mro__):
            for value in klass.__dict__.values():
                if isinstance(value, LazyAttribute):
                    yield value