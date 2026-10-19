from linchat.providers.base import parse_sse_lines


def test_basic_data_events():
    lines = ["data: {\"a\": 1}", "", "data: {\"b\": 2}", ""]
    assert list(parse_sse_lines(lines)) == ['{"a": 1}', '{"b": 2}']


def test_multiline_data_joined_by_newline():
    lines = ["data: line1", "data: line2", ""]
    assert list(parse_sse_lines(lines)) == ["line1\nline2"]


def test_crlf_and_whitespace_tolerance():
    lines = ["data:   {\"x\": 9}  \r", ""]
    assert list(parse_sse_lines(lines)) == ['{"x": 9}']


def test_ignores_comments_and_nonevents():
    lines = [": ping", "event: foo", "id: 7", "data: {}", ""]
    assert list(parse_sse_lines(lines)) == ["{}"]


def test_keep_done_sentinel():
    lines = ["data: [DONE]", ""]
    assert list(parse_sse_lines(lines)) == ["[DONE]"]
