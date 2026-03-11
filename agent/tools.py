import os
import httpx

MCP_REGISTRY = "https://registry.modelcontextprotocol.io/v0/servers"
SKILLSMP_API = "https://skillsmp.com/api/v1/skills/ai-search"
AWESOME_SUBAGENT_BASE_URL = "https://raw.githubusercontent.com/VoltAgent/awesome-claude-code-subagents/main/categories"

# Embedded catalog index from awesome-claude-code-subagents (127+ entries)
AWESOME_SUBAGENT_CATALOG = [
    # 01-core-development
    {"name": "api-designer", "description": "REST and GraphQL API architect", "category": "01-core-development"},
    {"name": "backend-developer", "description": "Server-side expert for scalable APIs", "category": "01-core-development"},
    {"name": "electron-pro", "description": "Desktop application expert", "category": "01-core-development"},
    {"name": "frontend-developer", "description": "UI/UX specialist for React, Vue, and Angular", "category": "01-core-development"},
    {"name": "fullstack-developer", "description": "End-to-end feature development", "category": "01-core-development"},
    {"name": "graphql-architect", "description": "GraphQL schema and federation expert", "category": "01-core-development"},
    {"name": "microservices-architect", "description": "Distributed systems designer", "category": "01-core-development"},
    {"name": "mobile-developer", "description": "Cross-platform mobile specialist", "category": "01-core-development"},
    {"name": "ui-designer", "description": "Visual design and interaction specialist", "category": "01-core-development"},
    {"name": "websocket-engineer", "description": "Real-time communication specialist", "category": "01-core-development"},
    # 02-language-specialists
    {"name": "typescript-pro", "description": "TypeScript specialist", "category": "02-language-specialists"},
    {"name": "sql-pro", "description": "Database query expert", "category": "02-language-specialists"},
    {"name": "swift-expert", "description": "iOS and macOS specialist", "category": "02-language-specialists"},
    {"name": "vue-expert", "description": "Vue 3 Composition API expert", "category": "02-language-specialists"},
    {"name": "angular-architect", "description": "Angular 15+ enterprise patterns expert", "category": "02-language-specialists"},
    {"name": "cpp-pro", "description": "C++ performance expert", "category": "02-language-specialists"},
    {"name": "csharp-developer", "description": ".NET ecosystem specialist", "category": "02-language-specialists"},
    {"name": "django-developer", "description": "Django 4+ web development expert", "category": "02-language-specialists"},
    {"name": "dotnet-core-expert", "description": ".NET 8 cross-platform specialist", "category": "02-language-specialists"},
    {"name": "dotnet-framework-4.8-expert", "description": ".NET Framework legacy enterprise specialist", "category": "02-language-specialists"},
    {"name": "elixir-expert", "description": "Elixir and OTP fault-tolerant systems expert", "category": "02-language-specialists"},
    {"name": "flutter-expert", "description": "Flutter 3+ cross-platform mobile expert", "category": "02-language-specialists"},
    {"name": "golang-pro", "description": "Go concurrency specialist", "category": "02-language-specialists"},
    {"name": "java-architect", "description": "Enterprise Java expert", "category": "02-language-specialists"},
    {"name": "javascript-pro", "description": "JavaScript development expert", "category": "02-language-specialists"},
    {"name": "powershell-5.1-expert", "description": "Windows PowerShell 5.1 and full .NET Framework automation specialist", "category": "02-language-specialists"},
    {"name": "powershell-7-expert", "description": "Cross-platform PowerShell 7+ automation and modern .NET specialist", "category": "02-language-specialists"},
    {"name": "kotlin-specialist", "description": "Modern JVM language expert", "category": "02-language-specialists"},
    {"name": "laravel-specialist", "description": "Laravel 10+ PHP framework expert", "category": "02-language-specialists"},
    {"name": "nextjs-developer", "description": "Next.js 14+ full-stack specialist", "category": "02-language-specialists"},
    {"name": "php-pro", "description": "PHP web development expert", "category": "02-language-specialists"},
    {"name": "python-pro", "description": "Python ecosystem master", "category": "02-language-specialists"},
    {"name": "rails-expert", "description": "Rails 8.1 rapid development expert", "category": "02-language-specialists"},
    {"name": "react-specialist", "description": "React 18+ modern patterns expert", "category": "02-language-specialists"},
    {"name": "rust-engineer", "description": "Systems programming expert", "category": "02-language-specialists"},
    {"name": "spring-boot-engineer", "description": "Spring Boot 3+ microservices expert", "category": "02-language-specialists"},
    # 03-infrastructure
    {"name": "azure-infra-engineer", "description": "Azure infrastructure and Az PowerShell automation expert", "category": "03-infrastructure"},
    {"name": "cloud-architect", "description": "AWS/GCP/Azure specialist", "category": "03-infrastructure"},
    {"name": "database-administrator", "description": "Database management expert", "category": "03-infrastructure"},
    {"name": "docker-expert", "description": "Docker containerization and optimization expert", "category": "03-infrastructure"},
    {"name": "deployment-engineer", "description": "Deployment automation specialist", "category": "03-infrastructure"},
    {"name": "devops-engineer", "description": "CI/CD and automation expert", "category": "03-infrastructure"},
    {"name": "devops-incident-responder", "description": "DevOps incident management", "category": "03-infrastructure"},
    {"name": "incident-responder", "description": "System incident response expert", "category": "03-infrastructure"},
    {"name": "kubernetes-specialist", "description": "Container orchestration master", "category": "03-infrastructure"},
    {"name": "network-engineer", "description": "Network infrastructure specialist", "category": "03-infrastructure"},
    {"name": "platform-engineer", "description": "Platform architecture expert", "category": "03-infrastructure"},
    {"name": "security-engineer", "description": "Infrastructure security specialist", "category": "03-infrastructure"},
    {"name": "sre-engineer", "description": "Site reliability engineering expert", "category": "03-infrastructure"},
    {"name": "terraform-engineer", "description": "Infrastructure as Code expert", "category": "03-infrastructure"},
    {"name": "terragrunt-expert", "description": "Terragrunt orchestration and DRY IaC specialist", "category": "03-infrastructure"},
    {"name": "windows-infra-admin", "description": "Active Directory, DNS, DHCP, and GPO automation specialist", "category": "03-infrastructure"},
    # 04-quality-security
    {"name": "accessibility-tester", "description": "A11y compliance expert", "category": "04-quality-security"},
    {"name": "ad-security-reviewer", "description": "Active Directory security and GPO audit specialist", "category": "04-quality-security"},
    {"name": "architect-reviewer", "description": "Architecture review specialist", "category": "04-quality-security"},
    {"name": "chaos-engineer", "description": "System resilience testing expert", "category": "04-quality-security"},
    {"name": "code-reviewer", "description": "Code quality guardian", "category": "04-quality-security"},
    {"name": "compliance-auditor", "description": "Regulatory compliance expert", "category": "04-quality-security"},
    {"name": "debugger", "description": "Advanced debugging specialist", "category": "04-quality-security"},
    {"name": "error-detective", "description": "Error analysis and resolution expert", "category": "04-quality-security"},
    {"name": "penetration-tester", "description": "Ethical hacking specialist", "category": "04-quality-security"},
    {"name": "performance-engineer", "description": "Performance optimization expert", "category": "04-quality-security"},
    {"name": "powershell-security-hardening", "description": "PowerShell security hardening and compliance specialist", "category": "04-quality-security"},
    {"name": "qa-expert", "description": "Test automation specialist", "category": "04-quality-security"},
    {"name": "security-auditor", "description": "Security vulnerability expert", "category": "04-quality-security"},
    {"name": "test-automator", "description": "Test automation framework expert", "category": "04-quality-security"},
    # 05-data-ai
    {"name": "ai-engineer", "description": "AI system design and deployment expert", "category": "05-data-ai"},
    {"name": "data-analyst", "description": "Data insights and visualization specialist", "category": "05-data-ai"},
    {"name": "data-engineer", "description": "Data pipeline architect", "category": "05-data-ai"},
    {"name": "data-scientist", "description": "Analytics and insights expert", "category": "05-data-ai"},
    {"name": "database-optimizer", "description": "Database performance specialist", "category": "05-data-ai"},
    {"name": "llm-architect", "description": "Large language model architect", "category": "05-data-ai"},
    {"name": "machine-learning-engineer", "description": "Machine learning systems expert", "category": "05-data-ai"},
    {"name": "ml-engineer", "description": "Machine learning specialist", "category": "05-data-ai"},
    {"name": "mlops-engineer", "description": "MLOps and model deployment expert", "category": "05-data-ai"},
    {"name": "nlp-engineer", "description": "Natural language processing expert", "category": "05-data-ai"},
    {"name": "postgres-pro", "description": "PostgreSQL database expert", "category": "05-data-ai"},
    {"name": "prompt-engineer", "description": "Prompt optimization specialist", "category": "05-data-ai"},
    # 06-developer-experience
    {"name": "build-engineer", "description": "Build system specialist", "category": "06-developer-experience"},
    {"name": "cli-developer", "description": "Command-line tool creator", "category": "06-developer-experience"},
    {"name": "dependency-manager", "description": "Package and dependency specialist", "category": "06-developer-experience"},
    {"name": "documentation-engineer", "description": "Technical documentation expert", "category": "06-developer-experience"},
    {"name": "dx-optimizer", "description": "Developer experience optimization specialist", "category": "06-developer-experience"},
    {"name": "git-workflow-manager", "description": "Git workflow and branching expert", "category": "06-developer-experience"},
    {"name": "legacy-modernizer", "description": "Legacy code modernization specialist", "category": "06-developer-experience"},
    {"name": "mcp-developer", "description": "Model Context Protocol specialist", "category": "06-developer-experience"},
    {"name": "powershell-ui-architect", "description": "PowerShell UI/UX specialist for WinForms, WPF, Metro frameworks, and TUIs", "category": "06-developer-experience"},
    {"name": "powershell-module-architect", "description": "PowerShell module and profile architecture specialist", "category": "06-developer-experience"},
    {"name": "refactoring-specialist", "description": "Code refactoring expert", "category": "06-developer-experience"},
    {"name": "slack-expert", "description": "Slack platform and @slack/bolt specialist", "category": "06-developer-experience"},
    {"name": "tooling-engineer", "description": "Developer tooling specialist", "category": "06-developer-experience"},
    # 07-specialized-domains
    {"name": "api-documenter", "description": "API documentation specialist", "category": "07-specialized-domains"},
    {"name": "blockchain-developer", "description": "Web3 and crypto specialist", "category": "07-specialized-domains"},
    {"name": "embedded-systems", "description": "Embedded and real-time systems expert", "category": "07-specialized-domains"},
    {"name": "fintech-engineer", "description": "Financial technology specialist", "category": "07-specialized-domains"},
    {"name": "game-developer", "description": "Game development expert", "category": "07-specialized-domains"},
    {"name": "iot-engineer", "description": "IoT systems developer", "category": "07-specialized-domains"},
    {"name": "m365-admin", "description": "Microsoft 365, Exchange Online, Teams, and SharePoint administration specialist", "category": "07-specialized-domains"},
    {"name": "mobile-app-developer", "description": "Mobile application specialist", "category": "07-specialized-domains"},
    {"name": "payment-integration", "description": "Payment systems expert", "category": "07-specialized-domains"},
    {"name": "quant-analyst", "description": "Quantitative analysis specialist", "category": "07-specialized-domains"},
    {"name": "risk-manager", "description": "Risk assessment and management expert", "category": "07-specialized-domains"},
    {"name": "seo-specialist", "description": "Search engine optimization expert", "category": "07-specialized-domains"},
    # 08-business-product
    {"name": "business-analyst", "description": "Requirements specialist", "category": "08-business-product"},
    {"name": "content-marketer", "description": "Content marketing specialist", "category": "08-business-product"},
    {"name": "customer-success-manager", "description": "Customer success expert", "category": "08-business-product"},
    {"name": "legal-advisor", "description": "Legal and compliance specialist", "category": "08-business-product"},
    {"name": "product-manager", "description": "Product strategy expert", "category": "08-business-product"},
    {"name": "project-manager", "description": "Project management specialist", "category": "08-business-product"},
    {"name": "sales-engineer", "description": "Technical sales expert", "category": "08-business-product"},
    {"name": "scrum-master", "description": "Agile methodology expert", "category": "08-business-product"},
    {"name": "technical-writer", "description": "Technical documentation specialist", "category": "08-business-product"},
    {"name": "ux-researcher", "description": "User research expert", "category": "08-business-product"},
    {"name": "wordpress-master", "description": "WordPress development and optimization expert", "category": "08-business-product"},
    # 09-meta-orchestration
    {"name": "agent-installer", "description": "Browse and install agents from this repository via GitHub", "category": "09-meta-orchestration"},
    {"name": "agent-organizer", "description": "Multi-agent coordinator", "category": "09-meta-orchestration"},
    {"name": "context-manager", "description": "Context optimization expert", "category": "09-meta-orchestration"},
    {"name": "error-coordinator", "description": "Error handling and recovery specialist", "category": "09-meta-orchestration"},
    {"name": "it-ops-orchestrator", "description": "IT operations workflow orchestration specialist", "category": "09-meta-orchestration"},
    {"name": "knowledge-synthesizer", "description": "Knowledge aggregation expert", "category": "09-meta-orchestration"},
    {"name": "multi-agent-coordinator", "description": "Advanced multi-agent orchestration", "category": "09-meta-orchestration"},
    {"name": "performance-monitor", "description": "Agent performance optimization", "category": "09-meta-orchestration"},
    {"name": "task-distributor", "description": "Task allocation specialist", "category": "09-meta-orchestration"},
    {"name": "workflow-orchestrator", "description": "Complex workflow automation", "category": "09-meta-orchestration"},
    # 10-research-analysis
    {"name": "research-analyst", "description": "Comprehensive research specialist", "category": "10-research-analysis"},
    {"name": "search-specialist", "description": "Advanced information retrieval expert", "category": "10-research-analysis"},
    {"name": "trend-analyst", "description": "Emerging trends and forecasting expert", "category": "10-research-analysis"},
    {"name": "competitive-analyst", "description": "Competitive intelligence specialist", "category": "10-research-analysis"},
    {"name": "market-researcher", "description": "Market analysis and consumer insights", "category": "10-research-analysis"},
    {"name": "data-researcher", "description": "Data discovery and analysis expert", "category": "10-research-analysis"},
]


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


async def fetch_subagent_content(name: str, category: str) -> str:
    """Fetch full .md content for a catalog subagent from GitHub."""
    url = f"{AWESOME_SUBAGENT_BASE_URL}/{category}/{name}.md"
    return await download_file(url)


def get_catalog_index_text() -> str:
    """Format the catalog index as a compact text list for LLM prompts."""
    lines = []
    current_cat = ""
    for entry in AWESOME_SUBAGENT_CATALOG:
        cat = entry["category"]
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n[{cat}]")
        lines.append(f"  - {entry['name']}: {entry['description']}")
    return "\n".join(lines)
