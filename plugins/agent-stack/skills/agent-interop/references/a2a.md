# A2A — when the other side is an agent, not a tool

**Load this when:** you are delegating an outcome to somebody else's autonomous agent,
publishing your own as callable, or choosing between A2A and MCP.

**Spec pinned:** A2A **v1.0**, `https://a2a-protocol.org/latest/specification/` · read 2026-08-13

Governance: created by Google, transferred to the **Linux Foundation**, Apache-2.0, run by a
Technical Steering Committee with AWS, Cisco, Google, IBM Research, Microsoft, Salesforce,
SAP and ServiceNow.

**The v0.x → v1.0 rename is the trap here.** The wire surface changed names between them, and
plenty of SDKs, tutorials and blog posts still document v0.3. A document that mixes the two
is wrong against at least one of them. Check every field name against the version you target.

## Contents

- The five design principles, and what each one bought
- The object model
- Discovery — the agent card
- The task lifecycle
- Three protocol bindings
- Getting results back
- Security
- Traps

## The five design principles, and what each one bought

Stated at announcement, and each is visible in the protocol:

| Principle | What it produced |
|---|---|
| **Embrace agentic capabilities** | agents collaborate without shared memory, tools or context — the peer is opaque by design |
| **Build on existing standards** | HTTP, SSE, JSON-RPC rather than a novel transport |
| **Secure by default** | enterprise authentication and authorization, aligned with OpenAPI's auth schemes |
| **Support for long-running tasks** | a task lifecycle that spans hours or days, with progress reported |
| **Modality agnostic** | parts carry more than text — audio, video, binary, structured data |

**The first one is the design decision that matters.** A2A's peer is deliberately a black
box: you send an outcome, not a plan. If your design needs to see inside the other agent,
A2A is the wrong protocol and you probably want an MCP server.

## The object model

| Object | What it is | Key fields |
|---|---|---|
| **AgentCard** | JSON metadata describing identity, capabilities, endpoint, skills and auth requirements | name, description, version, provider, capabilities, skills, security schemes |
| **Task** | a **stateful unit of work** with a unique id and a lifecycle | `id`, `contextId`, `status`, `artifacts`, `history`, `metadata` |
| **Message** | one turn of communication | `role` (`user` or `agent`), parts |
| **Part** | the fundamental content container inside messages and artifacts | one of `text`, `raw` (bytes), `url`, `data` (JSON); plus optional `mediaType`, `filename`, `metadata` |
| **Artifact** | a tangible output produced during a task | `artifactId`, human-readable name, one or more parts |

**`contextId` is the piece people miss.** It is server-generated and groups multiple related
tasks across interactions — the thing that makes a sequence of delegations one conversation
rather than a pile of unrelated jobs.

**`skills[]` on an agent card is not an Agent Skills `SKILL.md`.** A2A borrowed the word
for *an advertised capability of a remote agent* — `id`, `name`, `description`, `tags`,
`examples`, `inputModes`, `outputModes`. Agent Skills are instruction folders loaded into a
model's context. Two unrelated things, one word. Keep them apart in anything you write, or
every reader loses an hour.

## Discovery — the agent card

The standard location, following RFC 8615:

```
https://{agent-server-domain}/.well-known/agent-card.json
```

**Pre-0.3 deployments served `/.well-known/agent.json`** — expect both in the wild.

Top-level card fields in 1.0 — confirm against the live schema before implementing:
`name`, `description`, `version`, `provider`, `iconUrl`, `documentationUrl`,
`supportedInterfaces`, `capabilities`, `securitySchemes`, `securityRequirements`,
`defaultInputModes`, `defaultOutputModes`, `skills`, `extensions`, `signatures`.

**`capabilities` gates what you may attempt** — `streaming`, `pushNotifications`,
`extendedAgentCard`, `extensions`. Read it and branch; never assume streaming or push
exists because the docs describe them.

**Cards can be signed.** An unsigned card at a well-known URI is a claim, not proof —
verify `signatures` whenever the peer is not first-party.

A plain HTTP GET returns the card. Four discovery strategies exist, and they are not equal:

1. **Well-known URI** — the standard, and what you should publish.
2. **Authenticated extended cards** — fetched via `GetExtendedAgentCard`. This is the
   recommended way to expose sensitive capability information: **selective disclosure by
   client permission**, rather than a static public card carrying secrets.
3. **Curated registries** — catalogues queryable by skill, tag or provider. Note the honest
   gap: **the current specification does not prescribe a standard API for them**, so anything
   you build against one is vendor-specific.
4. **Direct configuration** — hardcoded URLs. Fine for a fixed pair of agents, and it does
   not scale or standardize.

**Never put a secret in the public card.** That is what the extended card exists for.

## The task lifecycle

The enum, spelled exactly as the specification defines it:

```
TASK_STATE_UNSPECIFIED
TASK_STATE_SUBMITTED
TASK_STATE_WORKING
TASK_STATE_INPUT_REQUIRED     <- interrupted, awaiting the client
TASK_STATE_AUTH_REQUIRED      <- interrupted, awaiting credentials
TASK_STATE_COMPLETED          <- terminal
TASK_STATE_CANCELED           <- terminal
TASK_STATE_REJECTED           <- terminal
TASK_STATE_FAILED             <- terminal
```

