import pathlib

import pytest


def fixtures_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def fx():
    """Access to tests/fixtures/ directory."""
    return fixtures_dir()
