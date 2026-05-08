import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

Base = declarative_base()

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class AlertSeverity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

# SQLAlchemy Models
class WorkItem(Base):
    __tablename__ = "work_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id = Column(String, index=True, nullable=False)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    rca = relationship("RCARecord", back_populates="work_item", uselist=False)

class RCARecord(Base):
    __tablename__ = "rca_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    work_item_id = Column(String, ForeignKey("work_items.id"), nullable=False, unique=True)
    root_cause_category = Column(String, nullable=False)
    fix_applied = Column(Text, nullable=False)
    prevention_steps = Column(Text, nullable=False)
    incident_start = Column(DateTime, nullable=True)
    incident_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    mttr_minutes = Column(Float, nullable=True)

    work_item = relationship("WorkItem", back_populates="rca")

# Pydantic Models for API
class SignalPayload(BaseModel):
    component_id: str
    signal_type: str
    payload: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RCAForm(BaseModel):
    root_cause_category: str
    fix_applied: str
    prevention_steps: str
    incident_start: datetime | None = None
    incident_end: datetime | None = None

class WorkItemOut(BaseModel):
    id: str
    component_id: str
    status: IncidentStatus
    severity: AlertSeverity
    created_at: datetime
    updated_at: datetime
    mttr_minutes: float | None = None
    rca: RCAForm | None = None

    model_config = ConfigDict(from_attributes=True)
