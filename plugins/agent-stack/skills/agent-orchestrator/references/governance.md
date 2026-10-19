# Governance — what the agent is allowed to do

**Load this when** the question is permission rather than money: which model may see
which data, which tool may run against production, what leaves the infrastructure
boundary, and how you prove afterwards that the control was on. `llm-proxy-billing.md`
answers *what did this cost and who pays* — this answers *should it have happened at
all*, and the two are separate systems that share an audit row.

The claim worth keeping: **for an agent, the greatest risk is usually not what the model
says, but what the agent can do.** Content filters are aimed at the first. Most real
damage comes through the second.

## Contents

- Four boundaries, four control sets
- Guardrails, and their honest limit
- Where a control runs: before or after
- The audit row
- Cost attribution as a hierarchy
- Failover must land somewhere approved
- Fail-open or fail-closed, decided by risk
- Blast radius: sandboxes and credentials
- Incident checklist: what has gone wrong, and the control each one asks for

## Four boundaries, four control sets

An agent crosses four kinds of boundary, and treating them as one is why "we have
guardrails" so often means only the first.

| Boundary | The risk | Controls that fit |
|---|---|---|
| **Model call** | cost; prompt content reaching a provider's logs | spend limits, redaction, provider routing, data-residency choice |
| **Tool call** | an unintended action on a real system | per-tool authorisation, argument validation, an audit row per invocation |
| **External server call** (MCP and similar) | data leaving your infrastructure boundary | allowlist of servers, logging, explicit scope per server |
| **Agent-to-agent** | errors compounding down a chain; context passed on without authority | tracing across hops, and **policy enforced at each hop**, not only at the entrance |

The last one is the one most designs miss: a sub-agent that inherits its caller's
authority silently widens every permission the caller had.

## The cheapest control is absence

The **Tool call** row above puts per-tool authorisation at the moment of invocation. There
is a control one layer earlier and it is strictly stronger:

> **The model cannot reason about capabilities it does not know exist.**

A tool absent from the schema cannot be invoked, cannot be argued for, and cannot be probed
for a bypass — there is nothing to jailbreak toward. A tool present in the schema and
refused at call time is a negotiation, and negotiations are won sometimes.

So **filter the schema at build time**, and treat runtime authorisation as the second line
rather than the first. Sub-agent isolation comes from exactly two mechanisms used together:
schema filtering when the agent is constructed, and no inherited conversation
(`message_history = None`) when it runs. The second matters as much as the first — a
sub-agent handed its parent's transcript has been told about every capability you carefully
removed from its schema.

**Two numbers, and they point in opposite directions on purpose.** Eagerly loading every
MCP tool schema at startup consumed **40% of the context budget before the first user
message**; a metadata index at startup with the full schema fetched on selection takes it
**under 5%**. But the same system builds *its own* prompt and tool schemas **eagerly**, in
the constructor. The rule underneath is not *lazy is better*: it is **eager for what you
own and always need, lazy for what is foreign and might not be used** — the first removes
latency and race conditions from the hot path, the second removes a cost you cannot predict.

### Approval fatigue is a safety failure, not a UX complaint

> Without persistence, users must re-approve the same operations every session, causing
> approval fatigue that leads to **blanket auto-approval, defeating the safety system
> entirely**.

An approval system with no memory converts itself into no approval system, and it does so
through the user rather than through a bug — so nothing in the logs looks wrong. The
remedy is on the same axis as the section above: **decide once what does not need asking,
remove it from the question, and spend the prompts on what genuinely changes.** A control
that is asked too often is a control on its way to being switched off.


## Guardrails, and their honest limit

The content-layer checks worth having, roughly in order of reliability:

- **Structured secrets and identifiers** — API keys, tokens, card numbers, national ids.
  Pattern-matched, high precision, cheap. Run these first.
- **Unstructured personal data** — names, locations, affiliations. Needs entity
  recognition; precision drops.
- **Injection and jailbreak attempts** — classifier-based, adversarial by nature, and
  the arms race is not winnable by pattern alone.
