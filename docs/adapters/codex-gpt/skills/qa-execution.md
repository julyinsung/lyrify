# QA 실행 및 증적 수집 Skill

## 사용할 때

Gate 4에서 승인된 구현물을 실제로 실행 검증하고, 테스트 결과서, 로그, 화면 증적, 후보 발견사항을 만드는 데 사용한다.

이 skill은 결함을 고치는 절차가 아니다. 결함 수정은 Orchestrator가 사용자와 처리 방향을 정한 뒤 별도 `qa-fix-loop` Run으로 수행한다.

## 필수 입력

- `docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md`
- `docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md`
- `docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md`
- 관련 구현 산출물과 실행 명령
- 화면이 있으면 관련 UI-ID와 Playwright 기준

## 절차

Gate 4 QA 실행은 한 번에 모두 수행하지 않고 다음 순서의 작은 QA Run으로 나눈다.

| 단계 | 목적 | 최소 확인 |
| --- | --- | --- |
| `QA-000` | 환경 준비/스모크 | 통합 브랜치 작업공간에서 통합된 소스 존재, 의존성 설치 가능성, DB/포트/환경변수, backend/frontend 기동 가능성, Playwright 설치/브라우저 캐시 |
| `QA-001` | 명령 기반 검증 | backend/frontend test, lint, build, `check-contract`, `check-trace`, `run-check`, 로그 증적 |
| `QA-002` | UI/E2E 증적 | `QA-000`이 준비한 QA workspace에서 서버 기동, UI-ID별 Playwright screenshot/log/trace |
| `QA-003` | 결과 정리/판정 후보 | `DOC-QA-G4-001`, `DOC-QA-G4-002`, 추적표 반영 후보, FIND/CR/ISSUE, Orchestrator 결정 필요 항목 |

`QA-000`은 Gate 4 전체에서 재사용할 QA workspace를 준비하는 단계다.
기본 QA workspace는 `workflow.integration_branch`의 현재 작업공간이다. QA worktree는 프로젝트 정책에서 명시적으로 활성화한 경우에만 사용한다.
후속 `QA-001`, `QA-002`, `QA-003`은 새 작업공간을 임의로 만들지 않고 `QA-000`이 결과에 기록한 같은 `qa_workspace_path`에서 실행한다.
`QA-000`이 `qa_workspace_path`를 남기지 못했거나 환경 차단 상태라면 후속 QA Run은 진행하지 않는다.

`QA-000`은 다음 항목을 명시적으로 확인한다.

| 확인 항목 | 기준 |
| --- | --- |
| Backend 빌드 도구 | Gradle wrapper 또는 프로젝트 지정 빌드 도구가 로컬 캐시/권한 기준으로 실행 가능한가 |
| Backend smoke | backend 최소 smoke test, test discovery, 또는 컴파일 확인이 가능한가 |
| Frontend 의존성 | `node_modules` 존재 여부 또는 `npm ci`/`npm install` 실행 가능 여부 |
| Playwright | `@playwright/test`와 browser cache 존재 여부 또는 `npx playwright install` 실행 가능 여부 |
| 포트 | backend/frontend 개발 포트(예: 8080, 5173 또는 프로젝트 지정 포트)가 사용 가능한가 |
| DB | SQLite 또는 프로젝트 지정 DB 파일을 생성/접근할 수 있는가 |
| 환경변수/출력 경로 | test profile, 필수 환경변수, 임시 디렉터리, 로그/증적 출력 디렉터리가 준비되어 있는가 |

