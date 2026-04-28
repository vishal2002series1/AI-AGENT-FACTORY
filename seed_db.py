import os
import json
import glob
from src.db.database import engine, SessionLocal, Base
from src.db.models import DomainAgent, Workflow

def seed():
    print("⏳ Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    REGISTRY_PATH = os.path.join(BASE_DIR, 'data_local', 'agent_registry.json')
    WORKFLOWS_DIR = os.path.join(BASE_DIR, 'workflows')
    
    # --- 1. SEED AGENTS ---
    if os.path.exists(REGISTRY_PATH):
        print(f"\n📥 Loading agents from {REGISTRY_PATH}...")
        with open(REGISTRY_PATH, 'r') as f:
            data = json.load(f)
            
        for agent_id, agent_data in data.items():
            existing = db.query(DomainAgent).filter(DomainAgent.id == agent_id).first()
            if not existing:
                new_agent = DomainAgent(
                    id=agent_id,
                    name=agent_data.get("name", agent_id),
                    routing_description=agent_data.get("routing_description", ""),
                    persona=agent_data.get("persona", ""),
                    authorized_tools=agent_data.get("authorized_tools", [])
                )
                db.add(new_agent)
                print(f"   ✅ Added Agent: {agent_id}")
            else:
                print(f"   ⚠️ Agent {agent_id} already exists.")
        
        # Commit agents first so they exist for the workflow mapping
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error committing agents: {e}")

    # --- 2. SEED WORKFLOWS FROM JSON ---
    if os.path.exists(WORKFLOWS_DIR):
        print(f"\n🏗️ Loading Workflows from {WORKFLOWS_DIR}...")
        workflow_files = glob.glob(os.path.join(WORKFLOWS_DIR, "*.json"))
        
        for wf_file in workflow_files:
            try:
                with open(wf_file, 'r') as f:
                    wf_data = json.load(f)
                    
                wf_id = wf_data.get("workflow_id")
                if not wf_id:
                    continue

                # DEFENSIVE CHECK: Does it already exist in the DB session?
                existing_wf = db.query(Workflow).filter(Workflow.id == wf_id).first()
                
                if not existing_wf:
                    new_wf = Workflow(
                        id=wf_id,
                        name=wf_data.get("workflow_name", wf_id),
                        description=wf_data.get("description", "")
                    )
                    db.add(new_wf)
                    print(f"   ✅ Added Workflow: {wf_id}")
                    
                    resolved_agents = wf_data.get("final_resolved_agents", [])
                    for agent_id in resolved_agents:
                        agent = db.query(DomainAgent).filter(DomainAgent.id == agent_id).first()
                        if agent:
                            new_wf.agents.append(agent)
                            print(f"      🔗 Mapped {agent_id} to {wf_id}")
                else:
                    print(f"   ⚠️ Workflow {wf_id} already exists. Skipping duplicate file.")
                    
                # Commit after EACH workflow to prevent one bad file from ruining the batch
                db.commit()
                
            except Exception as e:
                db.rollback()
                print(f"   ❌ Failed to process file {os.path.basename(wf_file)}: {e}")
        
    print("\n🎉 Database Seeding Complete!")
    db.close()

if __name__ == "__main__":
    seed()