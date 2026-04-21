# src/agents/config.py
from pydantic import BaseModel, Field
from typing import List, Optional

class AgentConfig(BaseModel):
    name: str = Field(..., description="The unique name of the agent (e.g., 'compliance_agent')")
    persona: str = Field(..., description="The system prompt instructing the agent how to behave")
    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-6", 
        description="The AWS Bedrock model identifier"
    )
    authorized_tools: List[str] = Field(default_factory=list, description="List of MCP tool names this agent can use")
    temperature: float = Field(default=0.0, description="Temperature for the LLM. 0.0 for deterministic financial tasks.")

# The "Registry" of our factory. Tomorrow, you can load this from a YAML file or database.
AEON_AGENT_REGISTRY = {
    "client_info_agent": AgentConfig(
        name="client_info_agent",
        persona="You are a precise data-retrieval agent. Use the execute_sql tool to fetch client facts. Return only the data.",
        authorized_tools=["execute_sql"]
    ),
    "compliance_agent": AgentConfig(
        name="compliance_agent",
        persona="You are a strict compliance auditor. Check for missing signatures and stale documents.",
        authorized_tools=["execute_sql"]
    ),
    "sentiment_agent": AgentConfig(
        name="sentiment_agent",
        persona="You are an empathetic communications analyst. Review transcripts for client concerns.",
        authorized_tools=["search_transcripts"]
        # We could override the model here if we wanted to use a cheaper model for sentiment
        # model_id="us.anthropic.claude-3-haiku-20240307-v1:0" 
    )
}