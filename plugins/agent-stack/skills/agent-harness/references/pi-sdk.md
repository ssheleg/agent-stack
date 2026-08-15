# Building on Pi — SDK, RPC, and the extension seams

**Load this when:** embedding an agent in your own process, driving one from another
language, or extending a harness — and you want a real API surface rather than a sketch.

**Spec pinned:** `@earendil-works/pi-coding-agent`, `pi.dev/docs/latest` (sdk, rpc, json, extensions, custom-provider) · read 2026-08-15

Read `pi.md` first for the harness itself. This file is the programmable half, and its
value is the **seams**: the eight or so places a real harness lets you intervene, each
matched to the rule it lets you implement.

## Contents

- Choosing a way in
- The SDK
- Custom tools
- RPC: driving it from any language
- JSON mode, and why it differs
- The extension API
- The seams that matter
- Custom providers
- Traps

## Choosing a way in

| You want | Use | Because |
|---|---|---|
| your process owns the loop, in Node | **SDK** | direct objects, no serialization |
| to drive an agent from Python, Go, a UI | **RPC** | JSONL over stdin/stdout, bidirectional |
| to consume a run's events, one shot | **JSON mode** | delta-only stream, linear in size |
| a scripted answer | **print** | `pi -p` |
| to change behaviour rather than call it | **an extension** | it runs inside the loop |

**The distinction people get wrong:** RPC and JSON both emit events, but only RPC accepts
commands. If you need to steer mid-run, it is RPC.

## The SDK

```bash
npm install @earendil-works/pi-coding-agent
```

```javascript
import { createAgentSession, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";

const modelRuntime = await ModelRuntime.create();
const { session } = await createAgentSession({
  sessionManager: SessionManager.inMemory(),
  modelRuntime,
});
```

**`AgentSession`** — `prompt(text, options?)`, `steer(text)` and `followUp(text)` to queue
during streaming, `subscribe(listener)`, `setModel()`, `setThinkingLevel()`, `compact()`,
`abort()`, `dispose()`.

**Events** arrive structured:

```javascript
session.subscribe((event) => {
  if (event.type === "message_update" &&
      event.assistantMessageEvent.type === "text_delta") {
    process.stdout.write(event.assistantMessageEvent.delta);
  }
});
```

**`SessionManager`** factories decide persistence: `inMemory()`, `create(cwd)`,
`continueRecent(cwd)`, `open(filePath)`. **`AgentSessionRuntime`** handles replacement —
`newSession()`, `switchSession(path)`, `fork(entryId)`.

**`createAgentSession()` options** worth knowing: `model` (from `@earendil-works/pi-ai`),
`thinkingLevel` (`"off"` … `"max"`), `tools` (names to enable), `cwd`, `agentDir`
(defaults `~/.pi/agent`), `resourceLoader`, `settingsManager`.

**`ModelRuntime`** carries credentials and availability:

```javascript
const modelRuntime = await ModelRuntime.create({
  allowModelNetwork: true,
  modelRefreshTimeoutMs: 15_000,
});
await modelRuntime.setRuntimeApiKey("anthropic", "sk-key");
const available = await modelRuntime.getAvailable();
```

Resolution: runtime overrides → `auth.json` → environment.

**`DefaultResourceLoader`** discovers extensions, skills and prompts, and is where you
override the system prompt for an embedded agent:

```javascript
const loader = new DefaultResourceLoader({
  cwd: process.cwd(),
  additionalExtensionPaths: ["/path/to/extension.ts"],
  systemPromptOverride: () => "Custom system prompt",
});
await loader.reload();
```

**`allowModelNetwork` and `systemPromptOverride` are the two options an embedded agent
almost always needs** — the first because a server should not discover models at runtime
unless you meant it, the second because the default prompt is a coding agent's and yours
probably is not.

## Custom tools

```javascript
const myTool = defineTool({
  name: "my_tool",
  description: "Does something useful",
  parameters: Type.Object({ input: Type.String() }),
  execute: async (_id, params) => ({
    content: [{ type: "text", text: `Result: ${params.input}` }],
    details: {},
  }),
});
```

Passed as `customTools: [myTool]`. Built-ins: `read`, `bash`, `edit`, `write`, `grep`,
`find`, `ls`.

**`details` is not decoration.** It is how a tool result carries structured state into the
session, and Pi's own guidance is to rebuild in-memory state after a restart by walking
`ctx.sessionManager.getBranch()` and reading it. That is **structured note-taking**
(`techniques.md`) with a durable home.

Write the `description` to `tools.md`'s standard — this is the same field, and the same
leverage.

## RPC: driving it from any language

