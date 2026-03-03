# Extending the Application

## Add a New Agent

The multi-agent pipeline can be extended with additional agent roles (e.g., a
Pharmacy Benefits agent, Prior Treatment Verification agent, or Financial
Review agent). Each agent follows a consistent pattern across seven files:

**Step 1 — Agent file** (`backend/app/agents/new_agent.py`):

Create a new agent module with the dual-mode pattern (skills vs prompt):

```python
import json
from pathlib import Path
from agent_framework_claude import ClaudeAgent
from app.agents._parse import parse_json_response
from app.config import settings
from app.tools.mcp_config import NEW_AGENT_MCP_SERVERS  # if using MCP

_BACKEND_DIR = str(Path(__file__).resolve().parent.parent.parent)

# Inline prompt for prompt mode (USE_SKILLS=false)
NEW_AGENT_INSTRUCTIONS = """\
You are a [Role Name] Agent for prior authorization review.
...your instructions, output format, rules...
"""

async def create_new_agent() -> ClaudeAgent:
    if settings.USE_SKILLS:
        return ClaudeAgent(
            instructions=(
                "You are a [Role Name] Agent. "
                "Use your [skill-name] Skill."
            ),
            default_options={
                "cwd": _BACKEND_DIR,
                "setting_sources": ["user", "project"],
                "allowed_tools": [
                    "Skill",
                    "mcp__server-name__tool_name",  # if using MCP
                ],
                "mcp_servers": NEW_AGENT_MCP_SERVERS,  # if using MCP
                "permission_mode": "bypassPermissions",
            },
        )
    return ClaudeAgent(
        instructions=NEW_AGENT_INSTRUCTIONS,
        default_options={
            "mcp_servers": NEW_AGENT_MCP_SERVERS,  # if using MCP
            "permission_mode": "bypassPermissions",
        },
    )

async def run_new_review(request_data: dict, upstream: dict | None = None) -> dict:
    agent = await create_new_agent()
    prompt = f"""Review the following prior authorization request.

--- REQUEST ---
Patient: {request_data.get('patient_name')}
...build prompt from request_data and any upstream findings...
--- END REQUEST ---

Return your structured JSON assessment."""

    async with agent:
        response = await agent.run(prompt)
    return parse_json_response(response)
```

Key conventions:
- `create_*()` factory returns a `ClaudeAgent` configured for either mode
- `run_*()` builds the prompt, executes the agent, and parses JSON output
- `parse_json_response()` extracts JSON from agent output robustly
- Agents that need upstream results accept them as an optional dict parameter

**Step 2 — SKILL.md** (`backend/.claude/skills/new-agent/SKILL.md`):

```markdown
# [Role Name] Skill

## Description
One-liner describing what this agent does.

## Instructions
[Same content as NEW_AGENT_INSTRUCTIONS — keep synced]

### Available MCP Tools (if applicable)
- `mcp__server-name__tool_name(param)` — Description

### Output Format
Return JSON:
{
    "field": "value"
}

### Quality Checks
Before completing, verify:
- [ ] All required fields present in output
- [ ] Output is valid JSON

### Common Mistakes to Avoid
- Do NOT generate fake data when a tool call fails
- Do NOT make final approval/denial decisions (synthesis agent does that)
```

**Step 3 — MCP config** (`backend/app/tools/mcp_config.py`):

If the agent uses MCP servers, create an agent-specific server group:

```python
NEW_AGENT_MCP_SERVERS = {
    "server-name": NEW_SERVER,
}
```

**Step 4 — Orchestrator** (`backend/app/agents/orchestrator.py`):

Import and register the agent in `run_multi_agent_review()`:

```python
from app.agents.new_agent import run_new_review
```

The pipeline has four phases:

```
Phase 1 (parallel):   Compliance + Clinical  → asyncio.gather()
Phase 2 (sequential): Coverage (needs Clinical findings)
Phase 3 (synthesis):  Reasoning-only, all results as input
Phase 4 (audit):      Build audit trail + justification PDF
```

To add a parallel agent:
```python
new_task = asyncio.create_task(
    _safe_run("New Agent", run_new_review, request_data)
)
compliance_result, clinical_result, new_result = await asyncio.gather(
    compliance_task, clinical_task, new_task
)
```

To add a sequential agent:
```python
new_result = await _safe_run(
    "New Agent", run_new_review, request_data, clinical_result
)
```

