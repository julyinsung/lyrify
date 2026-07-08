---
paths:
  - "docs/artifacts/01-requirements/**"
---

# Gate 1: 요구사항 정의 규칙

## 산출물

- `docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md`
- 템플릿: `docs/templates/REQUIREMENTS_SPEC_TEMPLATE.md`
- 메타데이터: `docs/core/DOCUMENT_METADATA.md` 형식 준수

## ID 체계

- `REQ-NNN` — 기능 요구사항
- `NREQ-NNN` — 비기능 요구사항 (성능, 보안, 운영, 컴플라이언스, 제약)
- `AC-NNN` — 인수기준. 요구사항/기능을 검증할 수 있는 기준 문장과 검증 방식까지만 적는다.
  - `Given/When/Then`, 선행조건, 예외조건, 검증 데이터, 테스트 절차, 자동화 파일명은 **Gate 3 테스트케이스**에 작성한다 (`docs/core/AGENT_RUN_PROTOCOL.md` §5 마지막 단락).
- ID 규칙은 `docs/core/ID_SYSTEM.md` §2-§3.

## 작업

- 비전(배경/대상/가치/성공기준/제약/기존시스템)을 사용자 인터뷰로 정리한다.
- 모든 `REQ`에 하나 이상의 `AC` 또는 `없음: [이유]`를 매핑한다.
- 외부 식별자(RFP, Jira, 감리 ID)는 `external_ids`로 보관한다(`ID_SYSTEM.md` §7).
- 추적표 갱신: `docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md`의 REQ/NREQ/AC 행을 추가한다.

## 완료 조건

`docs/core/AGENT_RUN_PROTOCOL.md` §5: 모든 `REQ-NNN`과 `NREQ-NNN`에 `AC-NNN`이 매핑되고, 추적표에 반영되어 있어야 한다.

## 다음 Gate 진입

`python vulcan.py check-trace` 통과 후 `python vulcan.py session --gate gate2 --status start ...`로 전환한다.
