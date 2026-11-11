import re
import socket
import struct


class ModbusTcpPlugin:
    def _mapping(self, raw):
        mapping = {}
        for line_number, line in enumerate(str(raw).splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(r"(\d{1,5})\s*=\s*([A-Za-z0-9_.-]{1,80})", line)
            if not match:
                raise ValueError("Register map line " + str(line_number) + " must look like 0=water_temperature")
            address = int(match.group(1))
            if address > 65535 or address in mapping:
                raise ValueError("Register address is invalid or repeated")
            mapping[address] = match.group(2)
        if not mapping:
            raise ValueError("Add at least one holding register to the register map")
        if len(mapping) > 100:
            raise ValueError("Register map can contain at most 100 registers")
        return mapping

    def _read(self, host, port, unit, start, count):
        transaction = (start + count) & 0xffff
        request = struct.pack(">HHHBBHH", transaction, 0, 6, unit, 3, start, count)
        with socket.create_connection((host, port), timeout=4) as connection:
            connection.settimeout(4)
            connection.sendall(request)
            header = self._recv_exact(connection, 7)
            response_tx, protocol, length, response_unit = struct.unpack(">HHHB", header)
            if response_tx != transaction or protocol != 0 or response_unit != unit or length < 2 or length > 256:
                raise RuntimeError("Modbus TCP returned an invalid response header")
            pdu = self._recv_exact(connection, length - 1)
        function = pdu[0]
        if function == (3 | 0x80):
            raise RuntimeError("Modbus device returned exception code " + str(pdu[1] if len(pdu)>1 else 0))
        if function != 3 or len(pdu) < 2 or pdu[1] != count * 2 or len(pdu) != 2 + count * 2:
            raise RuntimeError("Modbus device returned an unexpected register response")
        return list(struct.unpack(">" + "H" * count, pdu[2:]))

    @staticmethod
    def _recv_exact(connection, size):
        chunks = []
        remaining = size
        while remaining:
            chunk = connection.recv(remaining)
            if not chunk:
                raise RuntimeError("Modbus device closed the connection")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def collect(self, config, username=None, password=None):
        host = str(config["host"]).strip()
        port = int(config.get("port", 502))
        unit = int(config.get("unit_id", 1))
        mapping = self._mapping(config.get("register_map", ""))
        metrics = {}
        for address, name in sorted(mapping.items()):
            metrics[name] = self._read(host, port, unit, address, 1)[0]
        return [{
            "identity": host + ":" + str(port) + ":" + str(unit),
            "name": "Modbus TCP: " + host,
            "asset_type": "modbus_tcp_device",
            "state": "online",
            "health": "healthy",
            "metrics": metrics,
            "labels": {"host": host, "port": port, "unit_id": unit},
        }]

    def test(self, config, username=None, password=None):
        rows = self.collect(config, username, password)
        return {"message": "Read " + str(len(rows[0]["metrics"])) + " Modbus holding registers"}


def create_plugin():
    return ModbusTcpPlugin()
