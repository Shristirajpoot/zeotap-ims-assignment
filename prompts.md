# Prompts and LLM Usage Log

This application was architected and generated with the assistance of an AI coding assistant (Gemini 3.1 Pro). 

## Prompts Used:

1. **Architecture Planning**: "Design a resilient Incident Management System backend that can ingest 10,000 signals/sec with Python FastAPI. Use a debouncing mechanism, MongoDB for raw logs, PostgreSQL for Work Items, and Redis for cache. Also structure it using State and Strategy design patterns."
2. **State Pattern Implementation**: "Implement the State Design Pattern for an Incident that goes through OPEN -> INVESTIGATING -> RESOLVED -> CLOSED. Enforce a mandatory RCA requirement before transitioning to CLOSED, and calculate MTTR."
3. **Strategy Pattern Implementation**: "Implement a Strategy pattern for an Alerting strategy that determines severity (P0 to P3) based on the component ID and payload contents."
4. **Debouncing Logic**: "Write an async queue ingestion buffer that batches incoming signals. If multiple signals arrive for the same component within a time window, group them together and ensure only one WorkItem is created while inserting all raw signals into MongoDB."
5. **Frontend Development**: "Create a React dashboard with Tailwind CSS that fetches the incidents, displays them by severity, allows clicking an incident to view details and raw signals, and provides an RCA form to close the incident."
6. **Docker Configuration**: "Write a docker-compose.yml file that includes PostgreSQL, MongoDB, Redis, a FastAPI backend, and an Nginx-served React frontend."

The AI generated the scaffolding, models, logic, and configuration, which were then refined, tested, and assembled to ensure robust concurrency handling, database separation, and adherence to the SRE evaluation rubric.
