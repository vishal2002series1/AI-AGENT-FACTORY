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
    PortfolioData, FinancialPlanningFacts, ComplianceHub, UpcomingClientMeetings, TranscriptSummary,
    Email, EmailInsight, TranscriptInsights, NextBestAction, MarketHighlights
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
    print("Populating high-density enterprise synthetic data for complex workflow testing...")
    today = datetime.date.today()
    
    # --- 1. Advisor ---
    advisor = AdvisorDetails(AdvisorName="Sarah Jenkins", Title="Senior Wealth Advisor")
    session.add(advisor)
    session.commit()
    session.add(AdvisorPerformance(AdvisorId=advisor.Id, TotalAUM=210000000.0, Revenue=1800000.0, GrowthYTD=4.2))
    
    # --- 2. Clients ---
    c1 = ClientDetails(ClientName="Robert & Susan Johnson", RiskProfile="Moderate", MaritalStatus="Married", Segment="HNW", Age=68, UpcomingLifeEvents="Birth of first grandchild", FinancialGoals="Estate transfer", ClientSentiment="Positive", ClientNPS=8, TaxSensitivity="Medium")
    c2 = ClientDetails(ClientName="Emily Chen", RiskProfile="Aggressive", MaritalStatus="Single", Segment="Emerging Wealth", Age=35, UpcomingLifeEvents="IPO at tech company", FinancialGoals="Aggressive growth, liquidity", ClientSentiment="At Risk", AttritionRisk="High", ClientNPS=4, TaxSensitivity="High", OccupationInfo="Tech Executive")
    c3 = ClientDetails(ClientName="The Miller Family Trust", RiskProfile="Conservative", MaritalStatus="Married", Segment="UHNW", Age=75, UpcomingLifeEvents="Retirement", FinancialGoals="Capital preservation", ClientSentiment="Neutral", ClientNPS=6, TaxSensitivity="Low")
    c4 = ClientDetails(ClientName="David Alverez", RiskProfile="Growth", MaritalStatus="Divorced", Segment="HNW", Age=52, UpcomingLifeEvents="Selling business", FinancialGoals="Business transition, tax planning", ClientSentiment="Frustrated", AttritionRisk="Medium", ClientNPS=5, TaxSensitivity="High")
    
    session.add_all([c1, c2, c3, c4])
    session.commit()

    session.add_all([
        AdvisorClient(AdvisorId=advisor.Id, ClientId=c1.Id, WalletShare=0.8),
        AdvisorClient(AdvisorId=advisor.Id, ClientId=c2.Id, WalletShare=1.0),
        AdvisorClient(AdvisorId=advisor.Id, ClientId=c3.Id, WalletShare=0.6),
        AdvisorClient(AdvisorId=advisor.Id, ClientId=c4.Id, WalletShare=0.4) # Low wallet share = opportunity
    ])

    # --- 3. Planning & Compliance (Multiple overlaps for complex queries) ---
    session.add_all([
        FinancialPlanningFacts(ClientId=c1.Id, LastPlanUpdate=today - datetime.timedelta(days=180), EstatePlanDate=today - datetime.timedelta(days=1800), HasRMD=False),
        ComplianceHub(ClientId=c2.Id, FlagType="Missing Signature", Description="Missing signature on updated IPS document.", IsResolved=False),
        ComplianceHub(ClientId=c2.Id, FlagType="Stale KYC", Description="KYC profile has not been updated in 3 years.", IsResolved=False),
        FinancialPlanningFacts(ClientId=c2.Id, LastPlanUpdate=today - datetime.timedelta(days=30), EstatePlanDate=today - datetime.timedelta(days=100), HasRMD=False),
        FinancialPlanningFacts(ClientId=c3.Id, LastPlanUpdate=today - datetime.timedelta(days=800), EstatePlanDate=today - datetime.timedelta(days=400), HasRMD=True),
        ComplianceHub(ClientId=c4.Id, FlagType="Unsigned Margin Agreement", Description="Margin trading enabled but agreement pending.", IsResolved=False),
    ])

    # --- 4. Dense Portfolio Data (To test concentration and drift logic) ---
    # Emily: Tech heavy, massive NVDA concentration, low basis
    session.add_all([
        PortfolioData(ClientId=c2.Id, Ticker="NVDA", AssetName="Nvidia Corp", AssetClass="Equity", MarketValue=2500000.0, CostBasis=50000.0),
        PortfolioData(ClientId=c2.Id, Ticker="AAPL", AssetName="Apple Inc.", AssetClass="Equity", MarketValue=300000.0, CostBasis=250000.0),
        PortfolioData(ClientId=c2.Id, Ticker="MSFT", AssetName="Microsoft Corp", AssetClass="Equity", MarketValue=150000.0, CostBasis=100000.0),
        PortfolioData(ClientId=c2.Id, Ticker="VTI", AssetName="Vanguard Total Stock ETF", AssetClass="Equity", MarketValue=50000.0, CostBasis=48000.0),
        PortfolioData(ClientId=c2.Id, Ticker="CASH", AssetName="Money Market", AssetClass="Cash", MarketValue=10000.0, CostBasis=10000.0),
    ])
    # Robert: Diversified, slightly heavy in SPY
    session.add_all([
        PortfolioData(ClientId=c1.Id, Ticker="SPY", AssetName="S&P 500 ETF", AssetClass="Equity", MarketValue=1500000.0, CostBasis=1000000.0),
        PortfolioData(ClientId=c1.Id, Ticker="BND", AssetName="Total Bond ETF", AssetClass="Fixed Income", MarketValue=800000.0, CostBasis=820000.0),
        PortfolioData(ClientId=c1.Id, Ticker="VXUS", AssetName="Total Intl Stock ETF", AssetClass="Equity", MarketValue=400000.0, CostBasis=380000.0),
    ])

    # --- 5. Escalating Emails (To test Sentiment trends and extraction) ---
    emails = [
        Email(ClientId=c2.Id, DateSent=today - datetime.timedelta(days=14), Subject="Checking in on tech stocks", Body="Hi Sarah. Just watching the news. Tech seems a bit shaky. Should we review the NVDA position soon?"),
        Email(ClientId=c2.Id, DateSent=today - datetime.timedelta(days=5), Subject="RE: Checking in", Body="Sarah, I haven't heard back. NVDA dropped 4% today. I am getting very anxious about this concentration. We need a plan before my IPO lockup expires."),
        Email(ClientId=c2.Id, DateSent=today - datetime.timedelta(days=1), Subject="Urgent: Portfolio Review", Body="Sarah, NVDA is swinging wildly. The lack of proactive communication here is frustrating. Please call me today."),
        Email(ClientId=c4.Id, DateSent=today - datetime.timedelta(days=3), Subject="Competitor pitch", Body="Sarah, Morgan Stanley just pitched me a comprehensive business exit strategy. What exactly are we doing to prepare for my sale next year?")
    ]
    session.add_all(emails)
    session.commit()
    
    session.add_all([
        EmailInsight(EmailId=emails[0].Id, SentimentScore=0.5, RequiresAction=False, ExtractedThemes="Market Curiosity"),
        EmailInsight(EmailId=emails[1].Id, SentimentScore=0.3, RequiresAction=True, ExtractedThemes="Volatility Anxiety, Concentration Risk"),
        EmailInsight(EmailId=emails[2].Id, SentimentScore=0.1, RequiresAction=True, ExtractedThemes="Frustration, High Flight Risk, Communication Gap"),
        EmailInsight(EmailId=emails[3].Id, SentimentScore=0.2, RequiresAction=True, ExtractedThemes="Competitor Threat, Business Transition")
    ])

    # --- 6. Market Highlights ---
    session.add_all([
        MarketHighlights(Date=today, AssetClass="Equity", HighlightText="Semiconductor stocks show intense intraday volatility amid macro tech selloff.", MarketImpact="Bearish"),
        MarketHighlights(Date=today, AssetClass="Fixed Income", HighlightText="10-year Treasury yields stabilize as inflation data meets expectations.", MarketImpact="Neutral")
    ])

    # --- 7. Transcripts & ChromaDB ---
    transcripts = [
        {"client": c1, "id": "TR-001", "text": "Robert noted their new grandchild was born last month. We need to look at setting up a 529 plan. He is also asking if their trust documents are still valid."},
        {"client": c2, "id": "TR-002", "text": "Emily's company RSUs vested. She holds a highly concentrated low-basis position in NVDA. She expressed anxiety about market volatility affecting her net worth but doesn't want to trigger massive capital gains."},
        {"client": c3, "id": "TR-003", "text": "Discussed RMDs for the Miller trust. They are frustrated with the lack of proactive outreach recently."},
        {"client": c4, "id": "TR-004", "text": "David is aggressively looking for M&A targets to sell his manufacturing business. We need to loop in the commercial banking team and start estate tax mitigation planning immediately."}
    ]

    for t in transcripts:
        session.add(TranscriptSummary(ClientId=t['client'].Id, TranscriptId=t['id'], Summary=t['text']))
        session.add(TranscriptInsights(TranscriptId=t['id'], OverallSentiment="Neutral", ActionItems="Review documents", KeyLifeEventsMentioned=t['client'].UpcomingLifeEvents))
        collection.add(
            documents=[t['text']],
            metadatas=[{"client_id": t['client'].Id, "client_name": t['client'].ClientName, "sentiment": "neutral"}],
            ids=[t['id']]
        )

    session.commit()
    print("Enterprise Database generation complete! High-density data ready for all complex Workflows.")

if __name__ == "__main__":
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    db_session, vector_col = init_databases()
    populate_data(db_session, vector_col)
    db_session.close()