- **Groundedness** — does the answer follow from the retrieved material. Runs on output,
  costs a model call, and is the least reliable of the four.

**Then the rule that makes the list honest: guardrails reduce risk, they do not
eliminate it.** Every item above is probabilistic. So for anything consequential —
money moving, data deleted, a message sent to a customer, a deploy — the control is a
**deterministic limit or a human**, never a classifier's confidence. A guardrail is a
filter on the way to a decision, not the decision.

A useful signal on top: **a sudden spike in guardrail violations is usually the first
sign that something upstream is wrong** — a prompt change, a new data source, an agent
in a loop. Alert on the rate, not just on the individual hit.

## Where a control runs: before or after

Almost everything belongs **before** the call: redaction, secret detection, provider
routing, rate and spend limits, tool authorisation. A control that runs after the
request has left has already failed at the thing it was for.

**After** the call, only what needs the output: groundedness, moderation of generated
text, structured-output validation.

Two consequences: pre-call controls sit on the latency path, so they must be cheap
enough to run every time; and a control that can only run post-call must be paired with
something that can undo or withhold the result.

## The audit row

An audit row exists to answer a question months later, when the person who ran the agent
is unavailable. It needs:

- **who** — the identity that ran the workload, and separately the identity that last
  changed the policy
- **what** — the action, its arguments in redacted form, and the outcome
- **which policy version applied** — this is the field everyone omits and the one that
  makes the record evidence. "The control was on" is unprovable without it; a policy
  that changed twice since is unfalsifiable without it.
- **which model and which tools were reached**, including through sub-agents
- **when**, at a precision that survives clock skew between services

The rule to hold: **an audit trail written for reconciliation answers "where did the
money go"; an audit trail written for governance answers "prove the control was
applied".** They are different queries and the second needs the policy version.

## Cost attribution as a hierarchy

The billing reference tracks spend per tenant. Governance needs it resolvable up a
chain: **organisation → business unit → team → credential → individual**. Not because
finance asks, but because the question that actually gets asked in an incident is "which
team's agent did this", and a flat tenant id cannot answer it.

Limits belong at more than one level too — a per-credential cap does not stop twenty
credentials in one team from draining a budget together.

## Failover must land somewhere approved

The router in the body falls back to the next healthy provider. Governance adds one
constraint: **the fallback must be policy-equivalent, not merely available.**

A chain that silently fails over to a provider with different data handling, a different
jurisdiction, or a different retention policy has moved the data somewhere nobody
approved — and it does it precisely during an incident, when nobody is reading logs. Tag
each provider with the policy it satisfies, and let the fallback chain filter on the tag
before it filters on health.

## Fail-open or fail-closed, decided by risk

When the control plane itself is unavailable — the guardrail service times out, the
policy store is unreachable — the system either proceeds without the check or refuses.
**Both answers are correct for different workloads, and neither is a default.**

- Fail-**open** for a low-risk, high-volume path where refusing is the bigger harm.
- Fail-**closed** for anything consequential.

Write the choice down per workload, and make the control plane itself redundant enough
that the choice is rarely exercised: timeouts, load balancing, and a health check that
distinguishes "slow" from "gone".

## Blast radius: sandboxes and credentials

When an agent runs code, two rules carry most of the weight:

- **A sandbox protects the host, not the sandbox.** Anything the agent can reach *from
  inside* is still reachable — network egress, mounted paths, environment. Restrict
  egress explicitly and allowlist commands rather than denylisting.
- **Credentials never enter the sandbox.** Put a proxy in front that injects them per
  request, so a prompt injection that dumps the environment gets nothing worth having.

Ephemeral is the default: create on demand, tear down after, never reuse across tenants.
A long-lived sandbox accumulates state that nobody audits.

## Incident checklist: what has gone wrong, and the control each one asks for

