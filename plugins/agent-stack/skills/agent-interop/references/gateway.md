# The gateway layer — one controlled seam for agent traffic

**Load this when:** many clients meet many servers, tool access needs to differ per caller,
or somebody has asked who is allowed to call what and you cannot answer from one place.

**Spec pinned:** agentgateway `1.4.x` from `agentgateway.dev/docs/standalone/latest` · read 2026-08-13

Linux Foundation, Apache-2.0, written in Rust.

This file is **vendor-neutral first**: what a gateway for agent traffic must do, then
agentgateway as a named reference implementation. Swap the implementation and the first half
still holds.

## Contents

- Why an API gateway is not enough
- What a gateway must do
- Federation and the name-collision problem
- Where authorization belongs
- agentgateway, concretely
- Traps

## Why an API gateway is not enough

A conventional gateway assumes stateless request/response. Agent traffic breaks four of its
assumptions at once, and each break is a feature you would otherwise build by hand:

| Assumption | What agent traffic does |
|---|---|
| one request, one upstream | **multiplexes** across several tool servers and merges the result into one surface |
| the server answers when asked | servers **initiate** events — SSE streams, change notifications |
| the protocol is fixed | MCP and A2A **revise**, so the hop has to negotiate versions rather than pass bytes |
| authorization is per route | authorization is **per tool and per client**, inside one route |

There is also a threat class with no HTTP analogue: **tool tampering, tool shadowing, and
rug-pull** — where a server's advertised tools change after approval, or one server's tool
name shadows another's. A proxy that only forwards cannot see any of it happen.

## What a gateway must do

Independent of product:

1. **Terminate and re-establish the protocol**, not tunnel it — otherwise none of the rest is
   possible.
2. **Federate many servers behind one endpoint**, with a deliberate answer to name
   collisions.
3. **Carry server-initiated events** across the hop, including reconnects, without silently
   dropping subscriptions.
4. **Authorize per tool and per caller**, not per route.
5. **Pin and negotiate protocol revisions**, so one server upgrading does not break every
   client at once.
6. **Detect change in the advertised surface.** A tool set that changes after approval is the
   rug-pull; somebody has to notice.
7. **Emit one audit trail** across every hop, with the identity that made the call attached
   to it.
8. **Route model traffic too**, where the same seam fronts LLM providers — otherwise you run
   two proxies and two policies.

**The reason to want one at all:** without it, each of these lands in every client
separately, and the security answer becomes "it depends which client".

## Federation and the name-collision problem

Two servers, both exposing `search`. The model sees one name and the router picks by load
order — which is a coin flip that looks like a bug in the model.

The general answer is **namespacing at the federation point**, and the general trap is
**doing it inconsistently**, because tool names are what the model learned. A name that
changes between sessions invalidates every prompt, cache and eval that referenced it.

agentgateway's shape, as a concrete instance: multiple **targets** combine into one backend —
"Virtual MCP" — with tool names prefixed by target name (`time_get_current_time`,
`everything_echo`), controlled by `prefixMode`:

| `prefixMode` | Behaviour |
|---|---|
| `conditional` *(default)* | prefix only when the backend has more than one target |
| `always` | prefix even with a single target |
| `never` | never prefix — names must already be unique, or initialization fails |

**`conditional` is a friendly default and a latent break.** Add a second target and every
tool name in the first one changes. If anything persists tool names — a prompt, a cached
plan, an eval fixture — choose `always` up front and pay the ugliness once.

```yaml
backends:
  - mcp:
      targets:
        - name: time
          stdio:
            cmd: uvx
            args: ["--with", "mcp<2", "mcp-server-time"]
        - name: everything
          stdio:
            cmd: npx
            args: ["@modelcontextprotocol/server-everything"]
```

## Where authorization belongs

**At the gateway, and again at each hop.** A gateway is the right place to express "this
client may call these tools" because it is the one place that sees every call. It is the
wrong place to make it the *only* check, because a server reachable by any other path is
unprotected.

Two rules that survive any product choice:

- **Policy per hop, not only at the entrance.** A chain of agents passes context onward, and
  authority does not automatically travel with it.
- **The gateway sees the calls, not the intent.** It can enforce that a tool may be called;
  it cannot tell whether the model was manipulated into calling it. Content inspection is
  probabilistic — anything consequential needs a deterministic limit or a human. See
  `agent-orchestrator/references/governance.md`.

## agentgateway, concretely

A unified HTTP and gRPC proxy written in Rust — a control plane and a data plane — under the
Linux Foundation, Apache-2.0. It covers three planes at once:

| Plane | What it does |
|---|---|
| **LLM providers** | OpenAI-compatible routing across 20+ providers (OpenAI, Anthropic, Bedrock, Azure, Gemini, Cohere, Ollama, …) |
| **MCP** | tool federation across many servers, per-client authorization |
| **A2A** | inter-agent calls, capability discovery |

**Local configuration — and read this before copying an example.** The current top-level keys
are `config`, `gateways`, `routes` / `tcpRoutes`, `llm`, `mcp`, `ui`, plus `services` /
`workloads` for advanced backends. **`binds` is the deprecated predecessor to `gateways`** —
and the project's own overview page still introduces it, which is exactly the kind of drift
this skill's rule zero exists for. A minimal MCP config:

```yaml
mcp:
  port: 3000
  targets:
    - name: everything
      stdio:
        cmd: npx
```

**Security policies** available as first-class config: JWT authentication, API-key
authentication, HTTP authorization, external authorization, and **MCP-specific
authorization** — the last being the per-tool control that a generic gateway lacks.

**On Kubernetes** it is conformant to the **Gateway API** — `HTTPRoute`, `GRPCRoute`,
`TCPRoute`, `TLSRoute` — so it uses standard resources rather than a proprietary CRD set.
That is the strongest single argument for it in a cluster that already runs Gateway API: the
routing objects are ones your platform team already reviews.

## Traps

- **Introducing a gateway and leaving the direct paths open.** The policy is then advisory.
- **`prefixMode: conditional` plus a second target**, silently renaming every tool.
- **Copying a config from a blog post.** `binds` versus `gateways` is a live example; the
  config surface moves faster than the articles.
- **Treating the gateway as the security boundary.** It is *a* boundary. The sandbox, the
  credentials and the per-hop policy are the others.
- **Federating servers you do not trust into one namespace.** Federation makes a hostile
  server's tools look exactly as legitimate as everyone else's.
- **Forgetting the reconnect.** MCP notification delivery is best-effort; a hop in the middle
  makes a dropped subscription more likely, not less. Poll as well.
