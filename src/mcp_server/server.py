# src/mcp_server/server.py
import os
import sqlite3
import chromadb
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

mcp = FastMCP("AeonWealthMCP")

LOCAL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data_local'))
# 🛑 FIX: Point to the newly ingested Excel database
SQLITE_DB_PATH = os.path.join(LOCAL_DATA_DIR, 'aeon_db.sqlite') 
CHROMA_DB_PATH = os.path.join(LOCAL_DATA_DIR, 'chroma_db')

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
try:
    vector_collection = chroma_client.get_collection(name="advisor_notes")
except Exception as e:
    print(f"Warning: Could not load ChromaDB collection: {e}")
    vector_collection = None

@mcp.tool()
def execute_sql(query: str) -> str:
    """
    Execute a read-only SQL query against the Aeon Wealth relational database.
    Tables available from the latest ingestion: 
    AIGroupInsight, AdvisorClients, AdvisorCoaching, AdvisorDetails, AdvisorPerformance, 
    ClientDetails, CollaborationHub, ComplianceHub, Email, EmailInsight, EmailReply, 
    MarketHighlights, NextBestAction, NextBestActionLandingPag, OpenOpportunities, 
    PortfolioData, PortfolioSimulator, SmartInsights, SocialListening, Transcript, 
    TranscriptInsights, TranscriptSummary, UpcomingClientMeetings, chat_memory.
    """
    try:
        if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE")):
            return "Error: Only SELECT queries are allowed."

        # 🛑 FIX: Print to sys.stderr so it shows up in your terminal!
        print(f"\n      🟦 [MCP SQL Executing]:\n{query}\n", file=sys.stderr)

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No results found."
            
        res = " | ".join(columns) + "\n"
        res += "-" * len(res) + "\n"
        for row in rows:
            res += " | ".join(str(val) if val is not None else "NULL" for val in row) + "\n"
            
        return res
    except Exception as e:
        # Print errors to the terminal too so you can see if the LLM messed up!
        print(f"\n      ❌ [MCP SQL ERROR]: {str(e)}\n")
        return f"SQL Error: {str(e)}"

@mcp.tool()
def get_database_schema(table_names: list[str] = None) -> str:
    """
    Returns the exact CREATE TABLE schemas for the requested tables.
    Use this to understand the exact column names and data types before writing SQL.
    """
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        if table_names and len(table_names) > 0:
            placeholders = ','.join(['?'] * len(table_names))
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name IN ({placeholders})", tuple(table_names))
        else:
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
            
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No schema found for the requested tables."
            
        res = "--- Database Schema ---\n"
        for row in rows:
            # Depending on the query, the sql string is either at index 0 or 1
            sql_str = row[1] if len(row) > 1 else row[0]
            if sql_str:
                res += sql_str + ";\n\n"
                
        return res
    except Exception as e:
        return f"Schema Error: {str(e)}"

@mcp.tool()
def compute_portfolio_concentration(client_id: int) -> str:
    """
    Deterministic Compute: Calculates portfolio concentration metrics for a specific client.
    Returns top position percentage, Herfindahl-Hirschman Index (HHI), sector concentration, 
    and flags any concentrated low-basis positions to avoid LLM math hallucinations.
    """
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Ticker, AssetClass, MarketValue, CostBasis FROM PortfolioData WHERE ClientId = ?", 
            (client_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return f"No portfolio data found for ClientId {client_id}."

        total_market_value = sum(row[2] for row in rows)
        if total_market_value == 0:
            return "Total market value is zero."

        positions = []
        hhi = 0.0
        asset_class_totals = {}
        low_basis_flags = []

        for ticker, asset_class, mkt_val, cost_basis in rows:
            weight = mkt_val / total_market_value
            hhi += (weight * 100) ** 2  # Standard HHI uses whole percentages squared
            
            asset_class_totals[asset_class] = asset_class_totals.get(asset_class, 0) + mkt_val
            
            # Check for low basis (e.g., basis is less than 20% of market value)
            if cost_basis is not None and mkt_val > 0 and (cost_basis / mkt_val) <= 0.2:
                low_basis_flags.append(f"{ticker} (Basis: ${cost_basis:,.2f} / Mkt: ${mkt_val:,.2f})")
            
            positions.append({"ticker": ticker, "weight": weight, "mkt_val": mkt_val})

        positions.sort(key=lambda x: x["weight"], reverse=True)
        top_position = positions[0]

        res = f"--- Deterministic Portfolio Analytics for ClientId {client_id} ---\n"
        res += f"Total Market Value: ${total_market_value:,.2f}\n"
        res += f"Top Position: {top_position['ticker']} at {top_position['weight']*100:.1f}%\n"
        res += f"Herfindahl-Hirschman Index (HHI): {hhi:.1f} (Highly concentrated if > 2500)\n\n"
        
        res += "Asset Class Exposures:\n"
        for ac, val in asset_class_totals.items():
            res += f"- {ac}: {(val/total_market_value)*100:.1f}%\n"

        if low_basis_flags:
            res += "\n⚠️ Concentrated Low-Basis Positions Detected:\n"
            for flag in low_basis_flags:
                res += f"- {flag}\n"
        else:
            res += "\nNo significant low-basis concentration detected.\n"

        return res
    except Exception as e:
        return f"Compute Error: {str(e)}"

@mcp.tool()
def search_transcripts(semantic_query: str, n_results: int = 3) -> str:
    """
    Search advisor notes and call transcripts for specific client concerns, life events, or themes.
    Use this when you need unstructured qualitative data or conversational context.
    """
    if not vector_collection:
        return "Error: Vector database not initialized."

    try:
        results = vector_collection.query(
            query_texts=[semantic_query], 
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant transcripts found."
        
        res = "--- Retrieved Transcripts ---\n"
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            client_name = meta.get("client_name", "Unknown Client")
            res += f"[Client: {client_name}]: {doc}\n"
            
        return res
    except Exception as e:
        return f"Vector DB Error: {str(e)}"

@mcp.tool()
def search_market_news(query: str) -> str:
    """
    Search the web for real-time market news, macroeconomic events, and financial intelligence.
    Use this to answer questions about recent market volatility, specific stock news, or economic indicators.
    """
    from tavily import TavilyClient
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not found in environment variables."
        
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth="basic", max_results=3)
        
        res = "--- Web Search Results ---\n"
        for r in response.get('results', []):
            res += f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}\n\n"
            
        return res
    except Exception as e:
        return f"Tavily Search Error: {str(e)}"

if __name__ == "__main__":
    print("Starting Aeon Wealth MCP Server...")
    mcp.run(transport="stdio")