---
name: agent-interop
description: >-
  Use when an agent must talk to something outside its own process — building or consuming an
  MCP server, exposing or calling another agent over A2A, publishing to the MCP Registry, or
  putting a gateway in front of agent traffic. Carries the MCP 2026-07-28 wire surface and what it
  deprecated (server/discover, stateless per-request _meta, elicitation in form and URL mode,
  subscriptions/listen; sampling, roots, logging and dynamic client registration going),
  A2A 1.0 agent cards, task states and three bindings, registry namespaces and server.json, tool
  federation, and what a gateway must do that an API gateway does not. Triggers - "MCP server",
  "MCP client", "A2A", "agent card", "agent interoperability", "MCP registry", "server.json",
  "agentgateway", "tool federation", "MCP-сервер", "карточка агента", "интероперабельность
  агентов", "реестр MCP", "шлюз для агентов". Not for designing one server's tool set, nor for
  a skill's own construction — that is make-skill.
---

# Agent interop — the protocols an agent speaks outside its own process

`agent-orchestrator` builds the loop. `agent-evals` proves it behaves. This skill covers
everything the loop reaches that is **not in its process**: a tool server, a peer agent, a
registry, and the gateway between them.

---

## Rule zero — a protocol claim without a date is a guess

Every one of these specifications moved in the twelve months before **2026-08-13** — the
date every reference below was read — and each moved in a way that silently breaks code
written against the previous revision. Concretely, and each one measured on that date
against the live specification rather than recalled:

- MCP replaced the `initialize` handshake with `server/discover` and made the protocol
  **stateless**; a client that opens with `initialize` is speaking a revision that is on its
  way out.
- MCP **deprecated `sampling`, `roots` and `logging`** — three things an older model will
  reach for first, because for a year they were the interesting part of the client side.
- A2A renamed its wire surface between v0.x and v1.0, and SDKs and blog posts still
  documented v0.3 as of 2026-08-13.
- agentgateway **deprecated `binds`** in favour of `gateways` — while its own overview page
  still introduced `binds` as a core concept as of 2026-08-13.

So: **every reference in this skill opens with a `**Spec pinned:**` line**, and
`test/validate.py` fails the build without one. That is a mechanical check, not an
aspiration — the class of error it prevents is the one where prose reads as current
because nothing on the page says otherwise.

**Before you write wire-level code, fetch the spec.** These references tell you what to look
for and what changed; they are not a substitute for the document. Read the pinned revision,
then check whether a newer one exists. Every entry in the link map below is fetchable.

---

## Which protocol answers which question

| The question you actually have | The answer | Where |
|---|---|---|
| I want to give a model a capability against a live system | **MCP server** | `references/mcp.md` |
| My server is written and the client cannot connect to it | mounting and transports | `references/mcp-ship.md` |
| I want my application to consume other people's tool servers | **MCP client** | `references/mcp.md`, then `references/mcp-scale.md` |
| I have more servers than fit in a context window | client scaling patterns | `references/mcp-scale.md` |
| I want another team's *autonomous agent* to accomplish an outcome for me | **A2A** | `references/a2a.md` |
| I want my agent discoverable and callable by other agents | **A2A agent card** | `references/a2a.md` |
| I want people to find and install my MCP server | **MCP Registry** | `references/registry.md` |
| I have many servers, many clients, and a security team | **a gateway** | `references/gateway.md` |

**The one-line rule between the two big ones.** MCP connects a model to a *capability* you
control the shape of; A2A connects you to a *peer* whose insides you deliberately cannot
see. The official framing is exact and worth keeping: *"A2A is about agents partnering on
tasks, while MCP is more about agents using capabilities."* Real systems run both — an A2A
server whose internals speak MCP — and that is the recommended architecture, not a
compromise.

**The tell that you picked wrong:** if you find yourself inventing a task lifecycle, a
progress channel and a resumable handle on top of `tools/call`, you wanted A2A. If you find
yourself publishing an agent card for something that is one HTTP call with a JSON schema,
you wanted MCP.

---

## References

