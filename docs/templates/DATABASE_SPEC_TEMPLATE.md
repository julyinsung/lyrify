# DB명세서

```yaml
---
document_id: DOC-DATA-G2-002
title: Database Specification
title_ko: DB명세서
project: 프로젝트명
gate: G2
status: Draft
version: v0.1
owner_role: Data Architect
author: 작성자 또는 에이전트
reviewer: Technical Architect
approver: Approver
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
related_ids:
  - DB-001
change_reason: 최초 초안 작성
---
```

## 1. 문서 목적

본 문서는 프로젝트의 데이터 객체, 테이블, 컬럼, 키, 제약조건, 보안 분류, 데이터 표준 준용 여부를 정의한다.

DB명세서는 프로젝트 단어사전과 연결되어야 하며, 프로그램 설계서와 테스트케이스가 참조하는 데이터 기준이 된다.

## 2. 작성 기준

- 데이터 객체는 `DB-001` 형식으로 부여한다.
- 주요 테이블/컬렉션/엔티티는 하나 이상의 `REQ`, `FUNC`, `PGM`과 연결한다.
- 컬럼명과 데이터 타입은 프로젝트 단어사전의 `TERM`, `DOMAIN`을 우선 참조한다.
- 개인정보, 인증정보, 식별정보, 민감정보는 보안 분류와 `SEC` 연결을 작성한다.
- 공공데이터 공통표준에 없는 용어는 프로젝트 단어사전에 신규 등록한다.
- 논리/물리 ERD 원본은 DBML로 작성하고, 사람이 검토할 export 이미지는 별도 파일로 관리한다.
- 논리 ERD는 `docs/artifacts/02-design/data/erd/logical/logical-erd.dbml`에 둔다.
- 물리 ERD는 `docs/artifacts/02-design/data/erd/physical/physical-erd.dbml`에 둔다.
- PNG/SVG/PDF export는 `docs/artifacts/02-design/data/erd/exports/`에 둔다.

## 3. 데이터 객체 목록

| DB-ID | 논리명 | 물리명 | 유형 | 관련 REQ | 관련 FUNC | 관련 PGM | 상태 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DB-001 |  |  | Table / Collection / File | REQ- | FUNC- | PGM- | Draft |

## 4. ERD 산출물

| 구분 | 원본 DBML | 보기용 Export | 기준 | 상태 |
| --- | --- | --- | --- | --- |
| 논리 ERD | docs/artifacts/02-design/data/erd/logical/logical-erd.dbml | docs/artifacts/02-design/data/erd/exports/logical-erd.png | 엔티티, 주요 속성, 관계 | Draft |
| 물리 ERD | docs/artifacts/02-design/data/erd/physical/physical-erd.dbml | docs/artifacts/02-design/data/erd/exports/physical-erd.png | 테이블, 컬럼, PK/FK, 인덱스 | Draft |

## 5. 테이블 상세

### DB-001 논리명

| 항목 | 내용 |
| --- | --- |
| DB-ID | DB-001 |
| 논리명 |  |
| 물리명 |  |
| 설명 |  |
| 관련 요구사항 | REQ- |
| 관련 기능 | FUNC- |
| 관련 프로그램 | PGM- |
| 보안 분류 | 일반 / 식별정보 포함 / 개인정보 포함 / 인증정보 포함 / 민감정보 포함 |
| 관련 보안항목 | SEC- |

#### 5.1 컬럼 정의

| 순번 | TERM-ID | 논리명 | 물리명 | 도메인 | 데이터 타입 | 길이 | PK | FK | NN | 기본값 | 보안 분류 | 관련 SEC | 설명 |
| ---: | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | TERM-001 |  |  | DOMAIN-001 | VARCHAR |  | Y/N | Y/N | Y/N |  | 일반 | SEC- |  |

#### 5.2 키 및 제약조건

| 구분 | 이름 | 대상 컬럼 | 설명 | 비고 |
| --- | --- | --- | --- | --- |
| PK |  |  |  |  |
| FK |  |  |  |  |
| UK |  |  |  |  |
| CHECK |  |  |  |  |

#### 5.3 인덱스

| 인덱스명 | 컬럼 | 유형 | 목적 | 관련 NREQ/PT |
| --- | --- | --- | --- | --- |
|  |  | Unique / Normal / FullText |  | NREQ-/PT- |

#### 5.4 데이터 보안

| 컬럼 | 보안 분류 | 저장 보호 | 전송 보호 | 로그 출력 | 참조 표준 | 관련 SEC | 검증 방향 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 일반 / 식별정보 / 인증정보 / 개인정보 / 민감정보 |  |  |  | KISA-SD-2021 SR- | SEC- | UT-/IT- |

## 6. 테이블 관계

| 출발 DB-ID | 관계 | 대상 DB-ID | 관계 설명 | 비고 |
| --- | --- | --- | --- | --- |
| DB-001 | 1:N | DB-002 |  |  |

## 7. 데이터 표준 검토

| TERM-ID | 논리명 | 공공데이터 표준 용어 | 영문 약어 | 도메인 | 표준 준용 상태 | 등록/변형 사유 |
| --- | --- | --- | --- | --- | --- | --- |
| TERM-001 |  |  |  |  | 확인필요 |  |

## 8. 변경이력

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 | YYYY-MM-DD | 최초 초안 작성 |  |  |  |

## 9. 검토 체크리스트

| 항목 | 확인 |
| --- | --- |
| 모든 데이터 객체에 `DB-ID`가 부여되었는가 |  |
| 주요 컬럼이 프로젝트 단어사전의 `TERM`과 연결되었는가 |  |
| 공공데이터 공통표준 검토 결과가 기록되었는가 |  |
| 개인정보/인증정보/민감정보가 분류되었는가 |  |
| 보호 대상 컬럼이 `SEC`와 연결되었는가 |  |
| 프로그램 설계서에서 참조 가능한 수준으로 키/제약조건이 정의되었는가 |  |
| 논리/물리 ERD DBML 원본이 작성되었는가 |  |
| ERD export 이미지 또는 PDF가 사람이 검토 가능한 형태로 생성되었는가 |  |
| DB명세서의 테이블/컬럼/관계가 DBML과 일치하는가 |  |
