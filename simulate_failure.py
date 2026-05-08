import asyncio
import httpx
import random
from datetime import datetime

API_URL = "http://localhost:8000/ingest"

async def simulate_outage(component_id: str, outage_duration_sec: int, signals_per_sec: int):
    print(f"Starting simulated outage for {component_id} ({signals_per_sec} signals/sec for {outage_duration_sec}s)")
    async with httpx.AsyncClient() as client:
        for _ in range(outage_duration_sec):
            tasks = []
            for _ in range(signals_per_sec):
                payload = {
                    "component_id": component_id,
                    "signal_type": "timeout",
                    "payload": {"error": "Connection refused", "latency_ms": random.randint(5000, 15000)},
                    "timestamp": datetime.utcnow().isoformat()
                }
                tasks.append(client.post(API_URL, json=payload))
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

async def main():
    print("Simulating RDBMS outage...")
    await simulate_outage("RDBMS_01", 3, 50)  # 150 signals total
    
    print("Simulating Cache failure...")
    await simulate_outage("CACHE_02", 2, 20)  # 40 signals total

    print("Simulating API latency...")
    await simulate_outage("API_GW", 4, 100) # 400 signals total

if __name__ == "__main__":
    asyncio.run(main())
