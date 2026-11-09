# A product's agent surface: one contract, its gates, its safety, its discovery

**Load this when:** a product (not an agent) must be usable by agents: exposing its functions
over MCP, an HTTP API or a CLI; an agent asks for an action a person must approve or perform;
outside agents need credentials; or a change may break what agents call.

**Spec pinned:** MCP revision `2026-07-28` (current per `modelcontextprotocol.io/specification/versioning`), OAuth 2.1 / MCP authorization; canon AN-1 to AN-10 of the sshlg-skills design `2026-11-09-ai-native` · read 2026-11-09

**Who owns what.** Tool shape (names, descriptions, schemas, error wording) is
`agent-harness/references/tools.md`. The wire is `mcp.md`. This file is the product layer
above both: which contract, which clients, which gates, which credentials. Every rule is
stated once in its home; elsewhere it is cited by `file:line`.

## Contents

- The canon index
- Profiles: `public`, `internal`, `library`
- AN-3: one contract, many clients
- The contract source, its snapshot, and the diff that classifies a change
- AN-7: the gate protocol
- AN-8: a safe surface
- Outbound events and webhooks
- Discovery
- CLI readiness
- Special cases
- Traps

## The canon index

Raw base: `https://raw.githubusercontent.com/ssheleg/<repo>/main/`. A companion that is not
installed is read through its raw URL.

| Id | Rule | Home | Raw path |
|---|---|---|---|
| AN-1 | Parity by story: every `must`/`should` story a person completes, an agent completes, acting and being notified; exceptions named per capability | super-ux `scenario-format.md`, "Contract v5: agents and capabilities" | `super-ux/main/plugins/super-ux/skills/references/scenario-format.md` |
| AN-2 | Design order: stories, capabilities, contract, logic, automation, human surfaces, look and words | super-ux `system-map.md` | `super-ux/main/plugins/super-ux/skills/references/system-map.md` |
| AN-3 | One contract, many clients | this file | `agent-stack/main/plugins/agent-stack/skills/agent-interop/references/agent-surface.md` |
| AN-4 | Why a person: `Gate` (`body`, `approval`, `legal`) and serving reasons, each with evidence | super-ux `scenario-format.md` | as AN-1 |
| AN-5 | The attention budget: decisions, exceptions, outcomes first | super-ux `ux-design-principles.md` | `super-ux/main/plugins/super-ux/skills/references/ux-design-principles.md` |
| AN-6 | Automation by default, callable, observable, stoppable | super-ux `system-map.md` | as AN-2 |
| AN-7 | The gate protocol | this file | as AN-3 |
| AN-8 | A safe surface | this file | as AN-3 |
| AN-9 | Discoverable and proven: proving call and contract tests gate; a cold agent run judges | mechanics: agent-stack `agent-evals/references/operability.md`; in the pipeline: task-pipeline `references/agent-surface.md` | `agent-stack/main/plugins/agent-stack/skills/agent-evals/references/operability.md`; `task-pipeline/main/plugins/task-pipeline/skills/task-pipeline/references/agent-surface.md` |
| AN-10 | Telemetry knows the actor (`actor`, `on_behalf_of`, `client_id` as properties) | the analytics agent's event catalogue guidance (request filed, no public home yet) | none |

A product's capabilities and their gates live in its `docs/ux/capabilities.md` (`CAP-NN`,
super-ux contract v5). This file reads that registry; it never defines a second one.

## Profiles: `public`, `internal`, `library`

| Profile | Callers | Owes |
|---|---|---|
| `public` | agents of people outside the organisation | everything below, with OAuth 2.1 per-client consent, published discovery, and the adversarial persona in `operability.md` |
| `internal` | the organisation's own agents and automations | AN-3, AN-7, AN-8 under the estate's binding (for Fabric: T0/T1/T2, `gateway.md:131-159`); no public client registration |
| `library` | code that imports it; no server | types, docs and doctests as the contract; the exported API as the snapshot where the toolchain emits one; no gate protocol, no credentials, no post-deploy call |

## AN-3: one contract, many clients

**Rule.** The human interface calls the same contract the agents call. A function reachable
only through a screen is a defect ("UI-only function", AN-2).

**Mechanical proxy.** The set of operations the frontend invokes is a subset of the agent
surface, or each extra one is marked `internal` with a reason.

- [ ] List the frontend's operations (API routes, RPC names, GraphQL operations) from code or
  the network log of a scripted session.
- [ ] List the agent surface from the snapshot (below).
- [ ] Every frontend operation not in the agent surface carries a marker beside its
  definition: `internal: <reason>`. Accepted reasons: a sync transport (offline replication),
  a render-only endpoint (thumbnails, layout data), a session-plumbing call (token refresh).
- [ ] A marker whose reason is a user action is not accepted: that action is a capability and
  owes a tool.

## The contract source, its snapshot, and the diff that classifies a change

**Source.** Schema-first, committed before the logic: MCP tool definitions with `inputSchema`,
`outputSchema` and annotations; an OpenAPI document; or a CLI spec. The code validates against
the source or is generated from it.

