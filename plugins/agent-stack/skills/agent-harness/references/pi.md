# Pi — a harness you can read, and what each of its parts implements

**Load this when:** you want a **worked example** of the harness doctrine, are choosing a
kernel to build on, or are auditing a system built on Pi.

**Spec pinned:** Pi (`@earendil-works/pi-coding-agent`, MIT, Earendil Inc.), `pi.dev/docs/latest` · read 2026-08-15

**Why this file exists.** Everything else in this skill states a rule; Pi is small enough
to read and complete enough to have made every one of those decisions in public. So each
section below says **what Pi does** and then **which rule it is an instance of** — the
value is in the second half. Where Pi disagrees with the doctrine, that is said too.

This is not a substitute for `pi.dev`. It moves faster than this file; the stamp above is
the honest boundary.

## Contents

- What Pi is, and the stance underneath it
- Four ways to run it
- Sessions are a tree, not a log
- Compaction, with the actual numbers
- Configuration and precedence
- Skills, prompts and packages
- Trust, and the deliberate absence of a sandbox
- Containerization — three patterns, three threat models
- Providers and credentials
- Where Pi and this pack's doctrine differ
- Traps

## What Pi is, and the stance underneath it

*"A minimal agent harness."* Its stated position is **primitives, not features**: it ships
`read`, `write`, `edit`, `bash` and a loop, and deliberately omits sub-agents and plan mode,
expecting you to build them as extensions.

**This is the kernel layer of `layers.md`, made concrete.** The omissions are the argument:
a kernel that shipped a plan mode would have chosen your planning shape for you. When
comparing Pi against a workbench, remember the comparison is across layers and will not
converge.

## Four ways to run it

| Mode | Invocation | For |
|---|---|---|
| **Interactive TUI** | `pi` | a human at a terminal |
| **Print** | `pi -p "…"` | one shot, text out |
| **JSON** | `pi --mode json "…"` | events as JSON lines, for another tool's UI |
| **RPC** | `pi --mode rpc` | a long-lived subprocess you drive both ways |
| **Embedded** | the SDK | your process owns the loop |

**One agent, five front doors.** That separation — a core that does not know which surface
is attached — is the same shape `agent-orchestrator` describes when it insists the loop
must not know which provider answered. Details of the last three: `pi-sdk.md`.

## Sessions are a tree, not a log

Sessions persist to `~/.pi/agent/sessions/` as **JSONL, one entry per line**, each carrying
an 8-character hex `id` and a `parentId`. The current position is a leaf; context is built
by walking leaf→root.

| Entry type | Holds |
|---|---|
| `session` | the header: `version` (currently **3**), `id`, `timestamp`, `cwd` |
| `SessionMessageEntry` | a message with its role and content |
| `ModelChangeEntry` / `ThinkingLevelChangeEntry` | mid-conversation switches, recorded rather than implied |
| `CompactionEntry` | a summary, with an optional `retainedTail` |
| `BranchSummaryEntry` | what an abandoned branch was about |
| `CustomEntry` / `CustomMessageEntry` | extension data — the second participates in context, the first does not |

Commands: `/tree` navigates within one file, `/fork` starts a new session from an earlier
prompt, `/clone` duplicates the active branch, `/export` writes HTML, `/share` uploads a
private gist. Flags: `pi -c` continues, `pi -r` browses, `--no-session` keeps nothing.

**This implements `agent-orchestrator/references/runtime.md` → *time travel and forking*.**
That file argues you must be able to fork a past checkpoint and debug **through the real
loop** rather than a reconstruction. A parent-pointer tree is what makes that cheap: no
copy, no replay, and the abandoned branch leaves a `BranchSummaryEntry` behind so the
context is not simply lost.

**Two design details worth stealing.** Model and thinking-level changes are *entries*, so a
session explains its own cost curve. And the version field is honest about migration —
v1 was linear, v2 introduced the tree, v3 unified role naming.

## Compaction, with the actual numbers

Auto-compaction fires when `contextTokens > contextWindow - reserveTokens`.

