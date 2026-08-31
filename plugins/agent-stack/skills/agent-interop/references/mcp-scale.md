# MCP at scale — when there are more tools than context

**Load this when:** the host connects to more than a handful of servers, tool definitions are
eating the context window, or chained tool calls are pushing large intermediate results
through the model.

**Spec pinned:** MCP `2026-07-28`, `docs/2026-07-28/develop/clients/client-best-practices` · read 2026-08-13

## Contents

- The two costs, and which pattern fixes which
- Progressive tool discovery
- Dynamic server management
- The prompt-cache interaction nobody expects
- Programmatic tool calling (code mode)
- Security surface
- Traps

## The two costs, and which pattern fixes which

They are different problems and confusing them wastes a rewrite:

| Cost | Symptom | Pattern |
|---|---|---|
| **Definitions** — *when* tools enter context | the window is largely consumed before the user's message is read | **progressive discovery** |
| **Results** — *how* tools are invoked | every intermediate result flows through the model on the way to the next call | **programmatic tool calling** |

The published illustration is stark: loading everything upfront at ~150,000 tokens of
definitions against ~2,000 for discovering on demand. They compose — discovery narrows what
the model knows about, code mode narrows what it has to read.

## Progressive tool discovery

The naive host passes every connected server's `tools/list` output to the model at the start
of every conversation. For a handful of tools this is correct and you should not do anything
cleverer.

**The switch is a threshold, and the guidance is explicit:** express it as a percentage of
the context window — **1%–5%** — load definitions normally until it is reached, then switch.

Once switched, the host fetches definitions as usual but **defers injecting them**, exposing
a `search_tools` meta-tool instead. Three layers:

1. **Catalog** — `search_tools({query: "update salesforce record"})` returns names and
   one-line descriptions only.
2. **Inspect** — `get_tool_details({name: "salesforce_updateRecord"})` returns the full
   schema for that one tool.
3. **Execute** — the model calls it, having loaded only what it needed.

**Retrieval strategy**, and none is automatically right:

| Strategy | Good at | Cost |
|---|---|---|
| Keyword (BM25, regex) | descriptive names; simple, predictable | misses synonyms |
| Embedding | synonyms and semantic matches | index to build and maintain |
| Subagent (small fast model picks) | works very well | the most expensive |
| Hybrid | scoring across rankings, or per use case | complexity |

**Check the provider first.** OpenAI and Anthropic both ship built-in tool search; prefer the
platform's over a hand-rolled one unless you need access-control filtering or domain-specific
ranking in the retrieval itself.

**Implementation guidance worth obeying:** offer multiple detail levels (name-only,
name+description, full schema); cache definitions host-side so re-injection needs no round
trip; **re-index on `notifications/tools/list_changed`**; group tools by their source server
so the model can reason about related capability.

## Dynamic server management

The same idea one level up. Rather than connecting to everything at startup: keep a registry
of available servers with high-level descriptions, connect when the model asks for that
capability, and **disconnect when it is no longer relevant** to free context.

This suits general-purpose agents, where intent is unknown at the start. It also composes
with Agent Skills: a skill file can declare which servers it needs, and the host connects
them only when that skill is invoked.

## The prompt-cache interaction nobody expects

This is the part that turns a clever discovery implementation into a regression, and it is
easy to ship without noticing.

Most providers cache the prompt prefix — **including the `tools` array**. Adding or removing
a definition mid-conversation **invalidates that cache**, and the resulting miss can cost more
tokens than the definitions you so carefully removed.

**This is one instance of a general rule**, and the platform now has a cache-safe path the three
mitigations below were approximating: `defer_loading` keeps deferred definitions out of the
system-prompt prefix and appends discovered ones inline as `tool_reference` blocks, leaving the
cached prefix untouched (at least one tool must stay non-deferred — all-deferred is a 400). The
economics, the arithmetic and the other invalidators are in `agent-orchestrator`'s
`references/kv-cache.md`.

Three mitigations, in the order they are usually right:

- **Append** newly discovered definitions after the cache breakpoint rather than re-sorting
  the array.
- Or route every call through **one stable `call_tool({name, args})` meta-tool**, so the
  array never changes at all.
- Treat **server disconnection as a conversation-boundary operation**, not a per-turn one.

**Measure this rather than reasoning about it.** Whether your discovery scheme is a net win
depends on your provider's caching and your conversation shape, and the loss is invisible in
a token count that only sums definitions.

## Programmatic tool calling (code mode)

Instead of the model calling tools, the model **writes code that calls tools**; the code runs
in a sandbox and only its output returns to the model.

**How it is wired:**

1. The host generates a typed API from each server's tool schemas. Where a tool declares
   `outputSchema`, the generated return type is precise — which is the concrete reason to
   provide one.
2. The model writes a script against those functions.
3. The sandbox executes it. Calls are **intercepted and routed back through the host broker**
   to the right MCP server. Intermediate data flows server-to-server without entering
   context. Only `console.log` output returns.

The canonical example: "find all error logs from the past hour and file a ticket for each
unique error." Direct calling pushes thousands of log entries through the model; code mode
filters and deduplicates inside the sandbox and returns one summary line.

**When `outputSchema` is missing**, prefer the simple path — accept a generic type and handle
it downstream; the real fix belongs to the server author. A typed extraction via a small
fast model is available for single-shot calls outside loops, but it adds latency, can
hallucinate or drop fields, and its result must be validated before use.

**Sandbox options**, listed as examples rather than endorsements — evaluate maturity
yourself: Deno or `isolated-vm` for JavaScript; Monty (experimental) for Python; pctx
(early-stage) for TypeScript; Wasmtime for anything compiled to Wasm. Whichever you pick, the
integration is the same: inject stubs, intercept over an in-process or stdio channel so
network permission can stay fully denied, dispatch as `tools/call`.

**Errors:** convert `isError: true` into a thrown exception in the generated wrappers so
model-authored code can `try`/`catch`. If an uncaught error kills the script, surface it as
the script's result so the model can self-correct — and note that the model is then
responsible for reporting side effects already committed.

## Security surface

Code mode adds a code-execution surface, and each of these is a real control rather than
advice:

- **Per-call authorization.** The broker is still the MCP host for specification purposes.
  Approving the *script* does not approve every call it makes at runtime. Categorical grants
  are fine ("allow `ticketing_createIssue` for this run"); evaluating each call against the
  grant is not optional.
- **Cross-server data flow.** A result from server A is untrusted input to server B. Apply
  the same review policy to brokered calls as to direct ones — **truncating output does not
  prevent exfiltration**.
- **Network isolation.** The sandbox gets no direct network access; everything goes through
  the broker.
- **No credential exposure.** Keys live with the host; generated code calls typed functions
  and the host attaches auth when forwarding.
- **Resource limits.** Timeouts and memory caps, or one runaway script is an outage.
- **Output filtering.** Validate and truncate console output before it re-enters the model.

## Traps

- **Switching to discovery too early.** Below the threshold it is pure overhead plus a
  failure mode: the model cannot use a tool it never found.
- **A search index that never re-indexes.** Without honoring `list_changed`, discovery
  confidently returns tools that no longer exist.
- **Counting definition tokens and calling it a saving.** See the prompt-cache section.
- **A sandbox with network access.** It is then not a sandbox, it is a proxy for the model.
- **Assuming the sandbox bounds authorization.** It bounds *execution*. Authorization is the
  broker's job, per call.
