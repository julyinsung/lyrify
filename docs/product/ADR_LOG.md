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
| ADR-001 | 로컬 무균성 및 자동화 트레이드오프를 위한 Docker 및 Web Audio/LRCLIB 하이브리드 가사 싱크 아키텍처 채택 | Accepted | 2026-07-08 | CMP-006, API-006, SCN-004 |

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

## 4. ADR 상세 기록

### ADR-001: Docker 및 Web Audio/LRCLIB 하이브리드 가사 싱크 아키텍처 채택

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-001 |
| Context | AI 기반 오디오 가사 싱크(Forced Alignment)를 위해 로컬 AI 구동(Python, PyTorch 등)이 필요하나, 사용자 로컬 PC에 복잡한 AI 구동 의존성을 강제 설치하는 것은 무겁고 환경을 오염시킬 위험이 있음. 반면 클라우드 API(Google STT)는 인터넷이 필수적이며 사용자의 유료 GCP API 키 등록 등의 번거로운 과정이 동반됨. |
| Decision | 시스템에 Docker 데몬이 실행 중일 경우 로컬 Docker Gentle/Whisper API 컨테이너를 호출하여 AI 싱크 정렬을 처리하고, Docker가 없을 경우 가벼운 Web Audio 기반 비트 감지(세미 오토) 및 무료 온라인 가사 API(LRCLIB)를 백업으로 사용하는 하이브리드 백엔드 처리 방식을 채택함. |
| Alternatives | 1. 로컬 Python/PyTorch 환경 강제 설치 (기각 - 일반 사용자 환경 오염 및 설치 진입 장벽).<br>2. Google GCP Speech-to-Text API 강제 적용 (기각 - 결제 카드 등록 및 유료 사용 거부감, 인터넷 필수 조건 제약). |
| Consequences | - 장점: 로컬 PC의 독립성과 무균성을 보존하며, 사양 및 환경에 맞춤화된 최적의 사용자 경험 제공.<br>- 비용: 백엔드에서 Docker 존재 여부를 검사하고 여러 동기화 흐름을 유연하게 처리하기 위한 분기 개발 공수 발생. |
| Related Scenario / Contract | SCN-004, CMP-006, API-006 |
| Status | Accepted |
