```skill
---
name: foundry-multi-agent-solution-accelerator
description: "Scaffold a complete, production-pattern Microsoft Foundry Multi-Agent Solution Accelerator from scratch for any domain vertical. USE FOR: gathering business and technical requirements, generating project structure, README, Azure Bicep infra, azure.yaml, Foundry Hosted Agent code, FastAPI orchestrator, Next.js frontend, Docker Compose, agent registration scripts, SVG architecture diagrams, observability, security hardening, CI/CD setup, and Responsible AI documentation. Produces a fully azd-deployable template with one 'azd up' command. DO NOT USE FOR: modifying existing agents, deploying to Foundry (use microsoft-foundry skill), general Azure resource management."
---

# Foundry Multi-Agent Solution Accelerator — Universal Scaffold Skill

This skill generates a **complete, production-pattern multi-agent solution accelerator** deployable to **Microsoft Foundry** with `azd up`. It is fully domain-agnostic and applies to any vertical (Healthcare, Finance, Legal, HR, Supply Chain, etc.). It produces every file needed: requirements documentation, project structure, README, Bicep infra, `azure.yaml`, agent containers, orchestrator backend, frontend, Docker Compose, SVG architecture diagrams, observability, security hardening, CI/CD, and Responsible AI documentation.

---

## Required Workflow

Follow these steps **in order**. Do not skip or reorder steps. Each step's output feeds the next.

---

### Step 1 — Gather Business & Technical Requirements

This is the most important step. **Do not generate any files until this step is complete.**

#### 1A — Business Requirements

Ask the user (or infer from context) the following. Document answers before proceeding.

| # | Question | Guidance |
|---|---|---|
| B1 | **What business problem does this solution solve?** | One sentence. This becomes the README opening and spec.yaml description. |
| B2 | **Who are the end users?** (e.g. analysts, reviewers, agents, customers) | Drives UI design and access control decisions. |
| B3 | **What is the primary input?** (e.g. document, form, data record, text) | Drives upload form, backend schema, agent input contract. |
| B4 | **What is the primary output / decision?** (e.g. approve/reject, risk score, summary, action plan) | Drives Synthesis agent design and decision panel. |
| B5 | **What is the target SLA / latency?** (e.g. <2 min per case) | Drives parallelism decisions, agent timeout config, ACA scaling rules. |
| B6 | **Is human-in-the-loop required?** (override capability, review step) | Drives frontend decision panel, override API, audit trail. |
| B7 | **What domain industry?** (Healthcare, Finance, Legal, HR, etc.) | Drives TRANSPARENCY_FAQ.md, spec.yaml industry, compliance notes. |
| B8 | **What regulations or compliance requirements apply?** (HIPAA, SOC2, GDPR, etc.) | Drives TRANSPARENCY_FAQ.md limitations section and production hardening guidance. |

#### 1B — Technical Requirements

| # | Question | Guidance |
|---|---|---|
| T1 | **Number and names of specialist agents** (recommend 3–5) | Each agent must have a distinct, non-overlapping scope. Always include a Synthesis/Decision agent as the final stage. |
| T2 | **Orchestration topology** | Options: all-parallel → synthesis; parallel-batch → sequential → synthesis; fully sequential. Default: parallel-then-synthesis. |
| T3 | **External data sources / MCP tools needed per agent** (optional) | Determines which agents need `MCPStreamableHTTPTool`. List tool name, URL, auth type. |
| T4 | **Azure OpenAI model name** | Default: `gpt-5.4`. Other options: `gpt-4o`, `gpt-4.1`. Model choice determines available regions. |
| T5 | **Azure regions** | Constrained by model availability. `gpt-5.4`: `eastus2`, `swedencentral`. `gpt-4o`: most regions. |
| T6 | **Deployment SKU** | `GlobalStandard` (default) or `DataZoneStandard` (data residency, limited regions). |
| T7 | **Frontend required?** | Default: yes (Next.js). If no frontend, skip Step 9. |
| T8 | **Additional Azure services needed?** (e.g. Azure Storage, Cosmos DB, Service Bus, Key Vault) | Determines extra Bicep modules beyond the base set. |
| T9 | **Persistent storage required?** | Default scaffold uses in-memory. Production requires Azure Cosmos DB or PostgreSQL (Flexible Server). |
| T10 | **Authentication / RBAC required?** | Default scaffold has no auth. Production requires Microsoft Entra ID + app registration. |

#### 1C — Document the Requirements

Create `docs/requirements.md` with a structured summary of all B1–B8 and T1–T10 answers. This document is the source of truth for all subsequent generation steps.

---

### Step 2 — Generate Project Structure

Based on the requirements gathered in Step 1, generate the following folder layout. Replace `<agent-N>` with actual agent names. Add or remove optional sections based on T7–T8.

```
<project-slug>/
├── azure.yaml                          # azd project descriptor + pre/postprovision hooks
├── docker-compose.yml                  # Local dev: all containers without Azure
├── docker-compose.override.yml         # Local overrides (ports, volumes, hot-reload)
├── .env.example                        # All env vars documented with descriptions
├── README.md
├── TRANSPARENCY_FAQ.md                 # Responsible AI FAQ
├── CODE_OF_CONDUCT.md                  # Standard Microsoft OSS CoC
├── CONTRIBUTING.md
├── SECURITY.md                         # Vulnerability reporting process
├── SUPPORT.md
├── LICENSE                             # MIT
├── SKILL.md                            # This file (for future scaffolding)
│
├── agents/
│   ├── <agent-1>/
│   │   ├── agent.yaml                  # Foundry Hosted Agent descriptor
│   │   ├── Dockerfile
│   │   ├── main.py                     # MAF entry point (from_agent_framework)
│   │   ├── requirements.txt
│   │   ├── schemas.py                  # Pydantic structured output model
│   │   └── skills/
│   │       └── <agent-1>-skill/
│   │           └── skill.md            # Domain rules, decision criteria, output contract
│   └── <agent-N>/  (repeat for each agent)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── e2e_test.py                     # End-to-end integration tests
│   └── app/
│       ├── __init__.py
│       ├── main.py                     # FastAPI app factory + lifespan
│       ├── config.py                   # pydantic-settings Settings class
│       ├── observability.py            # OTel + Azure Monitor setup
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── <agent-N>.py            # Per-agent HTTP dispatcher (one file per agent)
│       │   ├── orchestrator.py         # Fan-out/fan-in coordinator
│       │   └── hosted_agents.py        # Two-mode dispatcher (local vs Foundry)
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py              # Shared API request/response schemas
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── agents.py               # /agents/* endpoints
│       │   └── review.py               # /review/* endpoints (submit, status, result)
│       └── services/
│           ├── __init__.py
│           └── storage.py              # In-memory store (swap for DB in prod)
│
├── frontend/                           # Optional — omit if T7=no
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── next.config.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── postcss.config.mjs
│   ├── components.json                 # shadcn/ui config
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── upload-form.tsx             # Input submission UI
│   │   ├── progress-tracker.tsx        # Pipeline phase / agent status
│   │   ├── decision-panel.tsx          # Final output + human override (if B6=yes)
│   │   ├── agent-details.tsx           # Per-agent expandable result cards
│   │   ├── confidence-bar.tsx          # Visual confidence indicator
│   │   ├── header.tsx
│   │   └── ui/                         # shadcn/ui primitives
│   └── lib/
│       ├── api.ts                      # Typed fetch client → backend
│       ├── types.ts                    # TypeScript interfaces mirroring Pydantic schemas
│       ├── sample-case.ts              # Demo data for local testing
│       └── utils.ts
│
├── infra/
│   ├── main.bicep                      # Subscription-scoped entry point
│   ├── main.parameters.json            # azd parameter bindings
│   ├── abbreviations.json              # Azure resource name prefix map
│   └── modules/
│       ├── ai-foundry.bicep            # Foundry account + project + model deployment
│       ├── container-registry.bicep    # ACR (Standard or Premium)
│       ├── container-apps-env.bicep    # Managed Environment + Log Analytics
│       ├── container-app.bicep         # Reusable per-app module
│       ├── monitoring.bicep            # App Insights + Log Analytics workspace
│       └── role-assignments.bicep      # RBAC for all managed identities
│
├── scripts/
│   ├── register_agents.py              # Foundry agent registration + start (postprovision)
│   └── check_agents.py                 # Agent health check
│
└── docs/
    ├── requirements.md                 # Output of Step 1 (B1–T10)
    ├── architecture.md                 # Narrative architecture description
    ├── api-reference.md                # All API endpoints documented
    ├── DeploymentGuide.md              # Step-by-step azd up walkthrough
    ├── extending.md                    # How to add agents, swap models, add tools
    ├── production-migration.md         # In-memory → DB, adding auth, scaling
    ├── troubleshooting.md              # Common errors + fixes
    └── images/
        └── readme/
            ├── solution-architecture.svg   # Azure-native architecture (Step 7)
            ├── agentic-architecture.svg    # Agent pipeline flow (Step 7)
            └── interface.png               # 1600×900 UI screenshot (fit+center, no distortion)
