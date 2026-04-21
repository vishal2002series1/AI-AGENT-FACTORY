# src/core/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class AdvisorDetails(Base):
    __tablename__ = 'AdvisorDetails'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    AdvisorName = Column(String(255), nullable=False)
    Title = Column(String(100))
    
    clients = relationship("AdvisorClient", back_populates="advisor")
    performance = relationship("AdvisorPerformance", back_populates="advisor", uselist=False)

class AdvisorPerformance(Base):
    __tablename__ = 'AdvisorPerformance'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    AdvisorId = Column(Integer, ForeignKey('AdvisorDetails.Id'))
    TotalAUM = Column(Float)
    Revenue = Column(Float)
    GrowthYTD = Column(Float)
    
    advisor = relationship("AdvisorDetails", back_populates="performance")

class ClientDetails(Base):
    __tablename__ = 'ClientDetails'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ClientName = Column(String(255), nullable=False)
    RiskProfile = Column(String(50))
    MaritalStatus = Column(String(50))
    Segment = Column(String(50))
    Age = Column(Integer)
    RecentLifeEvent = Column(String(255)) # Captures "major life events" from requirements
    
    advisors = relationship("AdvisorClient", back_populates="client")
    meetings = relationship("UpcomingClientMeetings", back_populates="client")
    transcripts = relationship("TranscriptSummary", back_populates="client")
    compliance = relationship("ComplianceHub", back_populates="client")
    portfolio = relationship("PortfolioData", back_populates="client")
    planning_facts = relationship("FinancialPlanningFacts", back_populates="client", uselist=False)

class AdvisorClient(Base):
    __tablename__ = 'AdvisorClient'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    AdvisorId = Column(Integer, ForeignKey('AdvisorDetails.Id'))
    ClientId = Column(Integer, ForeignKey('ClientDetails.Id'))
    WalletShare = Column(Float)
    
    advisor = relationship("AdvisorDetails", back_populates="clients")
    client = relationship("ClientDetails", back_populates="advisors")

class PortfolioData(Base):
    __tablename__ = 'PortfolioData'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ClientId = Column(Integer, ForeignKey('ClientDetails.Id'))
    Ticker = Column(String(20))
    AssetName = Column(String(255))
    AssetClass = Column(String(100))
    MarketValue = Column(Float)
    CostBasis = Column(Float) # Needed for "Concentrated low-basis position" workflow
    
    client = relationship("ClientDetails", back_populates="portfolio")

class FinancialPlanningFacts(Base):
    __tablename__ = 'FinancialPlanningFacts'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ClientId = Column(Integer, ForeignKey('ClientDetails.Id'))
    LastPlanUpdate = Column(Date) # Needed for "stale plan dates" workflow
    EstatePlanDate = Column(Date) # Needed for "estate documents > 3 years old" workflow
    HasRMD = Column(Boolean, default=False)
    
    client = relationship("ClientDetails", back_populates="planning_facts")

class ComplianceHub(Base):
    __tablename__ = 'ComplianceHub'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ClientId = Column(Integer, ForeignKey('ClientDetails.Id'))
    FlagType = Column(String(100)) # e.g., "Missing Signature", "Stale IPS"
    Description = Column(Text)
    IsResolved = Column(Boolean, default=False)
    
    client = relationship("ClientDetails", back_populates="compliance")

class UpcomingClientMeetings(Base):
    __tablename__ = 'UpcomingClientMeetings'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ClientId = Column(Integer, ForeignKey('ClientDetails.Id'))
    MeetingType = Column(String(100))
    MeetingDate = Column(Date)
    
    client = relationship("ClientDetails", back_populates="meetings")

class TranscriptSummary(Base):
    __tablename__ = 'TranscriptSummary'
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ClientId = Column(Integer, ForeignKey('ClientDetails.Id'))
    TranscriptId = Column(String(100), unique=True)
    Summary = Column(Text)
    
    client = relationship("ClientDetails", back_populates="transcripts")