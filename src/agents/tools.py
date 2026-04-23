# src/agents/tools.py
import asyncio
import os
import sys
from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Define how to connect to the MCP Server
server_params = StdioServerParameters(
    command=sys.executable,
    args=[os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/mcp_server/server.py'))],
)

def run_mcp_tool_sync(tool_name: str, arguments: dict) -> str:
    """
    Synchronous wrapper to connect to the MCP Server, execute the tool, 
    and return the result via the official MCP protocol.
    """
    async def _execute():
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return "No output from MCP server."
                
    return asyncio.run(_execute())

# --- LangChain Adapters for our MCP Tools ---

@tool
def execute_sql(query: str) -> str:
    """
    Execute a read-only SQL query against the Aeon Wealth relational database.
    Use this to fetch deterministic client facts, portfolio data, meetings, and compliance flags.
    Tables available: AIGroupInsight, AdvisorClients, AdvisorCoaching, AdvisorDetails, 
    AdvisorPerformance, ClientDetails, CollaborationHub, ComplianceHub, Email, EmailInsight, 
    EmailReply, MarketHighlights, NextBestAction, NextBestActionLandingPag, OpenOpportunities, 
    PortfolioData, PortfolioSimulator, SmartInsights, SocialListening, Transcript, 
    TranscriptInsights, TranscriptSummary, UpcomingClientMeetings, chat_memory.
    """
    return run_mcp_tool_sync("execute_sql", {"query": query})

@tool
def compute_portfolio_concentration(client_id: int) -> str:
    """
    Deterministic Compute: Calculates portfolio concentration metrics for a specific client.
    Returns top position percentage, Herfindahl-Hirschman Index (HHI), sector concentration, 
    and flags any concentrated low-basis positions. 
    ALWAYS use this tool instead of calculating concentration via SQL.
    """
    return run_mcp_tool_sync("compute_portfolio_concentration", {"client_id": client_id})

@tool
def search_transcripts(semantic_query: str, n_results: int = 3) -> str:
    """
    Search advisor notes and call transcripts for specific client concerns, life events, or themes.
    Use this when you need unstructured qualitative data or conversational context.
    """
    return run_mcp_tool_sync("search_transcripts", {"semantic_query": semantic_query, "n_results": n_results})

@tool
def search_market_news(query: str) -> str:
    """
    Search the web for real-time market news, macroeconomic events, and financial intelligence.
    Use this to answer questions about recent market volatility, specific stock news, or economic indicators.
    """
    return run_mcp_tool_sync("search_market_news", {"query": query})

@tool
def get_database_schema(table_names: list[str] = None) -> str:
    """
    Returns the exact CREATE TABLE schemas for the requested tables.
    ALWAYS use this tool before writing SQL queries using execute_sql to ensure you use the exact correct column names.
    """
    args = {"table_names": table_names} if table_names else {}
    return run_mcp_tool_sync("get_database_schema", args)

# Make sure to add it to the final roster!
AEON_TOOLS = [
    execute_sql, 
    compute_portfolio_concentration, 
    search_transcripts, 
    search_market_news, 
    get_database_schema   # <--- Added here
]