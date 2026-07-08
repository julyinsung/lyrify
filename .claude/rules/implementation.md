---
paths:
  - "src/**"
---

# 구현 규칙

## 진입 조건

- 현재 `session.json.current_gate`가 `impl` 또는 그 이상이어야 한다.
- Gate 2 설계 검수(요구사항/보안/화면/UI/개발표준)가 모두 통과되어 있어야 한다.
- Gate 3 테스트 설계가 끝나 있어야 한다 (Hotfix 예외는 사용자 명시 승인 필요).
- 개발표준정의서가 Draft가 아니어야 한다.

## Build Wave 단위 진행 (`docs/core/AGENT_RUN_PROTOCOL.md` §5.1)

구현 범위가 중간 이상이거나 subagent/여러 커밋/여러 모듈/UI 증적이 함께 필요한 경우:

1. **Implementation Plan Run** 생성 — `docs/adapters/codex-gpt/skills/implementation-plan.md` 절차로 전체 구현을 `BW-NNN`로 분할.
2. **Build Wave Run**으로 하나씩 진행 — active Wave는 동시에 하나만.
3. Wave 종료마다 코드 + 테스트 + 추적표 + 검증 결과 + 커밋 후보를 함께 남긴다.

작은 단일 Run 구현은 Wave 생략 가능. 단, Run에 생략 이유·단일 범위·관련 ID·실행 테스트·추적표 갱신 기준·커밋 메시지 후보를 적는다.

Wave 시작/완료는 `python vulcan.py wave-start`, `wave-complete`, `sync-session`으로 처리한다. `session.json` 수동 편집 금지.

## 병렬 실행 조건

같은 Wave 내부에서 수정 범위가 겹치지 않는 subagent 병렬 작업은 허용. 단,

- 두 단위가 같은 DB 테이블/마이그레이션을 변경하지 않을 것
- API 호출 의존이 없을 것
- 공유 컴포넌트/모듈이 충돌하지 않을 것

## 단위 테스트

- Developer(`build` persona)가 `UT-NNN`을 구현과 함께 작성·실행한다.
- Test-Cases에 `UT` 참조만 둔다(중복 정의 금지).
- 테스트가 통과해야 Wave 완료로 본다.

## 팀 소통

- build-frontend ↔ build-backend(둘 다 `build`): API 스펙·응답 형식을 사전에 맞춘다.
- 구현 완료 → `evidence` persona로 `evidence` 투입(스크린샷 기반 UI 검수).
- evidence Fail → `build`로 build-frontend 재투입(최대 2회).
- evidence 통과 → `review` persona로 `review` 인계.

## Implementation Run 완료 기준 (`AGENT_RUN_PROTOCOL.md` §5.1)

- 개발표준 준수 확인
- 추적표 증적에 실제 구현 파일 경로 연결
- 구현 또는 테스트 파일 안에 `REQ`/`PGM`/`SCR`/`SEC`/`UT`/`IT` 중 하나 이상의 ID 표시
- Gate 3 정의 테스트 실행 — Pass/Fail/Skip/미실행 상태 기록
- 화면 구현 시 desktop/mobile 양쪽에서 시안/화면설계서 대비 확인
- 테스트케이스/추적표/Run 기록 갱신
