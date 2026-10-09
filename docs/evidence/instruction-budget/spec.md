# Instruction budget cleanup — bounded implementation

Source baseline: `07d8fc8a6a0ac56ef389e96b093def101367e4f1` (agent-stack 0.25.3).

The task is to prevent instruction-file overflow recurring after local cleanup.
The owned public deliverable is an on-demand agent-harness procedure and a
read-only, explicit-input measurement tool. Private instruction text, paths,
settings and authentication state do not enter this repository.

## Contract

- Keep essential authority, safety, routing and working agreements loaded.
- Extract task-specific detail only behind a concrete load condition and verify
  requirement-to-destination coverage; an eager import is not a context saving.
- Measure Unicode characters, UTF-8 bytes, lines and file hashes separately from
  tokens. A caller-provided character threshold is a local budget, not a host cap.
- Traverse only explicitly allowed imports. Never discover a home directory,
  read an unlisted imported file, execute instructions or edit an input.
- Distinguish measured, partial and over-budget. Missing/unreadable/unlisted
  imports and cycles never produce a complete PASS. Shared imports are counted
  once by resolved path; equal content in distinct files is reported, not erased.
- A syntax approximation is not a host load receipt. Require fresh host inspection
  before claiming that a running session consumed the optimized instructions.

## Acceptance

Synthetic regressions cover Unicode, eager imports, relative resolution, escaped
spaces, Markdown code, quoted paths, recursion, diamond references, cycles,
missing/unlisted files, symlink aliases, duplicate content, budget boundaries,
empty inputs, invalid UTF-8, bounded reads and unchanged input bytes. The existing
native suite and both strict plugin checks must pass. Review precedes release.

No global router changes, third-party skill rewrites, MCP authentication changes,
or outcome-improvement claims are part of this patch.
