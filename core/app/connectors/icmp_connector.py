import ipaddress
import subprocess
from app.connectors.base import BaseConnector


class ICMPConnector(BaseConnector):
    name = "icmp"
    connector_type = "polling"

    def health_check(self, host: str, timeout: int = 2) -> dict:
        host = host.strip()
        if not host or len(host) > 253 or host.startswith("-"):
            raise ValueError("Enter a valid host name or IP address")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if any(character not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-:' for character in host):
                raise ValueError('Enter a valid host name or IP address')
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), "--", host],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        if result.returncode == 0:
            return {"status": "healthy"}
        return {"status": "unhealthy"}

    def discover(self, host: str, **kwargs) -> dict:
        result = self.health_check(host)
        return self.emit_event("icmp.discovered", {"host": host, **result})
