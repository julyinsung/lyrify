# QA 발견사항

```yaml
---
document_id: DOC-QA-G4-001
title: QA Finding
title_ko: QA 발견사항
project:
gate: G4
status: Draft
version: v0.1
owner_role: QA Reviewer
author:
reviewer:
approver:
created_at:
updated_at:
related_ids:
  - FIND-001
change_reason: 최초 초안 작성
---
```

## 1. 발견사항 개요

결함이 없으면 문서를 Draft로 비워두지 않고 아래 형식으로 명시한다.

```text
No Findings
```

| 항목 | 내용 |
| --- | --- |
| QA 결과 | No Findings |
| 판단 근거 | 실행한 QA 명령, 화면 증적, Test Result 문서 기준으로 신규 FIND 없음 |
| 관련 Run | RUN- |
| 후속 조치 | 없음 / Backlog / 관찰 필요 |

결함이 있으면 아래 FIND 단위 표를 사용한다.

| 항목 | 내용 |
| --- | --- |
| FIND-ID | FIND-001 |
| 제목 |  |
| 발견 출처 | QA / Review / Test Failure / UI Evidence / Security Review |
| 발견일 |  |
| 심각도 | Blocker / Major / Minor / Trivial |
| 상태 | Open / In Progress / Fixed / Verified / Closed / Escalated |
| CR 필요 여부 | Yes / No |
| 관련 Run | RUN- |

## 2. 관련 추적 ID

| 구분 | 관련 ID |
| --- | --- |
| 요구사항 | REQ- / NREQ- |
| 인수조건 | AC- |
| 기능 | FUNC- |
| 화면 | SCR- |
| 프로그램 | PGM- |
| 데이터 | DB- / TERM- |
| 보안 | SEC- / KISA-SD-2021 SR- |
| 테스트 | UT- / IT- / PT- / UI- |
| 증적 | UI- / LOG- / EV- |

## 2.1 증적 매칭

QA 발견사항의 증적은 전체 테스트 증적을 반복하지 않고, 해당 FIND/ISSUE 판단에 직접 필요한 증적만 연결한다.

| FIND/ISSUE ID | 관련 테스트/화면 ID | 증적 ID | 증적 성격 | 상태 | 설명 |
| --- | --- | --- | --- | --- | --- |
| FIND-001 | UT- / IT- / UI- | UI- / LOG- / EV- | 발견 증적 / 수정 후 검증 증적 / 미해결 상태 확인 증적 | Open / Fixed / Verified |  |

## 3. 현상

| 항목 | 내용 |
| --- | --- |
| 재현 조건 |  |
| 실제 결과 |  |
| 기대 결과 |  |
| 첨부 증적 | 발견사항 판단에 직접 필요한 증적 ID 또는 경로만 작성한다. 전체 테스트 증적 목록은 Test Result 문서에 둔다. |

## 4. 분류 판단

| 질문 | 답변 | 근거 |
| --- | --- | --- |
| 기존 요구사항 의미가 바뀌는가 | Yes / No |  |
| AC 추가/삭제/변경이 필요한가 | Yes / No |  |
| 설계 변경이 필요한가 | Yes / No |  |
| 보안 기준 완화가 필요한가 | Yes / No |  |
| 기존 설계를 만족시키기 위한 수정인가 | Yes / No |  |

판정:

```text
G4 QA Fix Loop / CR 승격 / ISSUE 유지
```

## 5. 조치 내용

| 항목 | 내용 |
| --- | --- |
| 원인 |  |
| 수정 파일 |  |
| 수정 요약 |  |
| 문서 갱신 |  |
| 테스트 갱신 |  |
| 증적 갱신 |  |

## 6. 검증 결과

| 검증 | 명령/방법 | 결과 | 근거 |
| --- | --- | --- | --- |
| 단위 테스트 |  | Passed / Failed / Not Run |  |
| 통합 테스트 |  | Passed / Failed / Not Run |  |
| 화면 테스트 |  | Passed / Failed / Not Run |  |
| 보안 검증 |  | Passed / Failed / Not Run |  |
| 추적표 확인 |  | Passed / Failed / Not Run |  |

## 7. 종료 판단

| 항목 | 확인 |
| --- | --- |
| 기존 설계 범위 내 수정임을 확인했는가 |  |
| 관련 테스트가 통과했는가 |  |
| 증적이 갱신되었는가 |  |
| 추적표 또는 Run 기록에 반영했는가 |  |
| CR 승격이 불필요한 사유를 기록했는가 |  |

## 8. 변경이력

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 |  | 최초 작성 |  |  |  |
