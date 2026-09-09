#!/usr/bin/env python3
"""FIX-AS-09.01 — extensible OTel fields, and total vs bucket tokens (sherlock
audit, AS-09).

The finding: `gen_ai.operation.name` was called a closed 17-value enum where a
value outside it "is not an extension" — but the semconv treats it as a
well-known SET; a provider value with no match is allowed and must not be
silently dropped, an unknown value kept raw. And the token text claimed
input+output "misses reasoning and cache writes entirely", when those are
SUBSETS of the totals, not additions.

The fix under test: the doc states the extensible set with raw-value
preservation and a schema-revision/observation-date rule; the cost model
subtracts the cached portion rather than re-adding buckets. The
total-vs-bucket accounting is run as behaviour.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "plugins", "agent-stack", "skills", "agent-evals",
                   "references", "otel-genai.md")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_extensible_set():
    flat = " ".join(open(DOC, encoding="utf-8").read().split())
    for needle in ("well-known SET, not a closed enum",
                   "a provider\noperation with no matching well-known value is allowed to "
                   "carry a custom value".replace("\n", " "),
                   "an unknown value is stored RAW",
                   "schema revision and the commit SHA",
                   "plus the observation date"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"
    assert "closed 17-value enum" not in flat, "the closed-enum claim survived"
    assert "misses reasoning tokens and\ncache writes entirely".replace("\n", " ") not in flat, \
        "the 'misses reasoning/cache entirely' claim survived"


def t_doctrine_states_total_vs_bucket():
    flat = " ".join(open(DOC, encoding="utf-8").read().split())
    for needle in ("TOTALS and\nDISJOINT BILLING BUCKETS".replace("\n", " "),
                   "`reasoning.output_tokens` is a SUBSET of\n`output_tokens`".replace("\n", " "),
                   "SUBTRACT the cached portion from\nthe total".replace("\n", " "),
                   "The fix is NOT to add reasoning or modality counters back onto "
                   "the totals"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"


# ---------------- the token accounting, executed


def preserve_operation(value, well_known):
    """A well-known value is kept as-is; an unknown one is kept RAW, never
    dropped."""
    return {"name": value, "well_known": value in well_known}


def cost(usage, rates):
    """Correct cost: the cached input portion is priced at the cache rate, the
    rest of the input at the full rate, output at the output rate. Reasoning
    and modality counters are SUBSETS and are NOT re-added."""
    inp = usage["input_tokens"]
    cache_read = usage.get("cache_read.input_tokens", 0)
    cache_write = usage.get("cache_write.input_tokens", 0)
    full_input = inp - cache_read              # cache_read is a subset of input
    out = usage["output_tokens"]               # reasoning is a subset of output
    return (full_input * rates["input"]
            + cache_read * rates["cache_read"]
            + cache_write * rates["cache_write"]
            + out * rates["output"])


WELL_KNOWN = {"chat", "embeddings", "execute_tool", "invoke_agent", "plan"}


def t_unknown_operation_kept_raw():
    known = preserve_operation("chat", WELL_KNOWN)
    assert known["well_known"] is True
    custom = preserve_operation("provider.rerank", WELL_KNOWN)
    assert custom["name"] == "provider.rerank" and custom["well_known"] is False, \
        "an unknown operation value was dropped or renamed — the finding itself"


def t_cache_read_is_not_billed_at_full_rate():
    usage = {"input_tokens": 1000, "output_tokens": 200,
             "cache_read.input_tokens": 800}
    rates = {"input": 3.0, "cache_read": 0.3, "cache_write": 3.75, "output": 15.0}
    c = cost(usage, rates)
    # 200 full input @3 + 800 cache_read @0.3 + 200 output @15
    assert c == 200 * 3.0 + 800 * 0.3 + 200 * 15.0, f"cost mis-priced: {c}"
    naive = (usage["input_tokens"] * rates["input"]
             + usage["output_tokens"] * rates["output"])
    assert c < naive, "the corrected cost did not undercut the naive full-price input"


def t_reasoning_and_modalities_not_double_counted():
    # reasoning.output_tokens is a subset of output_tokens; adding it would
    # double-count. The cost function ignores it, so passing it changes nothing.
    base = {"input_tokens": 500, "output_tokens": 300, "cache_read.input_tokens": 0}
    rates = {"input": 3.0, "cache_read": 0.3, "cache_write": 3.75, "output": 15.0}
    c1 = cost(base, rates)
    with_reasoning = dict(base, **{"reasoning.output_tokens": 120,
                                   "text.output_tokens": 180})
    c2 = cost(with_reasoning, rates)
    assert c1 == c2, "reasoning/modality subsets were re-added to the total — double billing"


def main():
    case("the doctrine states the extensible well-known set and provenance",
         t_doctrine_states_extensible_set)
    case("the doctrine separates totals from disjoint billing buckets",
         t_doctrine_states_total_vs_bucket)
    case("an unknown operation value is kept raw, not dropped",
         t_unknown_operation_kept_raw)
    case("cache reads are not billed at the full input rate",
         t_cache_read_is_not_billed_at_full_rate)
    case("reasoning and modality subsets are not double-counted",
         t_reasoning_and_modalities_not_double_counted)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
