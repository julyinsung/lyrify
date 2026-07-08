# Vulcan-Anvil Ex 문서 메타데이터

> 상태: 초안 v0.1
> 목적: Vulcan-Anvil Ex 공식 문서에 공통으로 들어갈 메타데이터를 정의한다.

## 1. 메타데이터 블록

모든 공식 문서는 문서 앞부분에 메타데이터 블록을 둔다.

Markdown 예시:

```yaml
---
document_id: DOC-CORE-G1-001
title: Requirements Specification
title_ko: 요구사항정의서
project: Sample Project
gate: G1
status: Draft
version: v0.1
owner_role: Requirements Lead
author: Codex
reviewer: Approver
approver: Approver
created_at: 2026-05-07
updated_at: 2026-05-07
related_ids:
  - REQ-001
  - NREQ-001
change_reason: Initial draft
---
```

Word, HWPX, PowerPoint, Spreadsheet 산출물은 같은 필드를 YAML 대신 표지 또는 문서 정보 표로 표현할 수 있다.

## 2. 필수 필드

| 필드 | 필수 여부 | 의미 |
| --- | --- | --- |
| `document_id` | 필수 | 안정적으로 유지되는 문서 ID |
| `title` | 필수 | 영문 또는 이식 가능한 문서명 |
| `title_ko` | 선택 | 사람이 읽는 한국어 문서명 |
| `project` | 필수 | 프로젝트명 |
| `gate` | 필수 | Phase 또는 Gate 코드 |
| `status` | 필수 | 현재 문서 상태 |
| `version` | 필수 | 문서 버전 |
| `owner_role` | 필수 | 문서 책임 역할 |
| `author` | 필수 | 문서를 작성한 사람 또는 에이전트 |
| `reviewer` | 선택 | 검토자 역할 또는 이름 |
| `approver` | 선택 | 최종 승인자 역할 또는 이름 |
| `created_at` | 필수 | 최초 작성일 |
| `updated_at` | 필수 | 마지막 수정일 |
| `related_ids` | 선택 | 문서가 다루는 관련 ID 목록 |
| `change_reason` | 선택 | 마지막 의미 있는 변경 사유 |

## 3. 상태값

| 상태 | 의미 |
| --- | --- |
| `Draft` | 작성 중 |
| `Review Requested` | 검토 또는 승인 요청 상태 |
| `Approved` | 승인된 베이스라인 |
| `Changed` | 승인 후 변경되었고 검토 대기 중 |
| `Superseded` | 새 문서로 대체됨 |
| `Archived` | 더 이상 활성 문서는 아니지만 증적으로 보관됨 |

## 4. 변경이력

공식 문서는 표지 또는 메타데이터 섹션 다음에 변경이력 표를 둔다.

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 | 2026-05-07 | 최초 초안 작성 | Codex |  |  |

규칙:

- 초안 단계의 변경이력은 간단히 관리할 수 있다.
- 승인된 문서는 의미 있는 변경이력을 보존해야 한다.
- 승인은 `v1.0` 베이스라인을 만든다.
- `v1.0` 이후의 모든 의미 있는 변경은 승인된 베이스라인이 왜 바뀌었는지 설명해야 한다.

## 5. 역할명

Core 문서에서는 직책명이 아니라 책임 기반 역할명을 사용한다.

권장 역할명:

| 역할 | 책임 |
| --- | --- |
| `Requirements Lead` | 요구사항, 범위, 인수기준 |
| `Business Analyst` | 업무 맥락과 사용자 흐름 |
| `Product Architect` | Phase 0 수준의 솔루션 방향 |
| `Technical Architect` | 기술 설계 |
| `Data Architect` | 데이터 모델과 DB 설계 |
| `UX/UI Designer` | 화면 흐름과 사용자 경험 설계 |
| `Test Designer` | 테스트 계획과 테스트 케이스 설계 |
| `QA Reviewer` | 검증, 테스트 결과 리뷰, 품질 판정 |
| `Security Reviewer` | 보안 통제와 보안약점 검토 |
| `Documentation Curator` | 문서 일관성, 용어, 버전 품질 관리 |
| `Approver` | Gate와 베이스라인 승인 |

## 6. 문서 유형

| 유형 | 버전 필수 | 변경이력 필수 | 예시 |
| --- | --- | --- | --- |
| 공식 산출물 | 필수 | 필수 | 요구사항정의서, 설계서, 테스트계획서, 테스트결과서 |
| 작업 메모 | 선택 | 선택 | Discovery 메모, 기술 검토 메모 |
| 반복 보고서 | 선택 | 선택 | 주간보고서, 회의록 |
| 증적 | 선택 | 선택 | 스크린샷, 로그 export, CI 결과 |

## 7. 프로젝트별 확장 필드

프로젝트는 감리 또는 고객 요구에 맞춰 필드를 추가할 수 있다.

예시:

```yaml
customer_document_no: KISA-PT-AN-요구사항정의서
external_approval_no: APR-2026-001
source_contract: RFP-2026-01
```

Core 도구는 프로젝트 Adapter가 별도로 검증하도록 지정하지 않은 확장 필드는 무시할 수 있어야 한다.

## 8. 운영 상태와 업무 내용의 분리

문서 메타데이터와 업무 산출물 본문은 구분해서 작성한다.

다음 항목은 프로젝트의 업무 제약, 요구사항, 성공 기준, 비목표로 기록하지 않는다.

- 현재 `session.json.current_gate` 값
- 현재 Run 번호 또는 에이전트의 작업 제한
- `vulcan.py check-trace` 통과 여부
- 대시보드 표시 상태
- 에이전트가 다음 Gate로 넘어가기 전 멈춰야 한다는 운영 지침

이 정보는 `session.json`, `docs/runs/`, 완료 보고, 검증 로그에 남긴다.

예를 들어 "현재 Gate는 gate1이다"는 프로젝트 제약이 아니다. 필요한 경우 Run 기록이나 완료 보고에 "현재 session gate가 gate1이라 구현은 보류했다"처럼 운영 판단으로 남긴다.
