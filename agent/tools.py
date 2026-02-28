import httpx

MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers"
SKILLS_API = "https://claude-plugins.dev/api/skills"
PLUGINS_API = "https://claude-plugins.dev/api/plugins"


async def search_mcp(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(MCP_REGISTRY, params={"search": query, "limit": limit})
        r.raise_for_status()
        return r.json().get("servers", [])


async def search_skills(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(SKILLS_API, params={"search": query, "limit": limit})
        r.raise_for_status()
        return r.json().get("skills", [])


async def search_plugins(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(PLUGINS_API, params={"search": query, "limit": limit})
        r.raise_for_status()
        return r.json().get("plugins", [])


async def download_file(url: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text
