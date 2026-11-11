import json
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

class ProxmoxPluginError(RuntimeError):
    pass

class ProxmoxConnectorPlugin:
    def _validate(self, base_url, token_id, token_secret):
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Proxmox URL must be HTTPS and must not contain embedded credentials")
        if not token_id or "!" not in token_id or not token_secret:
            raise ValueError("A Proxmox API token ID and secret are required")

    def get(self, base_url, token_id, token_secret, path, verify_tls=True, timeout=8):
        self._validate(base_url, token_id, token_secret)
        url = base_url.rstrip("/") + "/api2/json/" + path.lstrip("/")
        context = ssl.create_default_context() if verify_tls else ssl._create_unverified_context()
        request = Request(url, headers={"Authorization":"PVEAPIToken="+token_id+"="+token_secret,"Accept":"application/json","User-Agent":"Sentinel/0.1"})
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                body = response.read(2_097_153)
                if len(body) > 2_097_152:
                    raise ProxmoxPluginError("Proxmox response exceeded the 2 MiB limit")
                payload = json.loads(body.decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401,403):
                raise ProxmoxPluginError("Proxmox rejected the read-only API token") from exc
            raise ProxmoxPluginError("Proxmox API returned HTTP " + str(exc.code)) from exc
        except (URLError,TimeoutError,ssl.SSLError,json.JSONDecodeError) as exc:
            raise ProxmoxPluginError("Could not read a valid response from the Proxmox API") from exc
        if not isinstance(payload,dict) or "data" not in payload:
            raise ProxmoxPluginError("Proxmox returned an unexpected API response")
        return payload["data"]

    def test(self, config, token_id, token_secret):
        started=time.monotonic()
        verify=bool(config.get("verify_tls",True))
        version=self.get(config["url"],token_id,token_secret,"version",verify)
        resources=self.get(config["url"],token_id,token_secret,"cluster/resources",verify)
        if not isinstance(resources,list):
            raise ProxmoxPluginError("Proxmox resource inventory was not a list")
        return {"version":str(version.get("version","unknown")),"release":str(version.get("release","")),
          "resource_count":len(resources),"nodes":sum(1 for x in resources if x.get("type")=="node"),
          "guests":sum(1 for x in resources if x.get("type") in ("qemu","lxc")),
          "latency_ms":round((time.monotonic()-started)*1000,1)}

    def collect(self,config,token_id,token_secret):
        resources=self.get(config["url"],token_id,token_secret,"cluster/resources",bool(config.get("verify_tls",True)))
        if not isinstance(resources,list):
            raise ProxmoxPluginError("Proxmox resource inventory was not a list")
        return resources

def create_plugin():
    return ProxmoxConnectorPlugin()
