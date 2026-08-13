# MCP — the wire, and what moved under it

**Load this when:** you are writing an MCP server or client, debugging a handshake, or
deciding which primitive a capability belongs in.

**Spec pinned:** MCP revision `2026-07-28` from `modelcontextprotocol.io/specification/latest` · read 2026-08-13

**Re-verify before locking a contract.** Fetch the URL above and check which revision it
serves now. The rest of this file tells you *what to look for*; it is not the document.

## Contents

- What MCP is, and the two layers
- The change that breaks old code: stateless, and `server/discover`
- Server primitives — tools, resources, prompts
- Client primitives — elicitation, and the MRTR pattern
- The deprecation register
- Notifications are opt-in now
- Caching
- Transports and authorization
- Extensions
- Traps

## What MCP is, and the two layers

MCP connects an **AI application to capability providers**. Three participants: a **host**
(the AI application), a **client** (one per server, owned by the host), and a **server** (the
program providing context or capability). One host runs many clients; one remote server
serves many clients.

Two layers, and keeping them apart saves an argument later:

| Layer | What it defines |
|---|---|
| **Data** | the JSON-RPC 2.0 protocol: discovery, primitives, notifications |
| **Transport** | the channel, framing and authorization: stdio or Streamable HTTP |

The same JSON-RPC message shape rides both transports. A bug is almost always in one layer
or the other, and naming which one first is half the debugging.

## The change that breaks old code: stateless, and `server/discover`

This is the single most important paragraph in this file, because every model trained before
2026-07-28 gets it wrong with total confidence.

**MCP is a stateless protocol.** The specification's own summary line reads *"Stateless,
self-contained requests. Per-request capability negotiation."* There is no session the server
infers things from. Every request carries what the server needs, in `_meta`:

```json
{
  "jsonrpc": "2.0", "id": 1, "method": "tools/list",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientInfo": { "name": "example-client", "version": "1.0.0" },
      "io.modelcontextprotocol/clientCapabilities": { "elicitation": {} }
    }
  }
}
```

**There is no `initialize` handshake.** Discovery is a single request, `server/discover`,
which every server **must** implement and a client **may** send before anything else:

```json
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "resultType": "complete",
    "supportedVersions": ["2026-07-28"],
    "capabilities": { "tools": { "listChanged": true }, "resources": {} },
    "_meta": { "io.modelcontextprotocol/serverInfo": { "name": "example-server", "version": "1.0.0" } },
    "ttlMs": 3600000, "cacheScope": "public"
  }
}
```

Because every request is self-describing, **calling `server/discover` is optional**: a client
may fire any request and handle the error if the version is unacceptable. A server that
cannot speak the requested version rejects with `UnsupportedProtocolVersionError`, listing
what it does support; the client retries on a mutually supported one. That error is a normal
path, not a crash.

**What this costs you if you get it wrong:** a client written to open with `initialize` and
then omit `_meta` from subsequent calls talks to nothing. It fails at the first request, not
at a subtle edge, which is the one mercy here.

## Server primitives — tools, resources, prompts

Three, and the useful distinction is **who decides to use each one**:

| Primitive | Controlled by | For | Methods |
|---|---|---|---|
| **Tools** | the **model** | actions — writes, API calls, queries | `tools/list`, `tools/call` |
| **Resources** | the **application** | read-only context — files, schemas, records | `resources/list`, `resources/templates/list`, `resources/read` |
| **Prompts** | the **user** | templated workflows, often surfaced as slash commands | `prompts/list`, `prompts/get` |

Getting this wrong is the most common design error in a first server: a "tool" that only
reads and that the model must be told not to call is a **resource**; a "resource" the model
is supposed to decide about is a **tool**.

**Tools.** `name` (unique within the server; prefer `calculator_arithmetic` over
`calculate`), `title` (human-readable), `description`, `inputSchema` (JSON Schema), and an
optional **`outputSchema`** — which is worth providing, because it is what lets a host
generate typed stubs for programmatic calling (`mcp-scale.md`).

**Tool errors do not arrive as transport failures.** A failed tool returns a *successful*
JSON-RPC response carrying `isError: true`. Client code that only catches transport
exceptions treats every tool failure as a success containing an apology.

**Resources** have a URI and a MIME type. Two discovery shapes: **direct** (`calendar://events/2024`)
and **templates** (`weather://forecast/{city}/{date}`), where templates carry `uriTemplate`,
`name`, `title`, `description`, `mimeType` and support parameter completion.

**Prompts** are user-invoked, never auto-triggered, and take declared `arguments`.

## Client primitives — elicitation, and the MRTR pattern

**One survives: elicitation.** Servers request information from the user mid-operation
instead of failing on missing input, via `elicitation/create`.

**Two modes, and the difference is a security rule, not a preference:**

- **Form mode** — the server sends a `requestedSchema`; the client renders a form and
  validates the response against it.
- **URL mode** — the server hands over a URL the user opens. The interaction happens out of
  band; its data never passes through the client or the model's context. The client learns
  only whether the user consented, and **never fetches the URL automatically**.

**Servers must not use form mode for passwords, API keys, access tokens or payment
credentials.** Those belong in URL mode, precisely so the secret never enters the client or
the LLM context. This is the one rule in this file most likely to be broken by an
implementation that "just works".

