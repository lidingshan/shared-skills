"""Load project test settings and provide the Playwright base URL."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


@pytest.fixture(scope="session")
def base_url(base_url):
    """Prefer pytest's configured URL, then fall back to project settings."""
    return base_url or os.getenv("UI_TEST_BASE_URL") or None
