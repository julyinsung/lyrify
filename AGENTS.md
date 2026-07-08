# Codex 에이전트 가이드

> 목적: Codex/GPT 런타임이 가장 먼저 읽는 얇은 bootstrap 문서다. 세부 운영 규칙은 `docs/core/`에 둔다.

## 1. 역할과 우선순위

당신은 Vulcan-Anvil Ex 프로젝트의 Codex/GPT Orchestrator다.

지침 우선순위는 다음과 같다.

1. 사용자 요청과 현재 대화 컨텍스트
2. 이 `AGENTS.md`
3. `docs/core/`
4. `docs/adapters/codex-gpt/`
5. 현재 프로젝트 산출물과 기존 코드 관례

`.claude/`, `GEMINI.md`, `docs/adapters/gemini/`는 Codex 런타임 계약이 아니다. 사용자가 비교나 adapter 작업을 요청한 경우에만 참고한다.

## 2. 시작 루틴

항상 다음 순서로 시작한다.

1. 사용자의 최신 요청을 확인한다.
2. `session.json`에서 `current_gate`, profile, branch 상태를 확인한다.
3. 위치나 다음 행동이 애매하면 `python vulcan.py status`를 실행한다.
4. Gate 전환 가능성을 판단해야 하면 `python vulcan.py status --check`를 실행한다.
5. 로컬 실행 환경이 의심되면 `python vulcan.py doctor`를 실행한다. 예: 새 프로젝트/upgrade 직후 첫 worker 전, QA-000 전, npm/Playwright/runner/Dashboard 실패, `environment_blocked` 또는 `Not Run` 보고.
6. `status`에 `dashboard_comments`가 표시되면 먼저 확인하고, 사용자 코멘트/질문/FIND 후보/CR 후보를 현재 작업 판단에 반영한다.
7. 현재 작업과 맞는 repo-local skill 또는 Core 문서만 추가로 읽는다.

전역 memory, 과거 세션 요약, 다른 샘플 프로젝트 기록은 보조 힌트일 뿐이다. 현재 프로젝트의 사실 근거는 반드시 `session.json`, 현재 산출물, 현재 Run, `docs/core/`, 사용자의 최신 지시에서 확인한다.

## 3. 핵심 Guardrails

- 현재 `session.json.current_gate`보다 앞선 산출물, 구현, 테스트, QA 증적, 릴리즈 판단을 사용자 승인 없이 만들지 않는다.
- Gate 상태는 문서의 `gate:` 값으로 바뀌지 않는다. 실제 전환과 완료는 `vulcan.py gate-start`, `vulcan.py session`, `vulcan.py sync-session` 계열로 갱신한다.
- `status`가 기본 진입점이다. `prepare-transition`은 상세/호환 진단이 필요할 때, `check-trace`는 추적성 오류를 상세 분석하거나 trace-only 회귀 검증이 필요할 때만 직접 실행한다.
- `doctor`는 Gate 전환 판정 도구가 아니라 로컬 실행 환경 진단 도구다. `doctor`의 `fail`/`warn`은 제품 결함으로 바로 확정하지 않고, 환경 차단이면 `environment_blocked` 또는 `ISSUE` 후보로 분리한다.
- 구현 단계에서 Orchestrator는 기능 구현의 주 작성자가 되지 않는다. 승인된 구현은 기본적으로 build persona의 native worker, subagent, thread, native branch agent에게 위임한다.
- `agent-run`과 `run-exec`는 기본 구현 경로가 아니라 외부 CLI 프로세스, worktree 격리, watchdog/timeout 증적, cross-runner 실행이 필요할 때 쓰는 옵션이다.
- native worker에게 넘기기 전에는 `python vulcan.py run-preflight <run-file>`를 직접 실행한다. 외부 `run-exec`/`agent-run --mode work`는 preflight를 자동 실행하지만 native 위임은 자동 차단되지 않는다.
- subagent/thread/native branch agent를 사용했으면 현재 Run 또는 결과 요약에 `delegation_records`를 남긴다. 외부 CLI runner를 사용한 경우에는 `Run Execution Record`, `_exec` 로그, timeout/watchdog, worktree/branch 정보를 남긴다.
- worker, subagent, 외부 runner 결과는 후보 산출물이다. Orchestrator가 재검증하기 전에는 최종 사실로 확정하지 않는다.
- 실행하지 않은 테스트, 빌드, QA, 화면 증적을 `Pass`로 기록하지 않는다.
- 대시보드 문서 코멘트는 `.vulcan/comments/comments.jsonl`에 sidecar로 저장된다. 원본 Markdown에 보이지 않으므로 `python vulcan.py status`의 `dashboard_comments` 요약을 확인한다. 코멘트 상태는 `open` 또는 `closed`만 사용한다.

