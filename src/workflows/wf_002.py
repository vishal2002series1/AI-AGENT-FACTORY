# AUTO-COMPILED WORKFLOW: WF_002
import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from src.agents.config import registry_manager
from src.agents.factory import AgentFactory

class WF_002State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

def build_WF_002_graph():
    factory = AgentFactory()
    workflow = StateGraph(WF_002State)
    
    synthesis_agent_cfg = registry_manager.agents.get('synthesis_agent')
    workflow.add_node('synthesis_agent', factory.build_node(synthesis_agent_cfg))
    schema_discovery_agent_cfg = registry_manager.agents.get('schema_discovery_agent')
    workflow.add_node('schema_discovery_agent', factory.build_node(schema_discovery_agent_cfg))
    concentration_risk_agent_cfg = registry_manager.agents.get('concentration_risk_agent')
    workflow.add_node('concentration_risk_agent', factory.build_node(concentration_risk_agent_cfg))
    threshold_query_agent_cfg = registry_manager.agents.get('threshold_query_agent')
    workflow.add_node('threshold_query_agent', factory.build_node(threshold_query_agent_cfg))

    # Declarative Routing
    workflow.add_edge(START, 'schema_discovery_agent')
    workflow.add_edge('concentration_risk_agent', 'synthesis_agent')
    workflow.add_edge('threshold_query_agent', 'concentration_risk_agent')
    workflow.add_edge('synthesis_agent', END)
    workflow.add_edge('schema_discovery_agent', 'threshold_query_agent')

    return workflow.compile()