Each file opens with its own **Load this when** line and its revision stamp. This table is
an index; the trigger lives in the file, so the two cannot drift apart.

| File | Read it when |
|---|---|
| [`references/mcp.md`](references/mcp.md) | you are **building or calling an MCP server** — the layers, per-request `_meta`, `server/discover`, the three server primitives and the one surviving client primitive, notifications, caching, transports, and the full deprecation register |
| [`references/mcp-ship.md`](references/mcp-ship.md) | the server is written and **cannot be reached** — mounting inside an existing web app, transport-level auth, client config, and the 404 that is really a double path |
| [`references/mcp-scale.md`](references/mcp-scale.md) | the host has **more servers and tools than context** — progressive discovery, programmatic tool calling, cache interaction, and the security surface each one opens |
| [`references/a2a.md`](references/a2a.md) | the other side is **another agent, not a tool** — agent cards and discovery, the task lifecycle and its terminal states, three protocol bindings, streaming versus push |
| [`references/registry.md`](references/registry.md) | you are **publishing a server** or building something that consumes the registry — `server.json`, reverse-DNS namespaces and how ownership is proved, the publish flow, and the registry's three refusals |
| [`references/gateway.md`](references/gateway.md) | agent traffic needs **one controlled seam** — what a gateway must do that an API gateway does not, federation and name collisions, and where authorization actually belongs |

---

## Boundaries — what this skill is not

