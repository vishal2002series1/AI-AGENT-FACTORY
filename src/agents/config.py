# src/agents/config.py
from pydantic import BaseModel, Field
from typing import List

class AgentConfig(BaseModel):
    name: str = Field(..., description="The unique name of the agent")
    routing_description: str = Field(..., description="Short 1-liner for the Supervisor to understand when to route here")
    persona: str = Field(..., description="The full system prompt instructing the agent how to behave")
    model_id: str = Field(default="us.anthropic.claude-sonnet-4-6")
    authorized_tools: List[str] = Field(default_factory=list)
    temperature: float = Field(default=0.0)

# The Full Enterprise 10-Agent Registry (Optimized for Context Windows)
AEON_AGENT_REGISTRY = {
    # Workflow 1
    "client_info_agent": AgentConfig(
        name="client_info_agent",
        routing_description="Retrieves demographic facts, AUM, and risk profiles.",
        persona="You are a precise data-retrieval agent. Use execute_sql to fetch client demographics. When discussing clients, inject UI tokens like [CARD:ClientProfile:{client_id}] for the frontend.",
        authorized_tools=["execute_sql"]
    ),
    "compliance_agent": AgentConfig(
        name="compliance_agent",
        routing_description="Checks for missing signatures, stale IPS documents, and regulatory gaps.",
        persona="You are a strict compliance auditor. Query ComplianceHub. Flag issues using tokens like [FLAG:Compliance:{flag_type}].",
        authorized_tools=["execute_sql"]
    ),
    "financial_planning_agent": AgentConfig(
        name="financial_planning_agent",
        routing_description="Reviews RMD status, stale estate plans, and upcoming life events.",
        persona="You are a wealth planner. Query FinancialPlanningFacts to review RMDs and stale plans.",
        authorized_tools=["execute_sql"]
    ),
    
    # Workflow 2
    "portfolio_analytics_agent": AgentConfig(
        name="portfolio_analytics_agent",
        routing_description="Calculates concentration risk, HHI, and identifies low-basis assets.",
        persona="You are a quantitative portfolio analyst. ALWAYS use compute_portfolio_concentration to evaluate concentration risk. Do not attempt math manually.",
        authorized_tools=["execute_sql", "compute_portfolio_concentration"]
    ),
    "performance_benchmark_agent": AgentConfig(
        name="performance_benchmark_agent",
        routing_description="Compares advisor and portfolio performance against firm benchmarks.",
        persona="You are a performance attribution specialist. Review AdvisorPerformance and compare against PolicyBenchmark data.",
        authorized_tools=["execute_sql"]
    ),
    "market_intelligence_agent": AgentConfig(
        name="market_intelligence_agent",
        routing_description="Searches the web for real-time market news and macroeconomic impacts.",
        persona="You are a macroeconomic intelligence agent. Use web search to fetch real-time market news explaining portfolio volatility.",
        authorized_tools=["search_market_news", "execute_sql"]
    ),
    
    # Workflow 3
    "meeting_prep_agent": AgentConfig(
        name="meeting_prep_agent",
        routing_description="Drafts meeting agendas based on upcoming schedules and recent notes.",
        persona="You are a meeting strategy specialist. Query UpcomingClientMeetings and cross-reference with transcripts to draft agendas. Output actionable items using [PLAN_ITEM:{action}].",
        authorized_tools=["execute_sql", "search_transcripts"]
    ),
    "nba_agent": AgentConfig(
        name="nba_agent",
        routing_description="Evaluates Next Best Actions and opportunity scoring for households.",
        persona="You are a Next Best Action engine. Query the NextBestAction table. Surface high-confidence opportunities using [OPPORTUNITY:{category}:{confidence}].",
        authorized_tools=["execute_sql"]
    ),
    
    # Workflow 4
    "sentiment_agent": AgentConfig(
        name="sentiment_agent",
        routing_description="Detects attrition risks and emotional themes in client communications.",
        persona="You are an empathetic communications analyst. Review TranscriptInsights and EmailInsight tables to detect negative sentiment and flight risk.",
        authorized_tools=["execute_sql", "search_transcripts"]
    ),
    "interaction_summarizer_agent": AgentConfig(
        name="interaction_summarizer_agent",
        routing_description="Summarizes complex email chains and call transcripts into concise bullet points.",
        persona="You are an executive assistant. Summarize communications focusing on unresolved concerns.",
        authorized_tools=["execute_sql", "search_transcripts"]
    )
}