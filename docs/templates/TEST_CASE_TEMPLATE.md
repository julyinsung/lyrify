# 테스트케이스

```yaml
---
document_id: DOC-QA-G3-001
title: Test Case Specification
title_ko: 테스트케이스 정의서
project: 프로젝트명
gate: G3
status: Draft
version: v0.1
owner_role: Test Designer
author: 작성자 또는 에이전트
reviewer: QA Reviewer
approver: Approver
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
related_ids:
  - REQ-001-01
  - AC-001-01
  - UT-001
  - IT-001
change_reason: 최초 초안 작성
---
```

## 1. 문서 목적

본 문서는 요구사항, 인수기준, 보안항목, 비기능 요구사항을 검증하기 위한 테스트 케이스를 정의한다.

테스트는 테스트 자체를 위해 존재하지 않는다. 모든 테스트는 `REQ`, `AC`, `NREQ`, `SEC`, `CR` 중 하나 이상과 연결되어야 한다.

## 2. 작성 기준

- 단위테스트는 `UT-001` 형식으로 부여한다.
- 통합테스트는 `IT-001` 형식으로 부여한다.
- 성능테스트는 `PT-001` 형식으로 부여한다.
- Gate 3 테스트 설계는 그룹 요구사항 `REQ-001`이 아니라 상세 요구사항 `REQ-001-01` 단위로 매핑한다.
- 각 상세 `REQ-NNN-NN`은 하나 이상의 `UT`, `IT`, `UI`, `PT` 또는 승인된 검토 테스트와 연결한다.
- 각 테스트는 관련 `REQ-NNN-NN`, `AC-NNN-NN`, `SEC`, `NREQ` 중 하나 이상과 연결한다.
- 보안 테스트는 가능한 경우 외부 보안 기준 `SR`을 함께 기록한다.
- 화면 테스트는 상태/시나리오 단위로 `UI-001-01` 형식까지 세분화하고 관련 `SCR-ID`, 기준 시안, viewport, 기대 화면, 캡처 경로를 기록한다.
- 하나의 화면 흐름에 기본/오류/성공/전환 상태가 있으면 각각 별도 UI 테스트와 증적을 둔다.
- 기준 시안이 UI Implementation Contract를 가지면 UI 테스트의 기대 화면과 비교 방식에 필수 유지, 변경 허용, 변경 금지 항목을 반영한다.
- 자동화 또는 명령 기반 검증은 실행 위치(cwd), Windows/POSIX 명령, 성공 기준, 로그/증적 경로를 기록한다.
- 테스트 결과와 증적은 Gate 4에서 테스트결과서와 요구사항추적표에 반영한다.

## 3. 테스트 범위

| 구분 | 포함 범위 | 제외 범위 | 비고 |
| --- | --- | --- | --- |
| 단위테스트 |  |  |  |
| 통합테스트 |  |  |  |
| 성능테스트 |  |  |  |
| 보안테스트 |  |  |  |
| 화면/UI테스트 |  |  |  |

## 4. 테스트 케이스 목록

| 테스트 ID | 유형 | 테스트명 | 대상 | 관련 REQ | 관련 AC | 관련 SEC/SR | 우선순위 | 상태 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UT-001 | Unit |  | PGM-001 | REQ-001-01 | AC-001-01 | SEC-001 / KISA-SD-2021 SR- | Must | Draft |
| UI-001-01 | UI |  | SCR-001 | REQ-001-01 | AC-001-01 | SEC-001 / KISA-SD-2021 SR- | Must | Draft |

### 4.1 상세 REQ별 테스트 매핑

> `check-trace`는 Gate 3에서 테스트케이스 문서 안의 상세 `REQ-NNN-NN` 매핑을 확인한다.
> 아래 표에는 요구사항정의서의 모든 상세 REQ를 빠짐없이 넣고, 테스트가 불필요하면 사유와 대체 검증을 명시한다.

| 상세 REQ-ID | 관련 AC-ID | UT-ID | IT-ID | UI-ID | PT-ID | 검증 방식 | 상태 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REQ-001-01 | AC-001-01 | UT-001 | IT-001 | UI-001-01 | 해당없음 | 자동 테스트 + UI 증적 | Planned |  |

