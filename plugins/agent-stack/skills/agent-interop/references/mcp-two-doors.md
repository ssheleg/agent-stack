# Two doors: every MCP server we build exposes `search` and `execute`

**Load this when:** you build, adapt or review an MCP server the estate builds or runs (an
agent's server, a product's agent surface, a data room, a gateway's own tools); or a
server's `tools/list` shows more than two tools.

**Spec pinned:** MCP revision `2026-07-28` (`tools/list`, `tools/call`, `outputSchema`, `isError`); the operator's rule of 2026-11-18 (fabric-agents-database session b590fc74: «два входа только поиски и экзекьюция ... best practice всегда для проектирования mcp ... особенно на датарумы») · read 2026-11-18

## Contents

- The rule
- Why two doors
- `search`: the catalogue of operations
- `execute`: one gated path for every operation
- Exceptions: at most three direct tools, each measured
- Moving an existing server to two doors
- The contract snapshot and its diff
- Conformance tests
- Traps

## The rule

**`tools/list` of a server we build or run answers exactly two tools: `search` and
`execute`.** Every function the server offers is an *operation*: `search` finds operations
by words and returns each with its schema; `execute` runs one by name with the same gate,
idempotency and audit the interface uses. No other tool, unless a measured case shows a call
that must skip `search` (below, at most three). Data rooms move first.

Scope: servers the estate builds or runs, whatever their transport (stdio, Streamable HTTP,
behind a gateway). A third-party server we only consume is not ours to reshape; its scale is
the host's problem (`mcp-scale.md`). A Fabric service's descriptor, auth and job contract are
the Fabric adapter's (`fabric-agent-adapter:building-fabric-services`); this file owns the
tool shape they serve.

## Why two doors

- **Context.** A host passes every tool definition to the model on every turn. Forty
  definitions cost thousands of tokens before the first call; two cost a few hundred, and the
  catalogue is read only when needed, only the operations that match.
- **Selection.** Choosing among many similar tools degrades with the size of the set
  (`agent-harness/references/tools.md`, "Fewer tools than you think"). Choosing between
  "find" and "do" does not.
- **One path.** Every operation crosses the same gate, validation, idempotency check, audit
  row and spend check in `execute`. Forty tools are forty places to forget one.
- **Stable surface.** Adding an operation changes the catalogue, not `tools/list`: clients
  that cache tool lists, prompts and evals naming the two tools keep working.

## `search`: the catalogue of operations

Read-only (`annotations.readOnlyHint: true`). Input:

```jsonc
{ "query": "string, optional: words of the task, any language; empty lists everything",
  "names": ["optional: exact operation names, to fetch their schemas"],
  "limit": 10,          // default 10, at most 50
  "cursor": "optional, from nextCursor" }
```

Output (`structuredContent`, with an `outputSchema`):

```jsonc
{ "operations": [ {
    "name": "invoice.refund",              // stable, namespaced, never renamed (AN-8)
    "purpose": "When and why to use it, and the neighbour it is confused with",
    "inputSchema": { /* JSON Schema, the same one execute validates */ },
    "outputSchema": { /* optional */ },
    "effect": "read | write | money | delete | publish",
    "gate": "none | relayed | human",      // AN-7; the capability row's gate
    "idempotent": true,
    "example": { "arguments": { /* valid against inputSchema */ } },
    "deprecated": { "replacedBy": "name", "sunset": "YYYY-MM-DD" }   // only when deprecated
  } ],
  "total": 37, "nextCursor": "…", "degraded": [] }
```

- Match on the operation's name, purpose and argument names, in Russian and English word
  forms where the server's users write both. Rank, then page; never return the whole
  catalogue unasked.
- Filter by the caller's scope: an operation the credential cannot run is not listed (it
  answers `unknown-operation` from `execute` too), so the catalogue never advertises what the
  caller is refused.
