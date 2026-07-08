# Vulcan-Anvil Ex 핵심 원칙

이 규칙은 **항상 로드**된다. 모든 작업의 공통 전제다.

## 원칙

- 플래너는 코드를 쓰지 않는다. 실행자는 계획만 따른다.
- Gate 문서 없이 구현을 시작하지 않는다.
- 각 Gate는 사용자 승인 후 전환한다.
- 작업 단위는 **Run**이다. 의미 있는 모든 변경은 `REQ`, `AC`, `FUNC`, `SCR`, `PGM`, `API`, `DB`, `SEC`, `UT`, `IT`, `PT`, `UI`, `FIND`, `CR` 같은 ID와 연결한다.
- `session.json`으로 Gate 상태를 추적한다. `session.json.current_gate`보다 앞선 산출물·구현·테스트·증적을 임의로 만들지 않는다.
- 에이전트가 명령어를 사용자에게 안내하는 것이 아니라 **직접 실행**한다 (`python vulcan.py ...`).
- `check-trace` 실패 상태에서 Gate 전환 금지.
- 실제로 실행하지 않은 테스트를 통과했다고 보고하지 않는다. `not_run` / `failed` / `partial`을 명시한다.

## 변경 분류 (`docs/core/CHANGE_CONTROL_PROCESS.md`)

- **FIND** — 승인 범위 안의 결함. Gate 4 QA Fix Loop로 처리.
- **CR** — 요구사항/인수기준/설계/보안기준선/데이터설계/릴리즈 범위 변경. Gate 재진입.
- **ISSUE** — 결론이 어려운 질문/위험/보류. Backlog로 남김.
- **Gate 4 Blocker/Major는 백로그 이월 금지** — 현 Gate 내에서 해결한다.

## 승인된 CR의 Gate 재진행

승인된 변경요청(CR)은 `python vulcan.py gate-start <gate>`로 필요한 Gate를 다시 진행 상태로 전환한다. 별도 rollback 명령은 없다. 영향 범위는 **CR 상세서**(`docs/artifacts/05-change/DOC-PM-CR-NNN`)와 **Run 문서**의 scope로 관리한다. Run 문서에는 관련 `CR-ID`, 영향받는 ID(REQ/AC/FUNC/SCR/PGM/API/DB/SEC/UT/IT/UI), 갱신할 산출물 범위, 실행할 테스트 기준을 기록한다.

## Build Wave (`docs/core/AGENT_RUN_PROTOCOL.md` §5.1)

구현 규모가 중간 이상이거나 subagent/여러 커밋/여러 모듈이 필요하면 `implementation-plan` Run을 만들어 Build Wave(`BW-NNN`)로 분할한다. active Wave는 하나만 둔다.

## 운영 상태와 업무 내용의 분리

`session.json.current_gate`, 현재 Run 번호, `check-trace` 통과 여부 같은 운영 상태는 프로젝트 제약/요구사항/성공 기준에 적지 않는다. `session.json`, `docs/runs/`, 완료 보고에만 남긴다.
