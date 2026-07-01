import paramiko


class SSHConnector:
    def discover(self, host: str, username: str, password: str, port: int = 22) -> dict:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10,
                banner_timeout=10,
                auth_timeout=10,
            )

            return {
                "hostname": self._run(client, "hostname"),
                "os": self._run(client, "cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'"),
                "kernel": self._run(client, "uname -r"),
                "architecture": self._run(client, "uname -m"),
                "cpu": self._run(client, "nproc"),
                "memory": self._run(client, "free -h | awk '/Mem:/ {print $2}'"),
                "uptime": self._run(client, "uptime -p"),
                "ip": host,
            }

        finally:
            client.close()

    def _run(self, client: paramiko.SSHClient, command: str) -> str:
        _stdin, stdout, stderr = client.exec_command(command, timeout=10)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        return output if output else error
