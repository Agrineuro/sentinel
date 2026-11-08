import json
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from app.connectors.base import BaseConnector


class HTTPConnector(BaseConnector):
    name = "http"
    connector_type = "polling"

    def health_check(self, url: str, timeout: int = 8) -> dict:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Health URL must be an absolute HTTP or HTTPS URL")
        request = Request(url, headers={"User-Agent": "Sentinel/0.1"})
        started = time.monotonic()
        with urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            body = response.read(262145)
            response_time_ms = round((time.monotonic() - started) * 1000, 1)
            metrics = {}
            if len(body) <= 262144:
                try:
                    payload = json.loads(body.decode("utf-8"))
                    candidate = payload.get("metrics", payload) if isinstance(payload, dict) else {}
                    if isinstance(candidate, dict):
                        for key in ("cpu_percent", "memory_used_percent", "disk_root_used_percent", "memory_total_gb"):
                            value = candidate.get(key)
                            if isinstance(value, (int, float)) and not isinstance(value, bool):
                                metrics[key] = float(value)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass
        if not 200 <= status < 300:
            return {"status": "unhealthy", "http_status": status, "response_time_ms": response_time_ms}
        return {"status": "healthy", "http_status": status, "response_time_ms": response_time_ms, "metrics": metrics}

    def discover(self, url: str, **kwargs) -> dict:
        result = self.health_check(url)
        return self.emit_event("http.discovered", {"url": url, **result})
