# Production metrics: what the agent moves, measured where it runs

**Load this when an agent is deployed and somebody must be able to say whether it works
there:** the registry of its metrics, the closed-period measurements, the before/after
verdict on a change, and the link back to the offline suite. SKILL.md §3 names the online
tier; this file is its contract.

Status: v1 (2026-11-11). The record names (`agent-metrics/1`, `agent-measurement/1`,
`agent-change-measure/1`) follow a cross-agent proposal of 2026-11-10 that the host's agent
contract is standardising; the fields below are the portable core. Where a host publishes
its own schema, the host's schema wins and this file explains the reasons behind it.

<!-- production-metrics: registry, measurement, change-measure, fixture-link | families: outcome, quality, reliability -->

## Contents

- [Why a green suite is not enough](#why-a-green-suite-is-not-enough)
- [The registry: agent-metrics/1](#the-registry-agent-metrics1)
- [Measurements: agent-measurement/1](#measurements-agent-measurement1)
- [Change verdicts: agent-change-measure/1](#change-verdicts-agent-change-measure1)
- [From a failing metric to a fixture](#from-a-failing-metric-to-a-fixture)
- [Traps](#traps)
- [Checklist](#checklist)

## Why a green suite is not enough

The offline suite answers "did my change break a case I already know". It cannot answer
"does the agent do, in production, the thing it exists for", because the failing input is
not in the dataset (SKILL.md §3). The case that made this file necessary:

> A deployed ad-sales agent launched campaigns automatically after a proven payment. A
> refactor left the launch step calling `agent.runTool?.()`, a method that no longer
> existed. Optional chaining turned the call into a silent no-op, every attempt ended in a
> refusal, and **the money path was dead for over three months while every unit test stayed
> green**. Following one live deal to its end found it. One number would have read 0 on the
> first closed day after the break: **"share of proven payments launched within 24 h"**, which read 0 of N.

The same retro found a second silent defect: the daily counts of the agent's autonomy had
never been stored (a table constraint refused the row kind) while the routine that wrote
them reported success. **A measurement pipeline is code too, and it fails the same way.**

## The registry: agent-metrics/1

One file per agent, kept with its source (for example `metrics.json`), optionally served
read-only so a dashboard can draw it. One entry per metric:

| Field | Carries | Rule |
|---|---|---|
| `id`, `version` | stable name, integer version | a definition **never changes in place**: a new meaning is the next `version`, and series of two versions are never joined |
| `family` | `outcome`, `quality`, `reliability`, `cost`, `speed`, `revenue`, `safety`, `adoption` | see the minimum set below |
| `means` | one sentence a person can check | written before the first measurement |
| `unit`, `direction` | `share`, `count`, `seconds`, `usd`…; `up` or `down` | a metric with no direction cannot be judged better or worse |
| `population` | `unit` (turn, ticket, chat, job, payment, campaign, session, run…) and `filter` | the filter is a sentence plus a code reference; **a metric without a named population is refused** |
| `window` | `rolling` days, or `calendar` day/week/month | the window a verdict reads, not the measurement period |
| `source` | `kind` and `ref` | reuse what already measures it (usage and cost reports, load, an operations digest, a support-quality report, an eval receipt); `custom` only when nothing does, with the code reference |
| `baseline` | `value`, `n`, `window`, `measuredAt`, `evidence` | measured, never estimated; `n` is mandatory |
| `target`, `guardrail` | the value to reach; the metric that must not get worse on the way | a target with no baseline is a wish |
| `owner` | who answers for it | |

**Minimum set: every agent declares at least one `outcome`, one `quality` and one
`reliability` metric.** The outcome metric is what the agent exists to move, read on the
unit of value (a payment launched, a ticket resolved, a store listing shipped), never on
activity (messages sent, tool calls made). Cost comes from the usage record and is not
re-declared. An agent that answers people takes its quality and reliability metrics from
`support-quality.md` A2 rather than inventing new ones.

```json
{
  "schema": "agent-metrics/1",
  "agent": "sales-agent",
  "metrics": [{
    "id": "paid_launched_24h_share", "version": 1, "family": "outcome",
    "means": "Share of proven payments whose campaign started within 24 hours of the payment",
    "unit": "share", "direction": "up",
    "population": { "unit": "payment", "filter": "payments proven on chain, payment time in the window",
                    "ref": "src/metrics.js#paidLaunched24hShare" },
    "window": { "kind": "rolling", "days": 14 },
    "source": { "kind": "custom", "ref": "src/metrics.js#paidLaunched24hShare" },
    "baseline": { "value": 0.5, "n": 2, "window": "2026-10-27/2026-11-10",
                  "measuredAt": "2026-11-10T22:00:00Z", "evidence": "docs/reports/…" },
    "target": { "value": 0.95 }, "guardrail": null, "owner": "sales-agent"
  }]
}
```

Values in the example are illustrative.

## Measurements: agent-measurement/1

One record per metric and **closed** period. Written by the agent for `custom` sources;
other kinds are read from their own reports, never copied.

```json
{ "schema": "agent-measurement/1", "metric": { "id": "paid_launched_24h_share", "version": 1 },
  "agent": "sales-agent", "window": { "from": "2026-11-09T00:00:00Z", "to": "2026-11-10T00:00:00Z" },
  "value": 0.0, "n": 1, "approx": false, "notMeasured": [], "computedAt": "2026-11-10T00:40:00Z" }
```

- **Closed UTC periods only.** A half-day's share compared with a full day's is a different
  population.
- **Counts and shares, with `n`.** No person's data, no message text, no identifiers: the
  record is aggregate by construction.
- **Not measured is `null`, never 0, and named in `notMeasured`.** A 0 says the agent did
  nothing; a `null` says nobody looked. Confusing the two hides exactly the defect above.
- **Read the write back.** The routine that stores a measurement checks that the row exists
  before it reports success, and a series with no record for its last closed period is
  **stale**, which is a finding on its own, not a quiet gap on a chart.
- **The denominator is the population, not the survivors.** A share of "launched within
  24 h" computed over launched campaigns is 100% by construction; it must be computed over
  proven payments.

## Change verdicts: agent-change-measure/1

Did a release, a prompt change or a model swap move the metric? One record per metric and
change:

```json
{ "schema": "agent-change-measure/1", "metric": { "id": "paid_launched_24h_share", "version": 1 },
  "change": { "kind": "release", "ref": "v1.4.11..v1.4.14" },
  "pre":  { "window": "2026-10-27/2026-11-10", "value": 0.5, "n": 2 },
  "post": { "window": "2026-11-11/2026-11-25", "value": null, "n": null },
  "method": "unpaired", "interval": null, "verdict": "inconclusive",
  "prediction": { "value": 0.95, "by": "agent", "at": "2026-11-10T22:00:00Z" },
  "confounders": ["two payments in the pre window"] }
```

**The method comes from the design, as `statistics.md` requires** ("The design decides the
method"): `paired` when the same units are seen before and after (replaying the same
tickets through both versions), `unpaired` for two production windows (Welch SE, or two
Wilson intervals for shares), `naive` only for a description that claims nothing.
Production windows are almost always unpaired.

**The verdict is one of four words**, and the rule is mechanical so two readers reach the
same one:

| Verdict | When |
|---|---|
| `improved` | the post interval clears the pre interval in the metric's `direction` |
| `worse` | the post interval clears the pre interval against the `direction`, or the `guardrail` metric got `worse` |
| `no_effect_detected` | both windows are large enough to have shown the predicted effect (the intervals are narrower than it) and they overlap |
| `inconclusive` | anything else, and **always when either window's `n` is too small** for its interval to exclude the other's value |

**Small `n` is `inconclusive`, never a win.** Compute the Wilson interval (`statistics.md`,
"The band around a pass rate"): two payments at 1 of 2 span roughly 9% to 91%, which no
post window can clear. The honest output of that change is "inconclusive, the window needs
about N more units", and the record says so instead of "improved".

**A prediction is written before the change and scored after it.** It is what turns a
release note into a test of the team's understanding: a change predicted to move the outcome
metric from 0.5 to 0.95 that lands `no_effect_detected` is the most useful record in the
file. List the confounders you know (a seasonal week, a price change, a traffic source that
switched on) rather than leaving them for a reader to guess.

## From a failing metric to a fixture

The online tier finds; the offline tier keeps. The link between them is SKILL.md §6 applied
to a metric:

1. **Every unit that failed a metric is a candidate case.** A proven payment that did not
   launch within 24 h, a ticket that breached its reliability target: capture the state at
   the failure point from the trace (§7).
2. **Minimise and file it** in the tier that isolates it, carrying the metric's
   `{id, version}` and the measurement window it came from.
3. **It stays in the suite permanently**, so the regression that killed the metric in
   production fails the gate the next time.
4. **A metric breach routes its units to the annotation queue** (§6) when the cause is not
   mechanical, so a person labels what a judge cannot see.

The reverse link matters too: **an offline case that has never failed in production is
not evidence about production**, and an offline pass rate is never reported as an outcome
metric.

## Traps

| Trap | What it looks like | Prevented by |
|---|---|---|
| The silent no-op | an optional call (`x?.()`) on a renamed method, a feature flag left off: tests green, money path dead | an `outcome` metric on the unit of value, with a stale/zero alarm |
| The phantom success | the routine reports "stored", the row was refused | read-back before success; stale series as a finding |
| Survivor denominator | a share computed over the units that already succeeded | the population names the starting unit |
| Activity as outcome | "messages sent up 40%" | outcome read on the unit of value |
| Zero for missing | a gap drawn as 0, a 0 reported as "nothing happened" | `null` plus `notMeasured` |
| Definition drift | the filter edited, the series continued | `version`, series never joined across versions |
| A win on `n = 2` | "launch share 50% → 100%" after one release | Wilson intervals, `inconclusive` by rule |

## Checklist

- [ ] A registry file beside the agent's source, with at least one `outcome`, one `quality`
      and one `reliability` metric
- [ ] Every metric names its population (unit, a checkable filter, a code reference)
- [ ] Baselines measured with `n` and evidence, targets set against them
- [ ] Measurements over closed UTC periods, aggregate only, `null` for not measured
- [ ] Each measurement write read back; a stale series raised as a finding
- [ ] Every release that targets a metric carries an `agent-change-measure/1` with a
      prediction written beforehand and a verdict by the rule above
- [ ] Every unit that failed a metric minimised into a permanent offline fixture
