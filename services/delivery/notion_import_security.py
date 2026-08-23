from __future__ import annotations

import re
from typing import Final

from .record_normalization import DeliveryInventoryError


_CREDENTIALS: Final = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(rb"sk-(?:live|proj|test)-[A-Za-z0-9_-]{8,}"),
    re.compile(rb"sk_(?:live|test)_[A-Za-z0-9_-]{8,}"),
    re.compile(rb"(?<![A-Za-z0-9_])(?:api[-_ ]?key|client[-_ ]?secret|password|token)(?![A-Za-z0-9_])\s*(?:=|:)\s*[A-Za-z0-9_-]{12,}", re.IGNORECASE),
    re.compile(rb"\b[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b"),
    re.compile(rb"Bearer\s+[A-Za-z0-9._-]{12,}", re.IGNORECASE),
    re.compile(rb"aws_secret_access_key\s*(?:=|:)\s*[A-Za-z0-9/+=]{20,}", re.IGNORECASE),
    re.compile(rb"refresh_token\s*(?:=|:)\s*[^\s\"']{12,}", re.IGNORECASE),
    re.compile(rb"authorization\s*:\s*basic\s+[A-Za-z0-9+/=]{8,}", re.IGNORECASE),
    re.compile(rb"(?:private_key|client_email|service_account)\s*(?:\"|=|:)\s*[^\s]{8,}", re.IGNORECASE),
    re.compile(rb"aws_session_token\s*(?:=|:)\s*IQoJ[A-Za-z0-9/+=._-]{8,}", re.IGNORECASE),
    re.compile(rb"access_token\s*(?:=|:)\s*ya29\.[A-Za-z0-9._-]{8,}", re.IGNORECASE),
)


def assert_no_credentials(files: dict[str, bytes]) -> None:
    for content in files.values():
        if any(pattern.search(content) for pattern in _CREDENTIALS):
            raise DeliveryInventoryError("NOTION_CREDENTIAL_LEAK", "Generated import content contains credential-shaped material.")
