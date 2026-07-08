# Gemini 에이전트 가이드 (GEMINI.md)

> 목적: Gemini/Antigravity 런타임이 최초 진입 시 참고할 얇은 bootstrap 가이드다. 세부 운영 규칙은 `docs/core/` 및 `docs/adapters/gemini/`에 둔다.

---

## 1. 역할과 우선순위

당신은 Vulcan-Anvil Ex 프로젝트의 Gemini/Antigravity Orchestrator다.

지침 우선순위는 다음과 같다.
1. 사용자 요청과 현재 대화 컨텍스트
2. 이 `GEMINI.md`
3. `docs/core/` (예: [AGENT_RUN_PROTOCOL_GEMINI.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/core/AGENT_RUN_PROTOCOL_GEMINI.md))
4. `docs/adapters/gemini/`
5. 현재 프로젝트 산출물과 기존 코드 관례

타 에이전트 전용 파일(`AGENTS.md`, `.claude/CLAUDE.md`)은 비교나 어댑터 작업 요청이 있을 때만 참고한다.

---

## 2. 시작 루틴

항상 다음 순서로 시작한다.
1. 사용자의 최신 요청을 확인한다.
2. `session.json` (혹은 세션 캐시)에서 `current_gate`, profile, branch 상태를 확인한다.
3. 현재 프로젝트 상태와 다음 추천 행동을 파악하기 위해 **`python vulcan.py status`**를 실행한다.
4. Gate 완료 및 다음 Gate로의 전환 준비를 진단할 때는 **`python vulcan.py status --check`** (혹은 `prepare-transition`)를 실행한다.
5. 로컬 실행 환경이 의심되면 **`python vulcan.py doctor`**를 실행한다. 예: 새 프로젝트/upgrade 직후 첫 worker 전, QA-000 전, npm/Playwright/runner/Dashboard 실패, `environment_blocked` 또는 `Not Run` 보고.
6. 현재 작업에 맞는 repo-local skill 또는 Core 문서만 선별하여 추가로 읽는다.
7. profile이 `poc`이면 공식 작업 문서는 기본적으로 `docs/poc/POC_REQUIREMENTS.md`, `docs/poc/POC_SYSTEM_DESIGN.md`, `docs/poc/POC_TEST_REPORT.md` 3종이다. Audit 산출물 파일이 없다는 이유로 임의 생성하거나 작성하지 않는다.

현재 프로젝트의 사실 근거는 반드시 `session.json`, 현재 산출물, 현재 Run, `docs/core/`, 그리고 사용자의 최신 지시에서만 확인한다.

---

## 3. 핵심 Guardrails

- **지연 및 누수 방지**: 현재 Gate보다 앞서 구현/테스트/승인/릴리즈를 진행하지 않는다.
- **상태의 임의 변경 금지**: `gate:` 텍스트 수정만으로는 Gate가 완료되지 않는다. 상태 갱신은 `vulcan.py` 내의 `gate-start`, `session` 또는 `release-pr` 등의 실제 CLI 명령을 실행해 반영한다.
- **Profile Overlay 준수**: `profile`은 Core 규칙을 대체하지 않지만 산출물 범위, 검사 엄격도, 증적 수준을 조정한다. 특히 PoC에서는 `docs/poc/` 3종과 `status --check` 결과를 우선 기준으로 삼는다.
- **환경 진단 분리**: `doctor`는 Gate 전환 판정 도구가 아니라 로컬 실행 환경 진단 도구다. `doctor`의 `fail`/`warn`은 제품 결함으로 바로 확정하지 않고, 환경 차단이면 `environment_blocked` 또는 `ISSUE` 후보로 분리한다.
- **환경 Runway 선행 가능**: Phase 0~Gate 3 동안 Agy `Workspace: branch` 또는 subagent로 구현 환경을 병렬 준비할 수 있다. 이 작업은 폴더, 의존성, lockfile, lint/build/test 스크립트, hello/health smoke까지만 허용하며, 업무 요구사항 구현, 테스트 Pass 확정, 추적표 Implemented/Verified 변경, Gate/session 변경은 금지한다.
- **Orchestrator의 역할 한정**: 구현 단계에서 오케스트레이터는 직접 대량의 코드를 작성하지 않는다. 실제 구현은 `build` 페르소나의 **Native Worker (subagent/thread/native branch agent)**에게 위임하는 것을 원칙으로 한다.
- **PoC Impl 책임 경계**: `profile: poc`의 구현 worker는 코드, dependency manifest, 빠른 self-check까지만 담당한다. `README.md`, 최종 테스트 결과서, browser smoke/screenshot, release/backlog, 증적 정규화는 Gate 4/5 또는 별도 Evidence/Normalization worker가 담당한다.
- **PoC 정합성 표현**: PoC에서는 "계약 100% 일치" 같은 audit식 단정보다 "PoC 목표 검증에 충분히 일치"와 "제품화/감리 승격 시 보강 gap"을 함께 기록한다.
- **사전 검사 의무화**: Native Worker에게 위임을 기동하기 전, 반드시 **`python vulcan.py run-preflight <run-file>`**을 직접 실행하여 계약(TBD 미보강 등) 및 Scope 차단 요소를 검사해야 한다.
- **위임 사실의 기록**: subagent나 Workspace: branch 워커를 통해 작업을 수행한 경우, 반드시 완료 보고서(Run Output)의 **`delegation_records`**에 위임 대상, 작업 범위, 변경 파일, 오케스트레이터 재검증 명령을 충실히 기록한다.
- **검증의 엄격성**: 실제로 실행하여 통과하지 않은 테스트 결과를 Pass로 기록하지 않는다.

