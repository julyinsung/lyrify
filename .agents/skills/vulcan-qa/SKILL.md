---
name: vulcan-qa
description: Use for Vulcan Gate 4 QA execution, QA-000 workspace preparation, QA-001 command verification, QA-002 UI/E2E evidence, QA-003 result synthesis, QA findings, qa-fix-loop handoff, retest, and evidence normalization.
---

# Vulcan QA

Use this for Gate 4 QA and QA iterations.

## Preconditions

1. Confirm `session.json.current_gate` is `gate4`.
2. Confirm Impl was approved or explicitly completed for QA.
3. Run `python vulcan.py status` to confirm Gate, profile, branch, QA workspace, active Run, and dirty state.
4. Apply profile-specific QA evidence and review strictness from `docs/core/DELIVERY_PROFILES.md`.
5. Read the current QA Run and Gate 3 test cases.
6. Run `python vulcan.py doctor` before QA-000 when the machine/project has not been checked in this session, or when npm, Playwright, browser cache, runner, port, DB, or Dashboard readiness is uncertain.

## Staged QA

1. `QA-000`: prepare or confirm the QA workspace on the integration branch, dependencies, ports, DB, and smoke readiness.
2. `QA-001`: run command-based checks such as syntax, unit/integration tests, lint, build, and contract checks.
3. `QA-002`: collect UI/E2E evidence, screenshots, logs, and browser artifacts. For audit/product profiles, official UI Pass must be based on `@playwright/test` and `npx playwright test`; custom Playwright library scripts are PoC smoke/demo or auxiliary evidence only.
4. `QA-003`: synthesize Test Result, QA Finding, traceability status candidates, and approval/blocking issues.

`QA-001` to `QA-003` must reuse the workspace recorded by `QA-000`. A separate QA worktree is optional and should be used only when explicitly enabled by project policy.

## Failure Handling

- QA workers execute tests and collect evidence; they do not fix code immediately.
- If QA is delegated to a native subagent/thread, record the result in `delegation_records` with delegate, scope, evidence/log paths, result summary, and Orchestrator rerun commands.
- If QA is delegated to an external CLI runner, keep the full Run Execution Record, `_exec` logs, watchdog/timeout status, and any recovered transcript.
- If logs, screenshots, transcripts, or previous failures are mixed, use `qa-reader` to classify evidence before deciding a fix path.
- If a QA command is `Not Run` or `environment_blocked` because of local tooling, run `doctor` before retrying or classifying it as a product failure.
- If QA failure appears related to Program/API/DB/UI contract drift, use `contract-reviewer` before creating a `qa-fix-loop`.
- Classify failures as `FIND`, `CR`, `ISSUE`, or `environment_blocked`.
- Start `qa-fix-loop` only after Orchestrator/user decision.
- A `qa-fix-loop` Run must name the target `FIND-ID`, scope writable paths, and verification commands.

## Verification

- Run `python vulcan.py run-check <run-file>` for QA and fix Runs.
- Run `python vulcan.py status --check` after QA result synthesis to check Gate readiness.
- Run `python vulcan.py prepare-transition` only when detailed/compatibility transition diagnostics are needed.
- Run `python vulcan.py check-trace` only if the readiness output points to traceability errors that need detailed debugging.
- Run `python vulcan.py check-contract` when Program Design contracts are relevant.