**Delivery is the Multi Round-Trip Requests (MRTR) pattern**, and it is not a callback. When
a server needs input while handling, say, `tools/call`, it answers with an
`InputRequiredResult` whose `inputRequests` carries the `elicitation/create` request. The
client gathers input and **retries the original request**, attaching `inputResponses` and
echoing back any `requestState` the server supplied. A second request id, the same logical
call.

## The deprecation register

Deprecated as of `2026-07-28` under the feature-lifecycle policy (SEP-2596). Deprecated means
*still in the spec, scheduled for removal*: new implementations **SHOULD NOT** adopt it.
Earliest removal for the 2026-07-28 batch is the first revision released on or after
**2027-07-28** — later removal is a maintainer decision.

| Feature | Deprecated in | Migrate to |
|---|---|---|
| **Sampling** (`sampling/createMessage`) | `2026-07-28` | integrate directly with LLM provider APIs |
| **Roots** (`roots/list`) | `2026-07-28` | pass directories/files via tool parameters, resource URIs, or server configuration |
| **Logging** (`notifications/message`) | `2026-07-28` | `stderr` for stdio; OpenTelemetry for observability |
| **Dynamic Client Registration** | `2026-07-28` | Client ID Metadata Documents |
| `includeContext: "thisServer"` / `"allServers"` | `2025-11-25` | omit the field, or `"none"` |
| **HTTP+SSE transport** | `2025-03-26` | Streamable HTTP |

**Why this table matters more than its length suggests.** Sampling and roots were, for a
year, the most-written-about parts of the client side — so they are exactly what a model
reaches for first. A server built today around sampling is built on a feature with a
published removal window.

Authoritative and updated: `https://modelcontextprotocol.io/specification/2026-07-28/deprecated`.

## Notifications are opt-in now

A server does not push because it feels like it. The client opens a long-lived stream with
`subscriptions/listen`, naming the event types it wants:

```json
{ "method": "subscriptions/listen",
  "params": { "notifications": { "toolsListChanged": true } } }
```

The server acknowledges with `notifications/subscriptions/acknowledged`, whose `notifications`
field reflects **the subset it agreed to honor** — unsupported types are simply omitted, so
read the acknowledgement rather than assuming. Every notification on that stream carries
`io.modelcontextprotocol/subscriptionId` in `_meta`, matching the JSON-RPC id of the
`subscriptions/listen` request.

Then: `notifications/tools/list_changed`, and for watched resources (requested via the
`resourceSubscriptions` filter) `notifications/resources/updated`.

**Two gates, not one.** A notification arrives only if the client asked *and* the server
declared the matching capability (`tools: {"listChanged": true}`). Either missing means
silence.

**Delivery is best-effort**, explicitly so, especially across transport reconnects. **Poll as
well.** A cache refreshed only by notifications goes stale the first time a connection drops
and never recovers.

## Caching

List results, `server/discover` and `resources/read` carry `ttlMs` (freshness hint, ms) and
`cacheScope` (who may reuse it — e.g. `"public"`). Honor them.

**One rule beats the TTL:** treat a cached list as stale the moment a `list_changed`
notification arrives, even if its TTL has not expired.

## Transports and authorization

| Transport | When | Notes |
|---|---|---|
| **stdio** | local process on the same machine | no network overhead; typically one client |
| **Streamable HTTP** | remote | HTTP POST client→server, optional SSE for streaming; typically many clients |

Streamable HTTP supports standard HTTP auth — bearer tokens, API keys, custom headers — and
**MCP recommends OAuth** for obtaining them. Note the deprecation above: Dynamic Client
Registration is on its way out in favour of Client ID Metadata Documents, so an OAuth
integration designed around DCR today is designed around a scheduled removal.

**HTTP+SSE as a transport is deprecated** (since `2025-03-26`) and is not the same thing as
Streamable HTTP's optional SSE streaming. Documentation and SDK examples still conflate them.

## Extensions

Opt-in, negotiated, and worth checking before inventing an equivalent:

- **Tasks** — a durable handle for long-running requests: poll for status, supply input
  mid-flight, retrieve the result later. This is the answer to "my tool takes ten minutes",
  and it exists so you do not hold a connection open or invent a job table.
- **MCP Apps** — interactive UI rendered inline in the conversation.
- **Skills over MCP** — structured instruction sets discovered and consumed through MCP,
  which is how a server ships Agent Skills rather than only tools.

## Traps

- **Writing the client against a remembered handshake.** Covered above; it is the big one.
- **Treating `isError: true` as success.** It arrives inside a 200.
- **A tool named for the verb, not the domain.** `search` collides the moment a second
  server is connected; `flights_search` does not. Federation makes this expensive later
  (`gateway.md`).
- **Trusting tool output.** The specification is explicit that tool descriptions and
  annotations are **untrusted unless the server is trusted**. Output from a server is input
  to your agent, and it is attacker-controlled if the server is.
- **Consent designed as a checkbox.** The spec requires the host to obtain explicit user
  consent before invoking a tool and before exposing user data. A UI that pre-approves
  everything satisfies the letter and loses the point.
- **Assuming the SDK is current.** SDKs lag revisions. The wire is the contract; the SDK is
  a convenience that may still speak last year's.
