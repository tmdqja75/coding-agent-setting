"""Root conftest.py — loads .env before any test module is collected."""
from pathlib import Path
from dotenv import load_dotenv

# Load agent/.env before pytest collects/imports any test module.
# This ensures the ANTHROPIC_API_KEY is set before ChatAnthropic is
# instantiated at module level in agent/agent.py.
load_dotenv(Path(__file__).parent / "agent" / ".env")
