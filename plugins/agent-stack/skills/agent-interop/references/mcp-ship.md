# Shipping an MCP server — mount it, and debug the client that cannot reach it

**Load this when:** the server is written and now has to reach someone — mounting it inside
an existing web app, or fixing a client that will not connect.

**Spec pinned:** MCP `2026-07-28` transports; FastMCP/Starlette mounting shapes · read 2026-08-13

`mcp.md` is the protocol. This file starts where that one stops, and covers the part that
is not in any specification: where the endpoint actually lands, and why the client says 404.
For **publishing** to the registry, see `registry.md`. For designing the tool set in the
first place, Anthropic's `mcp-server-dev` plugin is built for it and this file does not
repeat it.

## Contents

- Mounting into an existing web app
- Auth middleware and a health endpoint
- Client configuration
- Debugging a client that will not connect

## Mounting into an existing web app

The common production shape: you already run a FastAPI/Starlette app, and the MCP server
should live at `/mcp` on the same host. It is also where the single most common bug lives.

**The double-path pitfall.** FastMCP defaults its internal `streamable_http_path` to
`/mcp/`. Mount that app at `/mcp` and the real endpoint becomes `/mcp/mcp` — so every
client pointed at `/mcp` gets 404, and the SSE fallback 404s too, which reads like the
server is down.

```python
mcp = FastMCP(
    "my_server",
    streamable_http_path="/",   # REQUIRED when mounting as a sub-app
    stateless_http=True,
    json_response=True,
)

app.mount("/mcp", mcp.streamable_http_app())
```

Set `streamable_http_path="/"` whenever the app is mounted rather than served standalone.
Standalone servers keep the default.

## Auth middleware and a health endpoint

**Wrap the mounted ASGI app rather than adding auth inside tool handlers.** The transport
handshake happens before any tool runs, so handler-level auth leaves the protocol surface
open — an unauthenticated caller can still enumerate what you expose.

```python
class MCPAuthMiddleware:
    _PUBLIC_PATHS = {"/health"}

    def __init__(self, app, *, store):
        self._app, self._store = app, store

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self._app(scope, receive, send)
        if scope.get("path", "") in self._PUBLIC_PATHS:
            return await self._app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        auth = headers.get(b"authorization", b"").decode()
        if not auth.startswith("Bearer "):
            return await self._send_401(send, "Missing Bearer token")
        if not await self._store.validate_api_key(auth[7:]):
            return await self._send_401(send, "Invalid API key")
        return await self._app(scope, receive, send)

app.mount("/mcp", MCPAuthMiddleware(mcp.streamable_http_app(), store=key_store))
```

Keep a health endpoint **outside** the mount and exempt from auth. It is what tells "the app
is up, the MCP path is wrong" apart from "the app is down" — the two produce identical
client errors.

```python
@app.get("/mcp/health")
async def mcp_health():
    return {"status": "ok", "server": "my_server", "transport": "streamable-http"}
```

## Client configuration

Remote (Streamable HTTP):

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://example.com/mcp",
      "headers": { "Authorization": "Bearer ${MY_SERVER_KEY}" }
    }
  }
}
```

Local (stdio):

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["--directory", "/path/to/project", "run", "python", "-m", "my_server"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

**Ship both forms in your README.** A user who has to derive the config from prose files an
issue instead.

## Debugging a client that will not connect

**404 — by far the most common.** Symptom: `Error POSTing to endpoint: Not Found`, then the
SSE fallback 404s as well. Bisect the path directly:

```bash
curl -X POST https://your-host/mcp/     -H 'Content-Type: application/json' -d '{}'
curl -X POST https://your-host/mcp      -H 'Content-Type: application/json' -d '{}'
curl -X POST https://your-host/mcp/mcp  -H 'Content-Type: application/json' -d '{}'
```

If `/mcp/mcp` answers — **even 401** — while `/mcp/` 404s, it is the double path. A 401 is a
*success* for this test: it proves routing reached the server.

**307.** Starlette redirects `/mcp` → `/mcp/`. Most clients follow it on POST; some do not,
and the failure looks like a hang. Either document the trailing slash or add an explicit
no-slash route.

**401.** Check the Bearer prefix and the key, then check that the client is actually sending
headers — several clients drop custom headers on the SSE fallback specifically, so the
initial POST authenticates and the stream does not.

**Version rejection.** Under `2026-07-28` a server that cannot speak the client's revision
answers `UnsupportedProtocolVersionError` listing what it does support. That is a readable
error, not a connection failure — read the list and retry on a common version rather than
treating it as the server being broken.
