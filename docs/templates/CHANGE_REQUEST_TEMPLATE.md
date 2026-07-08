# 변경요청 관리대장

```yaml
---
document_id: DOC-PM-G0-001
title: Change Request Register
title_ko: 변경요청 관리대장
project:
gate: G0
status: Draft
version: v0.1
owner_role: Orchestrator
author:
reviewer:
approver:
created_at:
updated_at:
related_ids: []
change_reason: 변경요청 목록과 처리 상태 관리
---
```

## 1. 변경요청 목록

| CR-ID | 제목 | 유형 | 우선순위 | 상태 | 다시 진행할 Gate | 상세 문서 | 관련 Backlog |
| --- | --- | --- | --- | --- | --- | --- | --- |
| — | (아직 없음) | — | — | — | — | — | — |

## 2. 상태 기준

| 상태 | 의미 |
| --- | --- |
| Draft | 초안 작성 중 |
| Reviewing | 영향도 검토 중 |
| Pending Approval | 사용자 승인 대기 |
| Approved | 승인됨 |
| Rejected | 반려됨 |
| Deferred | 보류됨 |
| Done | 반영 및 검증 완료 |

## 3. 운영 기준

- 상세 변경요청은 `DOC-PM-CR-NNN_*_v0.1.md` 문서로 작성한다.
- 상세 변경요청 문서는 `docs/templates/CHANGE_REQUEST_DETAIL_TEMPLATE.md`를 복사해 작성한다.
- 승인된 CR은 영향받는 `REQ/AC/FUNC/SCR/PGM/DB/SEC/UT/IT/UI`와 연결한다.
- 요구사항 또는 설계 기준선이 바뀌면 필요한 Gate를 `vulcan.py gate-start <gate>`로 다시 진행한다.
- 승인된 CR로 Gate를 다시 진행할 때는 반드시 관련 Run 문서를 작성한다.
- 즉시 반영하지 않는 CR은 백로그 항목과 연결한다.
- 모든 변경 후보가 백로그를 먼저 거치는 것은 아니다. 기준선 변경이 명확하면 CR 상세서를 먼저 만들고, 승인 후 즉시 처리하지 않을 때만 백로그와 연결한다.

## 4. 변경이력

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 |  | 최초 작성 |  |  |  |
