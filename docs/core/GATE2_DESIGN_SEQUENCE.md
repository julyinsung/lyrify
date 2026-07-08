# Gate 2 Design Sequence

> 상태: 초안 v0.1
> 목적: Gate 2 설계를 한 번에 뭉쳐 작성하지 않고, 효율적인 순서와 반복 갱신 지점에 따라 진행하기 위한 기준을 정의한다.

## 1. 핵심 원칙

Gate 2는 승인된 요구사항을 구현 가능한 설계와 테스트 입력으로 전개하는 단계다.

Gate 2는 산출물 목록을 채우는 작업이 아니라 설계 결정을 점진적으로 좁히는 작업이다.
따라서 SW 아키텍처, 화면, 기능, 프로그램/API, 데이터/DB, 보안, 개발표준을 한 번에 완성하려 하지 않는다.

SW 아키텍처 정의서는 Gate 2의 첫 산출물이자 마지막 검토판이다.
처음에는 설계 지도 역할을 하는 Draft로 시작하고, 상세 설계가 진행될 때마다 다시 보강한 뒤, Gate 3 진입 전 Baseline Candidate 또는 Baseline으로 정리한다.

## 2. 권장 순서

| 순서 | 단계 | 목적 | 주요 입력 | 주요 출력 |
| --- | --- | --- | --- | --- |
| G2-01 | Kickoff / 설계 범위 고정 | Gate 1 요구사항, AC, 미결 질문, 보류 항목을 확인한다 | 요구사항정의서, 추적표, Phase 0 산출물 | 설계 범위, 보류 항목, 질문, 이번 Gate 2 Run 범위 |
| G2-02 | SW Architecture Draft | 전체 구조와 주요 결정을 먼저 잡는다 | REQ/NREQ/AC, 기술 제약 | C1/C2, CNT 후보, ADR 후보, 보안/데이터/배포 경계, Pending |
| G2-02b | Deployment Infrastructure Draft | SW가 배포·운영될 인프라 경계와 미확정 질문을 드러낸다 | NREQ/SEC, 운영 제약, 인프라 담당자 입력 | L2/L3/L4/WAF/FW/WAS/DB/Storage/Monitoring 후보, 이중화, 포트/프로토콜, TBD 질문/영향 |
| G2-03 | Screen / User Flow | 사용자가 보는 화면과 상태 흐름을 확정한다 | REQ/AC, 화면 퍼블리싱 산출물, 기존 화면 | SCR, UIREF, 화면 상태, 메시지 위치, 사용자 흐름 |
| G2-04 | Function Spec | 화면과 요구사항을 기능 단위로 전개한다 | REQ/AC, SCR | FUNC, 기능 흐름, 예외 흐름 |
| G2-05 | Program Design / API Spec | 기능을 서버/클라이언트 책임과 구현 계약으로 내린다 | FUNC, SCR, SEC 후보 | PGM, 컴포넌트 책임, Interface Contract, Abstract Base Contract, Public Method Contract, API, DTO, 오류코드 |
| G2-06 | Data / DB Spec | 프로그램/API가 필요로 하는 데이터를 확정한다 | PGM, API, 화면 항목 | DB, TERM, WORD, DOMAIN, ERD/DBML, 제약조건 |
| G2-07 | Security Guide | 화면/API/DB 기준으로 보안 정책값을 확정한다 | SEC 후보, API, DB, 화면 메시지 | SEC별 정책값, 적용 위치, 오류 메시지, 검증 후보 |
| G2-08 | Development Standard | 구현자가 따라야 할 구조와 명령을 확정한다 | 아키텍처, PGM/API, 보안, 테스트 후보 | 패키지 구조, 레이어 규칙, DTO/Entity, 주석/로깅, 빌드/테스트 명령 |
| G2-09 | SW Architecture Baseline 보강 | 앞 설계 결정을 다시 아키텍처에 반영한다 | 상세 설계 전체 | CMP, FLOW, 품질속성, 상세 설계 링크, ADR 상태 |
| G2-10 | Design Review / Gate 3 승인 대기 | Gate 3로 넘길 수 있는지 검수한다 | 모든 Gate 2 산출물 | review Run, FIND/ISSUE/CR, Gate 3 승인 질문 |

## 3. SW 아키텍처 성숙도

| 성숙도 | 시점 | 최소 내용 | 검증 |
| --- | --- | --- | --- |
| Draft | Gate 2 시작 직후 | 시스템 목적, 주요 사용자, C1/C2, 주요 CNT, ADR 후보, Pending | `python vulcan.py check-architecture --level draft` |
| Baseline Candidate | 상세 설계 작성 후 | CMP, FLOW, 보안 아키텍처, 품질속성, 기술 스택 근거, 상세 설계 연결 초안, 배포·운영 인프라 영향 | `python vulcan.py check-architecture --level baseline` |
| Baseline | Gate 3 진입 전 | 상세 설계 문서 연결, 품질속성 검증 기준, ADR 상태, Gate 3 테스트 입력 | `python vulcan.py check-trace` |

아키텍처 문서의 Pending은 방치하지 않는다.
Gate 3 진입 전에는 닫거나, `RISK`, `ASM`, `Q`, `ISSUE`, `CR` 중 하나로 분류한다.

배포·운영 인프라 정보는 사용자가 제공하지 않으면 미확정일 수 있다.
이 경우 값을 꾸며서 채우지 않고 `DOC-ARCH-G2-002_Deployment-Infrastructure-Architecture_v0.1.md`에 `TBD`, 확인 질문, SW 영향, 확인 책임, 목표 시점을 남긴다.
health check, TLS 종료 위치, WAS/DB 이중화, 파일 저장소, 로그/백업/모니터링처럼 구현이나 QA에 영향을 주는 `TBD`는 Gate 3 또는 Impl 전 `RISK`, `ASM`, `Q`, `ISSUE`, `CR` 중 하나로 분류한다.

