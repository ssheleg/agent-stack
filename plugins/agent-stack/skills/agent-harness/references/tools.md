# Tools — the agent–computer interface

**Load this when:** the model picks the wrong tool, calls none, calls one with bad arguments,
or you are deciding what to expose in the first place.

**Spec pinned:** Anthropic *Writing tools for agents* and *Building effective agents*; `promptingguide.ai` agents/function-calling · read 2026-08-14

Anthropic's framing is worth adopting whole: this is the **agent–computer interface**, and it
deserves the same craft a human interface gets. Most teams spend their effort on the model
and none on the ACI, then conclude the model is bad at tool use.

## Contents

- Fewer tools than you think
- Namespacing
- The description is the product
- Return meaning, not identifiers
- Token efficiency is a correctness issue
- Errors that teach
- Poka-yoke: make the wrong call impossible
- Evaluating tools
- Traps

## Fewer tools than you think

**More tools do not lead to better outcomes.** The reflex — wrap every API endpoint, ship
forty tools, let the model choose — produces an agent that chooses badly, because selection
degrades with the size of the set and every definition costs context.

Build **a few thoughtful tools targeting specific high-impact workflows.** The test:
consolidate where a human would. `search_and_summarize` beats `search` + `fetch` +
`summarize` when the three are always used together, because it removes two decisions and
two round trips.

**The honest check, and it is brutal:** *if your engineers cannot definitively say which
tool applies to a case, the model cannot either.* Ambiguity between two tools is a design
defect, not a prompting problem.

## Namespacing

Group related tools under a common prefix — `asana_search`, `asana_create_task`,
`jira_search`. Boundaries become visible, and the model stops crossing services by accident.

This also matters at the federation layer: behind a gateway, tool names commonly gain a
prefix from their source server, and a name that changes between sessions invalidates every
prompt and eval that referenced it. See `agent-interop/references/gateway.md`.

## The description is the product

**Even small refinements to tool descriptions yield dramatic improvements.** The rule that
makes them good: **write as if explaining to a new team member**, and make implicit context
explicit.

A description must answer **when and why**, not only what:

```jsonc
// weak — restates the name, and says nothing about choosing it
{ "name": "search_users", "description": "Searches for users." }

// strong — the model can now decide
{ "name": "search_users",
  "description": "Find users by name, email or team. Use this before any operation \
that needs a user ID — IDs are never guessable. Returns at most 20 matches; narrow \
with `team` rather than paging when you can. Do NOT use for the current user: \
`get_current_user` is cheaper and always correct." }
```

Note what the strong version carries: **when to reach for it, what it costs, how to narrow,
and the neighbouring tool it is confused with.** That last clause is the highest-value
sentence in most tool descriptions and almost nobody writes it.

**Parameters carry their own guidance.** Use `enum` to constrain values rather than
describing the constraint in prose, give examples in parameter descriptions, and mark
required versus optional honestly — an optional parameter the tool actually needs is a
silent failure.

## Return meaning, not identifiers

Prioritise **contextual relevance over flexibility**. A response of
`{"id": "u_8f3a", "gid": "1209...", "rid": 44}` gives the model nothing to reason with; it
will echo identifiers into prose and hallucinate what they mean. Return
`{"name": "Ada Lovelace", "team": "Platform", "id": "u_8f3a"}` — the id stays for the next
call, the meaning arrives for the reasoning.

## Token efficiency is a correctness issue

Not merely a cost issue: a tool that returns 40,000 tokens of JSON has consumed the window
the agent needed to finish the task, and no amount of history trimming recovers it (see
`agent-orchestrator/references/context-engineering.md` → *tool-output offload*).

Build in **pagination, range selection, filtering and truncation — with sensible defaults**.
The default matters more than the capability: an agent will rarely opt into a limit it was
not given.

## Errors that teach

A tool error is a turn in a conversation. Compare:

```
Error: 422 Unprocessable Entity
```
```
Error: `due_date` must be ISO-8601 (e.g. 2026-08-14). You sent "next friday".
Call `resolve_date` first, or pass an absolute date.
```

The second costs nothing extra and converts a dead end into a recovery. **Return informative
messages that help the agent recover or try an alternative** — naming the alternative is the
part that gets skipped.

Two structural notes: under MCP a failed tool arrives as a *successful* response carrying
`isError: true`, so code that only catches transport exceptions treats every tool failure as
a success containing an apology (`agent-interop/references/mcp.md`). And in code-mode
harnesses, generated wrappers should convert that into a thrown exception so model-authored
code can `try`/`catch`.

## Poka-yoke: make the wrong call impossible

Borrowed from manufacturing, and the highest-leverage idea here: **change the interface so
the mistake cannot be made**, rather than documenting the mistake.

- Absolute paths instead of relative ones, when relative paths get resolved against a
  directory the agent guessed.
- An `enum` instead of a free-text field with a list of valid values in the description.
- One tool that does the two-step correctly instead of two tools that must be ordered.
- A required `confirm: true` on a destructive action, so a partially-formed call fails
  closed.

## Evaluating tools

Tools deserve **thorough documentation and testing**, and testing means running the agent
against real tasks and reading which tool it picked, with what arguments, and what came
back. Enable intermediate-step visibility and look for the three recurring faults:

| Symptom | Almost always |
|---|---|
| wrong tool chosen | two descriptions do not distinguish themselves; add the "do NOT use for…" clause |
| bad arguments | the parameter description assumes context the model does not have, or the type is too loose |
| result misread | the response returned identifiers, or too much, or both |

Fix the interface, not the prompt, when the fault is in this table.

## Traps

- **Wrapping the API you have** instead of designing the tools the agent needs.
- **A description written for a human reading docs** rather than a model choosing under
  uncertainty.
- **Unbounded responses** with an optional `limit` nobody sets.
- **Errors that are true and useless.** `null is not an object` names the symptom the model
  can do nothing with.
- **Treating tool output as trusted.** It is attacker-controlled input if the server is; the
  specification says descriptions and annotations are untrusted unless the server is.
- **Adding a tool to fix a prompt problem.** The set grows, selection degrades, and the
  original defect is still there.
