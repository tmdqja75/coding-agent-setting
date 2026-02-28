import pytest
import httpx
from unittest.mock import AsyncMock, patch
from tools import search_mcp, search_skills, search_plugins, download_file


@pytest.mark.asyncio
async def test_search_mcp_returns_list():
    mock_response = {
        "servers": [{"name": "brave-search", "description": "Web search via Brave"}],
        "metadata": {"count": 1}
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = lambda: mock_response
        mock_get.return_value.raise_for_status = lambda: None
        result = await search_mcp("web search")
    assert isinstance(result, list)
    assert result[0]["name"] == "brave-search"


@pytest.mark.asyncio
async def test_search_skills_returns_list():
    mock_response = {
        "skills": [{"name": "frontend-design", "description": "UI component builder"}],
        "total": 1
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = lambda: mock_response
        mock_get.return_value.raise_for_status = lambda: None
        result = await search_skills("frontend")
    assert isinstance(result, list)
    assert result[0]["name"] == "frontend-design"


@pytest.mark.asyncio
async def test_search_plugins_returns_list():
    mock_response = {
        "plugins": [{"name": "superpowers", "description": "Agent workflow skills"}],
        "total": 1
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = lambda: mock_response
        mock_get.return_value.raise_for_status = lambda: None
        result = await search_plugins("agent")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_download_file_returns_text():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.text = "# Skill content"
        mock_get.return_value.raise_for_status = lambda: None
        result = await download_file("https://raw.githubusercontent.com/example/skill.md")
    assert result == "# Skill content"
