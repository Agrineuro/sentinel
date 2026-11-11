import base64
import json
import math
import hashlib
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


class PrometheusPlugin:
    def _query(self, config, username=None, password=None):
        base = str(config["url"]).rstrip("/") + "/"
        parsed = urlparse(base)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Prometheus URL must be an HTTP(S) origin without embedded credentials")
        query_url = base + "api/v1/query?" + urlencode({"query": config.get("query", "up")})
        headers = {"Accept": "application/json", "User-Agent": "Sentinel-Prometheus-Plugin/1"}
        if username:
            token = base64.b64encode((username + ":" + (password or "")).encode()).decode()
            headers["Authorization"] = "Basic " + token
        request = Request(query_url, headers=headers)
        context = ssl.create_default_context() if config.get("verify_tls", True) else ssl._create_unverified_context()
        try:
            with urlopen(request, timeout=8, context=context) as response:
                body = response.read(2_097_153)
        except HTTPError as exc:
            raise RuntimeError("Prometheus returned HTTP " + str(exc.code)) from exc
        except (URLError, TimeoutError, ssl.SSLError) as exc:
            raise RuntimeError("Could not reach the Prometheus query API") from exc
        if len(body) > 2_097_152:
            raise RuntimeError("Prometheus response exceeded the 2 MiB limit")
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Prometheus returned invalid JSON") from exc
        if payload.get("status") != "success":
            raise RuntimeError("Prometheus query failed")
        result = payload.get("data", {}).get("result")
        if not isinstance(result, list) or len(result) > 1000:
            raise RuntimeError("Prometheus query result must contain at most 1000 vector samples")
        return result

    def collect(self, config, username=None, password=None):
        samples = self._query(config, username, password)
        resources = []
        for sample in samples:
            if not isinstance(sample, dict) or not isinstance(sample.get("metric"), dict):
                continue
            pair = sample.get("value")
            if not isinstance(pair, list) or len(pair) != 2:
                continue
            try:
                value = float(pair[1])
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value):
                continue
            labels = sample["metric"]
            metric_name = str(labels.get("__name__") or "sample")
            identity_data = json.dumps(labels, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            identity = metric_name + ":" + hashlib.sha256(identity_data.encode()).hexdigest()[:24]
            name = str(labels.get("instance") or labels.get("job") or metric_name)
            if metric_name == "up":
                state, health = ("online", "healthy") if value > 0 else ("offline", "offline")
            else:
                state, health = "observed", "unknown"
            resources.append({
                "identity": identity,
                "name": name + " · " + metric_name,
                "asset_type": "prometheus_sample",
                "state": state,
                "health": health,
                "metrics": {"value": value},
                "labels": labels,
            })
        return resources

    def test(self, config, username=None, password=None):
        samples = self._query(config, username, password)
        return {"message": "Prometheus query succeeded; received " + str(len(samples)) + " samples"}


def create_plugin():
    return PrometheusPlugin()
