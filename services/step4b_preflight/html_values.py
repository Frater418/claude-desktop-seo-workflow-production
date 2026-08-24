from __future__ import annotations

import html
import json
from urllib.parse import urlsplit


class HtmlValueError(ValueError):
    pass


def attribute(value: str) -> str:
    return html.escape(value, quote=True)


def text(value: str) -> str:
    return html.escape(value, quote=True)


def http_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HtmlValueError("Only absolute HTTP(S) URLs can be rendered.")
    return attribute(value)


def jsonld(graph: dict) -> str:
    serialized = json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return serialized.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def classes(*values: str) -> str:
    return " ".join(attribute(value) for value in dict.fromkeys(value for value in values if value))