## 5. 테스트 케이스 상세

### UT-001 테스트명

| 항목 | 내용 |
| --- | --- |
| 테스트 ID | UT-001 |
| 테스트 유형 | Unit / Integration / Performance / Security / Review |
| 테스트명 |  |
| 테스트 목적 |  |
| 테스트 대상 | PGM- / SCR- / DB- / IF- |
| 관련 요구사항 | REQ-001-01 |
| 관련 인수기준 | AC-001-01 |
| 관련 보안항목 | SEC- |
| 참조 표준 | KISA-SD-2021 SR- |
| 관련 비기능 요구사항 | NREQ- |
| 우선순위 | Must / Should / Could |

#### 5.0 시나리오

| 항목 | 내용 |
| --- | --- |
| Given |  |
| When |  |
| Then |  |

#### 5.1 사전 조건

| 번호 | 조건 |
| ---: | --- |
| 1 |  |

#### 5.2 테스트 데이터

| TERM-ID | 항목명 | 값 | 설명 | 보안 분류 |
| --- | --- | --- | --- | --- |
| TERM-001 |  |  |  | 일반 |

#### 5.3 테스트 절차

| 순서 | 수행 내용 | 기대 결과 |
| ---: | --- | --- |
| 1 |  |  |

#### 5.4 판정 기준

| 판정 | 기준 | 필수 증적 |
| --- | --- | --- |
| PASS | 기대 결과와 성공 기준을 모두 충족한다 | 실행 로그, 테스트 리포트, 화면 캡처, trace 중 해당 항목 |
| FAIL | 명령 실패, 기대 결과 불일치, 필수 증적 누락 중 하나 이상이 있다 | 실패 로그 또는 재현 증적 |
| Not Run | 테스트를 실행하지 못했다 | 미실행 사유, 영향 범위, 후속 조치 |
| Skipped | 승인된 사유로 이번 범위에서 제외했다 | 승인 근거 또는 적용 제외 사유 |

> Gate 3 테스트케이스의 상태는 계획/설계 상태를 표현한다. Gate 4의 실제 실행 결과는 `DOC-QA-G4-002_Test-Result_v0.1.md`에 기록하며, QA-003에서 이 문서를 기준으로 Pass/Fail/Not Run을 정리한다.

#### 5.5 자동화 정보

| 항목 | 내용 |
| --- | --- |
| 테스트 파일 |  |
| 테스트 함수/케이스명 |  |
| 실행 위치(cwd) |  |
| Windows 명령 |  |
| POSIX 명령 |  |
| 성공 기준 | exit code 0, 실패 0건, 기대 증적 생성 |
| 결과/증적 경로 |  |
| 실패/미실행 기록 | Fail / Not Run / Skipped 사유 |
| CI Job |  |

## 6. 성능 테스트 기준

| PT-ID | 관련 NREQ | 대상 | 지표 | 기준값 | 측정 방법 | 상태 |
| --- | --- | --- | --- | --- | --- | --- |
| PT-001 | NREQ- | PGM-/SCR- | 응답시간 / 처리량 / 동시 사용자 |  |  | Draft |

## 7. 보안 테스트 기준

| 테스트 ID | 관련 SEC | 참조 표준 | 테스트 내용 | 증적 |
| --- | --- | --- | --- | --- |
| UT-001 | SEC- | KISA-SD-2021 SR- |  |  |

## 8. 화면/UI 테스트 기준

화면/UI 테스트는 화면 하나를 크게 Pass 처리하지 않는다.
회원가입, 로그인, TODO처럼 사용 흐름이 있는 화면은 기본 화면, 오류 상태, 성공 상태, 다음 화면 전환을 별도 UI-ID로 분리한다.

