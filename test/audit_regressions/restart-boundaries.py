#!/usr/bin/env python3
"""Bounded text regression for the unsafe restart instructions in 0.28.1.

This watches known unsafe clauses return and critical admission clauses disappear.
It does not execute an agent or prove arbitrary prose/host semantics. Counterexample
schedules and the manual baseline/candidate reading live in the dated owner receipt.
No temporary trees, provider requests or runtime implementation are introduced.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HOME = ROOT / 'plugins/agent-stack/skills/agent-orchestrator'

def errors(skill, runtime):
    section = runtime.split('## A limit stop is not a wait\n', 1)[1].split('\n## ', 1)[0]
    flat = ' '.join(section.split())
    failures = []
    for forbidden in ('stop the workflow, then resume it',
                      'finished agents replay from the cache',
                      'Changed arguments invalidate the cache, so the whole run is paid for again.',
                      'usually finds it runs'):
        if forbidden in flat: failures.append('unqualified restart/cache claim: '+forbidden)
    for needle, label in (
        ('Do not stop the whole workflow for one failed lane.', 'lane isolation'),
        ('reconcile every sibling and in-flight effect before stopping', 'sibling admission'),
        ('Do not blindly replay an outward effect with an unknown outcome.', 'uncertain effect'),
        ('finite attempt cap and a deadline', 'retry ceiling'),
        ('Retry-After', 'provider timing'),
        ('recheck that the task is still active and authorized', 'current authority'),
        ('not a promise that an effect was not performed', 'checkpoint distinction'),
    ):
        if needle not in flat: failures.append('missing '+label)
    body = ' '.join(skill.split())
    if 'bounded, authorized resume' not in body or 'not every silence is a stall' not in body:
        failures.append('body bypasses bounded admission')
    return failures

def main():
    skill=(HOME/'SKILL.md').read_text();runtime=(HOME/'references/runtime.md').read_text()
    problems=errors(skill,runtime)
    for p in problems: print('FAIL:',p)
    if problems:return 1
    # Plants run against actual candidate text: a safe unrelated wording edit remains
    # accepted; removing a relevant constraint and restoring old operational commands fail.
    checks=0
    for phrase in ('Do not stop the whole workflow for one failed lane.',
                   'reconcile every sibling and in-flight effect before stopping',
                   'Do not blindly replay an outward effect with an unknown outcome.',
                   'finite attempt cap and a deadline','Retry-After',
                   'recheck that the task is still active and authorized'):
        assert phrase in runtime
        assert errors(skill,runtime.replace(phrase,'REMOVED')),phrase
        checks+=1
    for old in ('stop the workflow, then resume it',
                'finished agents replay from the cache',
                'usually finds it runs'):
        planted=runtime.replace('## A limit stop is not a wait\n','## A limit stop is not a wait\n'+old+'\n',1)
        assert errors(skill,planted),old
        checks+=1
    assert not errors(skill,runtime.replace('Log each attempt','Record each attempt'))
    checks+=1
    assert errors(skill.replace('bounded, authorized resume','resume now'),runtime)
    checks+=1
    print(f'PASS: restart-boundaries — candidate contract + {checks} text plants/controls; no agent replay')
    return 0
if __name__=='__main__':raise SystemExit(main())
