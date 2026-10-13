# FW01 source discovery completeness — agent-stack

## Frozen packet and baseline

Owner source: [63e155d](https://github.com/ssheleg/agent-stack/commit/63e155d9c1ca9df789535926acc3546f33954e3b).
Version remains 0.28.2; this packet changes owner validation and evidence only.
The [actual whole-validator baseline](baseline.json) executes `python3 -B test/validate.py`
in an immutable Git-source fixture: healthy exits 0, readable unauthorized maker exits
1, then its parent directory is made unreadable (OS PermissionError independently
confirmed) and the same validator exits 0. This proves a discovery omission, beyond
an extracted-helper observation. No complete owner suite or native runtime was run.

The upstream family finding is
[the bounded central receipt](https://github.com/ssheleg/sshlg-skills/blob/38b69b1d3c022f45e4ac3464c5b83f4b96047852/docs/evidence/completion-1013/fw01-discovery-followup.json).
SEO's same discovery seam was corrected at
[76d25cd](https://github.com/ssheleg/seo-aeo-audit/commit/76d25cd5c283bce7c4fdd25c7c42fee7038fe1b2).
Its lexical/exemption policy is not copied into this owner.

## Contract and acceptance

- Keep this owner's scanner predicate, skip directories, lexical matching and exact
  exemptions unchanged. Only discovery error handling is in scope.
- `os.walk` directory discovery failure must add an ordinary owner guard failure
  identifying relative source path and error class. It must not become an empty,
  apparently complete source set. Keep running readable checks to collect evidence.
- Existing unreadable source-file behavior already exits nonzero; no success claim
  or broad parser rewrite is introduced. Excluded dependency directories remain
  excluded, including when unreadable. No symlink traversal policy is changed.
- Add focused helper admission controls and actual whole-validator healthy,
  readable allocation, unreadable directory, and restoration controls. Confirm the
  permission plant actually fails under this user; root privilege must not produce
  a fake passing permission test. Restore permissions in finally; all fixtures go
  through the owner's residue ledger.
- Preserve versions and every published payload file. Verify npm pack path/digest
  equality against the accepted baseline. Independent peer review and normal PR
  admission follow; broader owner gate waits for the coordinator's serial slot.

Implementation is the next step. No scanner, runtime, board closure, publication
or installation is claimed by this source-first packet.

The first baseline harness attempt failed its own diagnostic-stream assertion:
this owner emits failure diagnostics on stderr, while make-skill uses stdout.
The actual readable plant already returned 1. The harness was corrected to inspect
both streams, then all three baseline conditions above were rerun successfully.
This was a harness failure, not a successful owner check or an implementation fix.

## Implemented and focused verification

Only the scanner's `os.walk` call gained an error callback (relative path and error
class); the owner's lexical rules, exemptions and skip set are unchanged. The new
`test/audit_regressions/fw01_discovery.py` passes 9 controls: helper healthy,
permission refusal, restoration, excluded dependency and absent-root admission;
actual whole-validator healthy, readable unauthorized maker, unreadable directory,
and restoration. Permission tests explicitly prove OS denial and restore modes in
finally. Both owned fixture trees were removed after success.

The [pack comparison](payload-parity.json) checks all 44 current npm payload
files (609,718 bytes) against accepted baseline Git blobs. Only test/docs
paths change; package selection and version are unchanged. Registry metadata confirms
that version exists; this is not a fresh immutable-tarball readback. No new release
or installed update is needed for this excluded validation/evidence source change.

## Independent review and owner aggregate

[Root's independent source acceptance](https://github.com/ssheleg/sshlg-skills/blob/85d1758e02cbf1759be861a7af2108d267c339a3/docs/evidence/completion-1013/fw01-sibling-peer.json) binds the implementation above
and independently replays all 9 controls. It accepts directory discovery refusal
within the documented scanner scope, without a filesystem race or symlink proof.

The exact implementation commit `bc0f66387850f30674ae14636f7e40d98e029d2b` then passed the complete owner
`npm test` command, exit 0, in 12.04 seconds. The
[structured result](owner-full.json) binds source, command and log digest;
[full output](owner-full.log.gz) preserves every group. Minimum observed free
space was 1533267968 bytes. The watchdog would stop only this owned
process group below 300 MiB; it did not fire. Owned scratch/cache trees were removed.
No provider, native-host or model behavior was exercised.

Next: commit this documentation freeze, promote the existing draft PR once, and
require genuine eligible PR jobs before normal integration. Hosted checks and merge
remain pending; no release or installed update is needed for this excluded source.

## Normal integration observed

[Eligible checks and merge receipt](normal-integration.json) records all genuine
PR jobs succeeding at the frozen head, followed by normal squash integration at
[b332a92](https://github.com/ssheleg/agent-stack/commit/b332a92e62417d615543c6398f7a01f6d85663bf).
The complete accepted Git tree equals the checked candidate tree. This follow-up
receipt is a documentation-only branch update; the accepted source above is the
pin target. No tag, registry publication or installed runtime update was performed.