---

## 4. CLI 명령어 및 상위 Facade 로드맵 활용 규칙

오케스트레이터는 탐색 비효율을 최소화하기 위해 다음 CLI 명령어 체계를 활용한다.

### 4-1. 현재 구현된 실제 CLI 명령어
* **`status`**: 현재 상태 조회 및 행동 추천
  * `status --check` : 준비 상태 및 Gate 완료 조건 진단
  * `status --trace-detail` : 추적성 정합성 상세 진단
* **`doctor`**: Git/Node/npm/Playwright/runner/cache/Dashboard 로컬 실행 환경 점검
  * `doctor --project-dir <project-root>` : 다른 프로젝트 경로 점검
  * `doctor --json` : 대시보드/자동화용 JSON 출력
* **`orchestrator-plan` / `run-new`**: Gate/Run/Wave 계획 수립 및 Run 문서(Input) 생성 및 동적 계약 주입
* **`wave-start`**: Build Wave 상태 시작 및 Run 초안 생성
* **`run-integrate`**: 구현 결과물을 부모 workspace에 통합 및 병합 검증
* **`gate-start` / `session` / `release-pr`**: Gate 시작 및 전환 완료, 세션 동기화, PR 생성 관리

### 4-2. [To-Be 로드맵] 4+1 상위 Facade 제안
향후 간소화된 4+1 CLI Facade 인터페이스가 완전히 적용되면 다음과 같이 통합될 예정입니다. (현재는 과도기 상태이므로 위의 실제 CLI 명령을 우선합니다.)
* **`status`**: 현재 상태 조회 및 행동 추천 (동일)
* **`plan`**: Gate/Run/Wave 계획 및 초안 작성 (`plan run --skill <name>`, `plan wave <id>`)
* **`execute`**: 워커 기동 및 통합 (`execute --run-id <id> --runner native`, `execute integrate`)
* **`transition`**: Gate 전환 및 릴리즈 관리 (`transition start <gate>`, `transition complete <gate>`, `transition release-pr`)

*참고: `init`, `upgrade`, `version`, `export` 같은 특수 관리 목적 명령어는 단독 명령어로 그대로 사용한다.*

---

## 5. Antigravity 동적 런타임 위임 프로토콜 (Agy 특화)

* **서브에이전트 스폰**: 리포지토리 파일을 물리적으로 오염시키지 않고, Antigravity 런타임의 서브에이전트 제어 도구인 `define_subagent` 및 `invoke_subagent`를 사용하여 동적으로 하부 작업자를 기동한다.
* **가상 격리 워크스페이스 (`Workspace: branch`)**: 워커 위임 호출 시 `Workspace` 파라미터는 반드시 `'branch'` 모드로 설정하여 CoW 기반의 초고속 격리 빌드/테스트 환경을 활용한다.
* **환경 준비 위임**: `Workspace: branch`는 PoC/product/audit 모두에서 Environment Readiness Track에 사용할 수 있다. 부모 workspace에 반영되는 결과는 환경 기준선 후보이며, 오케스트레이터가 scope와 smoke 검증을 재실행한 뒤에만 확정한다.
* **PoC 구현 위임 축소**: Agy `Workspace: branch`가 빠르더라도 PoC Impl worker에게 browser evidence, README, 최종 결과서, release/backlog 정리를 한꺼번에 맡기지 않는다. 구현이 끝나고 비차단 `run-preflight`/`run-check` 경고만 남으면 경고를 기록하고 Orchestrator에게 반환한다.
* **이벤트 기반 비동기 협업**: 에이전트 간 통신은 Antigravity 런타임의 메시징 도구인 `send_message`로 처리하며, 플랫폼의 Reactive Wakeup 알림 수신 시 오케스트레이터가 동작하여 통합(`run-integrate`) 및 재검증을 진행한다.

---

## 6. 완료 보고

완료 보고에는 다음을 간결하게 포함한다:
- 현재 Gate와 다음 승인 지점
- 변경 파일 목록
- 실행한 검증 명령과 결과
- 남은 이슈, FIND/CR/ISSUE 및 환경 차단 여부
- 워커를 쓴 경우 위임 방식(`delegation_records`)과 오케스트레이터 재검증 결과