**Step 5 — Synthesis prompt** (`backend/app/agents/orchestrator.py`):

Add the new agent's output to the synthesis prompt:

```python
prompt = f"""...existing synthesis prompt...

--- NEW AGENT REPORT ---
{json.dumps(new_result, indent=2, default=str)}

--- END REPORTS ---
..."""
```

**Step 6 — SSE progress events** (`backend/app/agents/orchestrator.py`):

Add the new agent to progress event emissions:

```python
await _emit({
    "phase": "phase_1",
    "agents": {
        "compliance": {"status": "running", "detail": "..."},
        "clinical": {"status": "running", "detail": "..."},
        "new_agent": {"status": "running", "detail": "Starting..."},
    },
})
```

Update `frontend/lib/types.ts` and `ProgressTracker` for the new agent.

**Step 7 — Audit trail and PDF** (optional):

Update `_build_audit_trail()`, `_generate_audit_justification()`, and
`generate_audit_justification_pdf()` for the new agent's data.

**Summary of files touched:**

| File | Change |
|------|--------|
| `agents/new_agent.py` | New file: agent factory + run function |
| `.claude/skills/new-agent/SKILL.md` | New file: skill instructions |
| `tools/mcp_config.py` | Add server group (if using MCP) |
| `agents/orchestrator.py` | Import, phase registration, synthesis prompt, SSE events |
| `frontend/lib/types.ts` | Add agent ID to types |
| `frontend/components/progress-tracker.tsx` | Render new agent status |
| `services/audit_pdf.py` | Render new agent data in PDF (optional) |

---

## Add a New MCP Server

Six files need changes:

**Step 1 — Configuration** (`backend/app/config.py`):

```python
class Settings:
    MCP_CPT_VALIDATOR: str = os.getenv(
        "MCP_CPT_VALIDATOR", "https://mcp.example.com/cpt-validator/mcp"
    )
```

**Step 2 — Environment files** (`backend/.env` and `backend/.env.example`):

```bash
MCP_CPT_VALIDATOR=https://mcp.example.com/cpt-validator/mcp
```

**Step 3 — Server registry** (`backend/app/tools/mcp_config.py`):

```python
CPT_SERVER = {"type": "http", "url": settings.MCP_CPT_VALIDATOR, "headers": _HEADERS}

CLINICAL_MCP_SERVERS = {
    "icd10-codes": ICD10_SERVER,
    "pubmed": PUBMED_SERVER,
    "clinical-trials": TRIALS_SERVER,
    "cpt-validator": CPT_SERVER,           # new
}
```

**Step 4 — Agent allowed tools** (e.g., `backend/app/agents/clinical_agent.py`):

```python
"allowed_tools": [
    "Skill",
    "mcp__cpt-validator__validate_cpt",    # new
    "mcp__cpt-validator__lookup_cpt",      # new
],
```

**Step 5 — SKILL.md**:

```markdown
#### CPT Validator MCP (cpt-validator)
- `mcp__cpt-validator__validate_cpt(code)` — Check if CPT code is valid
- `mcp__cpt-validator__lookup_cpt(code)` — Get description and RVU value
```

**Step 6 — Orchestrator** (only if creating a new agent role).

**Architecture summary:**

```
.env                    → URL configuration
config.py               → Settings class (reads env vars)
tools/mcp_config.py     → Server-to-agent mapping
agents/<agent>.py       → Tool allowlist (security boundary)
.claude/skills/*/SKILL.md → Usage instructions
agents/orchestrator.py  → Pipeline phases (only if adding a new agent role)
```

---

## Change the Decision Rubric

In **skills mode** (`USE_SKILLS=true`), edit:
- `backend/.claude/skills/synthesis-decision/SKILL.md`
- `backend/.claude/references/rubric.md`

In **prompt mode** (`USE_SKILLS=false`), edit `SYNTHESIS_INSTRUCTIONS` in
`orchestrator.py`.

**Important:** Both modes are synced. If you change one, update the other.

---

## Customize Notification Letters

Edit `backend/app/services/notification.py`. The `generate_approval_letter()`
and `generate_pend_letter()` functions accept parameters and produce structured
text. The `generate_letter_pdf()` function renders a professionally formatted
PDF using `fpdf2`.

---

## Add CPT/HCPCS Codes to the Lookup Table

Edit `_KNOWN_CODES` in `backend/app/services/cpt_validation.py`.

