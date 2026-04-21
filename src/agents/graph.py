# src/agents/graph.py
import operator
import sqlite3
import os
from typing import Annotated, Sequence, TypedDict, Literal
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.types import interrupt
from langgraph.checkpoint.sqlite import SqliteSaver

from src.agents.config import AEON_AGENT_REGISTRY, AgentConfig
from src.agents.factory import AgentFactory

# --- 1. The Universal State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: str
    routing_log: Annotated[list[str], operator.add]

# --- 2. The Supervisor's Brain (Structured Output) ---
# Notice we injected ASK_HUMAN into the router's vocabulary
agent_names = list(AEON_AGENT_REGISTRY.keys())
route_options = agent_names + ["ASK_HUMAN", "FINISH"]

class RouteDecision(BaseModel):
    next_node: Literal[tuple(route_options)] = Field(
        ...,
        description="The next agent to route to. Use 'ASK_HUMAN' if the user's request is ambiguous. Use 'FINISH' if fully answered."
    )
    reasoning: str = Field(..., description="Explanation of why this route was chosen. If asking a human, write the clarification question here.")

# --- 3. Build the Graph ---
def build_aeon_graph(arize_keys: dict = None):
    factory = AgentFactory()
    
    supervisor_llm = ChatBedrock(
        model_id="us.anthropic.claude-sonnet-4-6",
        region_name="us-east-1",
        temperature=0.0
    ).with_structured_output(RouteDecision)

    def supervisor_node(state: AgentState):
        # 🛡️ THE CIRCUIT BREAKER
        if len(state.get("routing_log", [])) > 6:
            return {
                "messages": [AIMessage(content="Circuit Breaker Activated: I have reached my maximum reasoning steps. Please try narrowing your query.")],
                "current_agent": "supervisor",
                "routing_log": ["Routed to FINISH because: Circuit breaker triggered"]
            }
            
        system_prompt = f"""You are the AEON Wealth Orchestrator. Route tasks to specialized agents.
        
        Available Agents:
        - client_info_agent: SQL data, AUM, age, missing documents.
        - sentiment_agent: Transcripts, client concerns.
        - compliance_agent: Strict compliance checks.
        
        CRITICAL RULES:
        1. If the user query is ambiguous (e.g. asking for 'Emily' when there might be multiple), route to 'ASK_HUMAN'.
        2. If all data is gathered, compile a final summary and route to 'FINISH'."""
        
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
        
        # 🛑 BEDROCK FIX: The conversation history cannot end with an AI message.
        # If the last message was from a worker agent, we append a 'Human' nudge to prompt the Supervisor.
        if messages and getattr(messages[-1], "type", None) == "ai":
            nudge = "Review the agent's output above. If the advisor's request is fully resolved, route to FINISH. If more data is needed, route to the appropriate agent."
            messages.append(HumanMessage(content=nudge))
        
        decision = supervisor_llm.invoke(messages)
        
        return {
            "current_agent": "supervisor",
            "routing_log": [f"Routed to {decision.next_node} because: {decision.reasoning}"]
        }

    # 🛑 THE HUMAN-IN-THE-LOOP NODE
    def human_clarification_node(state: AgentState):
        # Extract the exact question the LLM wants to ask the advisor
        question_to_ask = state["routing_log"][-1]
        
        # Calling interrupt() safely suspends the graph and saves state to SQLite
        human_response = interrupt(f"Clarification needed: {question_to_ask}")
        
        # When resumed, we inject the human's answer into the LLM's context
        return {
            "messages": [HumanMessage(content=f"[Advisor Clarification]: {human_response}")],
            "current_agent": "human"
        }

    # Initialize Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("ASK_HUMAN", human_clarification_node)
    
    # Load Factory Agents
    for agent_name, config in AEON_AGENT_REGISTRY.items():
        worker_node = factory.build_node(config)
        workflow.add_node(agent_name, worker_node)
        workflow.add_edge(agent_name, "supervisor")
        
    workflow.add_edge("ASK_HUMAN", "supervisor")

    def route_from_supervisor(state: AgentState) -> str:
        last_log = state.get("routing_log", [""])[-1]
        for name in route_options:
            if f"Routed to {name}" in last_log:
                return name
        return "FINISH"

    # Create the edge mapping
    edge_mapping = {name: name for name in route_options if name != "FINISH"}
    edge_mapping["FINISH"] = END # Map the string "FINISH" to LangGraph's actual END node

    workflow.add_conditional_edges("supervisor", route_from_supervisor, edge_mapping)
    workflow.add_edge(START, "supervisor")
    
    # 🧠 PERSISTENT MEMORY INTEGRATION
    # Ensure our local data directory exists for the checkpointer
    local_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data_local'))
    os.makedirs(local_data_dir, exist_ok=True)
    
    conn = sqlite3.connect(os.path.join(local_data_dir, "checkpoints.sqlite"), check_same_thread=False)
    memory = SqliteSaver(conn)
    
    return workflow.compile(checkpointer=memory)

aeon_app = build_aeon_graph()