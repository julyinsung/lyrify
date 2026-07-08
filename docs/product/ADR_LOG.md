# ADR Log

---
document_id: PROD-ADR
title: ADR Log
title_ko: 제품 아키텍처 의사결정 기록
project: lyrify
profile: product
gate_scope: gate2-gate5
status: Draft
version: v0.1
owner_role: Product Architect
author: Agent
reviewer: User
approver: User
created_at: 2026-07-08
updated_at: 2026-07-08
related_documents:
  - docs/product/PRODUCT_ARCHITECTURE.md
---

## 1. Decision Index

| ADR ID | 제목 | 상태 | 결정일 | 영향 범위 |
| --- | --- | --- | --- | --- |
| ADR-NONE | 현재 기록된 ADR 없음 | N/A | 2026-07-08 | 제품 아키텍처 의사결정이 생기면 ADR-001부터 추가 |

## 2. ADR 작성 기준

| 항목 | 내용 |
| --- | --- |
| 언제 작성하나 | 런타임, 데이터 저장소, 외부 연동, 보안 기준, 배포 방식처럼 후속 구현/운영에 영향을 주는 선택을 했을 때 작성한다. |
| 번호 규칙 | 첫 실제 의사결정은 `ADR-001`부터 시작한다. |
| 상태 | `Proposed`, `Accepted`, `Superseded`, `Rejected` 중 하나를 사용한다. |
| 비어 있을 때 | 실제 의사결정이 없으면 `ADR-NONE` 행을 유지한다. 아직 확정되지 않은 `ADR-001` placeholder 행은 남기지 않는다. |

## 3. ADR 상세 템플릿

새 ADR을 추가할 때 아래 형식을 복사해 사용한다.

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-001 |
| Context | 결정 배경 |
| Decision | 선택한 방향 |
| Alternatives | 검토한 대안 |
| Consequences | 장점, 비용, 후속 작업 |
| Related Scenario / Contract | 관련 SCN/API/DATA/UI/REG |
| Status | Proposed / Accepted / Superseded / Rejected |
