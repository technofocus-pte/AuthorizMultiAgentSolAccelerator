"""Compliance Validation Hosted Agent — MAF entry point.

Validates documentation completeness for prior authorization requests
using an 8-item checklist. Uses no external tools — pure reasoning
over the submitted request data.

Self-hosted FastAPI container; invoked over HTTP by the FastAPI orchestrator.
No MCP connections required for this agent.
"""
import json
import os
from pathlib import Path

import uvicorn
from agent_framework import FileAgentSkillsProvider
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from schemas import ComplianceResult

load_dotenv(override=True)  # override=True required for Foundry-deployed env vars

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
    result = await _agent.run(prompt, options={"response_format": ComplianceResult})
    if result.value:
        return JSONResponse(result.value.model_dump())
    return JSONResponse({"error": result.text or "Agent returned no structured output"})


def main() -> None:
    global _agent

    # --- No MCP tools — compliance check is pure reasoning ---

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
        name="compliance-agent",
        instructions=(
            "You are a Compliance Validation Agent for prior authorization requests. "
            "Use your compliance-review skill to validate documentation completeness "
            "using the 8-item checklist. You have NO tools — analyze only the request "
            "data provided in the prompt."
        ),
        tools=[],
        context_providers=[skills_provider],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
