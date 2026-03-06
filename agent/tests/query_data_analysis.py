import asyncio
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools import search_mcp, search_skills

QUERY = "data analysis"


async def main():
    print(f"Query: '{QUERY}'\n")

    print("=== MCP Servers ===")
    mcp_results = await search_mcp(QUERY)
    if mcp_results:
        for server in mcp_results:
            print(json.dumps(server, indent=2))
    else:
        print("(no results)")

    print("\n=== Skills (SkillsMP) ===")
    skill_results = await search_skills(QUERY)
    if skill_results:
        for skill in skill_results:
            print(json.dumps(skill, indent=2))
    else:
        print("(no results)")


asyncio.run(main())
