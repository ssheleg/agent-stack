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
