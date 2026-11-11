#!/usr/bin/env python3
"""Bounded text regression for agent-evals production metrics (0.33.0).

Watches the clauses that make a production metric decidable: the minimum set, the named
population, null for not measured, the read-back, the survivor denominator, small n as
inconclusive, and the link from a failing unit to a permanent fixture. Plants remove each
clause and must fail; an unrelated wording edit must pass. It does not execute an agent.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / 'plugins/agent-stack/skills/agent-evals'

CLAUSES = (
    ('at least one `outcome`, one `quality` and one `reliability` metric', 'minimum set'),
    ('a metric without a named population is refused', 'named population'),
    ('never changes in place', 'versioned definition'),
    ('Not measured is `null`, never 0', 'null not zero'),
    ('Read the write back.', 'read-back'),
    ('The denominator is the population, not the survivors.', 'survivor denominator'),
    ('Small `n` is `inconclusive`, never a win.', 'small n'),
    ('A prediction is written before the change and scored after it.', 'prediction'),
    ('It stays in the suite permanently', 'permanent fixture'),
)
VERDICTS = ('`improved`', '`worse`', '`no_effect_detected`', '`inconclusive`')


def errors(skill, ref):
    flat = ' '.join(ref.split())
    failures = [f'missing {label}' for needle, label in CLAUSES if needle not in flat]
    failures += [f'missing verdict {v}' for v in VERDICTS if f'| {v} |' not in flat]
    if '<!-- production-metrics:' not in ref:
        failures.append('missing contract marker')
    if 'references/production-metrics.md' not in skill:
        failures.append('SKILL.md does not route to production-metrics.md')
    if 'agent.runTool?.()' not in flat:
        failures.append('the motivating silent no-op case is gone')
    return failures


def main():
    skill = (HOME / 'SKILL.md').read_text(encoding='utf-8')
    ref = (HOME / 'references/production-metrics.md').read_text(encoding='utf-8')
    problems = errors(skill, ref)
    for p in problems:
        print('FAIL:', p)
    if problems:
        return 1
    checks = 0
    for needle, label in CLAUSES:
        assert needle in ' '.join(ref.split()), label
        planted = ' '.join(ref.split()).replace(needle, 'REMOVED')
        assert errors(skill, planted), label
        checks += 1
    for v in VERDICTS:
        assert errors(skill, ref.replace(f'| {v} |', '| maybe |')), v
        checks += 1
    assert errors(skill.replace('references/production-metrics.md', 'references/x.md'), ref)
    checks += 1
    assert not errors(skill, ref.replace('Values in the example are illustrative.',
                                         'The example values are illustrative.'))
    checks += 1
    print(f'PASS: production-metrics: {checks} plants/controls on the candidate text')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
