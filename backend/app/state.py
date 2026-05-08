from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from .models import WorkItem, IncidentStatus, RCARecord

class IncidentState(ABC):
    @abstractmethod
    async def transition_to(self, work_item: WorkItem, new_status: IncidentStatus, session: AsyncSession, rca_data: Optional[dict] = None) -> WorkItem:
        pass

class StateContext:
    def __init__(self):
        self.states = {
            IncidentStatus.OPEN: OpenState(),
            IncidentStatus.INVESTIGATING: InvestigatingState(),
            IncidentStatus.RESOLVED: ResolvedState(),
            IncidentStatus.CLOSED: ClosedState()
        }

    async def change_status(self, work_item: WorkItem, new_status: IncidentStatus, session: AsyncSession, rca_data: Optional[dict] = None) -> WorkItem:
        if work_item.status == new_status:
            return work_item
        current_state = self.states.get(work_item.status)
        if not current_state:
            raise HTTPException(status_code=400, detail="Invalid current state.")
        return await current_state.transition_to(work_item, new_status, session, rca_data)

class OpenState(IncidentState):
    async def transition_to(self, work_item: WorkItem, new_status: IncidentStatus, session: AsyncSession, rca_data: Optional[dict] = None) -> WorkItem:
        if new_status == IncidentStatus.INVESTIGATING:
            work_item.status = new_status
            return work_item
        raise HTTPException(status_code=400, detail="OPEN can only transition to INVESTIGATING.")

class InvestigatingState(IncidentState):
    async def transition_to(self, work_item: WorkItem, new_status: IncidentStatus, session: AsyncSession, rca_data: Optional[dict] = None) -> WorkItem:
        if new_status == IncidentStatus.RESOLVED:
            work_item.status = new_status
            work_item.resolved_at = datetime.utcnow()
            return work_item
        elif new_status == IncidentStatus.OPEN:
             work_item.status = new_status
             return work_item
        raise HTTPException(status_code=400, detail="INVESTIGATING can only transition to RESOLVED or OPEN.")

class ResolvedState(IncidentState):
    async def transition_to(self, work_item: WorkItem, new_status: IncidentStatus, session: AsyncSession, rca_data: Optional[dict] = None) -> WorkItem:
        if new_status == IncidentStatus.CLOSED:
            # Mandatory RCA Check
            stmt = select(RCARecord).where(RCARecord.work_item_id == work_item.id)
            result = await session.execute(stmt)
            existing_rca = result.scalar_one_or_none()
            
            if not existing_rca and not rca_data:
                 raise HTTPException(status_code=400, detail="Mandatory RCA required to close incident.")
            
            if rca_data and not existing_rca:
                # MTTR Calculation
                end_time = datetime.utcnow()
                start_time = work_item.created_at
                mttr_minutes = (end_time - start_time).total_seconds() / 60.0

                rca = RCARecord(
                    work_item_id=work_item.id,
                    root_cause_category=rca_data.get("root_cause_category"),
                    fix_applied=rca_data.get("fix_applied"),
                    prevention_steps=rca_data.get("prevention_steps"),
                    mttr_minutes=mttr_minutes
                )
                session.add(rca)

            work_item.status = new_status
            work_item.closed_at = datetime.utcnow()
            return work_item
        elif new_status == IncidentStatus.INVESTIGATING:
             work_item.status = new_status
             work_item.resolved_at = None
             return work_item
        raise HTTPException(status_code=400, detail="RESOLVED can only transition to CLOSED or INVESTIGATING.")

class ClosedState(IncidentState):
    async def transition_to(self, work_item: WorkItem, new_status: IncidentStatus, session: AsyncSession, rca_data: Optional[dict] = None) -> WorkItem:
        raise HTTPException(status_code=400, detail="CLOSED incidents cannot be reopened.")

state_context = StateContext()
