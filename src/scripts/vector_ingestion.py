# src/scripts/vector_ingestion.py
import os
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Embeddings (Simulating the future Embedding Microservice)
embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v1", # Standard Bedrock embedding model
    region_name="us-east-1"
)

# 2. Define Local Storage (Simulating Azure AI Search / pgvector)
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../local_vector_db'))
os.makedirs(DB_DIR, exist_ok=True)

def ingest_data():
    print("🚀 Starting Semantic Data Ingestion...")
    
    # Paths to your exported data
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data')) # Adjust path as needed
    transcript_path = os.path.join(data_dir, "postgres_export_20260420_101547.xlsx - public_Transcript.csv")
    email_path = os.path.join(data_dir, "postgres_export_20260420_101547.xlsx - public_Email.csv")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    # --- Ingest Transcripts ---
    if os.path.exists(transcript_path):
        print("   📚 Processing Transcripts...")
        df_transcripts = pd.read_csv(transcript_path)
        # Combine contextual columns for the embedder
        df_transcripts['semantic_text'] = "Call Type: " + df_transcripts['CallType'] + " | Transcript: " + df_transcripts['Transcript']
        
        loader = DataFrameLoader(df_transcripts, page_content_column="semantic_text")
        docs = loader.load()
        split_docs = text_splitter.split_documents(docs)
        
        # Ensure ClientId is stored as metadata for strict filtering later
        for doc in split_docs:
            doc.metadata = {"client_id": int(doc.metadata.get("ClientId", 0)), "source": "transcript"}
            
        Chroma.from_documents(split_docs, embeddings, persist_directory=os.path.join(DB_DIR, 'transcripts'))
        print(f"   ✅ Saved {len(split_docs)} transcript chunks to Vector DB.")
    else:
        print(f"   ⚠️ Could not find transcript CSV at {transcript_path}")

    # --- Ingest Emails ---
    if os.path.exists(email_path):
        print("   📧 Processing Emails...")
        df_emails = pd.read_csv(email_path)
        df_emails['semantic_text'] = "Subject: " + df_emails['Subject'] + " | Body: " + df_emails['Body']
        
        loader = DataFrameLoader(df_emails, page_content_column="semantic_text")
        docs = loader.load()
        split_docs = text_splitter.split_documents(docs)
        
        for doc in split_docs:
            doc.metadata = {"client_id": int(doc.metadata.get("ClientId", 0)), "source": "email"}
            
        Chroma.from_documents(split_docs, embeddings, persist_directory=os.path.join(DB_DIR, 'emails'))
        print(f"   ✅ Saved {len(split_docs)} email chunks to Vector DB.")
    else:
        print(f"   ⚠️ Could not find email CSV at {email_path}")

if __name__ == "__main__":
    ingest_data()
    print("🎉 Ingestion Complete. Vector DB is ready for queries.")