```

---

### Step 3 — Generate README.md

Use the following structure. Populate every section using the requirements from Step 1. Do not leave placeholder text in the final output.

#### Required sections (in order):

1. **H1 Title** — Solution name from B1
2. **Badges row** — `[![License: MIT]...]`, `[![Azure Deployable]...]`, `[![Agent Framework]...]`
3. **One-paragraph summary** — B1 answer + agent count from T1 + primary output from B4 + key SLA from B5 + tech stack
4. **`> [!NOTE]` Responsible AI callout** — link to TRANSPARENCY_FAQ.md, Microsoft AI principles
5. **Navigation anchors** — `[SOLUTION OVERVIEW] | [QUICK DEPLOY] | [BUSINESS SCENARIO] | [SUPPORTING DOCS]`
6. **Solution Overview**
   - SVG solution architecture diagram (`docs/images/readme/solution-architecture.svg`)
   - SVG agentic pipeline diagram (`docs/images/readme/agentic-architecture.svg`)
   - Key features as collapsible `<details>` blocks (one per agent + one for observability + one for local dev)
7. **Runtime Modes table**

   | Mode | How to start | What happens |
   |---|---|---|
   | Foundry Hosted Agent (recommended) | `azd up` | Agents registered with Foundry; Foundry manages container lifecycle |
   | Local / Docker Compose | `docker compose up` | All containers run locally — no Azure required |

8. **Quick Deploy**
   - Prerequisites checklist (Azure subscription, `azd` CLI, Docker, Python 3.12+, Node.js 20+)
   - Step-by-step `azd up` walkthrough
   - Environment variables reference table (name, required/optional, description, example)
9. **Business Scenario** — B1–B3 context, who uses it, what problem it solves
10. **Local Development** — `.env.example` setup, `docker compose up`, test endpoint
11. **Agent Details** — Table: agent name | responsibility | MCP tools | model | CPU/memory
12. **Project Structure** — Condensed annotated tree (top 2 levels only)
13. **Extending the Solution** — Adding an agent, swapping a model, adding an MCP tool
14. **Supporting Documentation** — Table linking all `docs/` files
15. **Responsible AI** — Link to TRANSPARENCY_FAQ.md + Microsoft Responsible AI page

**README conventions:**
- All diagrams must be SVG (not PNG) — SVGs scale cleanly on GitHub and in dark mode
- Section anchors must be lowercase with hyphens (e.g. `#quick-deploy`)
- Interface screenshot must be 1600×900 PNG — scale to fit with no distortion; use matching app background color for padding
- Never use `<br>` for spacing — use blank lines between sections

