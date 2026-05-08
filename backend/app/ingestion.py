import asyncio
import time
import logging
import json
from collections import defaultdict
from typing import List, Dict
from sqlalchemy.future import select

from .models import SignalPayload, WorkItem, IncidentStatus
from .db import AsyncSessionLocal, signal_collection, redis_client
from .alerting import alert_context

logger = logging.getLogger(__name__)

class IngestionBuffer:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.batch_size = 1000
        self.flush_interval = 2.0  # seconds

    async def ingest(self, signal: SignalPayload):
        await self.queue.put(signal)

    async def _process_batch(self, batch: List[SignalPayload]):
        if not batch:
            return

        # 1. Debouncing: Group by component_id
        grouped_signals: Dict[str, List[SignalPayload]] = defaultdict(list)
        for sig in batch:
            grouped_signals[sig.component_id].append(sig)

        # 2. Sink (Data Lake): Store raw signals in MongoDB
        mongo_docs = [s.model_dump() for s in batch]
        try:
             await signal_collection.insert_many(mongo_docs)
        except Exception as e:
             logger.error(f"MongoDB Insert failed: {e}")

        # 3. Process grouped signals
        async with AsyncSessionLocal() as session:
            try:
                for comp_id, signals in grouped_signals.items():
                    # Get the most recent signal for payload analysis
                    latest_signal = signals[-1]
                    
                    # Determine severity
                    severity = alert_context.get_severity(comp_id, latest_signal.payload)

                    # Check if an active Work Item exists in Postgres
                    stmt = select(WorkItem).where(
                        WorkItem.component_id == comp_id,
                        WorkItem.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING, IncidentStatus.RESOLVED])
                    )
                    result = await session.execute(stmt)
                    active_item = result.scalars().first()

                    work_item_id = None
                    if not active_item:
                        # Create new Work Item
                        new_item = WorkItem(
                            component_id=comp_id,
                            severity=severity,
                            status=IncidentStatus.OPEN
                        )
                        session.add(new_item)
                        await session.flush() # To get the generated ID
                        work_item_id = new_item.id
                        logger.info(f"Created WorkItem {work_item_id} for {comp_id}")
                    else:
                        work_item_id = active_item.id
                        # Optional: escalate severity if needed based on new signal
                        if severity < active_item.severity: # Assuming P0 < P1 in enum? Wait, String comparison. Let's keep simple.
                            pass

                    # 4. Cache (Hot-path): Update Real-time Dashboard state in Redis
                    if work_item_id:
                        cache_key = f"incident:{work_item_id}"
                        cache_data = {
                             "id": work_item_id,
                             "component_id": comp_id,
                             "severity": severity,
                             "status": active_item.status if active_item else IncidentStatus.OPEN,
                             "signal_count": len(signals), # Approximate for recent batch
                             "last_updated": time.time()
                        }
                        await redis_client.hset(cache_key, mapping=cache_data)
                        await redis_client.expire(cache_key, 3600) # Expire in 1 hour
                        
                await session.commit()
            except Exception as e:
                logger.error(f"Postgres/Redis Processing failed: {e}")
                await session.rollback()

    async def worker(self):
        self.running = True
        logger.info("Ingestion worker started")
        while self.running:
            batch = []
            start_time = time.time()
            
            # Try to get batch_size items or wait up to flush_interval
            while len(batch) < self.batch_size:
                try:
                    # Timeout to allow flushing if queue is slow
                    timeout = max(0.1, self.flush_interval - (time.time() - start_time))
                    item = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                    batch.append(item)
                    self.queue.task_done()
                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    logger.error(f"Queue error: {e}")
                    break
            
            if batch:
                await self._process_batch(batch)

ingestion_buffer = IngestionBuffer()