**Snapshot.** Generated from the running build, never hand-written; lints and diffs read it.

| Surface | Snapshot |
|---|---|
| MCP | the `tools/list` result (plus `resources/templates/list` and `prompts/list` where used) from a local stdio build, sorted by name, caching fields (`ttlMs`, `cacheScope`) removed |
| HTTP | the served OpenAPI document |
| CLI | `<cli> --help --json` for every command |

**Diff classes.** Compare the release candidate's snapshot with the last released one.

| Class | What the diff shows | Consequence |
|---|---|---|
| `none` | nothing | no contract change; nothing in this file is owed |
| `additive` | a new tool, a new optional input field, a new output field, a new event, a new error code on a new path | allowed inside a contract version; the capability row records `Since` |
| `breaking` | a tool removed or renamed; input narrowed (a new required field, an enum value removed, a type tightened); an output field removed or its meaning changed; an effect class widened; an auth scope or effect ceiling changed; an error code renamed | a new contract version and the deprecation path in AN-8; risk and stage gates are task-pipeline's (`references/agent-surface.md`) |

A description or an agent-facing error body that changed is a contract change too: agents read
it (`tools.md:48-76`). The diff names it `additive` unless it changes what a call means.

## AN-7: the gate protocol

**Rule.** A gated call is refused with a typed error naming the gate and carrying
`human_steps`; for a value the caller can supply, the server asks with MCP `input_required`
instead. The agent prepares everything, the person performs only the gate, the agent
continues. Gates and their evidence come from the capability row (AN-4).

**Which answer for which need.**

| Need | Answer |
|---|---|
| a value the caller has or can get (which invoice, a reason, a date) | MCP `input_required` (revision `2026-07-28` multi round-trip: the client retries the original request with the answers, `mcp.md:136-141`) |
| a secret, a payment card, a password | never a form field (`mcp.md:131-134`); a `body` gate with a URL |
| a person's decision (`approval`), the person's own body (`body`), a legal requirement (`legal`) | refusal with `human_steps` |
| work that outlives the request | a task under the extension `io.modelcontextprotocol/tasks` when negotiated, else a job handle (`mcp.md:216-249`) |

**Refusal shape** (an MCP tool error is a result with `isError: true`, `mcp.md:108-110`):

```json
{
  "isError": true,
  "structuredContent": { "error": {
    "code": "approval-required",
    "gate": "approval",
    "message": "Refunds above 200 EUR need a billing admin. Nothing was refunded.",
    "retryable": true,
    "human_steps": [{
      "action": "Approve refund of 500 EUR on invoice INV-1042",
      "url": "https://app.example.com/approvals/apr_7f3",
      "who": "billing-admin of org_19",
      "digest": "sha256:<RFC 8785 canonical JSON of the exact action>",
      "expires_at": "2026-11-10T12:00:00Z"
    }],
    "continue": { "tool": "billing_approval_get", "arguments": { "approval_id": "apr_7f3" },
                  "event": "approval.decided" }
  } }
}
```

- [ ] `code` comes from the refusal vocabulary (`gateway.md:251-255`) where one fits
  (`approval-required`); `gate` is always one of `body | approval | legal`.
- [ ] `human_steps[].url` opens the exact step, not a dashboard; the text a person reads goes
  through the product's copywriting route.
- [ ] `digest` binds the approval to the exact arguments (`gateway.md:240-249`); changed
  arguments need a new approval (`tools.md:130-133`).
- [ ] The agent continues by polling the named read or receiving the `Emits` event, then
  repeats the original call with the same idempotency key; the server consumes the approval
  once.
- [ ] **How the server knows the approval is genuine:** it reads its own approval record,
  written by the authenticated approver through the human surface, bound to digest, principal,
  callee and expiry. Nothing the agent sends proves an approval. `confirm: true` is a syntax
  guard, never an approval (`tools.md:127-133`).
- [ ] On an `internal` product, `approval` exists only with a recorded operator decision
  (AN-4); otherwise the delegated agent acts.

## AN-8: a safe surface

- [ ] **Credentials per client, scoped, revocable.** Outside agents: OAuth 2.1 / MCP
  authorization with consent per client. Client identity through Client ID Metadata Documents,
  not Dynamic Client Registration (deprecated, `mcp.md:155`, `mcp.md:208-211`). The client
  checks `iss` against the authorization server it expected before using a code or token. The
  Fabric T0/T1/T2 profile is one binding of this rule (tiers `gateway.md:131-159`, token and
  verification `gateway.md:182-213`).
- [ ] **Principal ceiling.** An agent's scope never exceeds the role of the person it acts for
  (`Roles` on the capability row); the server checks the principal's role on every call, not
  only at consent.
- [ ] **Effect classes declared** in the contract (annotations and `_meta`), using the effect
  vocabulary of `gateway.md:191`; annotations alone decide nothing (`tools.md:135-153`).
- [ ] **Idempotency key on every write.** A repeat with the same key returns the first result
  and causes no second effect; a repeat with the same key and other arguments is refused.
