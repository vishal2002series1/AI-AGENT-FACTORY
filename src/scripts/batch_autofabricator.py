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

def run_domain_fabrication():
    print("🚀 Starting Incremental Domain Fabrication...\n")
    
    base_dir = os.path.dirname(__file__)
    # 🛑 MAKE SURE THIS POINTS TO WORKFLOW 2
    wf_path = os.path.abspath(os.path.join(base_dir, '../../workflows/workflow_2_portfolio_performance.json'))
    
    with open(wf_path, 'r') as f:
        wf_data = json.load(f)
        
    wf_name = wf_data.get("workflow_name", "Unknown")
    description = wf_data.get("description", "")
    data_sources = wf_data.get("required_data_sources", [])
    
    print(f"📦 Analyzing Domain: {wf_name}")
    print(f"📖 Description: {description}")
    
    # Prepare existing agents summary
    existing_info = []
    for name, config in registry_manager.agents.items():
        existing_info.append(f"- {name}: {config.routing_description}")
    existing_agents_str = "\n".join(existing_info) if existing_info else "None"
    
    print(f"🔍 Found {len(registry_manager.agents)} existing agents. Fabricator will only build missing gaps.")
    
    # Spin up the Fabricator
    fabricator = DomainFabricator()
    output = fabricator.fabricate(wf_name, description, data_sources, existing_agents_str)
    
    if not output.domain_agents:
        print("\n✅ Fabricator determined existing agents can handle this entire workflow. No new agents built!")
        return

    print(f"\n🎉 Successfully Fabricated {len(output.domain_agents)} NEW Domain Agents:")
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

if __name__ == "__main__":
    run_domain_fabrication()