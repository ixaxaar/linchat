"""Provider protocol, event types, and SSE parsing helpers."""
from __future__ import annotations

import dataclasses
from typing import Any, Iterable, Iterator, Union


@dataclasses.dataclass
class TextDelta:
    text: str


@dataclasses.dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclasses.dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclasses.dataclass
class Done:
    reason: str = "stop"  # stop | tool_calls | max_hops | denied | error


@dataclasses.dataclass
class ErrorEvent:
    message: str


Event = Union[TextDelta, ToolCall, Usage, Done, ErrorEvent]


@dataclasses.dataclass
class Message:
    role: str  # user | assistant | tool
    content: Any = ""  # str, or provider-native list of parts
    tool_calls: list | None = None  # assistant turn: [{id, name, args}]
    tool_call_id: str | None = None  # tool turn: which call this answers
    name: str | None = None
    images: list[bytes] | None = None  # PNG bytes for vision providers


def parse_sse_lines(lines: Iterable[str]) -> Iterator[str]:
    """Yield one joined data payload per SSE event. Keeps '[DONE]' as-is."""
    data_lines: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        if line == "":
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip(" "))
        # other fields (event:, id:, retry:) ignored
    if data_lines:
        yield "\n".join(data_lines)


def iter_sse(resp) -> Iterator[str]:
    """Parse SSE from a streamed requests.Response."""
    return parse_sse_lines(resp.iter_lines(decode_unicode=True))
