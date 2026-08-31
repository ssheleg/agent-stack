# Statistics for agent evals — how many runs before a difference is real

**Load this when a number is about to change a decision:** picking between two models or
two harness configurations, setting a release threshold, deciding whether a regression is
real, or writing the sentence "X is better than Y" in a document somebody will act on.

Everything here is arithmetic over binary outcomes. It needs no library and no
statistician, and it is the layer most eval advice skips — including this skill's own
first eight sections, which say what to assert and never say how many times.

## Contents

- [The band around a pass rate](#the-band-around-a-pass-rate)
- [pass@k and pass^k are different questions](#passk-and-passk-are-different-questions)
- [Trials are not independent, and the published data says so](#trials-are-not-independent-and-the-published-data-says-so)
- [Pairing: same tasks, same seeds, per-task deltas](#pairing-same-tasks-same-seeds-per-task-deltas)
- [The harness is a variable, so pin it](#the-harness-is-a-variable-so-pin-it)
- [What a number authorises](#what-a-number-authorises)
- [The report contract](#the-report-contract)

---

## The band around a pass rate

A pass rate over `n` cases is an estimate, and its standard error is

```
SE(p) = sqrt( p * (1 - p) / n )
```

The 95% band is roughly `±1.96 · SE`. Computed, not quoted:

| n | p | 95% band |
|---|---|---|
| 100 | 0.70 | **±8.98 pp** |
| 400 | 0.70 | ±4.49 pp |
| 1000 | 0.70 | ±2.84 pp |

```python
import math
def band(p, n): return 1.96 * math.sqrt(p * (1 - p) / n) * 100   # percentage points
```

**So "the new one gets 73% where the old one got 70%, on a hundred cases" is not a
result.** It is a number inside its own noise. The error shrinks as `1/√n`, which is the
whole practical consequence: **the fix for a 2–3 pp expected gain is more tasks, not more
argument.** Quadrupling the set halves the band.

A corollary worth stating because leaderboards invite the opposite: **differences below
about 3 pp deserve scepticism until both configurations are documented and matched.**

> The formula assumes independent cases. A benchmark whose tasks share a fixture, an
> environment or a generator violates that, and the true band is wider than this. Wider,
> never narrower — so the table is a floor on your uncertainty, not a ceiling.

## pass@k and pass^k are different questions

Two metrics, one letter apart, measuring opposite things.

| Metric | Formula | Asks | Who it is for |
|---|---|---|---|
| `pass@k` | `1 − (1 − p)^k` | did **at least one** of k attempts succeed | a **capability ceiling** — a human picks the best of k |
| `pass^k` | `p^k` (if independent) | did **every** one of k succeed | a **reliability floor** — nobody is picking |

At `p = 0.6`, `k = 5`:

- `pass@5 = 1 − 0.4⁵ = 0.98976` → **99.0%**
- `pass^5 = 0.6⁵ = 0.07776` → **7.8%**

**A 91-point gap between two numbers describing the same agent.** The first makes a demo;
the second is what a payment, a refund or a permission change actually needs.

Anthropic states the same arithmetic for the everyday case: at a 75% per-trial rate, three
trials all passing is `0.75³ ≈ 42%` — verified, `0.421875`.

**The rule that follows: an operation with side effects may not "retry until it works."**
If a failed attempt leaves a charge, a message or a mutated row behind, `pass@k` is not
available to you as a metric — you cannot pick the best of five refunds. Sample in a
sandbox or a rollback-capable environment, and count **every** failure.

**A report that gives k without saying which k it means is unreadable.** *k independent
samples of one task* and *k consecutive tasks on one live pipeline* are different claims.

## Trials are not independent, and the published data says so

`pass^k = p^k` assumes each trial is a fresh coin flip. Real benchmarks do not behave that
way, and the τ-bench leaderboard is the cleanest demonstration — claude-3-5-sonnet on the
airline domain, published Pass^k beside what independence would predict from Pass^1:

| k | published Pass^k | `0.460^k` if independent |
|---|---|---|
| 1 | 0.460 | 0.460 |
| 2 | **0.326** | 0.212 |
| 3 | **0.263** | 0.097 |
| 4 | **0.225** | 0.045 |

The observed curve falls far slower than independence predicts. The reason is not
mysterious: **some tasks are reliably easy and some reliably hard**, so successes cluster
by task rather than scattering by trial. Positive correlation across trials of the same
task.

Two consequences, and they cut in opposite directions:

- **You cannot compute `pass^k` from `pass^1`.** Exponentiating a headline rate gives a
  number far below the truth. Measure `pass^k` directly, at the k you care about.
- **Anthropic's `0.75³ ≈ 42%` is a worst case, not a forecast.** It is the right shape for
  an argument — *consistency is a much harder bar* — and the wrong number to put in a
  release gate.

The other half of independence is the harness, not the task: Anthropic requires each trial
start from a clean environment, because *"unnecessary shared state between runs (leftover
files, cached data, resource exhaustion) can cause correlated failures."* Correlated
failures break the arithmetic above — so isolation is not hygiene, it is what makes the
metric mean anything.

## Pairing: same tasks, same seeds, per-task deltas

**Never subtract two independent averages.** Run both configurations over the *same* task
list with the *same* fixed seeds, record a per-task win/loss/tie, and test the deltas.

```
for task in tasks:            # identical list
    for seed in seeds:        # identical seeds, 3-5 of them
        a = run(config_A, task, seed)
        b = run(config_B, task, seed)
        delta[task, seed] = a - b
```

- **3–5 seeds per configuration**, reporting mean and spread. A single run screens a
  direction; it does not establish one.
- Test the paired deltas with **McNemar** (binary outcomes) or a **paired bootstrap**.
  Pairing removes the task-difficulty variance that dominates the unpaired comparison —
  which is exactly the correlation the previous section measured.
- Testing several hypotheses at once needs a **multiple-comparisons correction**, or an
  independent re-run of whichever ones came out positive. Five hypotheses at p<0.05 gives
  you roughly a one-in-four chance of a false positive somewhere.

**Ship on three conditions, not one:** the difference exceeds the noise band, it survives
the paired analysis, and it reproduces on a rerun.

## The harness is a variable, so pin it

The container spec is part of the measurement. On Terminal-Bench 2.0 the gap between the
most- and least-resourced setups was **6 percentage points (p < 0.01)** — larger than most
model differences anyone argues about.

The shape of the effect matters more than the number:

- Between **1× and 3×** the task's specified resources, scores move **within noise
  (p = 0.40)**.
- From 3× to uncapped, infrastructure errors drop a further **1.6 pp** and success jumps
  nearly **4 pp** — because the extra headroom lets the agent attempt strategies that only
  work with it: pulling large dependencies, spawning expensive subprocesses, running
  memory-hungry suites.
- Infrastructure errors alone: **5.8% of tasks at 1×**, cut to **2.1% at a 3× ceiling
  (p < 0.001)**.

So a tight cap and a generous cap **measure different agent strategies**, not the same
agent more or less precisely. The remedy is a **floor and a ceiling**, calibrated so that
scores at both fall within noise of each other — not a single pinned value.

The effect is task-distribution dependent and does not transfer: SWE-bench moves only
**1.54 pp from 1× to 5×**. Measure it for your own suite rather than importing a multiplier.

## What a number authorises

Evidence licenses the next action its scope supports, and nothing further. A worked
three-round loop on a deliberately narrow slice — four tasks, one run each, model, seed,
step limit and environment fixed, arm order alternated, **one variable changed per round**:

| Round | The only change | Success | Tokens vs control | What it authorised |
|---|---|---|---|---|
| H1 | added navigation and final-check instructions | 25% → 25% | 0.47× | the prompt is not the bottleneck — stop tuning it |
| H5 | accessibility feed → UIAutomator tree | 25% → **100%** | **2.498×** | right mechanism, too expensive — try to cheapen it |
| H5C | prune invisible/textless/non-actionable nodes | 100% → 100% | **0.506×** | qualifies for a full rerun |

Two rules fall out, and the second is the one people skip:

- **Observation before prompt.** More detailed instructions cannot restore information the
  agent never received. When a score will not move, ask what the agent could see before
  asking how it was asked.
- **4/4 on a slice is not 100% system-wide, and must not be reported as one.** With four
  tasks per arm these numbers can decide whether a larger rerun is worth paying for. They
  cannot estimate success across the benchmark. The ladder's output is *the next
  experiment*, not a result.

## The report contract

A comparison that will change a decision states all of these, or it is a claim rather than
a measurement:

- [ ] `n` — how many tasks, and `k` — how many runs each
- [ ] which reducer: `pass@k`, `pass^k`, `mean`, and **which k means what**
- [ ] the noise band for that `n`, computed
- [ ] paired or unpaired; if paired, the seed set
- [ ] the harness configuration: resource floor and ceiling, isolation between trials
- [ ] whether the difference reproduced on a rerun
- [ ] what the scope of the evidence authorises next — not what it suggests

**A green suite with none of these is a number, not a verdict.** That distinction is the
reason this file exists.