---

### Step 4 — Generate Azure Bicep Infrastructure

#### Design principles:
- Subscription-scoped (`targetScope = 'subscription'`) to create the resource group
- All modules are in `infra/modules/` and called from `main.bicep`
- Every resource gets `tags` with `azd-env-name` and a solution identifier
- Use `uniqueString()` for resource name tokens to avoid collisions
- All secrets output as `@secure()` — never output plain text secrets from Bicep
- Use `2025-06-01` API version for Cognitive Services / Foundry resources

#### `infra/main.bicep` — Required parameters:

```bicep
targetScope = 'subscription'

@minLength(1) @maxLength(64)
param environmentName string          // from azd

@minLength(1)
param location string                 // constrained by model — validate in preprovision hook

param modelDeploymentName string = '<model-name>'   // from T4 (e.g. gpt-5.4, gpt-4o)
param modelVersion string = '<version>'             // specific model version
param deploymentSkuName string = 'GlobalStandard'  // from T6

// Add additional params for any extra Azure services from T8
```

#### Module dependency order (strictly enforce):
```
monitoring → ai-foundry → container-registry → container-apps-env → container-app(×N) → role-assignments
```

#### `infra/modules/ai-foundry.bicep` — Critical patterns:

```bicep
// Foundry account: kind='AIServices', sku='S0'
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  kind: 'AIServices'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: accountName   // must be globally unique
    publicNetworkAccess: 'Enabled'
  }
}

// Foundry project is a child resource of the account
resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundryAccount
  name: projectName
}

// Model deployment lives under the ACCOUNT (not the project)
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundryAccount
  name: deploymentName
  sku: { name: deploymentSkuName, capacity: capacityK }
  properties: {
    model: { format: 'OpenAI', name: modelName, version: modelVersion }
  }
}

// CRITICAL: Project endpoint must be in this exact format
output projectEndpoint string = 'https://${foundryAccount.properties.customSubDomainName}.services.ai.azure.com/api/projects/${foundryProject.name}'
```

