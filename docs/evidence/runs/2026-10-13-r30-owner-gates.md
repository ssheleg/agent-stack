# R30 owner board and release gates — 2026-10-13

Base: `cb8f6993a61473f3974bc3af67925439ed4abb75`, version0.27.1.
Owner: agent-stack, leaseR30-GATES-1013. This is a bounded implementation packet
within the hub's original R30/B108/B109, not a closure of other members' gates.

## Contract and reproduction

The owner validator must refuse a malformed or duplicate declared board identity
and a release workflow whose tag ancestry guard can be bypassed. Preserve the
board's composite historical IDs, explicit umbrella namespace and summary table.
Use the already independently reviewed shared release parser, with no shell/YAML
semantic claim beyond its accepted structural grammar. Preserve release gates and
follow the current operator's nightly/explicit-candidate hosted-check policy.

Before the edit, the real `test/validate.py` passed at the base. Eight isolated
process plants then each returned0: duplicate declaration, missing board, missing
header, absent ancestry command, shallow checkout, conditional guard, ignored
failure and early successful exit. The test expected exit1 with the intended
reason and reported8failures. Owned failure copies remain in the residue ledger;
private temporary paths are not copied here.

## Implementation and controls

`test/member_gates.py` is byte-identical to telegram-dev's shared helper at
`711576f89d06525ee94ad4aac0f779a5baeefdd5`; only its release parser and Markdown
cell/label primitives are used. The board adapter is member-specific: one primary
8column declaration table; grouped IDs expanded for duplicate detection; explicit
umbrella IDs kept in a separate namespace. The3column summary is a reference,
not a second declaration. Unsupported primary header shapes fail closed.

The first port found AG-06b's historical command cell contained an even number
of backslashes before a pipe, making9 rendered cells. Its Markdown escape now
keeps8 cells without changing the displayed command. This correction is included
in the same board-contract change.

`python3 test/member_owner_gates_test.py` now passes14 real-process controls:
11 defects plus3 valid controls. Added probes cover composite-ID overlap, the
real even-backslash defect and a missing separator; valid controls retain the
summary, distinguish hub/local IDs and accept bold formatting. Every mutation
asserts changed bytes. The suite requires the expected diagnostic as well as
exit1; it is wired into npm test and the hosted workflow. Its14 owned trees were
removed on successful completion; failures remain attributable by residue.

## Delivery and bounds

Independent review and full local/hosted gates remain pending. No version, tag,
registry or installation is changed. The new nightly schedule is23:00Warsaw;
only deliberate ready-for-review promotion runs an explicit candidate. Routine
push/open/synchronize full-suite triggers are removed under operator policy.

Exact next task: independently review this candidate and its parser boundaries,
then run the owner full gate once, promote a frozen draft PR, integrate normally
and include it in a reviewed patch release. Do not advance the hub pin from this
unreleased branch.
