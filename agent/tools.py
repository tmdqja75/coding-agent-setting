import os
import httpx

MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers"
SKILLSMP_API = "https://skillsmp.com/api/v1/skills/ai-search"


async def search_mcp(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(MCP_REGISTRY, params={"search": query, "limit": limit})
        r.raise_for_status()
        return r.json().get("servers", [])


async def search_skills(query: str, limit: int = 10) -> list[dict]:
    api_key = os.getenv("SKILLSMP_API_KEY", "")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            SKILLSMP_API,
            params={"q": query, "limit": limit},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        r.raise_for_status()
        return [hit["skill"] for hit in r.json().get("data", {}).get("data", [])]


async def search_plugins(query: str, limit: int = 10) -> list[dict]:
    return []


async def download_file(url: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text
