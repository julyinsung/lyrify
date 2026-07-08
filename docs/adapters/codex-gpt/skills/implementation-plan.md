# 구현 계획 Skill

## 사용할 때

Gate 3 테스트 설계가 끝나고 구현 단계로 들어가기 직전에 사용한다.

구현 계획은 코드를 작성하는 Run이 아니다. Orchestrator가 승인된 요구사항, 설계, 테스트 기준을 읽고 구현을 `Implementation Scaffold`, 여러 `Build Wave`, 또는 단일 worker Run으로 나누는 운영 Run이다.

## 필수 입력

- `AGENTS.md`
- `docs/core/AGENT_PERSONAS.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/RUN_INPUT_CONTRACT.md`
- 관련 요구사항정의서
- 관련 요구사항추적표
- 관련 기능명세서
- 관련 프로그램 설계서
- 관련 화면설계서
- 관련 DB명세서
- 관련 개발표준정의서
- 관련 테스트케이스 정의서

## 절차

1. 구현 대상 `REQ`, `AC`, `FUNC`, `SCR`, `PGM`, `API`, `DB`, `SEC`, `UT`, `IT`, `UI`를 확인한다.
2. 구현 제외 범위와 후속 Backlog 후보를 분리한다.
3. 프로그램 설계서의 Interface Contract, Abstract Base Contract, Public Method Contract를 확인한다.
4. 신규 개발 또는 빌드 가능한 골격이 없는 프로젝트인지 확인하고, `Implementation Scaffold` 필요 여부를 먼저 결정한다.
   - 필요하면 첫 Wave는 `BW-000 implementation-scaffold`로 둔다.
   - 이미 충분하면 `contract_skeleton.mode: not-required`와 생략 근거, 확인한 파일/명령을 남긴다.
5. 의존성을 기준으로 `Build Wave`를 정의하되, 각 Build Wave Run은 기능/계약 단위의 완결 조각으로 나눈다.
6. 각 Wave에 목표, target_contracts, 관련 ID, 수정 파일 후보, 테스트, 추적표 갱신 항목, 커밋 후보를 연결한다.
   - Build Wave Run을 생성할 때는 가능한 한 `wave-start <BW-ID> --trace-seed <상세 REQ/AC/FUNC/PGM/API/SCR/DB/SEC/UT/IT/UI ID>`를 사용해 추적성 그래프 기반 초안을 만든다.
   - `--trace-seed`가 추천한 ID/문서는 초안이며, `scope.writable`, `interface_contract`, `contract_skeleton`, 검증 명령은 Orchestrator가 확정한다.
7. subagent 또는 독립 runner 위임이 가능한 Wave와 메인 Orchestrator가 직접 통합해야 할 Wave를 구분한다.
   - Frontend Build Wave는 기본 후보 runner를 `claude-cli`로 둔다.
   - Backend Build Wave는 기본 후보 runner를 `codex-cli`로 둔다.
   - frontend/backend처럼 작업지시서가 달라지면 같은 Wave 안에서 병렬화하지 말고 Wave를 나눈다.
   - Codex subagent/thread 같은 native worker를 우선 사용할 수 있으면 `delegation_records`로 결과를 기록하고, 외부 CLI runner가 필요한 경우에만 `Run Execution Record`와 `_exec` 로그를 요구한다.
8. 작은 단일 구현이라도 담당 worker 또는 subagent, 수정 허용 범위, 검증 명령을 명시한다. Wave 분할 생략은 Orchestrator 직접 구현을 의미하지 않는다.
9. Wave 간 순서, 병렬 가능성, 중단 조건을 기록한다.
10. 구현 시작 전 필요한 사용자 승인 또는 미해결 질문을 남긴다.
11. 구현 실행 시에는 한 번에 하나의 Wave만 active 상태로 둘 것을 명시한다.

## Build Wave 작성 기준

