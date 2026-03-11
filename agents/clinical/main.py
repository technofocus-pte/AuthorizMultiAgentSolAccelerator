"""Clinical Reviewer Hosted Agent — MAF entry point.

Validates ICD-10 codes, extracts clinical indicators with confidence
scoring, searches PubMed literature and ClinicalTrials.gov, and returns
a structured clinical profile for downstream coverage assessment.

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

from schemas import ClinicalResult

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
    result = await _agent.run(prompt, options={"response_format": ClinicalResult})
    if result.value:
        return JSONResponse(result.value.model_dump())
    return JSONResponse({"error": result.text or "Agent returned no structured output"})


def main() -> None:
    global _agent

    # --- MCP tool connections (self-hosted, no Foundry Tool registration) ---
    icd10_tool = MCPStreamableHTTPTool(
        name="icd10-codes",
        description="Validate and look up ICD-10 diagnosis and procedure codes",
        url=os.environ["MCP_ICD10_CODES"],
        http_client=_MCP_HTTP_CLIENT,
        load_prompts=False,
    )
    pubmed_tool = MCPStreamableHTTPTool(
        name="pubmed",
        description="Search biomedical literature on PubMed",
        url=os.environ["MCP_PUBMED"],
        http_client=_MCP_HTTP_CLIENT,
        load_prompts=False,
    )
    trials_tool = MCPStreamableHTTPTool(
        name="clinical-trials",
        description="Search ClinicalTrials.gov for relevant trials",
        url=os.environ["MCP_CLINICAL_TRIALS"],
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
        name="clinical-reviewer-agent",
        instructions=(
            "You are a Clinical Reviewer Agent for prior authorization requests. "
            "Use your clinical-review skill to validate ICD-10 codes, extract clinical "
            "indicators with confidence scoring, search supporting literature, and "
            "check for relevant clinical trials."
        ),
        tools=[icd10_tool, pubmed_tool, trials_tool],
        context_providers=[skills_provider],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
