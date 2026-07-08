# Build Wave Skill

## 사용할 때

구현 단계에서 `implementation-plan`이 정의한 하나의 `Build Wave`를 실행할 때 사용한다.

Build Wave는 전체 구현이 아니라 하나의 검증 가능한 구현 배치다. Wave가 끝나면 코드, 테스트케이스, Orchestrator가 재실행할 검증 명령, 문서/추적표 갱신 필요 항목, 커밋 후보가 함께 남아야 한다. worker는 요구사항추적표의 `Implemented` 또는 `Verified` 상태를 직접 확정하지 않고, 갱신해야 할 ID와 증적 후보를 보고한다.

Wave/worker Run은 시간 단위가 아니라 기능/계약 단위로 나눈다. 목표 시간은 10분 내외, 최대 15분 권장이지만 보조 기준이다. 15분을 넘길 것으로 예상되면 개발을 중간에 끊지 말고 더 작은 `FUNC/PGM/API/DB/SEC/TEST` 계약 묶음으로 다시 나눈다.

## 필수 입력

- `AGENTS.md`
- 현재 Build Wave Run
- Implementation Plan Run
- 현재 Wave의 `BW-ID`
- 현재 Run의 `target_contracts`
- 관련 개발표준정의서
- 관련 테스트케이스 또는 담당 테스트 파일

관련 설계 산출물 전체를 매번 정독하지 않는다.
작업자는 현재 Build Wave Run의 `source_documents.working_documents`를 우선 읽고, API/화면/프로그램/DB/보안 설계는 related ID나 기준 충돌이 있을 때 `reference_on_demand`에서 필요한 문서만 펼친다.
요구사항추적표, `AGENT_RUN_PROTOCOL`, `RUN_INPUT_CONTRACT`, `RUN_OUTPUT_CONTRACT`는 worker 구현 입력이 아니라 Orchestrator가 결과 통합과 상태/추적성 판단에 사용하는 `orchestrator_reference`다.

## 절차

1. Orchestrator는 `vulcan.py wave-start <BW-ID>`로 현재 Wave를 active 상태로 열고, 이미 다른 active Wave가 있으면 시작하지 않는다. 대표 상세 ID가 있으면 `vulcan.py wave-start <BW-ID> --trace-seed <ID>`를 우선 사용해 `related_ids`, `target_contracts`, `source_documents.reference_on_demand` 초안을 추적성 그래프에서 보강한다. 작업자 runner는 `wave-start`를 직접 실행하지 않고 Orchestrator가 연 Wave와 Run 지시를 따른다.
2. Implementation Plan에서 현재 `BW-ID`의 목표, `target_contracts`, 관련 ID, 수정 범위, 테스트를 확인한다.
3. 프로그램 설계서의 관련 `PGM`, Interface Contract, Abstract Base Contract, Public Method Contract를 확인한다.
4. 개발표준정의서에서 이번 Wave에 적용되는 패키지 구조, 계층 책임, 로깅, 주석, 예외/메시지, 테스트 명령을 확인하고 Run에 준수 체크리스트를 남긴다.
5. 현재 Run의 `development_standards_applied`와 `development_standard_checklist`를 코드/테스트 작성 체크리스트로 사용한다. 이 항목이 없으면 코드를 작성하기 전에 Orchestrator에게 Run 보완을 요청한다.
6. 개발표준의 필수 기준이 비어 있거나 서로 충돌하면 코드를 작성하지 않고 `FIND` 또는 `CR` 후보로 보고한다.
7. Wave 범위 밖 요구사항, 파일, 리팩터링은 건드리지 않는다.
8. 필요한 코드, 설정, 테스트, 메시지 리소스를 구현한다.
9. 구현 또는 테스트 파일에 관련 추적 ID를 남긴다.
10. 담당 테스트케이스를 작성/갱신하고 Orchestrator가 재실행할 테스트, 빌드, 린트, Run check 명령을 Run에 남긴다.
11. 가능하면 같은 명령을 self-check로 실행하고 결과를 보고한다. Node/Playwright 명령은 worker cache(`npm_config_cache`, `PLAYWRIGHT_BROWSERS_PATH`)를 사용한다.
12. worker worktree의 Node/Playwright self-check는 보조 검증이다. worker가 `npm run dev`, `npm run build`, `npx playwright test`를 완료하지 못해도 그 사실만으로 구현 실패로 단정하지 않는다.
13. npm registry, 권한, 인증, 네트워크, cache 문제로 `npm install`, `npm ci`, `npx playwright install`, lint/build/test를 실행하지 못했으면 `environment_blocked` 또는 `not_run`으로 기록하고 실패 명령/cwd/exit code/log path/Orchestrator 재실행 명령을 남긴다.
14. 요구사항추적표, session 상태, Wave 완료 상태, 전체 테스트 결과서 통합은 Orchestrator가 처리한다. 작업자 runner는 갱신 필요 항목만 보고한다.
15. 작업자 runner로 실행 중이면 `vulcan.py wave-complete <BW-ID>`, `vulcan.py sync-session`, `vulcan.py prepare-transition`, `vulcan.py check-trace`를 직접 실행하지 않고 Orchestrator에게 실행 필요 여부를 보고한다. Orchestrator는 worker 결과를 통합하고, worker가 만든 테스트케이스를 재실행한 뒤 `wave-complete`와 `sync-session`으로 session 상태를 갱신한다. Gate 전환 가능 여부는 `prepare-transition`으로 확인하고, 추적성 오류가 남을 때만 `check-trace`를 상세 진단으로 실행한다.
16. Codex subagent/thread 같은 native worker를 사용했으면 현재 Run의 `delegation_records`에 위임 대상, 범위, 변경 파일, 결과 요약, Orchestrator 재검증 명령을 남긴다. 외부 CLI runner를 사용한 경우에는 `Run Execution Record`와 `docs/runs/_exec/` 로그도 함께 남긴다.
17. 커밋 후보 메시지를 보고한다. 사용자가 승인하거나 자동 커밋 정책이 있으면 Wave 단위로 커밋한다.

