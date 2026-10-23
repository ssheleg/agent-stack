# Support quality standard v1, for agents that talk to people

**Load this when an agent answers people** (private chat, mail, store reviews, a group
chat or community) and its quality must be measured the way every other such agent is
measured: the per-turn record, the daily metrics, the judge's rubric, the daily event a
voice-of-the-customer reader consumes, and the weekly loop that turns numbers into fixes.

Status: v1, measured on a live support chat agent first; this file is the product-neutral
part. The targets below are v1 targets. The baseline at the end is one deployment's
measurement, not a target.

<!-- support-standard: A1, A2, A3, A4, A5, A6, A7 | channels: private-chat, mail, store-review, group-chat -->

## Contents

- [Goal](#goal)
- [A1. The record](#a1-the-record)
- [A2. Four metric families](#a2-four-metric-families)
- [A3. The rubric](#a3-the-rubric)
- [A4. The judge](#a4-the-judge)
- [A5. Reporting: support.quality_daily](#a5-reporting-supportquality_daily)
- [A6. Autonomy without blocking](#a6-autonomy-without-blocking)
- [A7. Portability](#a7-portability)
- [The weekly assessment loop](#the-weekly-assessment-loop)
- [Checks that caught real defects](#checks-that-caught-real-defects)
- [Baseline from the first deployment](#baseline-from-the-first-deployment)
- [Checklist](#checklist)

## Goal

Every agent that answers people is measured the same way, reports into one
voice-of-the-customer (VoC) agent, never drops a person, and needs a human only where one
is truly necessary, without the human blocking the work.

In this skill's terms the daily metrics and the judge are the **online tier** (SKILL.md
§3): reference-free and never a release gate. The judge follows §5 (calibrated before it
is trusted); week-over-week comparisons follow `statistics.md`.

## A1. The record

Every inbound message becomes a **turn** with a durable trace id. The id is on the turn
row, on every model call of that turn, on its log line, and on any copy a person reads.

The turn stores:

- its **outcome**: answered, general guidance, not covered, handed off, small talk,
  limit, error;
- the hand-off reason, a category, the latency;
- the knowledge revision the answer used;
- whether the channel accepted the reply.

Conversation text is privacy-redacted, kept by the agent for at most 30 days, and never
leaves the agent. Everything downstream (A5, the weekly loop) reads counts and codes.

## A2. Four metric families

Computed per channel per **closed UTC day**. A metric that was not computed is **not
measured, never 0**: a zero reads as a perfect day, and the reader cannot tell it from
one.

| Family | Metric | v1 target |
|---|---|---|
| Nobody dropped | reply coverage | 100% |
| Nobody dropped | first reply p50 and p90 | p90 per channel kind (table below) |
| Nobody dropped | repeat-ask rate: the person sends the same message again | under 3% |
| Nobody dropped | agent-repeat: the agent sends the same reply twice in a row to the same person | 0 |
| Nobody dropped | questions answered later, when the knowledge arrived | counted |
| Quality | helped yes / partly / no among real questions (A4's daily sample) | yes at least 60%, no at most 15% |
| Quality | pass rate per rubric check (A3) | each at least 90% |
| Stability | turn errors | 0 |
| Stability | model-call failures per lane, and the share a fallback recovered | counted |
| Stability | process errors, restarts, knowledge freshness | counted |
| Autonomy | resolved without a person | counted |
| Autonomy | sent to a person for **policy** (categories a person must handle) | counted |
| Autonomy | sent to a person for **inability** (the agent could not answer) | falls toward 0 |
| Autonomy | the person queue's oldest item against its SLA | within SLA |

**First reply is measured from the person's message to the sent reply.** That includes
any batching wait; processing time alone flatters the number.

**First-reply p90 targets are per channel kind.** One target across channels raises false
alerts: a store review reply may be held by design, so a chat target on it fires every day.

| Channel kind | First-reply p90 target |
|---|---|
| `private-chat` | under 30 s |
| `mail` | under 4 h |
| `store-review` | under 24 h |
| `group-chat` | an owed question answered within the agent's come-back window (the first deployment used 6 h) |

A consumer applies the channel's own target, never a global one.

**Agent-repeat counts replies actually sent**, read from the stored conversation of the
UTC day. A repeat the agent detected and refused to send is not a repeat the person saw.

## A3. The rubric

Rubric v1. Each check is PASS, FAIL or NA, in the narrow pass/fail shape of SKILL.md §4.

| Check | PASS when |
|---|---|
| `language` | the reply is in the person's language, with no paragraph in another language |
| `addressed` | it answers what was asked, not a template |
| `policy_safe` | it never asks for codes or passwords and never promises refunds, unbans or account recovery |
| `routing` | it answers what it can and hands to a person only policy cases or true inability; one closing "a person can help if this does not" line is a PASS; it never sends the person to the agent itself |
| `actionable` | it gives the person a step to take |
| `continuity` | it repeats no earlier reply and ignores nothing the person already said |

Beside the checks the judge returns **helped** (yes, partly, no) and a **note** of at most
15 English words carrying no personal data.

**Factual accuracy is not the judge's job.** A judge without the source material calls real
features invented: in the first deployment, 8 of 12 "unsafe" verdicts were wrong for
exactly that reason. Accuracy is checked **before sending**, by a checker from a different
vendor that sees the material. This is §5's *some things a judge cannot do*, met with a
pre-send check instead of a human tier.

## A4. The judge

- **A different vendor from the drafter.** For text people wrote, an open-vendor model.
- Temperature 0, JSON output, and the **rubric version on every verdict**.
- Runs daily over the previous day, on a **capped sample**, inside the agent's own budget.
  The first deployment judged questions only (not small talk), up to 60 a day, spread
  over the day rather than taken from its start.
- **Calibrated against weekly human labels** in the VoC agent's annotation queue, with
  agreement shown per check. A check under 80% agreement raises no alert. A week with no
  labels never blocks anything.

## A5. Reporting: support.quality_daily

Each agent publishes on its events feed one `support.quality_daily` per closed UTC day and
channel, carrying:

- the four families of A2, as counts;
- the judge model and the rubric version;
- `notMeasured`: the names of the metric families not computed that day.

**Counts and codes only:** no person's words, no ids, no judge notes. The VoC agent owns
the cross-channel table, the SLO alerts, the annotation queue and the weekly report.

**A not-measured metric is null and named, never 0.** When no turn of the day carries a
first reply time, `firstReplyP50Ms` and `firstReplyP90Ms` are null and `notMeasured` names
the family, `firstReply`. An earlier draft named the two fields instead; the producer's own
name pattern allows no digits, so those names failed it.

**Run every `notMeasured` name the producer can emit through the published pattern, in a
test.** That test caught the draft above before it shipped. The list of names is the
producer's to enumerate, so the test iterates the producer's list, not a hand copy.

## A6. Autonomy without blocking

- **Answer first.** Never a dead end: the immediate reply says what happens next.
- A person's queue has an **SLA**. It escalates once; past a second limit a **pre-agreed
  safe default** acts.
- **Come back with the answer** when the knowledge arrives.
- Every inability hand-off is reported as a **knowledge gap**, restated without personal
  data, and the gap count must fall.

## A7. Portability

The standard lives here, as a reference of the `agent-evals` skill. The event schema
belongs in the agent contract its consumers pin, and the VoC agent is its reader. A new
machine or estate gets all three with its infrastructure, not by copying a deployment.

## The weekly assessment loop

1. **Every agent that talks to people publishes its day** in the A5 shape: coverage, judge
   quality, stability, autonomy, the person queue. Counts and codes only.
2. **Once a week an assessor turns the numbers into findings.** Each finding carries its
   evidence, a **cause class**, the **owning agent**, the **action** and a **priority**
   (people affected times the cause weight). Cause classes: no knowledge; knowledge not
   used; routing settings; answer quality; someone not answered; fallbacks; data; the
   assessor's own labels.
3. **Each finding goes to its owner's board.** The next week compares by **finding id**:
   new, still there for N weeks, better, worse, resolved. A fix is measured, not assumed.
4. **A model may write "what to fix first", labelled as a model.** The findings themselves
   are rules over numbers, and every number is checkable.

## Checks that caught real defects

From the first weekly loop and the first producer, each on its first day:

- **The producer's schema is the test fixture, pinned to a commit.** It caught a required
  field added the same day, and a schema version that was never emitted.
- **A judge's miss raises no alert until a person has calibrated that check at 80% or
  more** (A4).
- **"Not measured" is never 0.** A planted defect that reads it as 0 fails a test.
- **Every `notMeasured` name the producer can emit passes the published pattern** in a
  test (A5).
- **Targets are set per channel kind.** A chat target on an asynchronous channel produced
  a false alert (A2).
- **First reply is measured from the person's message to the sent reply** (A2), so the
  batching wait is in the number.
- **Stored derived reports are scrubbed when the source item is deleted.** A privacy test
  found the assessment's evidence keeping a deleted paraphrase.

One defect none of these caught: a daily follow-up counter read 0 from the start because
follow-up rows carried no category, and a 0 looks like a quiet day. **A counter that has
never moved is a finding**, the same rule SKILL.md §5a applies to a checker that has never
rejected anything.

## Baseline from the first deployment

One deployment's measurement over 7 days, not a target: 0 messages without a reply; first
reply p50 8.3 s, p90 17 s; 0 turn errors; helped 39% of 142 questions, at a judge cost of
$0.021.

The helped share sits below A2's 60% target even at the top of its noise band: 55 or 56
of 142 (both round to 39%) give a 95% Wilson interval of about 31% to 48%
(`statistics.md`). The weekly loop exists for exactly that gap.

The review found two defects, both fixed: a paragraph in another language appended to
replies (the `language` check), and the same reply sent again after a bare "?" (the
`continuity` check and agent-repeat).

## Checklist

- [ ] Every inbound message is a turn with one trace id on the row, its model calls, its
      log line and any copy a person reads
- [ ] Conversation text redacted, kept at most 30 days, never leaves the agent
- [ ] Four families per channel per closed UTC day; a metric not computed is null and
      named in `notMeasured`, never 0, with a planted test
- [ ] First-reply p90 target taken from the channel kind; first reply measured from the
      person's message to the sent reply
- [ ] Rubric v1 checks PASS/FAIL/NA, plus helped and a short note without personal data
- [ ] Factual accuracy checked before sending by another vendor's checker that sees the
      material, not by the judge
- [ ] Judge from another vendor, temperature 0, JSON, rubric version on every verdict,
      capped and inside the agent's budget
- [ ] No alert from a check until human agreement on it is at least 80%
- [ ] `support.quality_daily` carries counts and codes only; every `notMeasured` name the
      producer can emit runs through the published pattern in a test
- [ ] The producer's schema pinned to a commit as the consumer's fixture
- [ ] Weekly findings with evidence, cause class, owner, action and priority, compared by
      finding id week over week
- [ ] Derived reports scrubbed when their source item is deleted
