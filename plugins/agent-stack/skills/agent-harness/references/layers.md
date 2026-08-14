# Layers — what your harness owns, and what it must not

**Load this when:** deciding what to build versus adopt, or comparing agent frameworks and
finding the comparison keeps sliding.

**Spec pinned:** the three-layer reading of Pi / Goose / OpenCode (gist `AIMOWAY/bd8007c8`); Anthropic agent guidance · read 2026-08-14

## Contents

- The question that resolves most framework arguments
- Three layers
- What a harness owns
- What a harness should delegate
- Choosing your layer
- Traps

## The question that resolves most framework arguments

"Which of these agent frameworks is better" is usually unanswerable because the candidates
sit at different heights. The question that resolves it:

> **Which layer of the agent stack am I trying to work at?**

Compare within a layer. Across layers, the comparison is a category error, and the argument
will not converge no matter how long it runs.

## Three layers

| Layer | What it is | Shape | Best when |
|---|---|---|---|
| **Kernel / harness** | the agent loop itself — runtime, LLM API abstraction, tool dispatch, a terminal UI | a toolkit you build *on* | you are building an agent product, or studying how agents actually work |
| **Workbench / orchestration** | a local environment: desktop app, CLI and API, extensions, workflows across many kinds of work | a product you *extend* | you want capability now, across coding, research and automation, without owning the loop |
| **Product agent** | a domain agent — most visibly coding: explore, plan, edit, test, with built-in modes | a product you *use* | the domain is the one it was built for |

The distinction is not quality. A kernel is *supposed* to be smaller than a workbench; that
is what makes it legible.

## What a harness owns

If you are building at the kernel layer, these are yours and nobody else's:

1. **The loop** — iterate, dispatch tools, decide when to stop. With a bounded iteration
   guard, because an unbounded loop is the defect that costs money while looking like work.
2. **The model boundary** — one abstraction over providers, so the loop does not know which
   vendor answered. See `agent-orchestrator` §6.
3. **Tool dispatch and the ACI** — registration, schemas, parallel versus sequential
   execution, error surfacing. See `tools.md`.
4. **Context accounting** — knowing how full the window is *before* the request fails, and
   what to do about it. See `agent-orchestrator/references/context-engineering.md`.
5. **Observability** — which tool, which arguments, which observation, how many tokens. If
   this is missing, every other item becomes unfalsifiable.
6. **The interrupt/resume contract** — one mechanism, not two. See
   `agent-orchestrator/references/runtime.md`.

## What a harness should delegate

The interesting stance, and it is a design position rather than an omission:

**Permission boundaries usually belong to the environment, not the harness.** Pi states this
explicitly — it provides the kernel and delegates sandboxing and permissions to whatever
surrounds it. Read as a weakness, it looks like a missing feature. Read as architecture, it
is a clear statement: *a harness that also claims to be a sandbox is claiming a guarantee it
cannot keep*, because it runs in the same process as the code it would be confining.

Two consequences worth stating plainly:

- **A harness advertising "safe tool execution" without an OS-level or container boundary is
  advertising a preference, not a control.** MCP says the same about roots: servers *SHOULD*
  respect them, and real enforcement is OS permissions and sandboxing.
- **Deciding the layer decides the audit.** If the harness delegates permission, the audit
  looks at what surrounds it, and "the harness has no permission model" stops being a
  finding and becomes a question about the deployment.

Also usually delegated: identity and secrets (a credential store, never the loop), durable
state (a database or a file system, not the conversation), and policy (see
`agent-orchestrator/references/governance.md` — permission, not protocol).

## Choosing your layer

- **Building a product with agentic features** → adopt a workbench or embed a kernel; do not
  write a third loop. Loops are commodity; your tools and prompt are not.
- **Building an agent platform others build on** → the kernel layer is yours, and the ACI is
  your product surface.
- **Automating your own work** → a product agent, and stop. The most common expensive mistake
  is building a kernel to solve a workbench problem.

**The test that catches the mistake early:** if you cannot name a behaviour you need that the
layer above does not provide, you are building the layer for its own sake.

## Traps

- **Comparing across layers**, then choosing on a benchmark that only makes sense within one.
- **Writing a loop because the loop is the interesting part.** It is a week; the tools and
  the prompt are the year.
- **Claiming a security boundary the layer cannot enforce.** Say what is enforced and by
  what; a sandbox protects the host, not the sandbox.
- **Adopting a workbench and then fighting its opinions.** Its opinions are the product; if
  you disagree with enough of them, you wanted the kernel.
- **Assuming the layer is stable.** These projects move; check what the current version
  actually owns before designing around a division of labour you read about once.
