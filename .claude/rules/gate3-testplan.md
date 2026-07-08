---
paths:
  - "docs/artifacts/03-test/**"
---

# Gate 3: 테스트 설계 규칙

## 산출물

- `docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md`
- 템플릿: `docs/templates/TEST_CASE_TEMPLATE.md`

## ID 체계

| Prefix | 의미 |
| --- | --- |
| `UT` | 단위테스트 (Developer가 구현 단계에서 작성·실행) |
| `IT` | 통합테스트 (모듈/시스템 연동) |
| `PT` | 성능/부하/스트레스/용량 테스트 |
| `UI` | 화면 렌더링·이벤트·반응형·캡처 증적 테스트 |

상세는 `docs/core/ID_SYSTEM.md` §3.

## 작성 규칙

- 각 테스트 케이스는 `REQ`/`AC` 또는 `SEC`/`SCR`/`PGM` 중 하나 이상과 연결한다.
- Gate 1 인수기준(`AC`)에 두지 않았던 검증 절차(`Given/When/Then` 외 세부 단계, 데이터, 자동화 파일명)는 여기에 작성한다.
- 화면 테스트(`UI`)는 viewport, 사용자 흐름, 기대 화면, 캡처/비교 기준을 함께 명시한다.
- 보안 테스트는 `SEC-NNN` 기반 시나리오로 작성한다.
- 테스트 도구/명령어는 `ENVIRONMENT.md`에 기록한다. Test-Plan에는 포함하지 않는다.

## 완료 조건

`docs/core/AGENT_RUN_PROTOCOL.md` §5: 모든 `AC`와 보안항목이 하나 이상의 `UT`/`IT`/`PT`/`UI`와 연결되어 추적표에 반영되어 있어야 한다.

## 추적표

`docs/artifacts/02-traceability/`에 `UT`, `IT`, `PT`, `UI` 컬럼을 갱신한다.
