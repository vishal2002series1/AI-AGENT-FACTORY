Steps to run the repo locally :

In root directory create local env

1. pip install -r requirements.txt

Run Autofabricator to setup some predefined subagents

2. python src/scripts/batch_autofabricator.py

Setup local db to store agents and workflows

3. python seed_db.py

Ingest excel based data into sqllite and chromadb vectordb
4. python src/scripts/ingest_db.py
5. python src/vector_ingestion.py

Run the FastAPI swagger

6. uvicorn main:app --reload