| 항목 | 작성 기준 |
| --- | --- |
| `BW-ID` | `BW-001`, `BW-002`처럼 안정 ID를 부여한다. |
| 목표 | 하나의 검증 가능한 구현 배치로 설명한다. |
| 관련 ID | `REQ/AC/FUNC/PGM/API/SCR/DB/SEC/UT/IT/UI` 중 해당 ID를 연결한다. |
| target_contracts | 이번 Wave/worker Run이 실제로 닫을 `FUNC/PGM/API/DB/SEC/TEST` 계약 묶음을 적는다. |
| 수정 범위 | 예상 파일 또는 디렉터리를 적는다. |
| 테스트 | worker가 작성/갱신할 테스트케이스와 Orchestrator가 재실행할 명령을 적는다. |
| 추적표 갱신 | 상태 후보, 증적 후보, 테스트 결과 갱신 필요 항목을 적는다. 실제 `Implemented`/`Verified` 반영은 Orchestrator 재검증 후 통합 단계에서 한다. |
| 커밋 후보 | Wave 완료 후 사용할 커밋 메시지 후보를 적는다. |
| 위임 | subagent/runner 위임 여부, 권장 runner, 책임 범위를 적는다. |

## Implementation Scaffold 판단 기준

Implementation Plan은 feature Build Wave를 만들기 전에 scaffold 필요 여부를 반드시 판단한다.

| 판단 | 조건 | 다음 행동 |
| --- | --- | --- |
| 필요 | 신규 개발, 빈 backend/frontend, 빌드 설정 부재, Program Design의 public signature가 코드에 없음 | `BW-000 implementation-scaffold` Run 생성 |
| 정렬 필요 | 기존 코드가 있으나 Program Design의 `PGM/IF/MTH/DTO`와 이름/타입/경로가 다름 | `BW-000 implementation-scaffold` 또는 alignment Run 생성 |
| 생략 가능 | 빌드 가능한 골격, public signature, DTO/schema, 테스트 skeleton이 이미 존재 | `contract_skeleton.mode: not-required`와 근거 기록 |

`BW-000 implementation-scaffold`는 업무 기능을 완성하지 않는다.
폴더, 빌드 설정, class/interface/method/DTO skeleton, 테스트 skeleton, compile/import/build smoke만 담당한다.
실제 feature 구현은 이후 `build-wave` Run이 담당한다.

## 실행 운영 기준

- Implementation Plan은 전체 구현 지도이고, 실제 구현 지시는 Wave별 `build-wave` Run으로 만든다.
- Wave별 `build-wave` Run을 만들 때 대표 상세 ID가 있으면 `wave-start --trace-seed`를 기본 후보로 사용한다. trace seed가 없거나 추적표가 아직 부실하면 `--related-ids`를 보조로 사용하되, parent REQ만 넣고 끝내지 않는다.
- 작은 단일 구현은 Implementation Plan 없이 단일 worker Run으로 갈 수 있지만, Orchestrator가 직접 기능 코드를 작성하는 기본 경로로 쓰지 않는다.
- Wave 수가 4개이고 scaffold가 필요하면 보통 `implementation-plan` Run 1개, `implementation-scaffold` Run 1개, `build-wave` Run 3개 이상이 생긴다.
- Wave/worker Run의 1차 분할 기준은 시간 분량이 아니라 기능/계약 단위다.
- 목표 시간은 10분 내외, 최대 15분 권장이지만 시간은 보조 기준이다.
- 15분을 넘길 것으로 예상되면 개발하다 중단하지 않고 더 작은 기능/계약 단위로 다시 나눈다.
- 컴파일/테스트가 깨지는 반쪽 구현은 완료 Run으로 만들지 않는다.
- Orchestrator는 현재 Build Wave Run의 작업지시서를 만들고, subagent에게 해당 Wave 범위와 구현에 필요한 문서만 전달한다.
- Orchestrator가 직접 수정할 수 있는 범위는 worker 결과 통합, 최소 연결 수정, 문서/추적표/session 갱신, worker 테스트케이스 재실행으로 제한한다.
- 사용자가 worker 사용을 명시하지 않았다는 점은 Orchestrator 직접 구현 사유가 아니다. 구현 진행 승인이 있으면 별도 요청이 없어도 native worker(subagent/thread/native branch agent) 위임을 기본 절차로 둔다.
- `agent-run`/`run-exec`는 필수 실행 경로가 아니라 별도 CLI 프로세스, worktree 격리, watchdog/timeout 증적, cross-runner 실행이 필요할 때 선택하는 옵션이다.
- 직접 구현 예외는 worker/subagent/thread 실행 불가, worker 결과 통합 중 충돌 해결에 필요한 최소 수정, 긴급한 1~2줄 연결 수정, 사용자의 명시적 직접 구현 승인에 한해 허용한다.
- 직접 수정 예외가 필요하면 `orchestrator_direct_edit_reason`, `direct_edit_scope.files`, `direct_edit_scope.estimated_loc`, `direct_edit_scope.contract_changed`, 실행 검증, 후속 검수 필요 여부를 Run에 기록한다.
- 직접 구현 예외는 2개 이하 파일, 약 30 LOC 이하, public API/PGM/IF/MTH/DTO/schema/DB/security/SCR/UI contract 변경 없음, 기존 테스트 또는 작은 테스트 보정으로 검증 가능한 경우로 제한한다.
- 3개 이상 파일, 약 100 LOC 이상, 15분 이상 예상, backend/frontend 동시 변경, 새 계약 추가, 테스트 본문 대량 추가가 보이면 Build Wave로 분리한다.
- 동시에 active 상태인 Wave는 하나만 허용한다.
- 한 Wave를 여러 runner에게 나누어 동시에 구현시키지 않는다. frontend/backend처럼 작업지시서가 분리되면 별도 Wave로 나눈다.
- 다음 Wave의 읽기 전용 조사나 질문 정리는 가능하지만 코드 수정은 현재 Wave 완료 후 시작한다.
- Wave 상태와 구현 진행률은 `session.json`을 직접 수정하지 않고 `vulcan.py wave-start`, `vulcan.py wave-complete`, `vulcan.py sync-session`으로 갱신한다.
- 작업자 runner는 Gate 전환, `session.json` Gate 상태 변경, 최종 승인 판단을 하지 않는다.
- 작업자 runner가 `wave-complete`, Gate 전환, PR merge, QA Pass가 필요하다고 판단하면 직접 확정하지 않고 Orchestrator 결정 필요 항목으로 반환한다.
- subagent/thread 위임을 계획한 Wave는 완료 시 현재 Run에 남길 `delegation_records` 항목도 계획한다. 최소 항목은 위임 대상, scope, 변경 파일, 결과 요약, Orchestrator 재검증 명령이다.

