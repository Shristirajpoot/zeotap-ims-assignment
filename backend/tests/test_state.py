import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.models import Base, WorkItem, IncidentStatus
from app.state import state_context

# Setup in-memory SQLite for testing
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture
async def session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_rca_validation_logic(session):
    # Create an initial WorkItem
    item = WorkItem(component_id="TEST_01", severity="P1", status=IncidentStatus.OPEN)
    session.add(item)
    await session.commit()

    # Move to INVESTIGATING
    item = await state_context.change_status(item, IncidentStatus.INVESTIGATING, session)
    assert item.status == IncidentStatus.INVESTIGATING

    # Move to RESOLVED
    item = await state_context.change_status(item, IncidentStatus.RESOLVED, session)
    assert item.status == IncidentStatus.RESOLVED

    # Attempt to move to CLOSED without RCA data -> should fail
    with pytest.raises(HTTPException) as excinfo:
        await state_context.change_status(item, IncidentStatus.CLOSED, session)
    assert excinfo.value.status_code == 400
    assert "Mandatory RCA required" in excinfo.value.detail

    # Attempt to move to CLOSED with RCA data -> should succeed
    rca_data = {
        "root_cause_category": "Test",
        "fix_applied": "Test Fix",
        "prevention_steps": "Test Prevention"
    }
    item = await state_context.change_status(item, IncidentStatus.CLOSED, session, rca_data)
    assert item.status == IncidentStatus.CLOSED
