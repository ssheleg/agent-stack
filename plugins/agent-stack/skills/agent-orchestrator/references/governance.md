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
