from __future__ import annotations

from collections.abc import Mapping

from services.delivery.contract_validation import JsonValue


class FrozenJsonDict(dict[str, JsonValue]):
    def __setitem__(self, key: str, value: JsonValue) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def __ior__(self, value: Mapping[str, JsonValue]) -> FrozenJsonDict:
        raise TypeError("delivery snapshot records are immutable")

    def clear(self) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def pop(self, key: str, default: JsonValue | None = None) -> JsonValue:
        raise TypeError("delivery snapshot records are immutable")

    def popitem(self) -> tuple[str, JsonValue]:
        raise TypeError("delivery snapshot records are immutable")

    def setdefault(self, key: str, default: JsonValue | None = None) -> JsonValue:
        raise TypeError("delivery snapshot records are immutable")

    def update(self, value: Mapping[str, JsonValue]) -> None:
        raise TypeError("delivery snapshot records are immutable")


class FrozenJsonList(list[JsonValue]):
    def __setitem__(self, index: int | slice, value: JsonValue | list[JsonValue]) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def __delitem__(self, index: int | slice) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def __iadd__(self, value: list[JsonValue]) -> FrozenJsonList:
        raise TypeError("delivery snapshot records are immutable")

    def __imul__(self, value: int) -> FrozenJsonList:
        raise TypeError("delivery snapshot records are immutable")

    def append(self, value: JsonValue) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def clear(self) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def extend(self, value: list[JsonValue]) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def insert(self, index: int, value: JsonValue) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def pop(self, index: int = -1) -> JsonValue:
        raise TypeError("delivery snapshot records are immutable")

    def remove(self, value: JsonValue) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def reverse(self) -> None:
        raise TypeError("delivery snapshot records are immutable")

    def sort(self) -> None:
        raise TypeError("delivery snapshot records are immutable")


def freeze_mapping(value: Mapping[str, JsonValue]) -> FrozenJsonDict:
    return FrozenJsonDict({key: freeze(item) for key, item in sorted(value.items())})


def freeze(value: JsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return freeze_mapping(value)
    if isinstance(value, list):
        return FrozenJsonList([freeze(item) for item in value])
    return value
