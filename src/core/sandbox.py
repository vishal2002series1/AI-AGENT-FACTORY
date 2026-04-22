# src/core/sandbox.py
import uuid
import importlib
from langchain_core.messages import HumanMessage

# Import our core components
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
        """Extracts raw data returned by tools so the Critic can verify attribution."""
        tool_logs = []
        for m in messages:
            if getattr(m, "type", None) == "tool":
                tool_logs.append(f"[Tool: {m.name}]: {m.content}")
        return "\n".join(tool_logs) if tool_logs else "No tools were called."

    def run_workflow_builder(self, test_query: str, max_iterations: int = 3):
        print("="*60)
        print(f"🏗️  AGENT BUILDER SANDBOX INITIATED")
        print(f"🎯 Goal: {test_query}")
        print("="*60)

        # --- PHASE 1: Try Existing Registry (The "Dry Run") ---
        print("\n▶️ PHASE 1: Testing Existing Agent Registry...")
        app = build_aeon_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        state = app.invoke({"messages": [HumanMessage(content=test_query)]}, config=config)
        final_answer = state["messages"][-1].content
        tool_logs = self.extract_tool_logs(state["messages"])
        
        print(f"\n[Existing Agents Answer]:\n{final_answer}\n")
        
        eval_result = self.critic.evaluate(test_query, tool_logs, final_answer)
        
        missing_phrases = ["unable to", "cannot find", "do not have", "no data was returned", "no relevant"]
        is_missing_capability = any(phrase in final_answer.lower() for phrase in missing_phrases)

        if eval_result.status == "PASS" and not is_missing_capability:
            print("✅ SUCCESS: Existing agents handled the workflow perfectly. No new agents needed.")
            return

        print("❌ GAP DETECTED: Existing agents failed or lacked capabilities.")
        if eval_result.status == "FAIL":
            print(f"Reason (Hallucination): {eval_result.reason}")
        else:
            print("Reason (Missing Capability): The agent correctly admitted it lacked the data/tools to answer fully.")

        # --- PHASE 2: The Fabricator Loop (TDD) ---
        print("\n▶️ PHASE 2: Fabricating New Agent(s) to Fill Gap...")
        feedback = eval_result.reason if eval_result.status == "FAIL" else "The previous agents lacked the tools or focus to find the data. Build specialized atomic agents with the correct tools."
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n🔄 Fabrication Loop {iteration}/{max_iterations}")
            
            # The Fabricator drafts the blueprints (returns FabricatorOutput)
            fabricator_output = self.fabricator.fabricate(test_query, critic_feedback=feedback)
            
            print(f"   Drafted {len(fabricator_output.new_agents)} granular agent(s):")
            temp_configs = []
            
            # 1. Temporarily add to memory registry
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

            # 2. Reload graph module so the Supervisor's Intent Router recognizes the new agents
            importlib.reload(src.agents.graph)
            temp_app = src.agents.graph.build_aeon_graph()
            
            # 3. Sandbox Test: Let the Supervisor coordinate the new team
            print("   Testing drafted agents via Sandbox Supervisor...")
            sandbox_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            sandbox_state = temp_app.invoke({"messages": [HumanMessage(content=test_query)]}, config=sandbox_config)
            
            sandbox_answer = sandbox_state["messages"][-1].content
            sandbox_tool_logs = self.extract_tool_logs(sandbox_state["messages"])
            
            # 4. Critic Evaluation
            new_eval = self.critic.evaluate(test_query, sandbox_tool_logs, sandbox_answer)
            
            if new_eval.status == "PASS":
                # --- PHASE 3: Commit to Registry ---
                print(f"\n✅ CRITIC APPROVED! Version {iteration} passed strict grounding.")
                for tc in temp_configs:
                    registry_manager.save_agent(tc) # Permanently saves to JSON
                print(f"🎉 {len(temp_configs)} new granular agent(s) are now permanently available to the Supervisor!")
                return
            else:
                print(f"   ⚠️ Critic Failed Draft {iteration}: {new_eval.reason}")
                feedback = new_eval.reason 
                
                # Rollback temporary agents so they don't pollute the next iteration
                for tc in temp_configs:
                    if tc.name in registry_manager.agents:
                        del registry_manager.agents[tc.name]

        print("\n🚨 MAX ITERATIONS REACHED. The Fabricator could not build a passing agent.")
        print("This likely means a required MCP tool does not exist. Please ask a developer to add it to tools.py.")