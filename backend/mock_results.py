import asyncio
import uuid
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.case import Case, EvidenceMetadata, TimelineEvent

from app.core.config import settings

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def run_mock():
    # Fixed case ID so it's easy to look up
    case_id = "mock-case-123"
    
    async with async_session() as session:
        # Check if exists, delete to reset
        # Note: cascade delete isn't fully configured in models for simplicity, so we manually delete
        await session.execute(TimelineEvent.__table__.delete().where(TimelineEvent.case_id == case_id))
        await session.execute(EvidenceMetadata.__table__.delete().where(EvidenceMetadata.case_id == case_id))
        await session.execute(Case.__table__.delete().where(Case.id == case_id))
        await session.commit()
        
        # 1. Create a Case
        print(f"Creating mock case: {case_id}")
        case = Case(
            id=case_id,
            filename="infected_win10_dump.raw",
            file_size=4294967296, # 4GB
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            storage_path="/tmp/mock_storage/infected_win10_dump.raw",
            status="COMPLETED",
            risk_score=95.0
        )
        session.add(case)
        
        # 2. Add Findings
        findings = [
            EvidenceMetadata(
                id=str(uuid.uuid4()),
                case_id=case_id,
                finding_type="HIDDEN_PROCESS",
                severity="HIGH",
                description="Potential hidden process: svchost.exe (PID 6632). Process found by memory scanning (psscan) but absent from standard process list (pslist). Indicates Direct Kernel Object Manipulation (DKOM).",
                confidence=0.9,
                evidence_data='{"source": "psscan", "process_info": {"PID": 6632, "ImageFileName": "svchost.exe"}}'
            ),
            EvidenceMetadata(
                id=str(uuid.uuid4()),
                case_id=case_id,
                finding_type="INJECTED_CODE",
                severity="HIGH",
                description="Injected code detected in svchost.exe (PID 6632). Memory segment has suspicious protections: PAGE_EXECUTE_READWRITE.",
                confidence=0.85,
                evidence_data='{"source": "malfind", "process_info": {"PID": 6632, "Protection": "PAGE_EXECUTE_READWRITE"}}'
            ),
            EvidenceMetadata(
                id=str(uuid.uuid4()),
                case_id=case_id,
                finding_type="SUSPICIOUS_NETWORK",
                severity="CRITICAL",
                description="CRITICAL: Suspicious process (PID 6632) is communicating with remote address 185.12.34.56:443 (State: ESTABLISHED). High probability of Command and Control (C2) activity.",
                confidence=0.95,
                evidence_data='{"source": "netscan", "network_info": {"PID": 6632, "ForeignAddr": "185.12.34.56", "ForeignPort": 443}}'
            )
        ]
        session.add_all(findings)
        
        # 3. Add Timeline Events
        now = datetime.datetime.now(datetime.timezone.utc)
        timeline = [
            TimelineEvent(
                id=str(uuid.uuid4()),
                case_id=case_id,
                timestamp=now - datetime.timedelta(minutes=45),
                event_type="PROCESS_START",
                details="Process started: explorer.exe (PID: 1204)"
            ),
            TimelineEvent(
                id=str(uuid.uuid4()),
                case_id=case_id,
                timestamp=now - datetime.timedelta(minutes=10),
                event_type="PROCESS_START",
                details="Process started: svchost.exe (PID: 6632)"
            ),
            TimelineEvent(
                id=str(uuid.uuid4()),
                case_id=case_id,
                timestamp=now - datetime.timedelta(minutes=5),
                event_type="NETWORK_CONNECTION",
                details="Network socket created by PID 6632 (Local: 192.168.1.55:49152, Remote: 185.12.34.56:443)"
            )
        ]
        session.add_all(timeline)
        
        await session.commit()
        print("\n--- MOCK DATA INJECTED SUCCESSFULLY ---")
        print(f"To view it, look up Case ID: {case_id} in the UI.")

if __name__ == "__main__":
    asyncio.run(run_mock())
