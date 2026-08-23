from __future__ import annotations

import re
from typing import Final

ACTION_IDENTIFIER: Final = r"^[a-z][a-z0-9_-]{2,127}$"
REMEDIATION_IDENTIFIER: Final = r"^[a-z][a-z0-9-]{2,127}$"
MAX_ACTIONS: Final = 32


def action_identifiers(value: tuple[str, ...]) -> tuple[str, ...]:
    if len(value) != len(set(value)) or any(re.fullmatch(ACTION_IDENTIFIER, item) is None for item in value):
        raise ValueError("actions must be unique identifiers")
    return value