**Terminal means terminal: a task that reached completed, canceled, rejected or failed cannot
restart.** Continuing work means a *new* task, linked by `contextId`. Client code that
retries by re-sending to the same `taskId` after a failure is coding against a state machine
that does not exist.

**Interrupted is not failed.** `INPUT_REQUIRED` and `AUTH_REQUIRED` are the protocol asking
you for something and holding the work open. A client that treats every non-`COMPLETED`
status as an error abandons tasks that were waiting for one field.

## Three protocol bindings

The specification defines three, and an agent may implement any of them:

| Binding | Section | Use when |
|---|---|---|
| **JSON-RPC** | §9 | the default; broadest tooling |
| **gRPC** | §10 | you already run gRPC and want streaming and typed stubs |
| **HTTP+JSON/REST** | §11 | plain REST clients, easiest to inspect and curl |

**A server declares which bindings it supports on its card; the client picks one.**

| Functionality | JSON-RPC / gRPC | REST |
|---|---|---|
| Send message | `SendMessage` | `POST /message:send` |
| Send streaming message | `SendStreamingMessage` | `POST /message:stream` |
| Get task | `GetTask` | `GET /tasks/{id}` |
| List tasks | `ListTasks` | `GET /tasks` |
| Cancel task | `CancelTask` | `POST /tasks/{id}:cancel` |
| Subscribe to task | `SubscribeToTask` | `POST /tasks/{id}:subscribe` |
| Create push config | `CreateTaskPushNotificationConfig` | `POST /tasks/{id}/pushNotificationConfigs` |
| Get push config | `GetTaskPushNotificationConfig` | `GET /tasks/{id}/pushNotificationConfigs/{configId}` |
| List push configs | `ListTaskPushNotificationConfigs` | `GET /tasks/{id}/pushNotificationConfigs` |
| Delete push config | `DeleteTaskPushNotificationConfig` | `DELETE /tasks/{id}/pushNotificationConfigs/{configId}` |
| Extended card | `GetExtendedAgentCard` | `GET /extendedAgentCard` |

**The v0.3.x names, so you recognize inherited code on sight:** slash-style JSON-RPC methods
— `message/send`, `message/stream`, `tasks/get`, `tasks/cancel`, `tasks/resubscribe`,
`tasks/pushNotificationConfig/{set,get,list,delete}`,
`agent/getAuthenticatedExtendedCard`. If you meet those, it is a **v0.x client**. Do not
"fix" the names to 1.0 without moving the whole contract — half-migrated is worse than
either version, and it works until it reaches the one field nobody updated.

The same drift runs through the states: 1.0 uses proto-style constants
(`TASK_STATE_COMPLETED`), v0.x used lowercase wire values (`submitted`, `working`,
`input-required`). A document showing both has been half-migrated.

## Getting results back

Three mechanisms, matched to how long the work takes and whether you can hold a connection:

| Mechanism | Shape | Right when |
|---|---|---|
| **Request/response with polling** | `SendMessage`, then `GetTask` on an interval | always available; work measured in seconds to minutes |
| **Streaming (SSE)** | `SendStreamingMessage` / `SubscribeToTask`; needs `capabilities.streaming` | you want incremental output and can hold the connection |
| **Push notifications** | server calls a webhook you registered; needs `capabilities.pushNotifications` | work spans hours or days, or the client is not always up |

Stream events are typed: `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent`.

**Push is the one that makes long-running real.** Streaming dies with the connection;
polling for six hours is a poor use of everyone's time. If your delegated work can outlive a
request, register a push config and design for the callback.

**Design for all three failing.** A long task whose stream drops must be recoverable **by
id** — which is precisely why A2A gives tasks ids and states instead of making them
fire-and-forget calls. Polling is the floor you fall back to.

## Security

- **Enterprise auth from the start** — the card declares its security schemes, aligned with
  OpenAPI's authentication approaches: API key, HTTP auth, OAuth2, OpenID Connect, mutual
  TLS. Read the card and satisfy what it declares; do not assume bearer tokens.
- **Scope the token to the task.** Authorization is per skill and per task; handing a peer
  a token broader than the work is how one delegation becomes an account compromise.
- **Verify card signatures for any peer that is not first-party.** A well-known URI proves
  where the file sits, not who wrote it.
- **`AUTH_REQUIRED` is a protocol state**, not an error path bolted on. Handle it.
- **The peer is opaque, and that cuts both ways.** You cannot verify how it reached its
  result, so anything it returns is untrusted input to your system — the same rule as tool
  output, with less recourse.
- **Trace across hops.** A chain of agents compounds errors, and policy has to be enforced at
  **each hop**, not only at the entrance. See `agent-orchestrator/references/governance.md`
  for the control set; this file only says which wire it rides.

## Traps

- **Building against v0.3 field names** because that is what the tutorial showed. Check the
  version.
- **Retrying into a terminal task.** New task, same `contextId`.
- **Treating `INPUT_REQUIRED` as a failure.** It is a question.
- **Publishing capability detail in the public card** instead of the authenticated extended
  card.
- **Choosing A2A for something with a JSON schema and one call.** That is a tool. The cost of
  A2A is a lifecycle, a card and a state machine; pay it when the other side is genuinely
  autonomous.
- **Assuming a registry API is standard.** It is not, yet.