| UI-ID | 관련 SCR | 기준 시안 | 관련 Contract | Viewport | 상태/시나리오 | 입력값 | 기대 화면 | 캡처 경로 | 비교 방식 | 상태 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UI-001-01 | SCR-001 | UIREF-001 | UICON-001 | Desktop 1280x720 | 회원가입 기본 화면 | 없음 | 이메일/비밀번호/비밀번호 확인/가입 버튼이 보이고 UICON-001의 필수 유지 요소를 따른다 | docs/artifacts/04-review/evidence/ui/UI-001-01_signup_default_desktop.png | Playwright screenshot / 시각 회귀 비교 / Contract diff | Draft |
| UI-001-02 | SCR-001 | UIREF-001 | UICON-001 | Desktop 1280x720 | 약한 비밀번호 오류 | password1! | 약한 비밀번호 오류 메시지가 보이고 가입이 차단된다 | docs/artifacts/04-review/evidence/ui/UI-001-02_signup_weak_password_desktop.png | Playwright screenshot / 시각 회귀 비교 / Contract diff | Draft |
| UI-001-03 | SCR-001 | UIREF-001 | UICON-001 | Desktop 1280x720 | 비밀번호 확인 불일치 | password / password2 | 비밀번호 확인 불일치 오류 메시지가 보인다 | docs/artifacts/04-review/evidence/ui/UI-001-03_signup_password_mismatch_desktop.png | Playwright screenshot / 시각 회귀 비교 / Contract diff | Draft |
| UI-001-04 | SCR-001 | UIREF-001 | UICON-001 | Desktop 1280x720 | 중복 이메일 오류 | 기존 이메일 | 중복 이메일 오류 메시지가 보인다 | docs/artifacts/04-review/evidence/ui/UI-001-04_signup_duplicate_email_desktop.png | Playwright screenshot / 시각 회귀 비교 / Contract diff | Draft |
| UI-001-05 | SCR-001 | UIREF-001 | UICON-001 | Desktop 1280x720 | 회원가입 성공 | 유효한 신규 계정 | 가입 완료 메시지와 로그인 안내가 보인다 | docs/artifacts/04-review/evidence/ui/UI-001-05_signup_success_desktop.png | Playwright screenshot / 시각 회귀 비교 / Contract diff | Draft |
| UI-001-06 | SCR-002 | UIREF-002 | UICON-002 | Desktop 1280x720 | 성공 후 로그인 연계 | 가입한 이메일 | 로그인 화면으로 이동했고 성공 메시지 또는 이메일 연계가 확인된다 | docs/artifacts/04-review/evidence/ui/UI-001-06_signup_to_login_desktop.png | Playwright screenshot / 시각 회귀 비교 / Contract diff | Draft |

> `관련 Contract`가 있는 행은 화면 모양만 보지 않는다. 필수 유지 요소, 허용된 차이, 금지된 차이를 함께 판정한다.

## 9. 변경이력

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 | YYYY-MM-DD | 최초 초안 작성 |  |  |  |

## 10. 검토 체크리스트

| 항목 | 확인 |
| --- | --- |
| 모든 테스트에 `UT`, `IT`, `PT` ID가 부여되었는가 |  |
| 요구사항정의서의 모든 상세 `REQ-NNN-NN`이 4.1 상세 REQ별 테스트 매핑 표에 포함되었는가 |  |
| 모든 테스트가 상세 `REQ-NNN-NN`, `AC-NNN-NN`, `NREQ`, `SEC`, `CR` 중 하나 이상과 연결되었는가 |  |
| 보안 테스트에 `SEC-ID`와 `SR-ID`가 연결되었는가 |  |
| 화면 테스트에 `UI-ID`, `SCR-ID`, 기준 시안, viewport, 캡처 경로가 연결되었는가 |  |
| 기준 시안의 UI Implementation Contract가 테스트 기대결과와 비교 방식에 반영되었는가 |  |
| 테스트 데이터가 프로젝트 단어사전과 연결되었는가 |  |
| PASS/FAIL 판정 기준이 명확한가 |  |
| 자동화 가능한 테스트에 파일/명령 정보가 작성되었는가 |  |
| 명령 기반 테스트에 실행 위치(cwd), OS별 명령, 성공 기준, 로그/증적 경로가 작성되었는가 |  |