| Setting | Default | Meaning |
|---|---|---|
| `reserveTokens` | 16,384 | held back for the response |
| `keepRecentTokens` | 20,000 | recent tail never summarized |

Preserved messages run from `firstKeptEntryId` onward and are sent alongside the summary.
`/compact [instructions]` runs it manually and the instructions steer the summary. Setting
`"enabled": false` disables the automatic path while leaving the manual one.

**Two caveats stated in the docs and worth carrying:** tool results are **truncated to 2,000
characters** while summarizing, and a turn larger than `keepRecentTokens` produces two
summaries that are then merged.

**This is the ladder from `agent-orchestrator/references/context-engineering.md` with one
rung.** Pi reserves, keeps a tail, and summarizes the rest. What that file adds and Pi
leaves to you: clearing old tool results *before* paying a summarizer, offloading a large
tool result to a file and keeping the path, and **typed carryover** — the observation that a
summarizer keeps the discussion and drops the state. Pi's `BranchSummaryEntry` and
`retainedTail` are the seams to hang that on.

## Configuration and precedence

| File | Scope |
|---|---|
| `~/.pi/agent/settings.json` | global |
| `.pi/settings.json` | project — **overrides global, merging nested objects** |

Keys cluster into model and thinking (`defaultProvider`, `defaultModel`,
`defaultThinkingLevel`, `thinkingBudgets`), UI, network and retry (`retry` with `enabled`,
`maxRetries`, `baseDelayMs`; `httpProxy`, `transport`, timeouts), content handling
(`shellPath`, `npmCommand`, `defaultTools`), and resources (`packages`, `extensions`,
`skills`, `prompts`, `themes`).

**Merge, not replace, is the part that matters.** A project that wants one different model
should not have to restate the whole file — and a harness that replaced wholesale would
make every project config a copy that drifts.

## Skills, prompts and packages

**Pi implements the Agent Skills standard**, with progressive disclosure: at startup it
scans skill locations and takes only `name` and `description` into the system prompt as XML;
the full `SKILL.md` loads when a task matches.

It discovers skills from `~/.pi/agent/skills/`, **`~/.agents/skills/`**, `.pi/skills/` and
`.agents/skills/` (project paths only after the project is trusted), from packages, from a
`skills` array in settings, and from `--skill <path>`.

> **Concretely relevant here: `~/.agents/skills/` is the ssheleg hub.** On the machine this
> file was written on, that directory holds 72 entries including every family skill, each
> with the `name` and `description` front matter Pi requires — so the family is already in a
> directory Pi reads. **Not verified by running Pi**, which is not installed here; this is a
> statement about the path and the front matter, not an observation of a load.

**Pi documents one deliberate divergence from the standard:** it allows a skill's `name` to
differ from its directory, calling that rule *"suboptimal for shared skill directories used
across multiple agent harnesses."* Which is exactly what `~/.agents/skills/` is. Note the
asymmetry before relying on it — `make-skill`'s validator enforces the strict rule, so a
skill built to Pi's leniency fails the family gate.

**Prompt templates** are Markdown in `~/.pi/agent/prompts/*.md`; the filename becomes the
command (`review.md` → `/review`). Front matter takes `description` and `argument-hint`
(`<required>`, `[optional]`). Arguments substitute as `$1`, `$@` / `$ARGUMENTS`,
`${1:-default}`, `${@:N}` and `${@:N:L}`. Discovery is **not recursive**.

**Packages** bundle extensions, skills, prompts and themes over npm or git, declared under a
`pi` key in `package.json` or by convention (`extensions/`, `skills/`, `prompts/`,
`themes/`). Installed with `pi install npm:@foo/bar@1.0.0`, `git:…`, an https URL, or a
path; `-l` writes to project settings for a team. Resource lists take globs with `!`
exclusions, `[]` for none, `+path` / `-path` to force.

## Trust, and the deliberate absence of a sandbox

Pi *"runs with the permissions of the user account that starts it"* and treats files that
user can write as inside the same trust boundary.

