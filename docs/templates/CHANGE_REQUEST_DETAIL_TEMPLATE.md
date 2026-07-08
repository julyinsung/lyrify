# 변경요청 상세서

```yaml
---
document_id: DOC-PM-CR-NNN
title: Change Request Detail
title_ko: 변경요청 상세서
project:
gate: G0
status: Draft
version: v0.1
owner_role: change-control
author:
reviewer:
approver:
created_at:
updated_at:
related_ids: []
change_reason: 개별 변경요청 영향도 분석 및 승인 판단
---
```

## 1. 변경요청 개요

| 항목 | 내용 |
| --- | --- |
| CR-ID | CR- |
| 제목 |  |
| 요청 출처 | 사용자 / 고객 / QA / 리뷰 / 운영 / 에이전트 발견 |
| 요청일 |  |
| 요청자 |  |
| 유형 | Requirement / Design / Security / UI / Data / Test / Release / Other |
| 우선순위 | P0 / P1 / P2 / P3 |
| 상태 | Draft / Reviewing / Pending Approval / Approved / Rejected / Deferred / Done |
| 관련 Backlog | BL- / 없음 |
| 관련 Finding 또는 Issue | FIND- / ISSUE- / 없음 |

## 2. 요청 내용

| 항목 | 내용 |
| --- | --- |
| 현재 상태 |  |
| 요청 변경 |  |
| 변경 사유 |  |
| 기대 효과 |  |
| 미반영 시 영향 |  |

## 3. 변경 분류 판단

| 판단 항목 | 결과 | 근거 |
| --- | --- | --- |
| 기존 요구사항/설계 내 결함인가 | Yes / No |  |
| 요구사항 또는 AC 변경이 필요한가 | Yes / No |  |
| 기능/화면/프로그램/DB/보안 설계 변경이 필요한가 | Yes / No |  |
| 테스트 기준 변경이 필요한가 | Yes / No |  |
| 릴리즈 범위 또는 승인 조건 변경인가 | Yes / No |  |

## 4. 영향도 분석

| 영향 영역 | 영향받는 ID 또는 파일 | 조치 |
| --- | --- | --- |
| 요구사항 | REQ- / NREQ- / AC- |  |
| 기능 설계 | FUNC- |  |
| 화면 설계 | SCR- / UIREF- |  |
| 프로그램/API 설계 | PGM- / API- |  |
| 데이터 설계 | DB- / TERM- |  |
| 보안 | SEC- / SR- / CWE- / OWASP- |  |
| 테스트 | UT- / IT- / PT- / UI- |  |
| 구현 파일 |  |  |
| 문서 |  |  |

## 5. Gate 진행 및 처리 방안

| 항목 | 내용 |
| --- | --- |
| 다시 진행할 Gate | G1 / G2 / G3 / Impl / G4 / G5 |
| 처리 Scope |  |
| 필수 Run | RUN- |
| 즉시 반영 여부 | 즉시 Run / Backlog 이월 / 보류 |
| Build Wave 필요 여부 | Yes / No |
| 예상 검증 |  |

## 6. 테스트 및 회귀 검증 기준

| 테스트 | 실행 기준 | 결과 |
| --- | --- | --- |
| 변경 관련 단위테스트 | 필수 | Pass / Fail / Not Run |
| 전체 단위테스트 | 자동화되어 있으면 원칙적으로 실행 | Pass / Fail / Not Run |
| 통합/API 테스트 | 영향받는 흐름 중심으로 실행 | Pass / Fail / Not Run |
| UI/화면 증적 | 화면 변경 시 필수 | Pass / Fail / Not Run |
| 성능/보안 검증 | 관련 기준 변경 시 실행 | Pass / Fail / Not Run |

## 7. 승인 판단

| 항목 | 내용 |
| --- | --- |
| 승인 여부 | Approved / Rejected / Deferred |
| 승인자 |  |
| 승인일 |  |
| 승인 조건 |  |
| 반려 또는 보류 사유 |  |

## 8. 반영 결과

| 항목 | 내용 |
| --- | --- |
| 반영 Run | RUN- |
| 반영 커밋 |  |
| 갱신 산출물 |  |
| 검증 결과 |  |
| 증적 |  |
| 추적표 반영 | Done / Pending / N/A |

## 9. 변경이력

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 |  | 최초 작성 |  |  |  |
