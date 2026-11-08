import io
import json
import shlex

import paramiko

from app.connectors.base import BaseConnector


class SSHConnector(BaseConnector):
    name = "ssh"
    connector_type = "polling"

    def _connect(self, host: str, username: str, secret: str, port: int, credential_type: str):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        options = {
            "hostname": host,
            "username": username,
            "port": port,
            "timeout": 10,
            "banner_timeout": 10,
            "auth_timeout": 10,
            "look_for_keys": False,
            "allow_agent": False,
        }
        if credential_type == "ssh_private_key":
            error = None
            for key_type in (paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey):
                try:
                    key = key_type.from_private_key(io.StringIO(secret))
                    client.connect(pkey=key, **options)
                    return client
                except paramiko.SSHException as exc:
                    error = exc
            raise ValueError(f"Unsupported or invalid private key: {error}")
        client.connect(password=secret, **options)
        return client

    def discover(
        self, host: str, username: str, password: str, port: int = 22,
        credential_type: str = "ssh_password",
    ):
        client = self._connect(host, username, password, port, credential_type)
        try:
            _stdin, stdout, _stderr = client.exec_command("uname -srmo && hostname && uptime -p")
            lines = stdout.read().decode(errors="replace").strip().splitlines()
            return self.emit_event(
                "ssh.discovered",
                {
                    "hostname": lines[1] if len(lines) > 1 else host,
                    "ip": host,
                    "os": lines[0] if lines else "Unknown Linux",
                    "uptime": lines[2] if len(lines) > 2 else "Unknown",
                    "port": port,
                    "credential_type": credential_type,
                },
            )
        finally:
            client.close()

    def health_metrics(
        self, host: str, username: str, secret: str, port: int = 22,
        credential_type: str = "ssh_password",
    ) -> dict:
        script = (
            "import json,os,platform,shutil;from pathlib import Path;"
            "m={};[m.__setitem__(k,int(v.strip().split()[0])*1024) "
            "for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())];"
            "t=m.get('MemTotal',0);a=m.get('MemAvailable',0);d=shutil.disk_usage('/');"
            "print(json.dumps({'hostname':platform.node(),'os':platform.platform(),"
            "'uptime_seconds':int(float(Path('/proc/uptime').read_text().split()[0])),"
            "'cpu_load_1m':os.getloadavg()[0],'cpu_count':os.cpu_count() or 1,"
            "'memory_total_bytes':t,'memory_used_percent':round((t-a)/t*100,1) if t else 0,"
            "'disk_root_used_percent':round(d.used/d.total*100,1)}))"
        )
        client = self._connect(host, username, secret, port, credential_type)
        try:
            _stdin, stdout, stderr = client.exec_command(f"python3 -c {shlex.quote(script)}", timeout=10)
            output = stdout.read().decode(errors="replace").strip()
            error = stderr.read().decode(errors="replace").strip()
            if not output:
                raise RuntimeError(error or "No health response from SSH host")
            return json.loads(output)
        finally:
            client.close()

    def health_check(self, host: str, username: str, password: str, port: int = 22):
        try:
            client = self._connect(host, username, password, port, "ssh_password")
            client.close()
            return {"status": "healthy"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}