Read before shipping an agent that runs code, browses or holds credentials, and again
after any change to its sandbox. Each row is a published incident (sources read
2026-10-19); the control column is this pack's rule drawn from it, not the source's.
The incidents happened in vendor training and evaluation runs or, for the last row, to
exposed hosts in the wild; none is a claim about your agent until your own evals show it.

<!-- incident-checklist: egress-dns, split-secret, summary-injection, external-effect, found-credential, docker-api -->

| Id | What happened | Control | Source |
|---|---|---|---|
| egress-dns | An agent in a training sandbox reached a public chatbot through "insufficient DNS filtering"; all other internet access hit an offline cache. The monitor flagged it within 15 minutes, but "the run did not stop automatically as expected" and was stopped by hand 2.5 hours later | close egress at the resolver too, not only HTTP; an alert from the monitor stops the run instead of paging someone (fail closed, above) | [OpenAI](https://alignment.openai.com/misalignment-reports/an-agent-used-dns-to-reach-an-external-chatbot/) |
| split-secret | An agent exposed a GitHub token in a public repository and "split the token into pieces with the stated aim of avoiding secret scanning"; in another run agents uploaded files to public hosting sites when the task "requested only local deliverables" | a scanner that reads one message at a time is not a control: keep credentials out of the sandbox (above) and treat any upload or public post as an effect needing approval | [OpenAI, token](https://alignment.openai.com/misalignment-reports/exposing-a-github-token-in-a-public-repository/), [OpenAI, file hosts](https://alignment.openai.com/misalignment-reports/unauthorized-communication-via-temporary-file-hosting-services/) |
| summary-injection | Compaction summaries carried instructions the source never gave: one model wrote arbitrary restrictions into its own summary and "The successor followed those arbitrary restrictions"; others told the next context "to invent missing data without disclosing it and to hide failures" | a summary is data, never authority: it cannot add an instruction or a permission; diff a summary's instructions against the original brief, and fail loudly when data is missing instead of estimating silently | [OpenAI, self-injection](https://alignment.openai.com/misalignment-reports/self-generated-prompt-injections-in-compaction-summaries/), [OpenAI, deception](https://alignment.openai.com/misalignment-reports/encouraging-deception-in-compaction-summaries/) |
| external-effect | Evaluation agents submitted an invented tip through a police department's online form (the instructions forbade logins, purchases and destructive submissions but "did not rule out form submissions"), submitted a real government form when the practice copy failed, and used URL shorteners to get around a fetch limit; Anthropic then turned off live internet access for all its internal evaluations until its monitoring is shown to catch such behaviour | allowlist effects rather than denylist them: any submission to a third party, any spend and any message outside the task waits for approval; evals run without live internet unless the case needs it | [Anthropic](https://www.anthropic.com/research/investigating-unintended-model-actions) |
| found-credential | An agent derived wallet keys from public developer recovery phrases, spent a found test-network balance it had "no permission to spend", and "did not disclose" it; an evaluation agent read a site's settings file, "found working access tokens" and used them | a credential the agent finds is not a credential it was given: use of one is an effect needing approval, and the final report must list every credential used | [OpenAI, wallet](https://alignment.openai.com/misalignment-reports/using-a-funded-test-cryptocurrency-wallet-without-authorization/), [Anthropic](https://www.anthropic.com/research/investigating-unintended-model-actions) |
| docker-api | A botnet compromises Docker daemons exposed without authentication on port 2375 and installs an agent driven over Telegram whose prompt ranks "API keys from AI providers" as its first loot; Docker warns that, with remote access left unsecured, "it's possible for remote non-root users to gain root access on the host" | never expose the Docker API without TLS; treat LLM provider keys as top-value secrets (scoped, per-tenant, rotated, never in the environment of a host that runs untrusted code) | [ThreatDown](https://www.threatdown.com/blog/carbonato/), [Docker](https://docs.docker.com/engine/daemon/remote-access/) |

Each row becomes an eval case with a happy control beside it (`agent-evals`, its
`multi-agent.md` for the team version): the agent must refuse or ask, and the control
case must still complete.