**Project trust** is asked for when a repository carries `.pi/settings.json`, local
extensions, skills, prompts or themes, a `.pi/SYSTEM.md` or `.pi/APPEND_SYSTEM.md`, or
project agent skills in ancestor directories. Decisions persist in `~/.pi/agent/trust.json`.

What it buys, in the docs' own words: it *"prevents a repository from silently changing pi's
settings or extensions before you approve it"* — and explicitly **does not** protect against
untrusted code, prompts, or model output.

**There is no built-in sandbox, on purpose.** The stated reasons: a partial in-process
sandbox creates false assumptions, real isolation needs an OS or container boundary, and Pi
is meant to invoke project toolchains with full local access. And the sentence worth
quoting to anyone who claims otherwise about any harness:

> *"prompt injection from repository files, comments, documentation, context files, or build
> output is expected local-agent risk and cannot be reliably prevented by pi."*

**This is `layers.md` → *what a harness should delegate*, stated by the project itself.** A
harness that also claimed to be a sandbox would be claiming a guarantee it cannot keep from
inside the same process. **For an audit this changes the finding**: "no permission model" is
not a defect here, it is a delegation — so audit what surrounds the process (`audit.md`,
track 6).

## Containerization — three patterns, three threat models

| Pattern | Isolates | Credentials live |
|---|---|---|
| **Gondolin extension** | built-in tools and `!` commands, in a micro-VM | on the host — auth never enters the boundary |
| **Plain Docker** | the whole Pi process | **inside the container** |
| **OpenShell** | filesystem, process, network, credentials by policy | per policy; local or remote gateway |

```bash
docker run --rm -it -e ANTHROPIC_API_KEY -v "$PWD:/workspace" pi-sandbox
```

**The distinction that decides which you want: extensions execute wherever the Pi process
runs.** Host-side Pi routing tools into a micro-VM keeps auth local and isolates execution;
containerized Pi needs the key inside the boundary. Mounting `/root/.pi/agent` as a named
volume keeps settings isolated — mounting your host directory *"exposes host auth and
session files to the container"*, which is the opposite of the intent.

## Providers and credentials

Two paths: **subscription OAuth** via `/login` (ChatGPT Plus/Pro, Claude Pro/Max, GitHub
Copilot, xAI, OpenRouter, Radius) with refresh handled, and **API keys**. 30+ providers.

Resolution order — **CLI `--api-key` → `auth.json` → environment variable → custom provider
keys in `models.json`**. `auth.json` is written `0600` and takes priority over the
environment, which is the ordering you want: an explicit file beats an inherited variable.

Keys support literals, `$ENV_VAR` interpolation, and shell commands
(`!security find-generic-password …`) — so a key can live in a system keychain rather than a
file. Registering a custom provider is `pi-sdk.md`.

## Where Pi and this pack's doctrine differ

Named rather than smoothed over:

- **No iteration guard is documented as a first-class setting.** `agent-orchestrator` treats
  a bounded loop as non-negotiable. Pi has `auto_retry` and abort; a max-iteration ceiling
  is yours to add. Check this first when auditing a Pi-based system.
- **No sub-agents.** Deliberate. `agent-orchestrator`'s sub-agent protocol and
  `techniques.md`'s "distilled summary, never a transcript" are things you build here.
- **Skill naming leniency** contradicts the standard `make-skill` enforces (above).
- **Compaction is one rung**, not the ladder.

None of these is a defect in a kernel. They are the difference between a harness and a
platform, and they are the work you are signing up for.

## Traps

- **Reading the omissions as gaps.** They are the layer boundary. If you need all of them
  filled, you wanted a workbench.
- **Assuming trust means safety.** It means the repository did not silently change your
  configuration. Nothing more, and the docs say so.
- **Mounting your host `~/.pi/agent` into a container** and calling the result isolated.
- **Building on skill-name leniency** and then failing a stricter harness's validator.
- **Forgetting `keepRecentTokens` against a large turn.** One turn bigger than the budget
  becomes two summaries merged — surprising if you are diffing summaries.
- **Treating the docs here as current.** Check the stamp; Pi moves.