**Against `make-skill`.** `make-skill` owns the *skill author's* view: whether a job wants a
skill or a server at all, declaring a server dependency in `compatibility`, and the fact that
tool names differ per host (`mcp__<server>__<tool>` in Claude Code, `mcp__plugin_<plugin>_<server>__<tool>`
for a plugin's own server). **This skill owns the wire.** If the question is "what does the
protocol say", it is here; if it is "how does my skill declare that it needs one", it is
there. The protocol is described in exactly one of the two places, and this is it.

**Against `agent-orchestrator`.** That skill routes between *model providers* and manages the
loop's own context. This one routes between *processes*. They meet at exactly one point: an
orchestrator that federates many MCP servers is subject to `references/mcp-scale.md`, and one
that fronts them with a proxy is subject to `references/gateway.md`.

**Against `agent-orchestrator/references/governance.md`.** That file decides *whether* a
boundary may be crossed and what an audit row must carry to prove a control was applied. This
skill describes *how* the crossing is spoken. Permission there, protocol here.

**Not covered at all:** designing the tool set of one server (what tools, what schemas, what
descriptions — that is a design problem, and Anthropic's `mcp-server-dev` plugin is built for
it); prompt wording; a single LLM call in a script.

---

## The neighbourhood — one verdict each

Named so an agent stops guessing, with the verdict stated rather than implied.
**Verdicts as of 2026-08-13**, the day this skill's references were pinned — this ground
moves, so re-verify anything marked *watch* before building on it.

| Thing | What it actually is | Verdict |
|---|---|---|
| **Agent Skills** (`agentskills.io`) | the open `SKILL.md` format this very file is written in — originally Anthropic's, now an open standard with wide client adoption | **Adopt, but not here.** The family owns it in `make-skill`. Relevant to interop in one way: MCP has a *Skills over MCP* extension, so a server can ship skills — see `references/mcp.md` |
| **ACP** (IBM's Agent Communication Protocol) | a former A2A competitor | **Dead as a choice.** Merged into A2A under LF AI & Data on 2025-08-29; its team stopped developing it. If you meet ACP in a doc, the answer today is A2A |
| **AGNTCY** (Cisco/Outshift → Linux Foundation, July 2025) | *not* an A2A rival — an infrastructure stack around multi-agent systems: OASF discovery, agent identity, SLIM messaging, observability. It archived its own competing protocol | **Orthogonal.** Evaluate it for identity and observability if you run many agents; it does not replace A2A or MCP |
| **AP2** (Agent Payments Protocol) | Google's payments extension **for A2A**, standardising through FIDO Alliance working groups. Signs intent as Verifiable Digital Credentials — Checkout Mandates and Payment Mandates, each with an Open and a Closed stage | **Watch, do not build on it yet.** Explicitly in progress rather than production-ready. It is the right shape for the problem — proving *this user authorized this purchase* — so track it if an agent will ever spend money |
| **"ChatGPT apps" / OpenAI's plugin surface** | checked, and it is **not a separate protocol**: an MCP server, plus Agent Skills for the workflows, plus optional UI | **Nothing new to learn.** Build the MCP server; the host packaging is the host's |
| **MCP extensions** — Tasks, MCP Apps, Skills over MCP | opt-in additions to the core protocol, negotiated per connection | **Read before inventing.** Long-running work has a durable-handle answer already; see `references/mcp.md` |

---

## The link map — where to go and read

Nothing here is summarised well enough to build against. These are the documents.

| Read | For | URL |
|---|---|---|
| MCP specification (current) | the normative requirements; always check the revision it serves | `https://modelcontextprotocol.io/specification/latest` |
| MCP architecture | the two layers, statelessness, the discovery exchange with real JSON | `https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture` |
| MCP server concepts | tools, resources, resource templates, prompts — who controls each | `https://modelcontextprotocol.io/docs/2026-07-28/learn/server-concepts` |
| MCP client concepts | elicitation's two modes and the MRTR pattern; the deprecated client features | `https://modelcontextprotocol.io/docs/2026-07-28/learn/client-concepts` |
| **MCP deprecation register** | the authoritative list of what is on the way out and its earliest removal | `https://modelcontextprotocol.io/specification/2026-07-28/deprecated` |
| MCP client best practices | progressive discovery and code mode, with the numbers | `https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices` |
| Build a server / build a client | the SDK-level walkthroughs | `https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server`, `…/build-client` |
| MCP + Agent Skills | how skills and servers compose, and the `mcp-server-dev` plugin | `https://modelcontextprotocol.io/docs/2026-07-28/develop/build-with-agent-skills` |
| MCP registry — about, quickstart | what it is, and the exact publish flow | `https://modelcontextprotocol.io/registry/about`, `https://modelcontextprotocol.io/registry/quickstart` |
| MCP docs index for machines | fetch this first if you are an agent exploring | `https://modelcontextprotocol.io/llms.txt` |
| A2A home and specification | v1.0, the three bindings, the normative surface | `https://a2a-protocol.org/latest/`, `https://a2a-protocol.org/latest/specification/` |
| A2A key concepts / life of a task / discovery | the object model, the lifecycle, the well-known URI | `https://a2a-protocol.org/latest/topics/key-concepts/`, `…/life-of-a-task/`, `…/agent-discovery/` |
| A2A and MCP | the official statement of how they divide | `https://a2a-protocol.org/latest/topics/a2a-and-mcp/` |
| agentgateway — standalone, Kubernetes | the config model, and the Gateway API story | `https://agentgateway.dev/docs/standalone/latest/`, `https://agentgateway.dev/docs/kubernetes/latest/` |
| Source repositories | when the docs are behind the code | `https://github.com/a2aproject/A2A`, `https://github.com/modelcontextprotocol/modelcontextprotocol`, `https://github.com/modelcontextprotocol/registry`, `https://github.com/agentgateway/agentgateway` |

**Fetch the `llms.txt` first when you are an agent.** Both `modelcontextprotocol.io` and
`agentgateway.dev` publish one, and both are versioned per docs release — which is how you
find the page that exists rather than the page you remember.

---

## Checklist — shipping anything that speaks these protocols

- [ ] The revision you build against is **written down** — in `compatibility`, a constant, or a README line
- [ ] You read the deprecation register before using a client feature
- [ ] Version mismatch has a handled path, not a crash
- [ ] Tool output is treated as **untrusted input**, including output from your own servers
- [ ] Nothing secret is requested through an elicitation form — that is URL mode's job
- [ ] Long-running work uses a durable handle rather than a held connection
- [ ] If you federate: name collisions are resolved deliberately, not by load order
- [ ] If you publish: the namespace is one you can prove you own
- [ ] Authorization is enforced per hop, not only at the entrance
