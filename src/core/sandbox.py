# src/core/sandbox.py
import uuid
import importlib
from langchain_core.messages import HumanMessage

import src.agents.graph
from src.agents.graph import build_aeon_graph
from src.core.evaluator import GroundingCritic
from src.agents.fabricator import AgentFabricator
from src.agents.config import AgentConfig, registry_manager

class SandboxOrchestrator:
    def __init__(self):
        self.critic = GroundingCritic()
        self.fabricator = AgentFabricator()

    def extract_tool_logs(self, messages):
        tool_logs = []
        for m in messages:
            if getattr(m, "type", None) == "tool":
                tool_logs.append(f"[Tool: {m.name}]: {m.content}")
        return "\n".join(tool_logs) if tool_logs else "No tools were called."

    # 🛑 THE NEW VISIBILITY ENGINE 🛑
    def execute_with_live_logs(self, app, input_messages, config):
        """Streams LangGraph events to the terminal so we aren't staring at a blank screen."""
        print("\n   [Live Execution Trace Started] ---------------------------")
        
        # Stream updates as they happen
        for event in app.stream(input_messages, config=config, stream_mode="updates"):
            for node_name, node_data in event.items():
                print(f"   🟢 [ACTIVE AGENT]: '{node_name}' is thinking...")
                
                # Did the supervisor make a routing decision?
                if "routing_log" in node_data and node_data["routing_log"]:
                    print(f"      🔀 Router decided: {node_data['routing_log'][-1]}")
                
                # Did an agent call a tool or get tool results?
                if "messages" in node_data and node_data["messages"]:
                    last_msg = node_data["messages"][-1]
                    
                    # Check if it's asking to run a tool
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            print(f"      🛠️  Executing Tool: `{tc['name']}`...")
                    
                    # Check if it just got data BACK from a tool
                    elif getattr(last_msg, 'type', '') == 'tool':
                        print(f"      ✅ Tool returned {len(str(last_msg.content))} characters of data.")
        
        print("   [Live Execution Trace Complete] --------------------------\n")
        
        # Return the final state from the checkpointer
        return app.get_state(config).values

    def run_workflow_builder(self, test_query: str, max_iterations: int = 3):
        print("="*60)
        print(f"🏗️  AGENT BUILDER SANDBOX INITIATED")
        print(f"🎯 Goal: {test_query}")
        print("="*60)

        print("\n▶️ PHASE 1: Testing Existing Agent Registry...")
        app = build_aeon_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        # Use our new Live Logs runner!
        state = self.execute_with_live_logs(app, {"messages": [HumanMessage(content=test_query)]}, config)
        
        final_answer = state["messages"][-1].content
        tool_logs = self.extract_tool_logs(state["messages"])
        
        print(f"\n[Existing Agents Answer]:\n{final_answer[:500]}... (truncated for brevity)\n")
        
        eval_result = self.critic.evaluate(test_query, tool_logs, final_answer)
        
        missing_phrases = ["unable to", "cannot find", "do not have", "no data was returned", "no relevant", "ambiguous_entity", "ask_human"]
        is_missing_capability = any(phrase in final_answer.lower() for phrase in missing_phrases)

        if eval_result.status == "PASS" and not is_missing_capability:
            print("✅ SUCCESS: Existing agents handled the workflow perfectly. No new agents needed.")
            return

        print("❌ GAP DETECTED: Existing agents failed or lacked capabilities.")
        if eval_result.status == "FAIL":
            print(f"Reason (Hallucination): {eval_result.reason}")
        else:
            print("Reason (Missing Capability): The agent correctly admitted it lacked the data/tools to answer fully.")

        print("\n▶️ PHASE 2: Fabricating New Agent(s) to Fill Gap...")
        feedback = eval_result.reason if eval_result.status == "FAIL" else "The previous agents lacked the tools or focus to find the data. Build specialized atomic agents with the correct tools."
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n🔄 Fabrication Loop {iteration}/{max_iterations}")
            
            fabricator_output = self.fabricator.fabricate(test_query, critic_feedback=feedback)
            
            print(f"   Drafted {len(fabricator_output.new_agents)} granular agent(s):")
            temp_configs = []
            
            for bp in fabricator_output.new_agents:
                print(f"     - {bp.name} (Tools: {bp.authorized_tools})")
                temp_config = AgentConfig(
                    name=bp.name,
                    routing_description=bp.routing_description,
                    persona=bp.persona,
                    authorized_tools=bp.authorized_tools
                )
                temp_configs.append(temp_config)
                registry_manager.agents[temp_config.name] = temp_config

            importlib.reload(src.agents.graph)
            temp_app = src.agents.graph.build_aeon_graph()
            
            print("   Testing drafted agents via Sandbox Supervisor (Positive Test)...")
            sandbox_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            
            # Use our new Live Logs runner!
            sandbox_state = self.execute_with_live_logs(temp_app, {"messages": [HumanMessage(content=test_query)]}, sandbox_config)
            
            sandbox_answer = sandbox_state["messages"][-1].content
            sandbox_tool_logs = self.extract_tool_logs(sandbox_state["messages"])

            print("   Testing drafted agents via Sandbox Supervisor (Negative Validation Run)...")
            neg_query = f"NEGATIVE TEST: Execute the following query but explicitly target a non-existent entity named 'FAKE_ENTITY_999': {test_query}"
            neg_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            
            # Use our new Live Logs runner!
            neg_state = self.execute_with_live_logs(temp_app, {"messages": [HumanMessage(content=neg_query)]}, neg_config)
            neg_answer = neg_state["messages"][-1].content
            
            new_eval = self.critic.evaluate(test_query, sandbox_tool_logs, sandbox_answer)
            
            if not any(kw in neg_answer.lower() for kw in ["ask_human", "ambiguous", "not found", "cannot", "unable", "fake_entity_999"]):
                new_eval.status = "FAIL"
                new_eval.reason = f"Failed Negative Test. Agent hallucinated a fuzzy match for a non-existent entity instead of halting."
            
            if new_eval.status == "PASS":
                print(f"\n✅ CRITIC APPROVED! Version {iteration} passed strict grounding and negative fallback validation.")
                for tc in temp_configs:
                    registry_manager.save_agent(tc) 
                print(f"🎉 {len(temp_configs)} new granular agent(s) are now permanently available to the Supervisor!")
                return
            else:
                print(f"   ⚠️ Critic Failed Draft {iteration}: {new_eval.reason}")
                feedback = new_eval.reason 
                
                for tc in temp_configs:
                    if tc.name in registry_manager.agents:
                        del registry_manager.agents[tc.name]

        print("\n🚨 MAX ITERATIONS REACHED. The Fabricator could not build a passing agent.")