- [ ] **Dry-run or sandbox** for every write: `dry_run: true` returns the planned effect
  without causing it, or a test tenant mirrors production behaviour.
- [ ] **Audit row** per call with the actor chain (`sub` and `act`, `gateway.md:187-188`), the
  client id, the capability, the argument digest, the effect and the result (fields:
  `agent-orchestrator/references/governance.md:115-131`). On erasure the person's id is
  pseudonymised, the chain's shape is kept, and the person's agent grants are revoked.
- [ ] **Untrusted content marked.** Text written by third parties sits in fields the tool
  description names as untrusted (for example `untrusted_text`); the lethal trifecta is a
  session property (`tools.md:155-178`).
- [ ] **Limits name their window.** Rate and spend refusals say which window ran out
  (`gateway.md:231-238`).
- [ ] **A tool is never renamed.** Deprecate it: mark it in the description and `_meta` with a
  sunset date and its replacement, keep it working until the sunset, and check usage by actor
  and client (AN-10) before removal. Removal is a `breaking` diff.

## Outbound events and webhooks

A capability's `Emits` (events an agent can subscribe to) reach agents two ways:

- **Connected MCP clients:** `subscriptions/listen` (`mcp.md:166-191`); best-effort, so a
  read that returns the same state stays available.
- **Webhooks to a registered receiver:**
  - [ ] signed over the raw body with a timestamp; the receiver verifies before parsing and
    rejects an old timestamp;
  - [ ] each delivery carries a stable event id; the receiver deduplicates by it;
  - [ ] retries with backoff up to a stated limit, then a terminal failed state the sender can
    list and replay;
  - [ ] the event catalogue documents each type and its payload; payloads follow the same
    data class and untrusted marking as the tool results.

The receiving side of these patterns is sheleg-dev's (`crypto-payments/SKILL.md`, *Webhook
signature verification* and *Idempotent webhook processing*;
`stripe-billing/references/webhook-events.md`); the sender mirrors them.

## Discovery

- [ ] **`AGENTS.md`** at the product's documentation root: what the surface does, the
  capability list (generated from `capabilities.md` and the snapshot, never hand-kept), how to
  get credentials, the registration command for at least one real client, and one proving call
  (a read-only tool, its arguments, the shape of a correct answer).
- [ ] **An onboarding guide** whose proving call was run with a real client on the deployed
  target (MCP: `server/discover`, then the call; `mcp.md:41-87`).
- [ ] **Registry** for a `public` MCP server: `registry.md`.
- [ ] `llms.txt` is not this file's: seo-aeo-audit owns it.
- [ ] A Fabric service publishes its `fabric-service/0.1` descriptor, dashboard and onboarding
  through `fabric-agent-adapter:building-fabric-services`.

## CLI readiness

- [ ] `--json` on every command that prints data; data to stdout, logs and progress to stderr.
- [ ] Stable, documented exit codes: `0` success, and one distinct code per class (usage, auth,
  not found, conflict, gate, transient). A code never changes meaning.
- [ ] Non-interactive: every prompt has a flag, and `--yes` skips every confirmation; with no
  TTY and no flag, fail at once naming the flag, never wait on stdin.
- [ ] No colour, spinners or tables when stdout is not a TTY or `NO_COLOR` is set.
- [ ] Help that teaches: each command's help has an example and names the next command;
  `--help --json` emits the machine-readable surface that is the snapshot.
- [ ] Writes take `--idempotency-key` (or a natural key) and `--dry-run`.
- [ ] Under `--json`, errors are JSON with a `code`; a gate returns the gate's exit code and
  `human_steps`.
- [ ] Secrets come from the environment or a credential store, never argv.

## Special cases

| Case | Rule |
|---|---|
| Feature flag | the tool list stays stable whatever the flag; a flagged-off call returns a typed `not-enabled` error; agent traffic stays out of human experiment results (AN-10) |
| LLM feature inside the product | `agent-orchestrator` owns the model call; the surface returns the raw data and the summary, the summary marked as model output, third-party text marked untrusted |
| Offline sync | the sync transport is `internal` under AN-3; agents act through the server's capabilities; the conflict policy is recorded with the capability |
| SSO and org-admin consent | an org admin's consent is a `body` gate; agent tokens follow the identity provider's session and revocation policy; SSO/SCIM has no family owner yet (hub board row BN-29) |
| Chat bot | the product's capabilities get the agent surface; the chat itself is a human channel (`manual`) |
| Charging money | AN-7 guards the product side; sheleg-dev wires the charge |

## Traps

- **An agent surface built from the screens.** It inherits the screens' gaps; build it from the
  capability rows, then make the screens its clients (AN-3).
- **`confirm: true` read as approval.** The model sets it.
- **A gate answered with a bare 403.** The agent cannot hand the person anything; name the
  gate and carry `human_steps`.
- **Renaming a tool for clarity.** Every caller's prompt, cache and eval breaks silently.
- **A hand-written snapshot.** It shows what someone believed shipped; generate it.
