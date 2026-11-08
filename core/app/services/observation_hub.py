from fastapi import WebSocket

class ObservationHub:
    def __init__(self):
        self.clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, subprotocol: str | None = None):
        await websocket.accept(subprotocol=subprotocol)
        self.clients.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.clients.discard(websocket)

    async def broadcast(self, observation: dict):
        stale = []
        for websocket in tuple(self.clients):
            try:
                await websocket.send_json(observation)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)

observation_hub = ObservationHub()
