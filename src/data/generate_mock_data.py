# src/data/generate_mock_data.py
import os
import datetime
import chromadb
from chromadb.utils import embedding_functions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.core.models import (
    Base, AdvisorDetails, AdvisorPerformance, ClientDetails, AdvisorClient,
    PortfolioData, FinancialPlanningFacts, ComplianceHub, UpcomingClientMeetings, TranscriptSummary
)

LOCAL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data_local'))
SQLITE_DB_PATH = os.path.join(LOCAL_DATA_DIR, 'aeon_mvp.db')
CHROMA_DB_PATH = os.path.join(LOCAL_DATA_DIR, 'chroma_db')

def init_databases():
    engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    
    try:
        chroma_client.delete_collection(name="advisor_notes")
    except:
        pass
    collection = chroma_client.create_collection(name="advisor_notes", embedding_function=emb_fn)

    return Session(), collection

def populate_data(session, collection):
    print("Populating holistic, edge-case driven synthetic data...")
    
    # 1. Advisor
    advisor = AdvisorDetails(AdvisorName="Sarah Jenkins", Title="Senior Wealth Advisor")
    session.add(advisor)
    session.commit()
    
    session.add(AdvisorPerformance(AdvisorId=advisor.Id, TotalAUM=150000000.0, Revenue=1200000.0, GrowthYTD=8.5))
    
    # 2. Clients (Engineered for specific excel question edge-cases)
    
    # Client A: Edge Case -> Over 50, estate plan > 3 years old, major life event. (Question #2 from Excel)
    c1 = ClientDetails(ClientName="Robert & Susan Johnson", RiskProfile="Moderate", MaritalStatus="Married", Segment="HNW", Age=68, RecentLifeEvent="Birth of first grandchild")
    # Client B: Edge Case -> Missing compliance signatures and low-basis concentration risk. (Question #68 from Excel)
    c2 = ClientDetails(ClientName="Emily Chen", RiskProfile="Aggressive", MaritalStatus="Single", Segment="Emerging Wealth", Age=35, RecentLifeEvent="IPO at tech company")
    # Client C: Edge Case -> High AUM, but no recent plan update or meeting scheduled. (Question #1 from Excel)
    c3 = ClientDetails(ClientName="The Miller Family Trust", RiskProfile="Conservative", MaritalStatus="Married", Segment="UHNW", Age=75, RecentLifeEvent="Retirement")
    
    session.add_all([c1, c2, c3])
    session.commit()

    # Mappings
    session.add_all([
        AdvisorClient(AdvisorId=advisor.Id, ClientId=c1.Id, WalletShare=0.8),
        AdvisorClient(AdvisorId=advisor.Id, ClientId=c2.Id, WalletShare=1.0),
        AdvisorClient(AdvisorId=advisor.Id, ClientId=c3.Id, WalletShare=0.6)
    ])

    # 3. Financial Planning Facts & Compliance
    today = datetime.date.today()
    session.add_all([
        # c1 has stale estate plan (5 years old)
        FinancialPlanningFacts(ClientId=c1.Id, LastPlanUpdate=today - datetime.timedelta(days=180), EstatePlanDate=today - datetime.timedelta(days=1800), HasRMD=False),
        # c2 has missing docs
        ComplianceHub(ClientId=c2.Id, FlagType="Missing Signature", Description="Missing signature on updated IPS document.", IsResolved=False),
        FinancialPlanningFacts(ClientId=c2.Id, LastPlanUpdate=today - datetime.timedelta(days=30), EstatePlanDate=today - datetime.timedelta(days=100), HasRMD=False),
        # c3 has stale financial plan (over 2 years) and NO meetings scheduled
        FinancialPlanningFacts(ClientId=c3.Id, LastPlanUpdate=today - datetime.timedelta(days=800), EstatePlanDate=today - datetime.timedelta(days=400), HasRMD=True)
    ])

    # 4. Portfolio Data (Including low-basis concentration)
    session.add_all([
        PortfolioData(ClientId=c1.Id, Ticker="SPY", AssetName="S&P 500 ETF", AssetClass="Equity", MarketValue=1500000.0, CostBasis=1000000.0),
        # c2 has a concentrated low-basis position (high market value, tiny cost basis)
        PortfolioData(ClientId=c2.Id, Ticker="NVDA", AssetName="Nvidia Corp", AssetClass="Equity", MarketValue=2500000.0, CostBasis=50000.0), 
        PortfolioData(ClientId=c3.Id, Ticker="BND", AssetName="Total Bond ETF", AssetClass="Fixed Income", MarketValue=8500000.0, CostBasis=8000000.0)
    ])

    # 5. Transcripts (Vector Data)
    transcripts = [
        {"client": c1, "id": "TR-001", "text": "Robert noted their new grandchild was born last month. We need to look at setting up a 529 plan. He is also asking if their trust documents are still valid."},
        {"client": c2, "id": "TR-002", "text": "Emily's company RSUs vested. She holds a highly concentrated low-basis position in NVDA. She expressed anxiety about market volatility affecting her net worth."},
        {"client": c3, "id": "TR-003", "text": "Discussed RMDs for the Miller trust. They are frustrated with the lack of proactive outreach recently."}
    ]

    for t in transcripts:
        session.add(TranscriptSummary(ClientId=t['client'].Id, TranscriptId=t['id'], Summary=t['text']))
        collection.add(
            documents=[t['text']],
            metadatas=[{"client_id": t['client'].Id, "client_name": t['client'].ClientName, "sentiment": "neutral"}],
            ids=[t['id']]
        )

    session.commit()
    print("Database generation complete! Strict adherence to Data Inventory and Excel workflows achieved.")

if __name__ == "__main__":
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    db_session, vector_col = init_databases()
    populate_data(db_session, vector_col)
    db_session.close()