#### `infra/modules/role-assignments.bicep` — Mandatory RBAC:

```bicep
// Each agent + backend container app managed identity MUST have both roles
// on the Foundry account scope:
// Cognitive Services OpenAI User: 5e0bd9bd-7b93-4f28-af87-19fc36ad61bd
// Azure AI User:                  53ca9b11-8b9d-4b51-acae-26b3df39f6f0
```

#### `infra/main.parameters.json`:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName":        { "value": "${AZURE_ENV_NAME}" },
    "location":               { "value": "${AZURE_LOCATION}" },
    "modelDeploymentName":    { "value": "${AZURE_OPENAI_DEPLOYMENT_NAME}" },
    "deploymentSkuName":      { "value": "${AZURE_OPENAI_DEPLOYMENT_SKU}" }
  }
}
```

#### Additional modules for optional services (from T8):

| Service | Module file | Notes |
|---|---|---|
| Azure Cosmos DB | `cosmos.bicep` | Use `serverless` SKU for dev, `provisioned` for prod |
| Azure Storage | `storage.bicep` | Use `Standard_LRS` for dev, `Standard_ZRS` for prod |
| Azure Key Vault | `keyvault.bicep` | Required if any secrets beyond Foundry endpoint |
| Azure Service Bus | `servicebus.bicep` | Use for async agent triggering at scale |

---

### Step 5 — Generate `azure.yaml` (azd project descriptor)

```yaml
name: <project-slug>
metadata:
  template: <project-slug>@1.0
requiredVersions:
  azd: '>= 1.18.0'

hooks:
  preprovision:
    # Validate region is supported for the chosen model
    # Prompt user to select deployment SKU (GlobalStandard vs DataZoneStandard)
    # Emit clear error messages with remediation instructions
    windows: { run: scripts/preprovision.ps1, shell: pwsh }
    posix:   { run: scripts/preprovision.sh,  shell: sh }

  postprovision:
    # 1. az acr login --name $ACR_NAME
    # 2. For each image: az acr build --registry $ACR_NAME --image <name>:$IMAGE_TAG --platform linux/amd64 ./<path>
    # 3. IMAGE_TAG = timestamp (YYYYMMDDHHmmss) — NEVER use 'latest' (Foundry won't re-pull)
    # 4. python scripts/register_agents.py
    windows: { run: scripts/postprovision.ps1, shell: pwsh }
    posix:   { run: scripts/postprovision.sh,  shell: sh }
```

**`azure.yaml` conventions:**
- `IMAGE_TAG` must always be a timestamp — `latest` prevents Foundry from re-pulling updated images
- `preprovision` must exit non-zero on validation failure to block broken deploys
- `postprovision` must validate all ACR images exist before calling `register_agents.py`
- All hook scripts must work on both Windows (PowerShell) and Linux/macOS (bash)

---

### Step 6 — Generate Foundry Hosted Agent Files (per agent)

For each agent identified in T1, generate all of the following:

#### `agents/<name>/agent.yaml`

```yaml
name: <agent-name>           # kebab-case — must match name used in register_agents.py
description: >               # REQUIRED — appears in Foundry portal Description column
  <One-paragraph description. Include: what this agent does, what tools/data it uses,
  what structured output it produces. ~2-3 sentences.>
runtime: agent-framework
version: "1.0.0"
resources:
  cpu: "1"       # use "0.5" for reasoning-only agents with no MCP tools
  memory: "2Gi"  # use "1Gi" for lightweight agents
