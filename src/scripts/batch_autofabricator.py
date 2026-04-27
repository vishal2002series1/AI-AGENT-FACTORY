# src/scripts/batch_autofabricator.py
import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.fabricator import DomainFabricator
from src.agents.config import AgentConfig, registry_manager

os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""

def run_domain_fabrication(target_file="workflow_2_portfolio_performance.json"):
    print("🚀 Starting Bounded Domain Fabrication...\n")
    
    base_dir = os.path.dirname(__file__)
    wf_path = os.path.abspath(os.path.join(base_dir, f'../../workflows/{target_file}'))
    
    with open(wf_path, 'r') as f:
        wf_data = json.load(f)
        
    wf_name = wf_data.get("workflow_name", "Unknown")
    description = wf_data.get("description", "")
    data_sources = wf_data.get("required_data_sources", [])
    user_mandatory_agents = wf_data.get("user_mandatory_agents", [])
    
    print(f"📦 Analyzing Domain: {wf_name}")
    print(f"📌 Mandatory Agents: {user_mandatory_agents}")
    
    # Prepare existing agents summary
    existing_info = []
    for name, config in registry_manager.agents.items():
        existing_info.append(f"- {name}: {config.routing_description}")
    existing_agents_str = "\n".join(existing_info) if existing_info else "None"
    
    print(f"🔍 Found {len(registry_manager.agents)} existing agents in global registry.")
    
    # Spin up the Fabricator
    fabricator = DomainFabricator()
    output = fabricator.fabricate(wf_name, description, data_sources, user_mandatory_agents, existing_agents_str)
    
    # 1. Process New Agents (Save to Global Registry)
    if output.domain_agents:
        print(f"\n🎉 Fabricated {len(output.domain_agents)} NEW Domain Agents:")
        for blueprint in output.domain_agents:
            print(f"   🟢 {blueprint.name}")
            config = AgentConfig(
                name=blueprint.name,
                routing_description=blueprint.routing_description,
                persona=blueprint.persona,
                authorized_tools=blueprint.authorized_tools,
                model_id=os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
            )
            registry_manager.save_agent(config)
    else:
        print("\n✅ No new agents required. Existing registry is sufficient.")

    # 2. Process Final Roster (Save to Workflow JSON)
    final_roster = output.final_resolved_agents
    print(f"\n📋 Final Resolved Agent Roster for {wf_name}:")
    for agent in final_roster:
        print(f"   🔹 {agent}")
        
    wf_data["final_resolved_agents"] = final_roster
    
    with open(wf_path, 'w') as f:
        json.dump(wf_data, f, indent=2)
        
    print(f"\n💾 Successfully bound {len(final_roster)} agents to {wf_path}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "workflow_2_portfolio_performance.json"
    run_domain_fabrication(target_file)