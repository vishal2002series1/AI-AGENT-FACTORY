# main.py
import uuid
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from src.db.database import engine, SessionLocal, Base
from src.db.models import DomainAgent, Workflow

from langchain_core.messages import HumanMessage
from src.engine.dynamic_graph import build_dynamic_graph

from src.agents.tools import AEON_TOOLS
from src.engine.dynamic_graph import get_llm
from langgraph.prebuilt import create_react_agent

# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aeon Agent Factory API", 
    description="Headless backend for dynamic LangGraph workflows.",
    version="2.0"
)

# --- Dependency: Database Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Schemas (API Contracts for the Frontend) ---
class AgentSchema(BaseModel):
    id: str
    name: str
    routing_description: str
    persona: str
    authorized_tools: list

    class Config:
        from_attributes = True

class WorkflowSchema(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        from_attributes = True

class MapAgentRequest(BaseModel):
    agent_id: str

class ChatRequest(BaseModel):
    workflow_id: str
    prompt: str
    session_id: Optional[str] = None  # Added for memory checkpointing

# --- New Schemas ---
class ToolSchema(BaseModel):
    name: str
    description: str

class PlaygroundRequest(BaseModel):
    persona: str
    prompt: str
    tools: List[str] = []

# --- API Endpoints ---

# --- 🛠️ Endpoint 1: List Tools ---
@app.get("/api/tools", response_model=List[ToolSchema], tags=["Tools"])
def list_available_tools():
    """Get all available tools that can be assigned to agents."""
    return [{"name": t.name, "description": t.description} for t in AEON_TOOLS]

# --- 🧪 Endpoint 2: Agent Playground ---
@app.post("/api/playground", tags=["Agent Playground"])
def test_agent_prompt(request: PlaygroundRequest):
    """
    Test an agent prompt/persona directly without saving it to the database.
    Perfect for prompt engineering and testing tool combinations.
    """
    try:
        # 1. Map requested tool names to actual tool objects
        selected_tools = [t for t in AEON_TOOLS if t.name in request.tools]
        
        # 2. Spin up a temporary, stateless React Agent
        temp_agent = create_react_agent(get_llm(), tools=selected_tools, prompt=request.persona)
        
        # 3. Execute the prompt
        inputs = {"messages": [HumanMessage(content=request.prompt)]}
        result = temp_agent.invoke(inputs)
        
        return {
            "status": "success",
            "persona_tested": request.persona,
            "tools_used": [t.name for t in selected_tools],
            "final_answer": result["messages"][-1].content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/", tags=["Health"])
def root():
    return {"status": "online", "message": "Aeon Agent Factory is running. Visit /docs for Swagger UI."}

@app.get("/api/workflows", response_model=List[WorkflowSchema], tags=["Workflows"])
def list_workflows(db: Session = Depends(get_db)):
    """Get all available workflows."""
    return db.query(Workflow).all()

@app.get("/api/workflows/{workflow_id}/agents", response_model=List[AgentSchema], tags=["Workflows"])
def get_agents_for_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """See which agents are currently mapped to a specific workflow."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.agents

@app.get("/api/agents", response_model=List[AgentSchema], tags=["Agents"])
def list_all_agents(db: Session = Depends(get_db)):
    """List all agents in the factory."""
    return db.query(DomainAgent).all()

@app.post("/api/agents", response_model=AgentSchema, tags=["Agents"])
def create_agent(agent: AgentSchema, db: Session = Depends(get_db)):
    """Manually create a new agent (Phase 1)."""
    db_agent = DomainAgent(**agent.model_dump())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@app.post("/api/workflows/{workflow_id}/map", tags=["Workflows"])
def map_agent_to_workflow(workflow_id: str, request: MapAgentRequest, db: Session = Depends(get_db)):
    """Attach an existing agent to a workflow."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    agent = db.query(DomainAgent).filter(DomainAgent.id == request.agent_id).first()
    
    if not workflow or not agent:
        raise HTTPException(status_code=404, detail="Workflow or Agent not found")
        
    if agent not in workflow.agents:
        workflow.agents.append(agent)
        db.commit()
        
    return {"message": f"Agent {agent.name} successfully mapped to {workflow.name}"}

@app.post("/api/chat", tags=["Execution"])
def execute_chat_workflow(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # Generate a new session ID if the frontend didn't provide one
        session_id = request.session_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": session_id}}
        
        # Pass the injected db session directly into the engine
        graph = build_dynamic_graph(request.workflow_id, db) 
        
        inputs = {"messages": [HumanMessage(content=request.prompt)]}
        trace = []
        final_answer = ""
        
        # Stream the graph execution exactly like your CLI script
        for event in graph.stream(inputs, config=config, stream_mode="updates"):
            if not event:
                continue
                
            for node_name, state_update in event.items():
                trace.append(node_name)
                
                if state_update is not None:
                    messages = state_update.get("messages")
                    if messages and isinstance(messages, list) and len(messages) > 0:
                        if hasattr(messages[-1], 'content') and messages[-1].content:
                            final_answer = messages[-1].content

        return {
            "workflow_id": request.workflow_id,
            "session_id": session_id,
            "execution_trace": trace,
            "final_answer": final_answer
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # This catches the Bedrock error and surfaces it to Swagger
        raise HTTPException(status_code=500, detail=str(e))