1. 현재 Run이 `QA-000`, `QA-001`, `QA-002`, `QA-003` 중 어느 단계인지 먼저 확인한다.
2. `QA-000`이면 후속 QA Run이 재사용할 `qa_workspace_path`와 기준 브랜치/커밋을 기록한다. 기본값은 현재 integration branch 작업공간이다.
3. `QA-001`, `QA-002`, `QA-003`이면 `QA-000`이 기록한 같은 `qa_workspace_path`에서 실행한다.
4. `QA-000`이 통과하지 않으면 `QA-001`/`QA-002`를 진행하지 않고 `environment_blocked` 또는 `Not Run`으로 사유를 기록한다.
5. Gate 3 테스트케이스와 개발표준정의서의 필수 검증 명령을 확인한다.
6. 명령별 실행 위치, 성공 기준, 로그/증적 저장 위치를 먼저 정한다.
7. 현재 QA 단계에 맞는 검증만 실행한다.
8. 실행 결과를 `Pass`, `Fail`, `Not Run`, `Skipped`, `environment_blocked` 중 하나로 기록한다.
9. 실패하면 코드를 바로 수정하지 않는다. 원인 가설, 재현 명령, 로그 경로, 영향 ID, 후보 FIND/CR/ISSUE를 `failure_reports`에 기록한다.
10. Playwright 화면 증적은 상태/시나리오별 UI-ID와 screenshot/log/trace를 1:1로 연결한다.
11. Playwright `dialog`는 무조건 숨기지 않는다. 예상된 dialog는 메시지/발생 시점/스크린샷을 기록한 뒤 처리할 수 있지만, 예상하지 않은 dialog는 Fail 또는 FIND 후보로 남긴다.
12. npm, Playwright, registry, cache, 권한, 네트워크 문제로 검증이 막히면 코드 실패로 단정하지 않고 `environment_blocked`로 기록한다.
13. 새 API, 새 메소드, 요구사항, 설계, 보안 기준 변경이 필요해 보이면 직접 만들지 않고 CR 후보로 반환한다.
14. QA Pass, Gate 완료, 릴리즈 가능 여부는 확정하지 않는다. Orchestrator 결정 필요 항목으로 반환한다.

QA-003에서 실제 실행 상태를 정리할 때는 `DOC-QA-G4-002_Test-Result_v0.1.md`를 원본으로 삼는다.
Gate 3 테스트케이스 문서는 계획과 기대 기준이며, QA-003에서 `Planned`를 `Pass`로 덮어쓰는 방식으로 실행 결과를 표현하지 않는다.
`check-trace`는 Gate 4에서 QA 테스트 결과서의 `결과` 컬럼을 우선 읽고, 결과서에 실행 상태가 없을 때만 Gate 3 테스트케이스를 fallback으로 참조한다.

## 금지

- 실패 원인을 확정하기 전에 코드를 수정하지 않는다.
- 검증 중 임의로 새 API, 새 메소드, 새 화면 상태를 만들지 않는다.
- `QA-000` 환경 확인 없이 UI/E2E 증적부터 진행하지 않는다.
- `QA-001`, `QA-002`, `QA-003`에서 `QA-000`이 남긴 workspace가 아닌 다른 작업공간을 임의로 사용하지 않는다.
- QA worktree가 활성화되어 있지 않은 프로젝트에서 Gate 4 QA용 worktree를 임의로 만들지 않는다.
- 하나의 QA Run에서 환경 확인, 전체 빌드, Playwright, 결과서 판정을 모두 끝내려고 하지 않는다.
- QA 실행 worker가 `qa-fix-loop`까지 이어서 수행하지 않는다.
- Playwright 없이 CDP/수동 캡처만으로 UI Pass를 선언하지 않는다.
- 예상하지 않은 Playwright dialog를 자동 accept만 하고 Pass로 숨기지 않는다.
- 실행하지 않은 테스트를 Pass로 기록하지 않는다.

## 출력

다음을 반환한다.

- 실행한 명령, cwd, exit code, 성공 기준, 결과
- 로그와 증적 파일 경로
- 현재 QA 단계와 다음 QA 단계 진행 가능 여부
- 상태별 UI 증적 매핑
- Playwright dialog 발생 여부, 예상/비예상 판정, 처리 결과
- 실패 원인 가설과 재현 명령
- 후보 `FIND`, `CR`, `ISSUE`
- `environment_blocked` 또는 `Not Run` 사유
- Orchestrator가 사용자와 협의해야 할 결정 항목

실패, 미실행, 환경 차단이 있으면 다음 구조를 반드시 남긴다.

```yaml
failure_reports:
  - qa_stage: QA-001
    failing_command: "npm run build"
    cwd: "qa_workspace/frontend"
    exit_code: 1
    observed_error: "Next build failed with module resolution error"
    log_path: "docs/artifacts/04-review/evidence/logs/QA-CMD-003_frontend-build.err.log"
    reproduction_command: "cd frontend && npm run build"
    impact_ids: [IT-002, NREQ-002]
    candidate_classification: FIND
    orchestrator_decision_needed:
      - "qa-fix-loop로 승인된 설계 범위 안에서 수정할지 결정 필요"
```