---

## Use MCP with Non-Claude Models

Use `MCPStreamableHTTPTool` from the Agent Framework:

```python
import httpx
from agent_framework import MCPStreamableHTTPTool

http_client = httpx.AsyncClient(headers={"User-Agent": "claude-code/1.0"})
mcp_tool = MCPStreamableHTTPTool(name="npi", url=NPI_URL, http_client=http_client)

async with mcp_tool:
    result = await mcp_tool.session.call_tool("npi_validate", {"npi": "1234567893"})
```

---

## Future Enhancement: Azure AI Search for Policy RAG

The current system retrieves coverage policies at runtime via the **CMS Coverage MCP server**, which provides Medicare LCDs and NCDs. This works well for Medicare cases but has limitations — the Synthesis agent already flags this with a disclaimer:

> *"Coverage policies reflect Medicare LCDs/NCDs only. If this review is for a commercial or Medicare Advantage plan, payer-specific policies may differ."*

**Azure AI Search** with vector indexing could significantly enhance the system by enabling semantic retrieval over a broader set of policy documents. Below are the opportunities, organized by which agent would benefit.

### Where AI Search Adds Value

| Agent | Index Content | What It Enables |
|-------|--------------|-----------------|
| **Coverage Agent** | Commercial payer PA policies (UHC, Aetna, BCBS, Cigna, etc.) | Payer-specific coverage criteria instead of Medicare-only. E.g., "UHC requires 6 weeks of conservative therapy before approving spinal fusion." |
| **Coverage Agent** | Medicare Advantage plan-specific supplements | Plan-level nuances beyond standard Medicare LCDs/NCDs |
| **Clinical Agent** | Clinical practice guidelines (ACR Appropriateness Criteria, NCCN, AUA, etc.) | Evidence-based clinical reasoning beyond what PubMed MCP returns — structured guidelines rather than raw literature |
| **Compliance Agent** | Organization-specific PA submission requirements | Internal checklists, required documentation templates, payer-specific form requirements |
| **Synthesis Agent** | Historical PA decisions (vectorized) | Precedent-based reasoning — "95% of similar cases with this diagnosis and procedure were approved" |

### How It Would Work

Azure AI Search would be exposed as an **MCP tool** (or direct SDK call) that agents query during their review:

```
Coverage Agent prompt → "Search payer policies for CPT 22630 with UnitedHealthcare"
                      → AI Search vector query → top-k relevant policy chunks
                      → Agent reasons over retrieved policy text
```

Each index would use:
- **Vector embeddings** (Azure OpenAI `text-embedding-3-large`) for semantic search
- **Hybrid search** (vector + keyword) for policy ID lookups
- **Metadata filters** (payer name, effective date, procedure category) for precision

### What You Would Need

| Requirement | Details |
|-------------|---------|
| **Policy documents** | PDFs or structured text from commercial payers. These are typically proprietary and obtained through payer contracts or provider portals. |
| **Azure AI Search resource** | Standard tier or higher for vector search support |
| **Embedding model** | An Azure OpenAI embedding deployment (e.g., `text-embedding-3-large`) in the same region |
| **Ingestion pipeline** | Document chunking, embedding, and indexing — can use Azure AI Search's built-in [integrated vectorization](https://learn.microsoft.com/en-us/azure/search/vector-search-integrated-vectorization) or a custom pipeline |
| **MCP server or tool wrapper** | Expose the search index as a tool the agents can call |

### What It Does NOT Replace

AI Search is a **retrieval** layer — it complements, not replaces, the existing MCP tools:

| Data Source | Keep Using | Why |
|-------------|-----------|-----|
| CMS Coverage MCP | ✅ | Live, authoritative Medicare LCD/NCD data |
| NPI Registry MCP | ✅ | Real-time provider verification |
| ICD-10 MCP | ✅ | Code validation and lookup |
| PubMed MCP | ✅ | Current medical literature |
| Clinical Trials MCP | ✅ | Active trial matching |

AI Search would add a **sixth data source** — payer policy documents — not replace the existing five.

### Implementation Priority

This enhancement is most valuable when:
1. The system needs to handle **commercial payer** cases (not just Medicare)
2. The organization has **access to payer policy documents** to index
3. There is a need for **historical decision** consistency across reviewers

Until policy documents are available for ingestion, the current CMS-only approach is appropriate for the demo scope.
