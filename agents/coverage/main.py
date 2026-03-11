"""Coverage Assessment Hosted Agent — MAF entry point.

Verifies provider NPI, searches Medicare coverage policies via CMS MCP,
maps clinical findings to policy criteria with MET/NOT_MET/INSUFFICIENT
assessment, and returns a structured coverage evaluation.

Self-hosted FastAPI container; invoked over HTTP by the FastAPI orchestrator.
MCP connections are owned by this container (no Foundry Tool registration needed).
"""
import json
import os
from pathlib import Path

import httpx
import uvicorn
from agent_framework import FileAgentSkillsProvider, MCPStreamableHTTPTool
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from schemas import CoverageResult

load_dotenv(override=True)  # override=True required for Foundry-deployed env vars

# DeepSense CloudFront routes on User-Agent — without this header the server
# returns a 301 redirect to the docs site instead of handling MCP messages.
_MCP_HTTP_CLIENT = httpx.AsyncClient(headers={"User-Agent": "claude-code/1.0"})

app = FastAPI()
_agent = None  # initialized in main()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/")
async def handle(request: Request) -> JSONResponse:
    """Receive orchestrator payload, run agent with MAF structured output."""
    payload = await request.json()
    prompt = json.dumps(payload, indent=2)
    result = await _agent.run(prompt, options={"response_format": CoverageResult})
    if result.value:
        return JSONResponse(result.value.model_dump())
    return JSONResponse({"error": result.text or "Agent returned no structured output"})


def main() -> None:
    global _agent

    # --- MCP tool connections (self-hosted, no Foundry Tool registration) ---
    npi_tool = MCPStreamableHTTPTool(
        name="npi-registry",
        description="Validate and look up provider NPI numbers from CMS NPPES",
        url=os.environ["MCP_NPI_REGISTRY"],
        http_client=_MCP_HTTP_CLIENT,
        load_prompts=False,
    )
    cms_tool = MCPStreamableHTTPTool(
        name="cms-coverage",
        description="Search Medicare NCDs, LCDs and coverage policy documents",
        url=os.environ["MCP_CMS_COVERAGE"],
        http_client=_MCP_HTTP_CLIENT,
        load_prompts=False,
    )

    # --- Skills from local directory ---
    skills_provider = FileAgentSkillsProvider(
        skill_paths=str(Path(__file__).parent / "skills")
    )

    # --- Agent using Responses API on Azure AI Foundry ---
    _agent = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    ).as_agent(
        name="coverage-assessment-agent",
        instructions=(
            "You are a Coverage Assessment Agent for prior authorization requests. "
            "Use your coverage-assessment skill to verify provider credentials, search "
            "coverage policies, and map clinical evidence to policy criteria with "
            "MET/NOT_MET/INSUFFICIENT assessment and per-criterion confidence scoring."
        ),
        tools=[npi_tool, cms_tool],
        context_providers=[skills_provider],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
