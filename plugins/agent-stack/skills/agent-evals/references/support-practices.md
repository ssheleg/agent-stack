# Practices for agents that answer people: pipeline, models, supervisors and the improvement loop

**Load this when building, auditing or improving an agent that answers people** (chat, mail, store
reviews, group chats), and `support-quality.md` already tells you how it is measured. That file is the
standard; this one is what an audit of five such agents in one estate found working and failing, and
the traps found in the system that measured them.

Evidence: unless a line says otherwise, every practice here is **`FIELD`** (one estate, five production
agents on four channels, read in code and live numbers on 2026-10-26 and 2026-10-27). A number is that
estate's measurement, never a forecast: `FIELD` means practitioner cases without a control.

## Contents

- [P1. The answer pipeline](#p1-the-answer-pipeline)
- [P2. Checks before sending](#p2-checks-before-sending)
- [P3. Hand-offs and promises](#p3-hand-offs-and-promises)
- [P4. Model lanes and fallbacks](#p4-model-lanes-and-fallbacks)
- [P5. Four supervisors, four granularities](#p5-four-supervisors-four-granularities)
- [P6. Measurement traps](#p6-measurement-traps)
- [P7. The improvement loop](#p7-the-improvement-loop)
- [P8. What lives once](#p8-what-lives-once)
- [Checklist](#checklist)

## P1. The answer pipeline

The best of the five agents (rated so by its operator, and with the fewest hand-offs) differed from the
other four in structure, not in model. Its writer model was the same as theirs.

- **A small closed rule set goes into the prompt whole.** Prices, payment terms, refunds, sign-in: put
  every approved rule in the prompt, ordered by owner and dated, instead of hoping retrieval ranks the
  right one first. That agent has no retrieval misses by construction. Retrieval stays for the long tail.
  The other four abstained on questions whose answer was published: one ranked a pricing fact at
  coverage 0.38 against a 0.6 floor because the question said "activate" and the fact did not.
- **One relevance threshold, at the knowledge service.** Four consumers each re-derived "may this item be
  given as an answer" with their own 0.6 and their own first-place rules. The service now returns an
  `answer` flag per item; a consumer reads it and keeps no threshold of its own.
- **The whole conversation, not its tail.** The best agent passes up to 24,000 characters (200 rows),
  sessions split at an 8-hour gap. Others passed 4 messages to the search step, or the mail subject plus
  600 characters including quoted history and greetings. Strip quoted text before a query; restate the
  question in the knowledge base's language for every language, not only foreign ones.
- **Numbers come from tools, never from the model.** Prices from a calculator, the person's own account
  state and order from the system, injected per turn.
- **Read a burst as one turn.** Debounce messages of one person (60 s in chat), and give a human a grace
  window before the first reply in a new conversation (5 min where an operator answers too).
- **Re-read the live tail before sending.** If a person or the agent already answered, skip the turn.

## P2. Checks before sending

- **Deterministic gates first, including false-state gates.** The model may not say that money arrived,
  that something is live, enabled or fixed, or that a person did something, unless the system backs it.
  In one agent's review of live conversations the two costliest errors in its history were exactly
  these. A rubric judge sees them only after the person read them.
- **A checker of another vendor than the writer, that sees the material.** All five agents do this; a
  same-vendor checker shared the writer's blind spots. Put the material **before** the instructions in
  the checker's context: one agent cut the checker's input to 16,000 characters after up to 20,000 of
  operator instructions, so correct answers were refused as invented.
- **Repair, then research, then hold.** On a failed check: one repair with the checker's reason; then a
  research turn on a stronger model that sees both rejected drafts and approved past answers; only then
  an honest holding line. Money reasons are never researched. The agents that handed off at the first
  refusal had the lowest "helped".
- **A hold comes back by itself.** When a person or the knowledge base answers the held question, the
  conversation is re-run and the person gets the answer without asking again.

## P3. Hand-offs and promises

- **A hand-off is not an answer.** Do not count it as answered, and keep hand-off and fallback templates
  out of the judge's sample: one mail agent's "helped 0 of 7" was mostly its judge grading routing
  templates. One group agent's prompt told it to hand off whenever the checker refused an inference,
  so answerable questions became "contact support" and the judge rated them "partly".
- **Split "could not" by cause.** One counter lumped real knowledge gaps with checker infrastructure
  errors, skipped repairs and turns that ran out of time. Keep `policy`, `inability` and
  `infrastructure` apart, or the biggest number tells nobody what to fix.
- **Keep a commitments ledger.** "I will pass this to the team and come back" needs an owner and a due
  date. The best agent's own review found one money request that waited 18 days. Count promises made
  and promises closed per week.
- **Per-conversation operator directives.** When an operator corrects one conversation, extract the
  correction and keep it for that conversation.
- **Count only what really waits for a person.** A queue that counts every open knowledge request,
  including hand-offs that expire after 7 days, reads 160 hours old by design.

## P4. Model lanes and fallbacks

| Lane | Job | Rule |
|---|---|---|
| Classifier | topic, language, intent, the English restatement | cheap, deterministic output schema with a closed enum and a description per value |
| Writer | the reply | the strongest model the latency allows |
| Fallback writer | the same reply | another model, on a throw, an empty answer, a provider refusal or prose without the required structure |
| Checker | approve or refuse a send | another vendor than the writer; sees the material |
| Research | the second attempt after a refusal | a stronger model, a hard time cap |
| Judge | the daily sample | another vendor than writer and checker; temperature 0; open vendor for text people wrote |

- **Reasoning budget is a latency setting; measure it.** One mail writer spent about 4,400 reasoning
  tokens on an 85-character mail and timed out at 90 s on 11 of 21 replayed mails; with reasoning off,
  0 of 21 timed out and p90 fell from 105 s to 33 s, while 17 of 21 send-or-hold decisions stayed the
  same. Replay a week offline before switching.
- **Count what a fallback recovered**, not only the first attempt's failures: 12 of 59 calls failed and a
  fallback recovered 11, so one run, not twelve, was lost.
- **Changing the writer model is a replay, not a guess.** Re-answer last week's judged sample offline on
  the current model and two candidates, judged blind; switch when "helped" rises enough without
  `policy_safe` falling. Retrieval and hand-off rules usually move "helped" more than the model does.

## P5. Four supervisors, four granularities

| Supervisor | Sees | Catches | Cannot catch |
|---|---|---|---|
| Pre-send checker | one draft and its material | unsupported claims, wrong routing, false state (with gates) | a conversation going in circles |
| Daily judge | a capped sample of sent turns | tone, addressed, actionable, continuity trends | factual accuracy without the material; anything before a person reads it |
| Weekly assessor | every agent's daily counts | owners, causes and priorities of what to fix, week over week | why a single conversation failed |
| Conversation coach | a whole thread | unkept promises, repeated loops, lost context across turns | per-turn facts (that is the checker's) |

A supervisor that has never rejected anything is a finding (SKILL.md §5a). Store every verdict with its
source (`human`, `llm_judge`, `code_check`) so it can be calibrated.

## P6. Measurement traps

Found in the system that measured the five agents, each of which had made a shipped number wrong:

- **A missing label counted as a disagreement.** Two channels carried no sentiment; agreement with the
  judge counted every null as a miss, so "tone agrees 46%" was mostly the method. Leave out pairs where
  either side is missing and count them apart.
- **A scaled count used as "people affected".** One reader kept judge check counts multiplied by 100 to
  preserve rate precision, then used them as the number of people a finding reached: those findings
  ranked about 100 times too high. Derive "affected" as the failed share times the judged sample.
- **Silence read as a fix.** A channel that stopped reporting produced no findings, so last week's
  findings were marked resolved. A finding whose channel was not measured is "not measured", never
  resolved.
- **A publishing lag read as silence.** One producer publishes day D at D+2 00:05 UTC by design; a
  2-day freshness threshold called it silent every night. Freshness is per producer.
- **A reader that passed a new event kind.** A reader that started accepting a new kind had already moved
  its cursor past the first event of it. A reader change that adds a kind ships with a one-time re-read.
- **One counter, two definitions.** An agent's own repeat count said 2 a week and its published
  `agentRepeat` said 19, because the published one also counted two templated hand-offs in a row.
- **Log lines counted as process errors.** One database outage of three minutes wrote 74 of a week's 82
  "process errors", one per traceback line. Count events, not lines.
- **Definitions that disagree with the code.** A share documented as answered over volume was computed as
  answered over decided; hand-offs to another bot were counted as hand-offs to a person; the same
  unanswered people were charged three times to one owner. Generate the definitions from the code or
  test them against it.
- **Uncalibrated judges opening ranked findings.** No live alert fired from an uncalibrated judge, but
  weekly findings did, at full weight. Until a check reaches 80% agreement with a person it is a note.
- **A model judge compared to a model labeller, both fitted to each other.** Rules were tuned to agree
  with the judge and the judge's rules were written to match. Agreement between them measures the
  fitting, not accuracy; anchor both to human labels.

## P7. The improvement loop

1. **Every abstention and inability becomes a gap**, restated without personal data, grouped by meaning
   at intake, not only by exact text.
2. **Re-answer when the knowledge changes**, but skip the model when the retrieved material is the same
   as last time; re-query after a gap closes to confirm the answer is now confident before rewriting.
3. **A proposal is gated in code, not only in the prompt.** A new user-facing fact without an owner's
   decision id is refused; the run that proposes a fact never also closes the gap it answers, a separate
   checker does; a refused publish is a partial day, not done.
4. **Measure the effect of each proposal**: abstentions and later answers on its question cluster for 7
   days before and after, with the sample size stated (`statistics.md`). Without it the loop reports
   what it did, never what it changed.
5. **Find the shared weak link first.** In this estate one ranking release moved connection questions
   from 3 to 24 of 28 and ban questions from 5 to 14 of 17 with the expected answer first, across every
   channel at once. A per-channel fix would have moved one.

## P8. What lives once

| Piece | Lives in |
|---|---|
| "May this item be given as an answer" | the knowledge service, as a per-item flag |
| Personal-data screening of text | one check the knowledge service exposes, plus one library |
| The knowledge client, gap outbox and re-query after close | one shared client package |
| The English restatement prompt and contract | the shared package |
| Rubric, vendor exclusion and the `support.quality_daily` builder | one support-quality package, its schema pinned by consumers |
| Hand-off policy categories | one owner decision record every agent reads |
| Channel-specific checks (store length, brand words, store policy) | the channel's own agent |

Five copies of one piece drift: in this estate four thresholds, six personal-data screens and two
definitions of one counter.

## Checklist

- [ ] Small closed rule sets in the prompt whole; retrieval only for the long tail
- [ ] One relevance threshold, at the knowledge service; consumers read its per-item flag
- [ ] The whole conversation in context; quoted mail stripped before a query; every language restated
- [ ] Numbers and account state from tools, never from the model
- [ ] Deterministic false-state gates before any model checker
- [ ] Checker of another vendor that sees the material, material placed before instructions
- [ ] Repair, then research, then an honest hold that comes back by itself
- [ ] Hand-offs and fallbacks never counted as answers nor judged as answers
- [ ] `policy`, `inability` and `infrastructure` hand-offs counted apart
- [ ] A commitments ledger: promises made and closed per week
- [ ] Fallback recoveries counted; reasoning budget measured by offline replay
- [ ] A model change decided by a blind offline replay of last week's sample
- [ ] Every supervisor's verdicts stored with their source; a never-rejecting supervisor is a finding
- [ ] Null labels left out of agreement; "affected" never taken from scaled counts
- [ ] A silent channel is "not measured", never resolved; freshness per producer
- [ ] A reader that adds an event kind re-reads its feed once
- [ ] Definitions tested against the code; no person charged twice
- [ ] Every proposal of the learning loop gated in code and measured before and after
