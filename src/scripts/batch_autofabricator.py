# src/scripts/batch_autofabricator.py
import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.fabricator import DomainFabricator
from src.agents.config import AgentConfig, registry_manager


# Suppress OpenTelemetry Spam
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""

def run_domain_fabrication():
    print("🚀 Starting Domain-Driven Agent Fabrication...\n")
    
    # Load the Workflow JSON
    base_dir = os.path.dirname(__file__)
    wf_path = os.path.abspath(os.path.join(base_dir, '../../workflows/workflow_1_client_prep.json'))
    
    with open(wf_path, 'r') as f:
        wf_data = json.load(f)
        
    wf_name = wf_data.get("workflow_name", "Unknown")
    description = wf_data.get("description", "")
    data_sources = wf_data.get("required_data_sources", [])
    
    print(f"📦 Analyzing Domain: {wf_name}")
    print(f"📖 Description: {description}")
    
    # Spin up the Fabricator
    fabricator = DomainFabricator()
    output = fabricator.fabricate(wf_name, description, data_sources)
    
    # Wipe the old registry clean
    registry_manager.agents = {}
    
    print(f"\n🎉 Successfully Fabricated {len(output.domain_agents)} Domain Agents:")
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
        
    # registry_manager.save_registry()
    print("\n✅ Domain Agents committed to permanent registry!")

if __name__ == "__main__":
    # We no longer use a static DAG file, so delete it if it exists
    dag_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workflows/WF_001_dag.json'))
    if os.path.exists(dag_path):
        os.remove(dag_path)
        print("🗑️  Deleted legacy static DAG file.")
        
    run_domain_fabrication()