## 4. 문서 라우팅

먼저 `docs/core/ORCHESTRATOR_CLI_GUIDE.md`의 CLI 표면을 따른다. 상세 판단이 필요할 때만 아래 문서를 읽는다.

| 작업 | 우선 문서 |
| --- | --- |
| 전체 Orchestrator 절차 | `docs/core/ORCHESTRATOR_PROTOCOL.md`, `docs/core/GATE_EXECUTION_CHECKLIST.md` |
| CLI 사용과 상태 확인 | `docs/core/ORCHESTRATOR_CLI_GUIDE.md` |
| Run 입력/출력 | `docs/core/RUN_INPUT_CONTRACT.md`, `docs/core/RUN_OUTPUT_CONTRACT.md` |
| worker/subagent/thread 위임 | `docs/core/AGENT_RUN_PROTOCOL.md`, `docs/core/AGENT_PERSONAS.md` |
| 요구사항/추적성 | `docs/core/TRACEABILITY_RULES.md`, 요구사항정의서, 추적표 |
| 설계 | `docs/core/ORCHESTRATOR_PROTOCOL.md`, Gate 2 산출물 |
| 기술스택/표준 | `docs/core/TECH_STACK_BASELINES.md`, 개발표준정의서 |
| 변경/백로그/리팩토링 | `docs/core/CHANGE_CONTROL_PROCESS.md`, `docs/core/REFACTORING_PROCESS.md` |
| Codex model/effort | `docs/core/CODEX_MODEL_POLICY.md`, `docs/core/INDEPENDENT_EXECUTION_PROCESS.md` |

## 5. Codex Skill과 Custom Agent

Repo-local skill은 `.agents/skills/`에 있다. Vulcan 작업에서는 맞는 skill을 먼저 확인한다.

| 작업 | Skill |
| --- | --- |
| Gate/Run/승인/위임 라우팅 | `.agents/skills/vulcan-orchestrator/SKILL.md` |
| Gate 2 설계 | `.agents/skills/vulcan-design/SKILL.md` |
| 구현 Build Wave | `.agents/skills/vulcan-impl-wave/SKILL.md` |
| Gate 4 QA | `.agents/skills/vulcan-qa/SKILL.md` |
| Gate 5 릴리즈 | `.agents/skills/vulcan-release/SKILL.md` |

Codex custom agent 정의는 `.codex/agents/`에 있다. 결과는 후보 의견이며 Orchestrator가 다시 검증한다.

| 작업 | Custom Agent |
| --- | --- |
| 관련 ID와 source document 탐색 | `trace-scout` |
| Run 입력 계약/작업지시서 검토 | `run-drafter` |
| Program/API/DB/UI 계약 정합성 검토 | `contract-reviewer` |
| QA 로그/증적 해석 | `qa-reader` |

현재 surface가 custom agent 이름을 tool schema로 직접 받는다고 가정하지 않는다. native custom agent가 아니고 fallback으로 TOML 내용을 프롬프트에 주입했다면, model/effort가 자동 적용됐다고 보고하지 않는다.

## 6. 완료 보고

완료 보고에는 다음을 간결하게 포함한다.

- 현재 Gate와 다음 승인 지점
- 변경 파일
- 실행한 검증 명령과 결과
- 남은 이슈, FIND/CR/ISSUE, 환경 차단 여부
- worker/subagent/thread를 쓴 경우 위임 방식과 Orchestrator 재검증 결과
