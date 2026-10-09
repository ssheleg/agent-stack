# CR-2 — 0.25.5 release receipt, 2026-10-09

This records source, publication and installed bytes separately. The
[handoff](handoff.md), [spec/source ledger](spec.md) and
[independent acceptance](review.md) carry the change and its limits.

## Source and review

- Baseline: `7f0c2f942ded0c8922650883db7347d2cc695577`, 0.25.4.
- Reviewed candidate: `c42bc97ab1eaa8dd80608bca63a86bb49653ea8a`.
- Candidate plus review receipt: `7c9f1b479ae742dfcd9d13b33bf1959824711780`.
- [Exact candidate hosted checks](https://github.com/ssheleg/agent-stack/actions/runs/37909830957): success.
- [PR 38](https://github.com/ssheleg/agent-stack/pull/38): merged by normal squash.
- Release source: `b512cb4d67c1acbfd36fde94935cc993e1fc91b7`.
  `git diff --exit-code 7c9f1b479ae742dfcd9d13b33bf1959824711780 b512cb4d67c1acbfd36fde94935cc993e1fc91b7`
  returned 0: merge tree equals checked candidate tree.
- Annotated tag `v0.25.5`: tag object `19240490dee4f97a45e0eaa3e19952b83492d483`,
  dereferenced commit `b512cb4d67c1acbfd36fde94935cc993e1fc91b7` verified from remote.
- Fresh remote branch checkout at `7c9f1b4` resolved the entry/spec/review and
  passed `python3 test/validate.py`; the isolated check directory was removed.

## Publication

[Release workflow 37909965476](https://github.com/ssheleg/agent-stack/actions/runs/37909965476)
completed SUCCESS at the release source: both native validation/house jobs,
GitHub release and npm publication succeeded. No full workflow was manually
dispatched. The existing tag workflow performed trusted publication.

Registry version `@ssheleg/agent-stack@0.25.5` reports:

```json
{
  "gitHead": "b512cb4d67c1acbfd36fde94935cc993e1fc91b7",
  "integrity": "sha512-OBjOREjJVvS06ej4fIvPpzMF3HN8irVr4w5IjGXlgE5gSMGp6dZH9jXL0MNjRFUOfn8itPydYttLXn546o61OA==",
  "shasum": "ca4a5bf4cde8dd7be9dfb84f45a66145f291ef86",
  "files_byte_compared": 44
}
```

The verifier fetched the version document from
`https://registry.npmjs.org/@ssheleg%2fagent-stack/0.25.5`, downloaded its
`dist.tarball`, recomputed SHA-512/SHA-1 against `dist.integrity`/`dist.shasum`,
then compared every regular tar member after removing the `package/` prefix to
`git show b512cb4d67c1acbfd36fde94935cc993e1fc91b7:<path>`. All 44 files matched,
including the new context-lifecycle reference; no non-regular member was accepted.
Registry metadata advertises SLSA v1 provenance at its attestation endpoint.
This receipt does not claim independent cryptographic verification of that
attestation. An initial 404 while publish was running was followed by this
successful readback; no duplicate publish was attempted.

## Native Codex installation

The installed version before update was 0.25.4. The host's own CLI help established
these supported commands, which were then run:

```bash
codex plugin marketplace upgrade agent-stack --json
codex plugin add agent-stack@agent-stack --json
codex plugin list --marketplace agent-stack --json
```

Upgrade reported no errors. Add/list reported `agent-stack@agent-stack`, version
0.25.5, installed and enabled. All 38 tracked files under the release commit's
`plugins/agent-stack/` were byte-compared to the native 0.25.5 cache, with no
missing, differing or extra files. No private cache path is included here.

## Limits and next owner

These checks establish source, packaged and installed bytes. Current-session
reload is NOT_OBSERVED; behavioral replay, quality and latency improvement remain
NOT_RUN. No private memory or archive was rewritten. Parent owns the hub pin,
family release and other-host update receipts. Its next task is to pin the exact
member release commit above and verify the family updater; the member payload
needs no further change for CR-2.
