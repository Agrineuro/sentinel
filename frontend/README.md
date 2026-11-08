# Sentinel UI Starter — functional integration build

## Run
```bash
npm install
npm run dev
```

## New functionality
- Working sidebar navigation
- Overview, full graph, observations, and settings screens
- Persistent settings in browser localStorage
- Configurable REST API and observation WebSocket URLs
- Backend connection tester
- Automatic API refresh every 30 seconds
- WebSocket reconnect support
- Searchable observation feed and raw-event inspector
- Visible backend/fallback connection state

## Expected backend routes
The frontend currently expects:
- `GET /api/health`
- `GET /api/observations?limit=50`
- `GET /api/connectors`
- `WS /ws/observations`

The client normalizes several common field names, so the exact response shape can vary slightly. Once Sentinel's current backend files are available, these adapters should be matched precisely to the real schemas.

## CORS
FastAPI must allow the Vite origin, commonly `http://192.168.1.192:5173` or the browser machine's URL.