## 검증 경계

Build Wave는 전체 Gate 4 QA가 아니다.

| 구분 | 수행자 | Wave에서의 의미 |
| --- | --- | --- |
| worker self-check | worker | 자기 수정 범위의 단위 테스트, API/컴포넌트 테스트, lint/build를 가능한 만큼 실행한다. Node/Playwright는 보조 검증이다. |
| Wave 종료 검증 | Orchestrator | worker 테스트를 재실행하고, 현재까지 가능한 build/run-check/회귀 검증으로 통합 깨짐을 확인한다. |
| Gate 4 QA | QA/review/evidence | 전체 사용자 시나리오, Playwright 화면 증적, Test Result, QA Finding을 확정한다. |

Wave가 전체 사용자 시나리오를 완성하지 않았다면 전체 E2E나 최종 화면 증적을 Wave 완료 조건으로 요구하지 않는다.
Gate 3 테스트 설계에서 이 Wave의 `target_contracts`에 매핑된 `UT/IT/UI`와 필요한 smoke 기준만 Wave 검증으로 수행한다.
Wave가 vertical slice를 완성한 경우에는 제한된 smoke/E2E를 실행할 수 있지만, 최종 QA Pass는 Gate 4에서만 판정한다.
최종 UI 확인과 Playwright 증적은 개별 worker worktree가 아니라 `workflow.integration_branch` 기준 `QA-000` QA workspace에서 수행한다.
완료 보고에는 "전체 통합 테스트 완료" 대신 "Wave 범위 계약 테스트와 가능한 회귀 검증 완료"처럼 범위를 명확히 쓴다.

## Orchestrator와 subagent 책임

- Orchestrator는 Build Wave Run 작업지시서 작성, native worker(subagent/thread/native branch agent) 위임, 결과 검토, 통합, worker 테스트케이스 재실행, 상태 갱신을 담당한다.
- Orchestrator는 Build Wave Run을 worker에게 넘기기 전에 `--trace-seed` 추천값을 확인하고, `scope.writable`, `target_contracts.interface_contract`, `contract_skeleton`, 검증 명령을 실제 구현 범위에 맞게 확정한다.
- 기능 구현의 주 작성자는 `build` persona의 native worker다. `agent-run --mode work`와 `run-exec`는 별도 CLI 프로세스, worktree 격리, watchdog/timeout 증적, cross-runner 실행이 필요할 때 선택하는 옵션이다.
- subagent/thread 위임은 외부 프로세스 실행 기록이 없을 수 있으므로 `delegation_records`로 책임 추적을 남긴다. `delegation_records`가 있으면 Orchestrator는 해당 변경을 재검증한 뒤 Wave 상태를 갱신한다.
- 작은 기능, 단일 파일, 단일 테스트 변경이라도 Orchestrator가 바로 구현 완료 처리하지 않는다. 단일 worker Run으로 위임하거나 직접 수정 예외를 기록한다.
- Orchestrator가 직접 수정할 수 있는 범위는 작은 연결 수정, 충돌 해결, 문서/추적표/session 갱신, 검증 보정으로 제한한다.
- 사용자가 worker 사용을 명시하지 않았다는 점은 직접 수정 예외 사유가 아니다. 구현 승인이 있으면 native worker 위임을 기본값으로 둔다.
- 직접 수정 예외는 worker/subagent/thread 실행 불가, worker 결과 통합 중 충돌 해결에 필요한 최소 수정, 긴급한 1~2줄 연결 수정, 사용자의 명시적 직접 구현 승인에 한해 허용한다.
- 직접 수정 예외가 필요하면 `orchestrator_direct_edit_reason`, `direct_edit_scope.files`, `direct_edit_scope.estimated_loc`, `direct_edit_scope.contract_changed`, 실행 검증, 후속 검수 필요 여부를 Run에 남긴다.
- 직접 구현 예외는 2개 이하 파일, 약 30 LOC 이하, public API/PGM/IF/MTH/DTO/schema/DB/security/SCR/UI contract 변경 없음, 기존 테스트 또는 작은 테스트 보정으로 검증 가능한 경우로 제한한다.
- 이 기준을 넘으면 직접 구현하지 않고 Build Wave Run 또는 worker Run으로 분리한다.
- 한 Wave를 여러 runner에게 나누어 동시에 구현시키지 않는다. backend/frontend처럼 작업지시서가 분리되어야 하면 서로 다른 `build-wave` Run, 보통 서로 다른 `BW-ID`로 나눈 뒤 순차 실행한다.
- 다른 Wave의 코드 수정은 현재 Wave가 완료될 때까지 금지한다.
- subagent, `codex-cli`, `claude-cli` 같은 작업자 runner는 Gate 전환, `session.json` Gate 상태 변경, 최종 승인 판단을 하지 않는다.
- 작업자 runner는 `wave-complete`, Gate 전환, QA Pass, PR merge가 필요하다고 판단하면 완료 보고의 Orchestrator 결정 필요 항목으로 반환한다.
- 작업자 runner의 `scope.writable`에는 담당 코드/테스트/자기 Run 문서만 둔다. 화면 증적처럼 직접 산출해야 하는 파일이 있을 때만 담당 증적 경로를 추가한다. 추적표, 테스트 결과서, `session.json`은 Orchestrator 통합 범위로 둔다.
- 시간이 부족하다는 이유로 빌드/테스트가 깨진 중간 구현을 완료 처리하지 않는다.

