from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String, nullable=False)
    status = Column(String, default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    storage_path = Column(String, nullable=False)

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    status = Column(String, default="QUEUED")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
class EvidenceMetadata(Base):
    __tablename__ = "evidence_metadata"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    finding_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    evidence_data = Column(String, nullable=False) # JSON string for now

class PluginResult(Base):
    __tablename__ = "plugin_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    plugin_name = Column(String, nullable=False)
    status = Column(String, nullable=False) # SUCCESS or FAILED
    execution_time = Column(Float, nullable=False)
    raw_output_path = Column(String, nullable=True)
    parsed_output = Column(String, nullable=True) # JSON string representing the output

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String, nullable=False) # PROCESS_START, PROCESS_EXIT, NETWORK_CONNECTION
    details = Column(String, nullable=False)
