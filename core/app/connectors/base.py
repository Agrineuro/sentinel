from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseConnector(ABC):
    """
    Sentinel Connector Contract v1

    Every system integration MUST implement this interface.
    """

    name: str
    connector_type: str

    @abstractmethod
    def discover(self, **kwargs) -> Dict[str, Any]:
        """
        Pull or receive system state and normalize it into a dict.
        """
        pass

    @abstractmethod
    def health_check(self, **kwargs) -> Dict[str, Any]:
        """
        Validate connectivity to the system.
        """
        pass

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardized event wrapper (used by all connectors).
        """
        return {
            "type": event_type,
            "source": self.name,
            "data": data,
        }
