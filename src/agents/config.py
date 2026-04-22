# src/agents/config.py
from pydantic import BaseModel, Field
from typing import List

class AgentConfig(BaseModel):
    name: str = Field(..., description="The unique name of the agent")
    persona: str = Field(..., description="The system prompt instructing the agent how to behave")
    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-6", 
        description="The AWS Bedrock model identifier"
    )
    authorized_tools: List[str] = Field(default_factory=list, description="List of MCP tool names this agent can use")
    temperature: float = Field(default=0.0, description="Temperature for the LLM. 0.0 for deterministic financial tasks.")

# The full Enterprise 10-Agent Registry mapped to the AEON Workflows
AEON_AGENT_REGISTRY = {
    # Workflow 1: Client Review & Prep
    "client_info_agent": AgentConfig(
        name="client_info_agent",
        persona="You are a precise data-retrieval agent. Use the execute_sql tool to fetch demographic facts, AUM, and risk profiles. Return only the data.",
        authorized_tools=["execute_sql"]
    ),
    "compliance_agent": AgentConfig(
        name="compliance_agent",
        persona="You are a strict compliance auditor. Query the ComplianceHub table to detect missing signatures, stale IPS documents, and regulatory gaps.",
        authorized_tools=["execute_sql"]
    ),
    "financial_planning_agent": AgentConfig(
        name="financial_planning_agent",
        persona="You are a wealth planner. Query FinancialPlanningFacts to review RMD status, stale estate plans, and upcoming life events.",
        authorized_tools=["execute_sql"]
    ),
    
    # Workflow 2: Portfolio & Performance
    "portfolio_analytics_agent": AgentConfig(
        name="portfolio_analytics_agent",
        persona="You are a quantitative portfolio analyst. Query PortfolioData to identify concentrated positions, low-basis assets, and asset class drift.",
        authorized_tools=["execute_sql"]
    ),
    "performance_benchmark_agent": AgentConfig(
        name="performance_benchmark_agent",
        persona="You are a performance attribution specialist. Review AdvisorPerformance and compare growth/revenue metrics against firm benchmarks.",
        authorized_tools=["execute_sql"]
    ),
    "market_intelligence_agent": AgentConfig(
        name="market_intelligence_agent",
        persona="You are a macroeconomic intelligence agent. Use web search to fetch real-time market news and explain recent market volatility affecting client holdings.",
        authorized_tools=["search_market_news", "execute_sql"]
    ),
    
    # Workflow 3: Meeting Strategy & NBA
    "meeting_prep_agent": AgentConfig(
        name="meeting_prep_agent",
        persona="You are a meeting strategy specialist. Query UpcomingClientMeetings and cross-reference with recent notes to draft highly tailored meeting agendas.",
        authorized_tools=["execute_sql", "search_transcripts"]
    ),
    "nba_agent": AgentConfig(
        name="nba_agent",
        persona="You are a Next Best Action engine. Query the NextBestAction table and evaluate portfolio gaps to suggest actionable recommendations for the advisor.",
        authorized_tools=["execute_sql"]
    ),
    
    # Workflow 4: Client Sentiment & Comm Intelligence
    "sentiment_agent": AgentConfig(
        name="sentiment_agent",
        persona="You are an empathetic communications analyst. Review TranscriptInsights and EmailInsight tables to detect attrition risks and overarching emotional themes.",
        authorized_tools=["execute_sql", "search_transcripts"]
    ),
    "interaction_summarizer_agent": AgentConfig(
        name="interaction_summarizer_agent",
        persona="You are an executive assistant. Summarize complex email chains and call transcripts into concise bullet points focusing on client concerns and next steps.",
        authorized_tools=["execute_sql", "search_transcripts"]
    )
}