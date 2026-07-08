---
paths:
  - "docs/artifacts/02-traceability/**"
---

# 요구사항추적표 갱신 규칙

산출물: `docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md`
템플릿: `docs/templates/TRACEABILITY_MATRIX_TEMPLATE.md`

`docs/core/TRACEABILITY_RULES.md`를 최종 근거로 한다.

## Gate별 갱신 책임

| Gate | 담당 persona / agent | 갱신 항목 |
| --- | --- | --- |
| Gate 1 | requirements | `REQ-NNN`, `NREQ-NNN`, `AC-NNN` 행 추가 (설계/테스트/리뷰 컬럼은 `-`) |
| Gate 2 | design, screen-design | `FUNC`, `PGM`, `API`, `SCR`, `DB`, `IF`, `SEC`, `UT 사전배정`, 설계 문서 경로 |
| Gate 3 | test-design | `UT`, `IT`, `PT`, `UI` |
| 구현 | build / build-frontend, build-backend | 구현 파일 경로, 단위 테스트 결과 |
| Gate 4 | review / review, evidence | 테스트 결과 증적, 화면 증적, FIND/CR 연결, 상태(`구현완료`/`수정예정`) |

## 원칙

- **미등록이면 `check-trace` 실패** → 해당 Gate 완료 불가.
- 설계/구현/테스트 문서 본문에는 관련 ID를 명시한다(`check-trace`가 grep으로 검사).
- 추적표 자체는 인공물이 아니라 **다른 산출물에서 모이는 결과**다. 추적표를 먼저 채워서 산출물 수를 부풀리지 않는다.
- 외부 식별자(`external_ids`)는 별도 컬럼에 보관한다(`ID_SYSTEM.md` §7).