- `purpose` is a tool description and follows `agent-harness/references/tools.md` ("The
  description is the product"): when, why, cost, and the confusable neighbour.

## `execute`: one gated path for every operation

Input:

```jsonc
{ "operation": "invoice.refund",
  "arguments": { /* validated against the operation's inputSchema */ },
  "idempotencyKey": "required for effect write, money, delete, publish",
  "dryRun": false }      // where the operation supports it (AN-8)
```

- Answers the operation's own result as `structuredContent`; a long operation answers a task
  (`io.modelcontextprotocol/tasks` where negotiated) or a job handle (`mcp.md`, Tasks).
  Polling and cancelling a job are operations too (`job.get`, `job.cancel`).
- Typed refusals (`isError: true`), never prose alone:
  `unknown-operation` (with up to three nearest names and "call search first"),
  `invalid-arguments` (with the JSON Schema path that failed), `idempotency-required`,
  `idempotency-conflict`, and the gate refusal of AN-7 (`agent-surface.md`, "AN-7: the gate
  protocol") with `human_steps`, or MCP `input_required` for a value the caller can supply.
- The gate, limits, audit row and spend check are the same functions the interface's button
  calls (AN-3). `execute` never runs anything that is not a catalogued operation: it is not a
  shell, an `eval`, or code mode (`mcp-scale.md`, "Programmatic tool calling").
- The `execute` description says: "Run an operation that `search` returned. Never guess a
  name; call `search` first unless the name came from it in this conversation."

## Exceptions: at most three direct tools, each measured

A direct tool beside the two doors is allowed only when a measured case shows a call that
must skip `search`, and never more than three. Record each in the server's contract source
beside the tool: its name, the call that cannot afford the round trip, the measurement
(calls per session, tokens or latency saved, the date and how it was measured), and who
decided. No measurement, no exception: "it is used a lot" is a reason to measure, not one.

Tools that a protocol outside the server requires by name (for example the Fabric kit's
`fabric.job.get` and `fabric.job.cancel` under `fabric-interop/0.1`) count against the three,
with that contract recorded as the reason, until the contract lets them fold into `execute`.

## Moving an existing server to two doors

1. **Inventory.** Every tool becomes an operation with the same name, schema and gate; the
   inventory is the catalogue. Add the interface's actions missing from it (AN-3).
2. **Serve both doors** from that catalogue; `tools/list` answers only `search`, `execute`
   and recorded exceptions.
3. **One release of aliases.** A `tools/call` by an old tool name still runs its operation
   through `execute`'s path and marks the result deprecated (`_meta` and a `deprecated`
   field naming `execute` and the sunset date). The next release removes the aliases.
4. **Move the callers.** Grep skills, prompts, docs, evals and other agents' code for the old
   tool names; change them in the same release or file a row with each owner.
5. **Snapshot and tests** below; the change is `breaking` for `tools/list` and `none` for the
   operations when names and schemas are kept.

## The contract snapshot and its diff

For a two-door server the contract snapshot (`agent-surface.md`, "The contract source, its
snapshot, and the diff that classifies a change") is `tools/list` plus the whole `search`
catalogue (every page, empty query, a credential holding every scope), sorted by operation
name. The diff classes apply to operations exactly as they applied to tools: an operation
removed or renamed is `breaking`, a new one is `additive`, and a changed `purpose` is a
contract change.

## Conformance tests

In the server's own suite, against a real client over the shipped transport:

- [ ] `tools/list` names equal `{search, execute}` plus the recorded exceptions, at most three.
- [ ] Every catalogued operation has `purpose`, `inputSchema`, `effect`, `gate` and an
  `example` whose arguments validate; each example runs through `execute` in a sandbox.
- [ ] `search` pages (`limit`, `nextCursor`) and hides operations outside the caller's scope.
- [ ] `execute` answers `unknown-operation`, `invalid-arguments` and `idempotency-required`
  typed; a gated operation refuses with the same gate the interface shows.
- [ ] In the migration release, every old tool name still runs and is marked deprecated.

## Traps

- **The catalogue as one blob.** A `search` that returns all operations with full schemas on
  every call moves the context cost instead of removing it. Page and rank.
- **`execute` as an escape hatch.** Arguments it does not validate, or an operation that runs
  arbitrary code, turn the second door into an unguarded one.
- **A gate only in the interface.** A refusal the button applies and `execute` skips is a
  bypass, not parity.
- **Renaming while migrating.** Keep names and schemas; change the shape of the surface and
  the vocabulary in two different releases.
- **Exceptions that grow.** A fourth "just this one" direct tool, or one without its
  measurement, is the drift the rule exists to stop.
