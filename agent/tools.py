import os
import httpx

MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers"
SKILLSMP_API = "https://skillsmp.com/api/v1/skills/ai-search"


async def search_mcp(query: str, limit: int = 10) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(MCP_REGISTRY, params={"search": query, "limit": limit})
            r.raise_for_status()
            return r.json().get("servers", [])
    except (httpx.HTTPStatusError, httpx.RequestError):
        return []


async def search_skills(query: str, limit: int = 10) -> list[dict]:
    api_key = os.getenv("SKILLSMP_API_KEY", "")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                SKILLSMP_API,
                params={"q": query, "limit": limit},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            hits = r.json().get("data", {}).get("data", [])
            results = []
            for hit in hits:
                file_meta = hit.get("attributes", {}).get("file", {})
                content_blocks = hit.get("content", [])
                results.append({
                    "name": file_meta.get("skill-name", ""),
                    "skill_id": file_meta.get("skill-id", ""),
                    "content": content_blocks[0]["text"] if content_blocks else "",
                })
            return results
    except (httpx.HTTPStatusError, httpx.RequestError):
        return []


async def search_plugins(query: str, limit: int = 10) -> list[dict]:
    return []


async def download_file(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
    except (httpx.HTTPStatusError, httpx.RequestError):
        return ""