## 권장 Wave 예시

```text
BW-000 Implementation Scaffold: 빌드 가능한 골격, public signature, DTO/schema, 테스트 skeleton
BW-001 Backend 인증/회원가입/로그인 API와 보안
BW-002 Backend TODO 데이터와 CRUD
BW-003 Frontend UI 상태와 오류/빈 상태
BW-004 Playwright 화면 증적, 테스트 결과, 추적표 정리
```

권장 실행 방식 예:

| BW-ID | 영역 | 기본 실행 | 외부 CLI runner가 유용한 경우 |
| --- | --- | --- |
| BW-000 | Scaffold | Codex/Claude native subagent 또는 thread | scaffold 결과를 별도 worktree에서 격리 검증해야 할 때 |
| BW-001 | Backend | Codex native subagent 또는 thread | codex-cli 실행 로그, timeout/watchdog, worktree 증적이 필요할 때 |
| BW-002 | Backend | Codex native subagent 또는 thread | cross-runner 비교가 필요할 때 |
| BW-003 | Frontend | Claude/Agy native subagent 또는 Codex thread | UI runner별 결과 비교가 필요할 때 |
| BW-004 | Evidence/QA | QA native subagent 또는 thread | 독립 CLI 검수/증적 회수가 필요할 때 |

## 완료 조건

- 모든 구현 대상 ID가 하나 이상의 Wave와 target_contracts에 배치되어 있다.
- scaffold 필요 여부가 명시되어 있으며, 필요하면 `BW-000 implementation-scaffold`가 첫 Wave로 정의되어 있다.
- 각 Wave가 기능/계약 단위의 검증 가능한 완결 조각이다.
- 작은 단일 구현이면 담당 worker와 단일 Run 범위가 명시되어 있다.
- Wave 간 의존성과 순서가 명확하다.
- 각 Wave에 테스트와 추적표 갱신 기준이 있다.
- subagent 위임 가능 범위와 충돌 가능 파일이 식별되어 있다.
- 사용자 승인 또는 미해결 질문이 명시되어 있다.
- Wave별 실행 Run 생성 기준과 한 번에 하나의 active Wave 원칙이 명시되어 있다.

## 출력

다음을 반환한다.

- Implementation Plan Run 요약
- `Build Wave` 목록
- Wave별 관련 ID
- Wave별 수정 파일 후보
- Wave별 테스트/검증 명령
- Wave별 권장 runner
- Wave별 커밋 메시지 후보
- subagent 위임 계획
- 중단 조건
- 다음 `build-wave` Run 제안

