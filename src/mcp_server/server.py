# src/mcp_server/server.py
import os
import sqlite3
import chromadb
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("AeonWealthMCP")

# Path resolution for local data
LOCAL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data_local'))
SQLITE_DB_PATH = os.path.join(LOCAL_DATA_DIR, 'aeon_mvp.db')
CHROMA_DB_PATH = os.path.join(LOCAL_DATA_DIR, 'chroma_db')

# Initialize Vector DB connection
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
    Use this to fetch deterministic client facts, portfolio data, meetings, and compliance flags.
    Tables available: ClientDetails, AdvisorDetails, AdvisorPerformance, AdvisorClient, 
    PortfolioData, FinancialPlanningFacts, ComplianceHub, UpcomingClientMeetings, TranscriptSummary.
    """
    try:
        # Security: Enforce read-only for the MVP
        if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE")):
            return "Error: Only SELECT queries are allowed."

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Extract column names
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No results found."
        
        # Format the output as a Markdown-style table so the LLM can easily read it
        res = " | ".join(columns) + "\n"
        res += "-" * len(res) + "\n"
        for row in rows:
            res += " | ".join(str(val) if val is not None else "NULL" for val in row) + "\n"
            
        return res
    except Exception as e:
        return f"SQL Error: {str(e)}"

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
        # Zip the documents and metadata together so the LLM knows which client said what
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            client_name = meta.get("client_name", "Unknown Client")
            res += f"[Client: {client_name}]: {doc}\n"
            
        return res
    except Exception as e:
        return f"Vector DB Error: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server using the standard input/output transport
    print("Starting Aeon Wealth MCP Server...")
    mcp.run(transport="stdio")