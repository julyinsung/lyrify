# API 정의서

```yaml
---
document_id: DOC-API-G2-001
title: API Specification
title_ko: API 정의서
project: 프로젝트명
gate: G2
status: Draft
version: v0.1
owner_role: API Designer
author: 작성자 또는 에이전트
reviewer: Technical Architect
approver: Approver
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
related_ids:
  - API-001
change_reason: 최초 초안 작성
---
```

## 1. 문서 목적

본 문서는 REST, GraphQL, 내부 HTTP API의 계약을 정의한다.

프로그램 설계서는 API와 처리 프로그램의 책임을 요약하고, 본 API 정의서는 클라이언트와 서버가 함께 따라야 하는 요청/응답 계약을 상세화한다.

## 2. 작성 기준

- API는 `API-001` 형식으로 부여한다.
- API는 하나 이상의 `REQ`, `AC`, `FUNC`, `PGM`, `SCR`, `SEC`와 연결한다.
- 요청/응답 필드는 프로젝트 단어사전의 `TERM-ID`와 가능한 한 연결한다.
- 인증, 권한, 세션, 입력검증, 오류 응답은 보안가이드의 `SEC-ID`를 따른다.
- API 응답 메시지는 개발표준정의서의 메시지 관리 기준을 따른다.
- 본 문서에 없는 API, 필드, 오류코드, 상태코드를 구현 단계에서 임의로 추가하지 않는다.
- API가 없는 프로젝트는 본 문서를 작성하지 않거나 `상태: N/A`로 두고, 프로그램 설계서에 `API 정의서: 해당없음`과 사유를 남긴다.
- 아래 표의 빈 행은 작성 위치를 보여주기 위한 자리일 뿐 실제 API가 있다는 뜻이 아니다. 실제 API가 확정되기 전에는 `API-001`, `/api/example`, `GET / POST` 같은 예시 값을 그대로 남기지 않는다.

## 3. API 목록

| API-ID | API명 | Method | Path | 관련 PGM | 관련 SCR | 인증 | 상태 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| API-001 |  |  |  | PGM- | SCR- | Y/N | Draft |

## 4. 공통 계약

| 항목 | 기준 |
| --- | --- |
| Base URL |  |
| 요청 Content-Type | application/json |
| 응답 Content-Type | application/json |
| 인증 방식 | Cookie Session / Bearer Token / 해당없음 |
| 권한 실패 | 401 / 403 |
| 공통 오류 응답 | `error.code`, `error.message`, `traceId` |
| 날짜/시간 형식 | ISO-8601 / HH:mm / 프로젝트 기준 |
| 필드명 규칙 | camelCase / snake_case |

## 5. API 상세

### API-001 API명

| 항목 | 내용 |
| --- | --- |
| API-ID | API-001 |
| Method |  |
| Path |  |
| 설명 |  |
| 관련 요구사항 | REQ- |
| 관련 인수기준 | AC- |
| 관련 기능 | FUNC- |
| 관련 프로그램 | PGM- |
| 관련 화면 | SCR- |
| 관련 보안가이드 | SEC- |
| 인증 필요 | Y/N |
| 권한 조건 |  |

#### 5.1 Request

| 위치 | TERM-ID | 필드명 | 타입 | 필수 | 검증 기준 | 예시 | 관련 SEC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Path / Query / Header / Cookie / Body | TERM- |  | string / number / boolean / array / object | Y/N |  |  | SEC- |

요청 예시:

```json
{}
```

#### 5.2 Response

| 상태코드 | TERM-ID | 필드명 | 타입 | 필수 | 설명 | 예시 | 보안 분류 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 200 | TERM- |  | string / number / boolean / array / object | Y/N |  |  | 일반 / 식별정보 / 인증정보 / 개인정보 |

응답 예시:

```json
{}
```

#### 5.3 Error

| 오류 ID | HTTP Status | error.code | 사용자 메시지 | 발생 조건 | 처리 기준 | 관련 AC/SEC |
| --- | ---: | --- | --- | --- | --- | --- |
| ERR-API-001 | 400 |  |  |  |  | AC- / SEC- |

오류 응답 예시:

```json
{
  "error": {
    "code": "ERR-API-001",
    "message": "요청을 처리할 수 없습니다."
  }
}
```

#### 5.4 처리 및 보안 기준

| 순서 | 처리 내용 | 관련 PGM | 관련 SEC/SR | 실패 처리 |
| ---: | --- | --- | --- | --- |
| 1 |  | PGM- | SEC- / KISA-SD-2021 SR- | ERR- |

#### 5.5 테스트 연결

| 테스트 ID | 테스트 유형 | 검증 내용 | 관련 AC/SEC |
| --- | --- | --- | --- |
| UT- | Unit |  | AC- / SEC- |
| IT- | Integration |  | AC- / SEC- |

## 6. 화면/API/DB 매핑

| API-ID | 화면 항목명 | API 필드명 | DB 컬럼명 | TERM-ID | 비고 |
| --- | --- | --- | --- | --- | --- |
| API-001 |  |  |  | TERM- |  |

## 7. 검토 체크리스트

| 항목 | 확인 |
| --- | --- |
| 모든 API에 `API-ID`가 부여되었는가 |  |
| API가 `REQ`, `AC`, `FUNC`, `PGM`, `SCR`과 연결되었는가 |  |
| 요청/응답 필드와 검증 기준이 작성되었는가 |  |
| 오류 응답과 상태코드가 작성되었는가 |  |
| 인증/권한/보안 기준이 `SEC-ID`와 연결되었는가 |  |
| 요청/응답 예시가 작성되었는가 |  |
| 테스트 ID가 연결되었는가 |  |

## 8. 변경이력

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 | YYYY-MM-DD | 최초 초안 작성 |  |  |  |
