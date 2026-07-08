---
name: vulcan-orchestrator
description: Use for Vulcan-Anvil Ex project orchestration, Gate status checks, Run planning, approval boundaries, worker/reviewer routing, traceability checks, and autonomous follow-up across Phase 0 through Gate 5.
---

# Vulcan Orchestrator

Use this as the entry skill for Vulcan-Anvil Ex work. Keep Core rules in project documents; this skill is only a short routing card.

## Start

1. Read `AGENTS.md`, `session.json`, and the user's latest request when Codex is the primary runner.
2. Confirm `session.json.current_gate` and do not create artifacts beyond the current approved Gate.
3. Run `python vulcan.py status` first when current Gate, profile, branch, Run, or next action is unclear.
4. Confirm the delivery profile from `session.json`, `python vulcan.py status`, or `python vulcan.py profile-status`.
5. Apply profile-specific depth, evidence, review, and Run-weight rules from `docs/core/DELIVERY_PROFILES.md`.
   - In `poc`, prefer subagent/result-summary flow for short experiments; create compact Runs only for external workers, independent review, long delegation, or reproducible experiment records.
   - In `poc`, do not create Gate-level Orchestrator Plan Runs by habit. Use `docs/poc` plus `python vulcan.py status --check` unless a Run is needed for handoff or replay.
   - In `poc`, allow `TBD` only with reason and next decision timing. Do not leave goals, success criteria, or actual execution results as `TBD`.
6. If the task is non-trivial, read `docs/core/ORCHESTRATOR_PROTOCOL.md`.
7. Use `docs/core/ORCHESTRATOR_CLI_GUIDE.md` for CLI usage; use `python vulcan.py branch-status` only when branch detail is needed beyond `status`.
8. Run `python vulcan.py doctor` only when local runtime readiness matters: after init/upgrade on an unfamiliar machine, before first worker if toolchain state is unknown, before Gate 4 QA-000/UI evidence, or after npm/Playwright/runner/Dashboard/environment-blocked failures.

## Route

- Discovery, requirements, design, implementation, QA, and release work should stay inside the active Gate.
- If a narrower Vulcan skill matches, use it before continuing:
  - `vulcan-design`
  - `vulcan-impl-wave`
  - `vulcan-qa`
  - `vulcan-release`
- Use existing Core and adapter docs for details. Do not copy full Core rules into prompts.
- When the user has approved autonomous orchestration or custom-agent assistance, use helper agents from `.gemini/agents/` or `.codex/agents/` selectively:
  - `trace-scout`: related IDs/source documents are broad or unclear.
  - `run-drafter`: a Run needs worker handoff quality review.
  - `contract-reviewer`: design, implementation, API, DB, UI, or release contract consistency is risky.
  - `qa-reader`: QA logs/evidence contain mixed failures, stale results, or unclear root causes.
- Custom agent results are advisory. Record whether execution was native custom agent or prompt-contract fallback when reporting.
- See `docs/reference/CODEX-CUSTOM-AGENT-STRATEGY.md` for details.

## Guardrails

- Gate transitions require explicit user approval or an explicit proceed instruction.
- Gate status is changed through `vulcan.py` commands, not by editing `session.json` directly.
- Use `python vulcan.py status --check` for Gate transition readiness summary. Use `prepare-transition` only when detailed/compatibility transition diagnostics are needed. Use `check-trace` only when traceability needs detailed debugging or trace-only regression verification.
- Use `doctor` as a local environment diagnostic, not as a Gate readiness substitute. `doctor fail/warn` should be reported as environment readiness, `environment_blocked`, or an ISSUE candidate unless a product defect is separately reproduced.
- Use `run-check`, `run-preflight`, and `check-contract` as applicable.
- Before native subagent/thread/native branch worker delegation, run `python vulcan.py run-preflight <run-file>` explicitly. `run-exec` and `agent-run --mode work` auto-run preflight, but native delegation does not.
- Treat `prepare-transition` preflight findings as a safety net for completed current-Gate worker Runs, not as a substitute for pre-worker handoff preflight.
- Worker, subagent, and external runner outputs are candidates until the Orchestrator verifies them.
- Native subagent/thread outputs should be normalized into `delegation_records`; external CLI runner outputs keep the full Run Execution Record and `_exec` logs.
- Do not treat global memory or other sample projects as project facts.

## CLI

Do not run `python vulcan.py --help` repeatedly to discover routine commands. Use `docs/core/ORCHESTRATOR_CLI_GUIDE.md` and start with:

- Current overview: `python vulcan.py status`
- Transition readiness summary: `python vulcan.py status --check`
- Local environment check: `python vulcan.py doctor`
- Retrospective/performance summary: `python vulcan.py metrics`

## Report

End with the current Gate, changed files, verification commands, remaining issues, and the next approval point.