```bash
pi --mode rpc [--provider … --model … --name … --no-session --session-dir …]
```

JSON Lines over stdin/stdout: **commands** in, **responses** (`type: "response"`)
acknowledging them, **events** streaming asynchronously.

> **Framing warning, quoted because it bites in exactly one language at a time:** *"Split
> records on `\n` only; accept optional `\r\n` input by stripping a trailing `\r`."* Some
> standard line readers split on Unicode separators too, and a model that emits one inside
> a string will then desynchronize your parser.

**Commands**, by group:

| Group | Commands |
|---|---|
| Prompting | `prompt`, `steer` (delivered after the current tool), `follow_up`, `abort` |
| State | `get_state`, `get_messages`, `set_model`, `cycle_model`, `set_thinking_level`, `set_steering_mode`, `set_follow_up_mode` |
| Sessions | `new_session`, `switch_session`, `fork`, `clone`, `get_session_stats`, `export_html`, `set_session_name` |
| Execution | `bash`, `compact`, `set_auto_compaction`, `set_auto_retry` |
| Introspection | `get_available_models`, `get_commands`, `get_fork_messages`, `get_entries`, `get_tree` |

**Event lifecycle**, in order:

```
agent_start → turn_start → message_start → message_update* → message_end
            → tool_execution_start → tool_execution_update* → tool_execution_end
            → turn_end → agent_end → agent_settled
```

Plus `queue_update`, `compaction_start/end`, `auto_retry_start/end`,
`bash_execution_update` (correlated by the command's `id`), and `extension_error`.

**`agent_settled` is the one to wait on, not `agent_end`** — it means no further auto-retry
is queued. A client that treats `agent_end` as final will occasionally act on a run that is
about to continue.

Message shapes are stable and worth matching: `UserMessage`, `AssistantMessage` (with
`model`, `usage`, `stopReason`), `ToolResultMessage` (`toolCallId`, `toolName`, `isError`),
`BashExecutionMessage` (`command`, `output`, `exitCode`, `cancelled`).

**Extensions can ask the user something over RPC**, which is the part most integrations
forget. `extension_ui_request` events carry `select`, `confirm`, `input`, `editor` and
expect an `extension_ui_response` with the matching `id`; `notify`, `setStatus`, `setWidget`
are fire-and-forget.

```json
{"type": "extension_ui_request", "id": "uuid-1", "method": "select", "title": "Choose", "options": ["A", "B"]}
{"type": "extension_ui_response", "id": "uuid-1", "value": "A"}
```

**A client that ignores these hangs the agent** whenever an extension asks a question. Not
implementing them is a decision; not knowing about them is an outage.

## JSON mode, and why it differs

`pi --mode json "…"` streams the same lifecycle, opening with a header:

```json
{"type":"session","version":3,"id":"uuid","timestamp":"...","cwd":"/path"}
```

**`message_update` records are delta-only** — they omit the cumulative `message` field and
`assistantMessageEvent.partial` *"to keep stream size linear."* Consumers assemble text from
`contentIndex` and `delta`.

That is a deliberate trade: RPC gives you snapshots you can resync from, JSON gives you a
stream that does not grow quadratically. **Pick JSON for pipelines, RPC for UIs.**

## The extension API

Auto-discovered from `~/.pi/agent/extensions/*.ts` (global), `.pi/extensions/*.ts`
(project, after trust) or an `extensions` array in settings. A file, a directory with
`index.ts`, or a package with its own `node_modules`.

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // may be async — do initialization here, not resource startup
}
```

**Registration surface:**

```typescript
pi.registerTool({ name, label, description, promptSnippet, promptGuidelines,
                  parameters, prepareArguments?, execute, renderCall?, renderResult? })
