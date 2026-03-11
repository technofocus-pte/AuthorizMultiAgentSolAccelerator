"""Synthesis Decision Hosted Agent — MAF entry point.

Synthesizes outputs from Compliance, Clinical, and Coverage agents into
a final APPROVE or PEND recommendation using gate-based evaluation,
weighted confidence scoring, and a structured audit trail.

Self-hosted FastAPI container; invoked over HTTP by the FastAPI orchestrator.
No MCP connections required — synthesis is pure reasoning over agent outputs.
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

from schemas import SynthesisOutput

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
    result = await _agent.run(prompt, options={"response_format": SynthesisOutput})
    if result.value:
        return JSONResponse(result.value.model_dump())
    return JSONResponse({"error": result.text or "Agent returned no structured output"})


def main() -> None:
    global _agent

    # --- No MCP tools — synthesis is pure reasoning over agent outputs ---

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
        name="synthesis-agent",
        instructions=(
            "You are the Synthesis Agent for prior authorization review. "
            "Use your synthesis-decision skill to evaluate the outputs from the "
            "Compliance, Clinical Reviewer, and Coverage agents through a strict "
            "3-gate pipeline (Provider → Codes → Medical Necessity) and produce "
            "a single APPROVE or PEND recommendation with weighted confidence scoring "
            "and a complete audit trail."
        ),
        tools=[],
        context_providers=[skills_provider],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