env:
  - name: AZURE_AI_PROJECT_ENDPOINT
    secretRef: azure-ai-project-endpoint
  - name: AZURE_OPENAI_DEPLOYMENT_NAME
    value: <model-deployment-name>   # from T4
  # Add per-agent MCP URLs here if this agent uses external tools (from T3)
  - name: APPLICATION_INSIGHTS_CONNECTION_STRING
    secretRef: app-insights-connection-string
```

#### `agents/<name>/main.py` — Mandatory patterns:

```python
"""<AgentName> Hosted Agent — MAF entry point."""
import os
from agent_framework import SkillsProvider
# Only import MCPStreamableHTTPTool if this agent uses MCP (from T3)
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.ai.agentserver.agentframework import from_agent_framework
from azure.identity import DefaultAzureCredential
from schemas import <OutputSchema>

def main() -> None:
    # 1. Normalize App Insights env var (adapter expects no-underscore variant)
    _ai_conn = os.environ.get("APPLICATION_INSIGHTS_CONNECTION_STRING")
    if _ai_conn:
        os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", _ai_conn)

    # 2. Load domain skill rules from skills/<name>-skill/skill.md
    skills = SkillsProvider.from_directory("skills")

    # 3. Wire MCP tools (only if this agent uses external tools)
    # tools = [MCPStreamableHTTPTool(server_url=os.environ["MCP_<TOOL>_URL"], ...)]

    # 4. Build Azure OpenAI client using managed identity (no API keys)
    client = AzureOpenAIResponsesClient(
        endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
        model=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "<model-name>"),
    )

    # 5. Start hosted agent server — structured output enforced via response_format
    from_agent_framework(
        client=client,
        skills=skills,
        # tools=tools,
        default_options={"response_format": <OutputSchema>},
    ).run()

if __name__ == "__main__":
    main()
```

#### `agents/<name>/schemas.py`:

```python
from pydantic import BaseModel, Field
from typing import Literal

class <OutputSchema>(BaseModel):
    """Structured output for <AgentName>. Every field must have a Field(description=...)."""
    summary: str = Field(description="Human-readable summary of findings")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Composite confidence 0-1")
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"]
    # --- Domain-specific fields go here ---
    errors: list[str] = Field(default_factory=list, description="Processing errors if any")
```

#### `agents/<name>/skills/<name>-skill/skill.md`:

```markdown
# <Agent Name> — Domain Skill

## Role
You are a specialized <domain> agent. Your sole responsibility is: <one sentence scope>.
You do NOT perform tasks outside this scope — other agents handle those.

## Input Contract
You receive: <describe input fields>

## Instructions
<Step-by-step reasoning process. Be explicit:>
1. <First thing the agent should check/do>
2. <Second step — include decision criteria, thresholds, tool call conditions>
3. <Edge cases and fallback behavior>