## 4. 교차 검토 지점

보안, 데이터, 개발표준은 마지막에 한 번만 검토하지 않는다.
다음 지점에서 교차 확인한다.

`product` profile에서는 Gate 2 초기에 `docs/core/PRODUCT_PROFILE_BASELINE.md`, `docs/core/SECURITY_BASELINE.md`, `docs/core/DATA_STANDARD_RULES.md`를 먼저 확인한다.
`audit` profile에서는 위 기준에 더해 `docs/core/REFERENCE_STANDARDS.md`, `docs/core/KISA_SECURITY_RULES.md`, `docs/seed-docs/reference-standards/`를 필요한 만큼 참조한다.
`poc` profile에서는 보안/데이터를 상세 제출 기준이 아니라 위험 식별과 제품화 전환 gap 중심으로 기록한다.

| 지점 | 확인 |
| --- | --- |
| 화면 설계 후 | 입력값, 메시지, 인증/권한 상태, UI Implementation Contract, UI 테스트 후보 |
| Program/API 설계 후 | API 오류코드, DTO 검증, 서비스 책임, SEC 적용 위치 |
| Data/DB 설계 후 | 용어/도메인, 개인정보/인증정보 분류, DB 제약조건 |
| Security Guide 작성 후 | 화면/API/DB/프로그램 설계가 보안 정책값과 모순되지 않는지 |
| Development Standard 작성 후 | 구현 구조, 테스트 명령, 보안 구현 규칙이 설계와 연결되는지 |
| Deployment Infrastructure 작성 후 | L4 health check, TLS 종료, WAS/DB 이중화, 파일 저장소, 로그/백업/모니터링이 SW 설계/보안/개발표준/QA에 미치는 영향 |

## 5. Run 분할 기준

작은 프로젝트는 하나의 Gate 2 Design Run으로 처리할 수 있다.
다만 다음 중 하나라도 해당하면 Gate 2를 여러 Run으로 나눈다.

- 화면이 3개 이상이거나 상태/시나리오가 많다.
- API/DB/보안 정책이 함께 바뀐다.
- SW 아키텍처의 Pending 또는 ADR 후보가 2개 이상이다.
- 데이터 표준, 개발표준, 보안 검토가 별도 집중 검토를 필요로 한다.

권장 Run 예:

```text
RUN-003 Gate2 Kickoff 및 Architecture Draft
RUN-004 화면/사용자 흐름 설계
RUN-005 기능/프로그램/API 설계
RUN-006 데이터/DB/용어 설계
RUN-007 배포·운영 인프라 영향 및 보안가이드 정리
RUN-008 개발표준 정리
RUN-009 SW Architecture Baseline 및 설계 검수
```

구현으로 넘어갈 프로그램 설계는 worker Run을 쪼갤 수 있을 만큼 구체적이어야 한다.
특히 `PGM-ID`, 컴포넌트 책임, Interface Contract, Abstract Base Contract, Public Method Contract, DTO/Entity/Data Contract, 오류/예외/메시지, 트랜잭션/보안/로깅, 테스트 연결을 남긴다.
구현 Run은 파일 개수나 시간만으로 나누지 않고, 닫힌 기능/프로그램 계약 단위로 나눈다. 10분 내외, 최대 15분 권장은 보조 기준이며, 중간 구현을 완료 처리하기 위한 기준이 아니다.

## 6. 금지사항

- Gate 2에서 구현 파일을 작성하지 않는다.
- Gate 2에서 실제 테스트 결과나 QA 증적을 완료로 선언하지 않는다.
- SW 아키텍처 Draft를 최종 승인본처럼 취급하지 않는다.
- 화면 퍼블리싱 산출물, Figma, 이미지 시안, 기존 화면 캡처를 `참고`라고만 두고 구현 기준을 모호하게 넘기지 않는다.
- 구현 기준 시안인데 UI Implementation Contract 없이 Gate 3 또는 구현으로 넘기지 않는다.
- 상세 설계에서 결정한 내용을 SW 아키텍처와 추적표에 되돌려 반영하지 않은 채 Gate 3로 넘기지 않는다.
- 사용자 승인 없이 Gate 3 테스트 설계로 넘어가지 않는다.

## 7. UI Baseline To Implementation Contract

화면 퍼블리싱 산출물 또는 외부 시안은 Gate 2에서 다음 중 하나로 분류한다.

| 유형 | 의미 | 후속 처리 |
| --- | --- | --- |
| Reference Only | 아이디어 참고용이며 구현자가 재해석할 수 있다 | 화면설계서에 참고 범위와 비목표를 기록한다 |
| Must Follow | 구현자가 구조, 레이아웃, 상태, 메시지 위치를 따라야 한다 | UI Implementation Contract를 작성하고 Gate 3/Impl/Gate 4에 전달한다 |
| Hybrid | 일부는 유지하고 일부는 변경 가능하다 | 필수 유지, 변경 허용, 변경 금지를 구분한다 |

UI Implementation Contract는 최소한 다음을 가진다.

- 기준 UIREF와 파일/URL
- 기준 CSS 또는 디자인 토큰
- 필수 유지 요소
- 변경 허용 항목과 근거
- 변경 금지 항목
- 구현 비교 방식
- 차이 발생 시 FIND/CR 판정 기준
