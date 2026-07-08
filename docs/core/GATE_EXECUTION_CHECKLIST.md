# Gate Execution Checklist

> 목적: 모든 runner와 adapter가 공통으로 따라야 하는 Gate 실행 체크리스트를 정의한다.

이 문서는 Codex, Claude, Gemini, Antigravity 같은 특정 런타임 전용 prompt가 아니다.
adapter별 prompt는 이 문서를 참조할 수 있지만, Core Gate 규칙을 대체하지 않는다.

## 1. 공통 원칙

- 항상 `session.json.current_gate`, 사용자 최신 지시, 현재 Run 문서를 먼저 확인한다.
- 현재 Gate보다 앞선 산출물, 구현, 테스트, QA 증적, 릴리즈 판단을 사용자 승인 없이 만들지 않는다.
- Gate 전환은 문서의 `gate:` 값으로 완료되지 않는다. 현재 위치는 `python vulcan.py status`로 확인하고, 전환 가능성은 기본적으로 `python vulcan.py status --check`로 진단한다. 실제 상태 갱신은 `vulcan.py gate-start`, `vulcan.py session`, `vulcan.py sync-session`으로 수행한다.
- `prepare-transition`은 상세/호환 전환 진단이 필요할 때 직접 실행하는 원자 명령이다. `check-trace`는 추적성 오류를 디버깅하거나 회귀 검증에서 추적성만 확인할 때 직접 실행한다.
- 의미 있는 변경은 관련 `REQ`, `NREQ`, `AC`, `FUNC`, `SCR`, `PGM`, `API`, `DB`, `SEC`, `UT`, `IT`, `UI`, `FIND`, `CR`, `RUN`과 연결한다.
- 실행하지 않은 테스트, 빌드, QA, 화면 증적을 `Pass`로 기록하지 않는다.
- 전역 memory, 과거 세션 요약, 다른 샘플 프로젝트 기록은 현재 프로젝트의 사실 근거로 사용하지 않는다.
- `docs/ref-docs/`는 민감한 참고자료일 수 있으므로 원문을 커밋하거나 산출물에 길게 인용하지 않는다.

## 2. Gate 종료 경계

- Gate 산출물을 완료하면 요약, 미해결 항목, 다음 Gate 제안, 사용자 승인 질문을 남기고 멈춘다.
- 사용자가 승인하기 전에는 다음 Gate 산출물 작성, 구현 착수, Gate 4 QA Pass, Gate 5 릴리즈 승인 선언을 하지 않는다.
- `status --check` 또는 상세 전환 진단이 실패하면 실패 위치, 영향 ID, 해결 후보를 남기고 다음 Gate로 넘어가지 않는다. 필요한 경우에만 `check-trace`를 추가 실행해 추적성 실패를 상세 분석한다.

## 3. Worker와 Subagent 경계

- worker, subagent, 외부 runner 결과는 후보 산출물이다. Orchestrator가 다시 검증하기 전에는 최종 사실로 확정하지 않는다.
- worker는 Gate 전환, `session.json` 직접 편집, 사용자 승인, QA Pass, 릴리즈 승인, merge 가능 판단을 직접 하지 않는다.
- worker가 범위 밖 변경이 필요하다고 판단하면 직접 수정하지 말고 Orchestrator 결정 필요 항목으로 반환한다.
- native subagent/thread/Agy Workspace: branch worker를 실행하기 전에는 Orchestrator가 `python vulcan.py run-preflight <run-file>`를 직접 실행한다. 외부 `run-exec`/`agent-run --mode work`는 자동 실행하지만 native 위임은 자동 차단되지 않는다.
- `prepare-transition`의 worker Run preflight 점검은 사후 안전망이다. worker 위임 전 preflight 실행을 생략해도 된다는 뜻이 아니다.
- subagent/thread를 사용한 경우에는 외부 CLI 수준의 `Run Execution Record`가 없을 수 있다. 대신 현재 Run 또는 결과 요약에 `delegation_records`를 남겨 위임 대상, 범위, 변경 파일, 결과 요약, Orchestrator 재검증을 추적한다.

## 4. Gate별 최소 확인

| Gate | 최소 확인 |
| --- | --- |
| Phase 0 | 목표, 사용자, 제약, 질문, 위험, 가정, 보류 항목이 분리되어 있는가 |
| Gate 1 | 상세 `REQ/NREQ/AC`가 테스트 가능한 문장이고 추적표 행과 연결되어 있는가 |
| Gate 2 | 아키텍처, 기능, 프로그램, API, DB, 보안, 화면/개발표준이 구현자가 따를 계약으로 전개되어 있는가 |
| Gate 3 | 테스트케이스가 요구사항, 보안, UI 상태/시나리오, 명령, 성공 기준, 증적 경로와 연결되어 있는가 |
| Impl | 승인된 Build Wave 범위 안에서 구현하고, worker Run 결과와 Orchestrator 재검증 명령이 남아 있는가 |
| Gate 4 | 테스트 결과, 로그, 화면 증적, FIND/CR/ISSUE 후보, QA 결과서가 실제 실행 결과를 기준으로 정리되어 있는가 |
| Gate 5 | 릴리즈 승인 근거, 잔여 위험, backlog, release note, 인수인계 항목이 정리되어 있는가 |

## 5. Adapter 문서 사용

- Core Run에는 이 문서를 기본 `read_first`로 둔다.
- Codex runner는 필요할 때 `docs/adapters/codex-gpt/GATE_PROMPTS.md`를 추가로 참고한다.
- Claude, Gemini, Antigravity runner는 각 adapter 문서 또는 루트 지침 파일을 참고하되, Codex 전용 prompt를 실행 계약으로 사용하지 않는다.