pi.registerCommand(name, { description, getArgumentCompletions?, handler })
pi.registerProvider(name, config) / pi.unregisterProvider(name)
pi.registerMessageRenderer / registerEntryRenderer / registerMarkdownTransformer
pi.registerShortcut(shortcut, options) / pi.registerFlag(name, options)
pi.on(eventName, handler) / pi.events.on|emit
pi.getActiveTools() / getAllTools() / setActiveTools(names)
pi.setModel(model) / getThinkingLevel() / setThinkingLevel(level)
pi.sendMessage / sendUserMessage / appendEntry / setSessionName / setLabel
pi.exec(command, args, options?)
```

**`promptSnippet` and `promptGuidelines` deserve attention**: a tool contributes not only a
schema but a line to the system prompt and a set of guidelines. That is `system-prompt.md`'s
*"tool policy belongs in the prompt"* built into the registration call, which is the right
place for it — the policy cannot drift from the tool because they are declared together.

**Context (`ctx`)** in every handler: `ui`, `mode` (`"tui" | "rpc" | "json" | "print"`),
`hasUI`, `cwd`, `isProjectTrusted()`, `sessionManager`, `modelRegistry`, `model`,
`thinkingLevel`, `signal`, `isIdle()`, `abort()`, `getContextUsage()`, `compact(options)`,
`getSystemPrompt()`. Commands additionally get `newSession()`, `fork()`, `navigateTree()`,
`switchSession()`, `waitForIdle()`, `reload()`.

**`ctx.mode` and `ctx.hasUI` are how an extension stays honest** across surfaces: an
extension that calls `ctx.ui.confirm()` unconditionally works in the TUI and hangs in a
pipeline unless the client implements the UI sub-protocol.

## The seams that matter

Pi exposes ~30 events. These are the ones that let you implement doctrine this pack
otherwise only describes:

| Event | What it lets you do | Implements |
|---|---|---|
| **`tool_call`** — *can block* | refuse a call before it runs, per caller, per argument | the per-hop permission gate of `agent-orchestrator/references/governance.md`; track 6 of `audit.md` |
| **`tool_result`** — *middleware chain* | rewrite, truncate or annotate a result; handlers see the previous handler's output | tool-output offload and token efficiency (`tools.md`) |
| **`context`** | modify messages **before** the provider call | the compaction ladder's upper rungs, and typed carryover |
| **`before_agent_start`** | inject a message, modify the system prompt | capability-aware prompt assembly (`system-prompt.md`) |
| **`before_provider_headers` / `before_provider_request` / `after_provider_response`** | mutate headers, inspect or replace the payload, handle the response | provider routing, proxying and cost attribution |
| **`session_before_compact` / `session_compact`** | decide what survives | *preserve decisions and open questions, not the discussion* |
| **`input`** — *can intercept* | rewrite or absorb a user message | routing before the loop |
| **`resources_discover`** | add skill/prompt/theme paths at runtime | dynamic capability |
| **`project_trust`** | act on the trust decision | the delegation boundary of `layers.md` |

**`tool_call` blocking is the single most important one for an audit.** It is where a
per-tool, per-caller policy can actually live in a Pi-based system — so its absence is a
finding, and its presence is where you read the policy.

**Lifecycle discipline**, from Pi's own guidance and worth generalizing: start background
resources in `session_start` and clean up in `session_shutdown`, **never from the factory**;
after `/new`, `/resume` or `/fork` a fresh context arrives and **stale `ctx` objects must not
be reused**; and tools that mutate files should use `withFileMutationQueue()` to avoid
racing the built-ins.

## Custom providers

```typescript
// route an existing provider through a proxy — baseUrl and/or headers only,
// and the existing model list is preserved
pi.registerProvider("anthropic", { baseUrl: "https://proxy.example.com" });

// or a whole new one
pi.registerProvider("my-llm", {
  baseUrl: "https://api.my-llm.com/v1",
  apiKey: "$MY_LLM_API_KEY",
  api: "openai-completions",
  models: [{
    id: "my-llm-large", name: "My LLM Large", reasoning: true,
    input: ["text", "image"],
    cost: { input: 3.0, output: 15.0, cacheRead: 0.3, cacheWrite: 3.75 },
    contextWindow: 200000, maxTokens: 16384,
  }],
});
```

For a non-standard API, implement `streamSimple`, pushing an `AssistantMessageEventStream`:
start → content (text, thinking blocks, tool calls) → done or error, updating usage and cost.

**The `cost` block is the hook for everything in
`agent-orchestrator/references/llm-proxy-billing.md`.** A provider that declares its per-token
cost makes attribution arithmetic rather than estimation — and a custom provider that omits
it silently makes every downstream number a guess.

Auth supports API keys with env interpolation, and OAuth with refresh, browser and
device-code flows.

## Traps

- **Waiting on `agent_end` instead of `agent_settled`**, and acting on a run that continues.
- **Ignoring `extension_ui_request`** in a non-TUI client, and hanging the first time an
  extension asks a question.
- **Splitting JSONL on anything but `\n`.** The docs warn about it; the failure is rare,
  data-dependent and looks like corruption.
- **Reusing a `ctx` after a session replacement.** It points at the old session.
- **Starting background work in the extension factory** rather than `session_start`, so it
  outlives the session and doubles on reload.
- **Registering a custom provider with no `cost`**, then trusting the spend numbers.
- **Assuming an extension is a boundary.** It runs in the Pi process, with the Pi process's
  permissions — see `pi.md` → *trust*.
