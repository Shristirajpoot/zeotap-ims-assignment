from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from .models import SignalPayload, WorkItemOut, RCAForm, WorkItem, IncidentStatus, RCARecord
from .db import get_db, signal_collection, redis_client
from .ingestion import ingestion_buffer
from .state import state_context

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Metrics counters
import time
metrics = {"processed_signals": 0, "last_reset": time.time()}

@router.post("/ingest", status_code=202)
@limiter.limit("10000/minute") # Rate limiter
async def ingest_signal(request: Request, payload: SignalPayload):
    # Quick ingest into memory queue
    await ingestion_buffer.ingest(payload)
    metrics["processed_signals"] += 1
    return {"status": "accepted"}

@router.get("/incidents", response_model=List[WorkItemOut])
async def get_incidents(session: AsyncSession = Depends(get_db)):
    # In a real system, we might query Redis for the live dashboard
    # For simplicity and correctness of states, we query Postgres and sort by severity
    stmt = select(WorkItem).order_by(WorkItem.severity, WorkItem.created_at.desc())
    result = await session.execute(stmt)
    incidents = result.scalars().all()
    
    # Eager load RCA (if any) could be done via options, but for simplicity we fetch it
    res = []
    for inc in incidents:
        rca_stmt = select(RCARecord).where(RCARecord.work_item_id == inc.id)
        rca_res = await session.execute(rca_stmt)
        rca = rca_res.scalar_one_or_none()
        
        inc_out = WorkItemOut.model_validate(inc)
        if rca:
            inc_out.rca = RCAForm(
                root_cause_category=rca.root_cause_category,
                fix_applied=rca.fix_applied,
                prevention_steps=rca.prevention_steps
            )
            inc_out.mttr_minutes = rca.mttr_minutes
        res.append(inc_out)
        
    return res

@router.get("/incidents/{incident_id}/signals")
async def get_incident_signals(incident_id: str, session: AsyncSession = Depends(get_db)):
    # First, get the component_id for the incident
    stmt = select(WorkItem).where(WorkItem.id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Query Data Lake (MongoDB) for raw signals related to this component
    cursor = signal_collection.find({"component_id": incident.component_id}).sort("timestamp", -1).limit(100)
    signals = await cursor.to_list(length=100)
    
    for sig in signals:
        sig["_id"] = str(sig["_id"])
        
    return signals

@router.put("/incidents/{incident_id}/status", response_model=WorkItemOut)
async def update_incident_status(incident_id: str, status: IncidentStatus, session: AsyncSession = Depends(get_db)):
    stmt = select(WorkItem).where(WorkItem.id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    updated_incident = await state_context.change_status(incident, status, session)
    await session.commit()
    return WorkItemOut.model_validate(updated_incident)

@router.post("/incidents/{incident_id}/rca", response_model=WorkItemOut)
async def submit_rca(incident_id: str, rca_data: RCAForm, session: AsyncSession = Depends(get_db)):
    stmt = select(WorkItem).where(WorkItem.id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # The RCA can be submitted and simultaneously close the incident
    updated_incident = await state_context.change_status(incident, IncidentStatus.CLOSED, session, rca_data.model_dump())
    await session.commit()
    return WorkItemOut.model_validate(updated_incident)

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