## Output Requirements
- Always return a JSON object matching the <OutputSchema> Pydantic model exactly
- Never return free-form prose as your final response
- If data is missing, set confidence_level to LOW and describe gaps in `errors`
- confidence_score must reflect actual certainty, not optimism
```

---

### Step 7 — Generate Azure-Native Architecture Diagrams in SVG

Generate **two SVG diagrams** for `docs/images/readme/`. Use **Gemini 2.0 Flash** (or Gemini 2.5 Pro) to generate the SVG markup — instruct it as follows:

#### 7A — `solution-architecture.svg` (Azure resource topology)

Prompt template to send to Gemini:
```
Generate a clean SVG architecture diagram showing an Azure-native multi-agent solution with these components:
- User/browser on the left
- Azure Container Apps hosting: Frontend (Next.js), Backend Orchestrator (FastAPI)
- Microsoft Foundry Hosted Agents: [list agents from T1]
- Azure OpenAI (<model from T4>) inside Foundry
- Azure Container Registry (stores Docker images)
- Azure Application Insights + Azure Monitor (cross-cutting observability)
- [Any additional services from T8]
Use Microsoft Azure icon colors: blue (#0078D4) for Azure services, purple for AI/Foundry.
Show data flow arrows: User → Frontend → Backend → Agents → Azure OpenAI.
Show cross-cutting arrows to App Insights from all compute.
Style: clean, minimal, dark background (#1E1E1E), white labels, rounded rectangles.
Output only the SVG markup, no explanation.
```

#### 7B — `agentic-architecture.svg` (agent pipeline flow)

Prompt template:
```
Generate a clean SVG flow diagram showing a multi-agent pipeline with these stages:
Input → [Agent 1 (parallel)] → [Agent 2 (parallel)] → [Agent 3 (sequential, depends on prior)] → Synthesis Agent → Output Decision
Show: agent names from T1, parallel execution with a fork/join visual, data flow labels.
Style: clean, minimal, white background or dark (#1E1E1E), color-coded agent boxes.
Output only the SVG markup, no explanation.
```

**SVG diagram requirements:**
- Must render correctly on GitHub (no external font imports, no JavaScript)
- Use `viewBox` with `preserveAspectRatio="xMidYMid meet"` for responsive scaling
- Embed all fonts as `font-family: system-ui, -apple-system, sans-serif`
- Test rendering in a browser before committing
- File size target: < 50 KB per SVG

---

### Step 8 — Generate Backend Orchestrator

#### Orchestration topologies (choose based on T2):

**Topology A — Parallel then Synthesis (default):**
```python
phase1 = await asyncio.gather(agent_1(data), agent_2(data), return_exceptions=True)
final = await synthesis_agent({"inputs": phase1})
```

**Topology B — Batched parallel → sequential → synthesis:**
```python
phase1 = await asyncio.gather(agent_1(data), agent_2(data), return_exceptions=True)
phase2 = await agent_3({**data, "phase1": phase1})
final = await synthesis_agent({"phase1": phase1, "phase2": phase2})
```

**Topology C — Fully sequential:**
```python
r1 = await agent_1(data)
r2 = await agent_2({**data, "r1": r1})
final = await synthesis_agent({"r1": r1, "r2": r2})
```

#### Two-mode dispatcher (`hosted_agents.py`):

```python
"""Two-mode dispatcher: direct HTTP (Docker Compose) vs Foundry routing (production)."""
FOUNDRY_MODE = bool(os.environ.get("AZURE_AI_PROJECT_ENDPOINT"))

async def dispatch(agent_name: str, payload: dict) -> dict:
    if FOUNDRY_MODE:
        endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
        token = await _get_token("https://cognitiveservices.azure.com/.default")
        url, headers = f"{endpoint}/responses", {"Authorization": f"Bearer {token}"}
        body = {**payload, "agent_reference": agent_name}
    else:
        host = os.environ.get(f"{agent_name.upper().replace('-','_')}_URL", f"http://{agent_name}:8000")
        url, headers, body = f"{host}/responses", {}, payload

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(url, json=body, headers=headers)
        r.raise_for_status()
        return r.json()
```

---

### Step 9 — Generate `docker-compose.yml` (Local Dev)

```yaml
# IMPORTANT: Do NOT set AZURE_AI_PROJECT_ENDPOINT on the backend service.
# Its absence triggers direct container-to-container routing (local mode).
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - AZURE_OPENAI_DEPLOYMENT_NAME=${AZURE_OPENAI_DEPLOYMENT_NAME:-<model-name>}
    depends_on: [<list all agent service names>]

  <agent-1>:
    build: ./agents/<agent-1>
    ports: ["8001:8000"]
    environment:
      - AZURE_AI_PROJECT_ENDPOINT=${AZURE_AI_PROJECT_ENDPOINT}
      - AZURE_OPENAI_DEPLOYMENT_NAME=${AZURE_OPENAI_DEPLOYMENT_NAME:-<model-name>}
      # Add MCP tool URLs if needed

  # Repeat for each agent on sequential ports (8002, 8003, ...)

  frontend:   # Omit if T7=no
    build: ./frontend
    ports: ["3000:80"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### Step 10 — Generate Responsible AI Documents

#### `TRANSPARENCY_FAQ.md` — Must address all six questions:

1. **What is this solution?**
   - Describe the accelerator, its tech stack, and its domain purpose (from B1, B7)
   - State explicitly: *"This is a solution accelerator — not a production-ready application."*

2. **What can it do?**
   - Bullet list of capabilities derived from each agent's T1 responsibilities
   - Include what the Synthesis agent produces

3. **What are its intended uses?**
   - Starting point for organizations building similar systems
   - Demonstrating multi-agent patterns with MAF + Foundry
   - **NOT** intended for: autonomous decision-making without human oversight; production use without testing; regulatory-compliance use without customer validation

4. **How was it evaluated?**
   - End-to-end functional testing (agent schema validation, decision logic)
   - Structured output validation (Pydantic model conformance)
   - Integration testing with external tools (if MCP tools used per T3)

5. **What are the limitations?**
   - In-memory storage — data lost on restart; production requires a database (T9)
   - No authentication/RBAC by default (T10)
   - English-only unless explicitly multilingual
   - External data sources may have coverage gaps or stale data (if MCP tools used)
   - AI output requires human review before any consequential action (from B6)
   - Compliance with regulations from B8 is the **customer's responsibility**

6. **What operational factors affect performance?**
   - Model temperature, token limits, and response latency
   - MCP server availability and rate limits (if applicable)
   - ACA scaling rules and cold-start latency
   - Network egress for external MCP tool calls

---

### Step 11 — Generate `spec.yaml` (Foundry Template Gallery)

```yaml
type: apptemplate
name: <kebab-case-solution-name>
version: 1
display_name: <Human Readable Solution Name>
description: "<One sentence: what it does + primary output + key benefit>"
longDescription: "<3-5 sentences: agents, tech stack, orchestration pattern, deployment story>"
repository: https://github.com/microsoft/<repo-name>
languages:
 - python
 - typescript     # remove if T7=no
author: Microsoft
models:
 - <model-name>   # from T4 (e.g. gpt-5.4, gpt-4o, gpt-4.1)
services:
 - "Microsoft Foundry"
 - "Microsoft Agent Framework"
 - "Azure OpenAI"
 - "Azure Container Apps"
 - "Azure Container Registry"
 - "Azure Monitor"
 - "Azure Application Insights"
 # Add services from T8 here (e.g. "Azure Cosmos DB", "Azure Storage")
templateType: SolutionTemplate
path: ./images
license: MIT
industry:
 - <Industry>     # from B7 (e.g. Healthcare, Financial Services, Legal)
tags:
 - multi-agent
 - agent-framework
 - foundry-hosted-agents
 - azure-container-apps
 - <domain-specific-tags>  # 3-5 tags derived from B7 and T1 agent names
regions:
 - <region-1>    # from T5 — only list regions where chosen model is available
 - <region-2>
disclaimer: "With any AI solutions you create using these templates, you are responsible for assessing all associated risks, and for complying with all applicable laws and safety standards."
```

---

### Step 12 — Observability Setup

Apply to every agent `main.py` and the backend `app/main.py`:

```python
# 1. Normalize env var (MAF adapter reads the no-underscore variant)
_ai_conn = os.environ.get("APPLICATION_INSIGHTS_CONNECTION_STRING")
if _ai_conn:
    os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", _ai_conn)

# For agents: from_agent_framework().run() auto-configures OTel when env var is set.
# For backend: configure manually:
```

```python
# backend/app/observability.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

def setup_observability(connection_string: str) -> None:
    if not connection_string:
        return
    exporter = AzureMonitorTraceExporter(connection_string=connection_string)
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
```

---

## Production Readiness — Additional Requirements

These are items beyond the default scaffold required for any production deployment. Document each gap in `docs/production-migration.md`.

### Security Hardening

| Item | Default scaffold | Production requirement |
|---|---|---|
| **Authentication** | None | Microsoft Entra ID + app registration; protect all API endpoints |
| **RBAC** | None | Role-based access control aligned with B2 user types |
| **Secrets management** | Env vars in ACA | Azure Key Vault; reference from ACA secret store |
| **Network isolation** | Public endpoints | VNet injection for ACA; private endpoints for Foundry + ACR |
| **Container security** | Base image only | Non-root user in Dockerfile; image vulnerability scanning in ACR |
| **API rate limiting** | None | Azure API Management or FastAPI middleware |
| **Input validation** | Pydantic only | Sanitize all inputs; reject oversized payloads |

### Scalability

| Item | Default | Production |
|---|---|---|
| **Storage** | In-memory dict | Azure Cosmos DB (serverless dev → provisioned prod) or PostgreSQL |
| **Session isolation** | Single process | Case IDs with distributed locking |
| **ACA scaling rules** | Default | HTTP-based autoscale; min replicas = 1 per agent |
| **Async processing** | Sync HTTP | Azure Service Bus queue for long-running cases |

### CI/CD Pipeline

Generate `.github/workflows/` with:

```yaml
# ci.yml — runs on every PR
# 1. Python: ruff lint + mypy type check + pytest (backend + agents)
# 2. TypeScript: eslint + tsc --noEmit (frontend)
# 3. Bicep: az bicep build --file infra/main.bicep (syntax validation)

# deploy.yml — runs on push to main
# 1. Build + push all Docker images to ACR with sha tag
# 2. Run register_agents.py to update Foundry agent versions
# 3. Run e2e_test.py smoke test against deployed environment
```

### Cost Optimization

- Set ACA min replicas = 0 for dev environments (agents cold-start on demand)
- Use `serverless` Cosmos DB SKU during development
- Set sensible `deploymentCapacityK` (tokens-per-minute) in `ai-foundry.bicep` — start at 100K TPM
- Tag all resources with environment name for cost center attribution

---

## Quality Checklist

Run through this checklist before delivering the scaffold. Every item must be ✅.

### Requirements & Documentation
- [ ] `docs/requirements.md` exists with all B1–T10 answers filled in
- [ ] `TRANSPARENCY_FAQ.md` covers all 6 required questions
- [ ] README includes both runtime modes table (Foundry + Docker Compose)
- [ ] `docs/production-migration.md` documents all production gaps

### Infrastructure
- [ ] `main.bicep` is subscription-scoped (`targetScope = 'subscription'`)
- [ ] Foundry project endpoint output uses exact format: `https://<subdomain>.services.ai.azure.com/api/projects/<project>`
- [ ] Role assignments grant **both** `Cognitive Services OpenAI User` AND `Azure AI User` to all agent + backend identities
- [ ] All secrets are passed as `@secure()` — no plain-text secret outputs from Bicep
- [ ] `main.parameters.json` binds all params to `${AZURE_*}` azd env vars

### `azure.yaml` & Deployment Hooks
- [ ] `IMAGE_TAG` is always a timestamp (`YYYYMMDDHHmmss`), never `latest`
- [ ] `preprovision` hook validates region against model availability and exits non-zero on failure
- [ ] `postprovision` hook validates ACR images exist before calling `register_agents.py`
- [ ] Hooks have both `windows` (pwsh) and `posix` (sh) variants

### Agents
- [ ] Every `agent.yaml` has a meaningful `description:` (2-3 sentences, not a placeholder)
- [ ] Every `main.py` uses `default_options={"response_format": Schema}` for structured output
- [ ] Every `schemas.py` has `confidence_score`, `confidence_level`, `summary`, and `errors` fields
- [ ] Every agent `skill.md` defines role, input contract, step-by-step instructions, and output requirements
- [ ] `register_agents.py` passes `description=agent_def["description"]` to `create_version()`
- [ ] For agents with MCP tools: `MCPStreamableHTTPTool` is wired in `main.py`

### Backend
- [ ] `docker-compose.yml` does NOT set `AZURE_AI_PROJECT_ENDPOINT` on the backend (enables local mode)
- [ ] `hosted_agents.py` correctly switches between Foundry mode and direct HTTP mode
- [ ] `orchestrator.py` uses `asyncio.gather` for parallel agents (not sequential awaits)
- [ ] `config.py` uses pydantic-settings with `.env` file support

### Frontend (if T7=yes)
- [ ] `lib/types.ts` mirrors all Pydantic schemas from backend `models/schemas.py`
- [ ] `progress-tracker.tsx` uses polling (not WebSocket) for simplicity
- [ ] `decision-panel.tsx` includes human override UI if B6=yes
- [ ] Interface screenshot is 1600×900 PNG, no distortion, no white/black bars if possible

### Architecture Diagrams
- [ ] Both SVGs render correctly in a browser before committing
- [ ] No external font imports in SVGs (use `system-ui`)
- [ ] Both SVGs use `viewBox` + `preserveAspectRatio="xMidYMid meet"`
- [ ] `solution-architecture.svg` shows all Azure services from T8 + cross-cutting App Insights
- [ ] `agentic-architecture.svg` correctly reflects the orchestration topology from T2

### Observability
- [ ] Both env var variants of App Insights connection string are set in all containers
- [ ] Backend calls `setup_observability()` in FastAPI lifespan
- [ ] Each agent span includes `gen_ai.agent.name` attribute for Foundry Traces correlation

### spec.yaml
- [ ] `regions` lists only regions where the model from T4 is actually available
- [ ] `industry` matches B7
- [ ] `tags` includes at least 5 meaningful terms
- [ ] `description` and `longDescription` are fully written (no placeholders)
```
