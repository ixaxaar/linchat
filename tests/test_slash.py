from linchat import slash


def test_parse_known_command():
    assert slash.parse("/run ls -la") == ("run", "ls -la")
    assert slash.parse("/open firefox") == ("open", "firefox")
    assert slash.parse("/clip") == ("clip", "")


def test_parse_rejects_unknown_partial_and_plain():
    assert slash.parse("/nope x") is None
    assert slash.parse("/ru") is None      # partial command is not a command
    assert slash.parse("run ls") is None
    assert slash.parse("/") is None
    assert slash.parse("/runx") is None


def test_complete_filters_by_prefix():
    names = [c.name for c in slash.complete("")]
    assert names == ["run", "open", "steam", "games", "find", "read", "clip", "snap"]
    assert [c.name for c in slash.complete("re")] == ["read"]
    assert [c.name for c in slash.complete("/f")] == ["find"]  # leading / tolerated
    assert [c.name for c in slash.complete("zzz")] == []
