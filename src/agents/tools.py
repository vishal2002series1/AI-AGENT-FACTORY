# src/agents/tools.py
import asyncio
import os
import sys
from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_aws import BedrockEmbeddings
from langchain_chroma import Chroma

embedder = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", region_name="us-east-1")
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../local_vector_db'))

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
def search_transcripts(client_id: int, query: str) -> str:
    """
    Semantic search over a specific client's past meeting transcripts and call notes.
    Use this to find qualitative information: life events, sentiment, family dynamics, or unprompted goals.
    
    Args:
        client_id (int): The ID of the client to search.
        query (str): The semantic question (e.g., 'Did the client mention estate planning or grandkids?')
    """
    try:
        vector_store = Chroma(persist_directory=os.path.join(DB_DIR, 'transcripts'), embedding_function=embedder)
        # STRICT FILTERING: Prevent retrieving data from the wrong client
        results = vector_store.similarity_search(query, k=3, filter={"client_id": client_id})
        
        if not results:
            return f"No relevant transcript snippets found for Client {client_id} regarding '{query}'."
            
        formatted_results = [f"- {res.page_content}" for res in results]
        return "\n".join(formatted_results)
    except Exception as e:
        return f"System Error retrieving transcripts: {str(e)}"

@tool
def search_client_emails(client_id: int, query: str) -> str:
    """
    Semantic search over a specific client's email history.
    Use this to find asynchronous requests, sent documents, or recent questions from the client.
    
    Args:
        client_id (int): The ID of the client to search.
        query (str): The semantic question (e.g., 'Did the client email about the new trust documents?')
    """
    try:
        vector_store = Chroma(persist_directory=os.path.join(DB_DIR, 'emails'), embedding_function=embedder)
        results = vector_store.similarity_search(query, k=3, filter={"client_id": client_id})
        
        if not results:
            return f"No relevant emails found for Client {client_id} regarding '{query}'."
            
        formatted_results = [f"- {res.page_content}" for res in results]
        return "\n".join(formatted_results)
    except Exception as e:
        return f"System Error retrieving emails: {str(e)}"

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

# Make sure to add ALL tools to the final roster!
AEON_TOOLS = [
    execute_sql, 
    compute_portfolio_concentration, 
    search_transcripts, 
    get_database_schema,
    search_client_emails
    # search_market_news
]