## 상태

| 상태 | 의미 |
| --- | --- |
| `Planned` | 계획됨 |
| `In Progress` | 구현 중 |
| `Implemented` | Wave 범위 코드 작성 완료. 추적표 최종 상태가 아니라 Orchestrator 재검증 전 후보 상태 |
| `Verified` | Orchestrator가 Wave 범위 테스트를 재실행해 통과 확인했고 `open_issues`가 비어 있음. Gate 4 QA Pass와는 다름 |
| `CompletedWithIssues` | 주요 산출물은 있으나 후속 worker, QA Fix, CR/FIND/ISSUE 분류가 필요한 항목이 남아 있음 |
| `Blocked` | 질문, 설계 누락, 환경 문제로 중단 |
| `Rolled Back` | 해당 Wave 변경을 되돌림 |

## 완료 조건

- Wave 관련 ID가 코드, 테스트, 작업자 Run 결과에 연결되어 있고, 추적표 갱신 필요 항목이 Orchestrator에게 전달되어 있다.
- Wave의 target_contracts가 기능/계약 단위의 완결 조각으로 닫혀 있다.
- 구현 파일의 패키지 구조, logger 선언, 주석/JavaDoc/docstring, 예외/메시지 처리가 개발표준정의서 및 `development_standard_checklist`와 모순되지 않는다.
- 테스트는 추적 ID만 남기지 않고 `@DisplayName`, Given/When/Then, 또는 입력값/기대값/출력값 설명 중 프로젝트 표준 방식으로 검증 의도를 드러낸다.
- 담당 테스트케이스와 Orchestrator 재실행 명령이 남아 있으며, worker self-check 결과 또는 Not Run 사유가 기록되어 있다.
- worker 환경에서 Node/Playwright 설치 또는 실행이 막히면 `environment_blocked` 또는 `not_run` 사유와 Orchestrator 재실행 명령이 기록되어 있다.
- worker worktree에서 화면 서버나 Playwright를 못 띄운 사실만으로 구현 실패를 확정하지 않는다. 통합 UI/Playwright 판정은 Gate 4 QA 입력으로 넘긴다.
- 실패한 테스트는 숨기지 않고 `FIND` 또는 `ISSUE`로 남긴다.
- `open_issues`가 남아 있으면 `Verified`로 닫지 않는다. 후속 조치가 필요하면 `CompletedWithIssues` 또는 `Blocked`로 보고하고, Orchestrator가 별도 보정 Run/QA Fix/CR 여부를 판단한다.
- 작업자 runner는 추적표 갱신 필요 항목을 보고하고, Orchestrator가 worker 테스트케이스와 현재 Wave 범위에서 가능한 회귀 검증을 재실행한 뒤 `vulcan.py wave-complete <BW-ID>`, `vulcan.py sync-session`으로 session을 반영한다. Gate 전환 준비는 `python vulcan.py prepare-transition`으로 확인하고, 추적성 오류가 남을 때만 `python vulcan.py check-trace`를 상세 진단으로 실행한다.
- Wave 완료를 Gate 4 QA Pass나 전체 E2E 완료로 표현하지 않는다.
- 다음 Wave 진행 가능 여부와 남은 위험을 보고한다.

## 출력

다음을 반환한다.

- `BW-ID`
- 수행한 구현 범위
- 변경 파일
- 관련 ID
- 개발표준 준수 체크리스트
- `development_standards_applied` / `development_standard_checklist` 준수 결과와 예외 사유
- 작성/갱신한 테스트케이스
- Orchestrator 재실행 명령
- worker self-check 결과 또는 Not Run 사유
- 추적표/문서 갱신 필요 항목
- 커밋 메시지 후보
- 다음 Wave 진행 여부
- `FIND`, `ISSUE`, `CR` 후보
