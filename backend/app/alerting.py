from abc import ABC, abstractmethod
from typing import Dict, Type
from .models import AlertSeverity

class AlertStrategy(ABC):
    @abstractmethod
    def determine_severity(self, component_id: str, payload: dict) -> AlertSeverity:
        pass

class RDBMSAlertStrategy(AlertStrategy):
    def determine_severity(self, component_id: str, payload: dict) -> AlertSeverity:
        # P0 for RDBMS failure
        return AlertSeverity.P0

class CacheAlertStrategy(AlertStrategy):
    def determine_severity(self, component_id: str, payload: dict) -> AlertSeverity:
        # P2 for Cache failure
        return AlertSeverity.P2

class APIAlertStrategy(AlertStrategy):
    def determine_severity(self, component_id: str, payload: dict) -> AlertSeverity:
        if payload.get("status_code", 200) >= 500:
            return AlertSeverity.P1
        return AlertSeverity.P3

class DefaultAlertStrategy(AlertStrategy):
    def determine_severity(self, component_id: str, payload: dict) -> AlertSeverity:
        return AlertSeverity.P2

class AlertContext:
    def __init__(self):
        self.strategies: Dict[str, AlertStrategy] = {
            "RDBMS": RDBMSAlertStrategy(),
            "CACHE": CacheAlertStrategy(),
            "API": APIAlertStrategy()
        }
        self.default_strategy = DefaultAlertStrategy()

    def get_severity(self, component_id: str, payload: dict) -> AlertSeverity:
        prefix = component_id.split("_")[0].upper()
        strategy = self.strategies.get(prefix, self.default_strategy)
        return strategy.determine_severity(component_id, payload)

alert_context = AlertContext()
