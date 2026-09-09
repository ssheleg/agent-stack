#!/usr/bin/env python3
"""FIX-AS-09.02 — disjoint billing buckets reconcile (sherlock audit, AS-09
leaf 2, on FIX-AS-09.01).

The rules under test: totals are NOT summed with cached/modality/reasoning
subsets; provider rates apply to DISJOINT buckets; a cached token is never
charged twice; and the price receipt reconciles with the totals against an
independent worked example. Documented in otel-genai.md, and the receipt is
recomputed as behaviour.

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


def t_doctrine_has_the_worked_receipt():
    flat = " ".join(open(DOC, encoding="utf-8").read().split())
    for needle in ("The worked receipt — a disjoint partition that reconciles",
                   "| input, full-rate = `input − cache_read` | 200 | $3.00 | $0.60 |",
                   "| **total** | | | **$3.84** |",
                   "sum back to the totals",
                   "reasoning's 120 is inside it, never a fourth line",
                   "OVER-charges by pricing the 800 cached tokens"):
        assert needle in flat, f"the doctrine no longer states {needle!r}"


# ---------------- the receipt, recomputed


def receipt(usage, rates):
    inp = usage["input_tokens"]
    cache_read = usage.get("cache_read.input_tokens", 0)
    cache_write = usage.get("cache_write.input_tokens", 0)
    out = usage["output_tokens"]
    full_input = inp - cache_read
    buckets = {
        "input_full": (full_input, rates["input"]),
        "cache_read": (cache_read, rates["cache_read"]),
        "cache_write": (cache_write, rates.get("cache_write", 0.0)),
        "output": (out, rates["output"]),
    }
    total = sum(tok / 1000 * rate for tok, rate in buckets.values())
    return buckets, total


USAGE = {"input_tokens": 1000, "cache_read.input_tokens": 800,
         "output_tokens": 200, "reasoning.output_tokens": 120}
RATES = {"input": 3.0, "cache_read": 0.30, "cache_write": 3.75, "output": 15.0}


def t_receipt_matches_the_worked_example():
    _b, total = receipt(USAGE, RATES)
    assert abs(total - 3.84) < 1e-9, f"the receipt does not reconcile: {total}"


def t_buckets_sum_back_to_the_totals():
    buckets, _ = receipt(USAGE, RATES)
    input_tokens = buckets["input_full"][0] + buckets["cache_read"][0]
    assert input_tokens == USAGE["input_tokens"], "input buckets do not sum to the total"
    assert buckets["output"][0] == USAGE["output_tokens"], \
        "output includes reasoning as an extra line — double counting"


def t_no_cached_token_charged_twice():
    buckets, _ = receipt(USAGE, RATES)
    # the 800 cached tokens appear ONLY in cache_read, never in input_full
    assert buckets["input_full"][0] == 200 and buckets["cache_read"][0] == 800
    assert buckets["input_full"][0] + buckets["cache_read"][0] == 1000, \
        "a cached token was priced in two buckets"


def t_naive_sum_overcharges():
    naive = (USAGE["input_tokens"] / 1000 * RATES["input"]
             + USAGE["output_tokens"] / 1000 * RATES["output"])
    _b, correct = receipt(USAGE, RATES)
    assert naive > correct, "the naive input+output did not over-charge vs the receipt"
    assert abs(naive - 6.0) < 1e-9, f"the naive figure is not the documented $6.00: {naive}"


def main():
    case("the doctrine carries the worked reconciling receipt",
         t_doctrine_has_the_worked_receipt)
    case("the receipt matches the worked example ($3.84)",
         t_receipt_matches_the_worked_example)
    case("the priced buckets sum back to the totals", t_buckets_sum_back_to_the_totals)
    case("no cached token is charged twice", t_no_cached_token_charged_twice)
    case("the naive input+output over-charges", t_naive_sum_overcharges)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
