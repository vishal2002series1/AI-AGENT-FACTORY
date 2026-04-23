# AUTO-COMPILED WORKFLOW: Client Review and Prep
# This is a statically governed Sub-Graph. Do not edit routing logic manually unless authorized.

import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.agents.config import registry_manager
from src.agents.factory import AgentFactory

# 1. Define Sub-Graph State
class WF_001State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Annotated[list[str], operator.add]

# 2. Build the Static Graph
def build_WF_001_graph():
    factory = AgentFactory()
    workflow = StateGraph(WF_001State)
    
    # 3. Load Authorized Agents
    life_event_detector_agent_config = registry_manager.agents.get('life_event_detector_agent')
    workflow.add_node('life_event_detector_agent', factory.build_node(life_event_detector_agent_config))
    financial_plan_review_checker_agent_config = registry_manager.agents.get('financial_plan_review_checker_agent')
    workflow.add_node('financial_plan_review_checker_agent', factory.build_node(financial_plan_review_checker_agent_config))
    at_risk_client_gap_reporter_agent_config = registry_manager.agents.get('at_risk_client_gap_reporter_agent')
    workflow.add_node('at_risk_client_gap_reporter_agent', factory.build_node(at_risk_client_gap_reporter_agent_config))

    # 4. Hardcode the Routing Edges (Parallel Execution -> Synthesis -> End)
    workflow.add_edge(START, 'life_event_detector_agent')
    workflow.add_edge(START, 'financial_plan_review_checker_agent')
    workflow.add_edge('life_event_detector_agent', 'at_risk_client_gap_reporter_agent')
    workflow.add_edge('financial_plan_review_checker_agent', 'at_risk_client_gap_reporter_agent')
    workflow.add_edge('at_risk_client_gap_reporter_agent', END)

    return workflow.compile()

# To use this as a Sub-Graph or test it independently:
if __name__ == "__main__":
    app = build_WF_001_graph()
    print("✅ WF_001 Compiled Graph Loaded Successfully.")
