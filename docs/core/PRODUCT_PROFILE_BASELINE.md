# Product Profile Baseline

> 상태: 초안 v0.1
> 목적: `product` profile 프로젝트가 `init` 직후 설계 단계에서 바로 참조할 보안, 데이터, 릴리즈 기준선을 정의한다.

본 문서는 `vulcan.py init` 시 새 프로젝트의 `docs/core/`에 포함되는 실행 기준선이다.
긴 배경과 검토 노트는 원본 프레임워크의 `docs/reference/PRODUCT-PROFILE-BASELINE.md`를 참고하되, 프로젝트 안에서 에이전트가 우선 읽을 기준은 본 문서다.

## 1. 포지션

Product Profile은 PoC와 Audit 사이의 중간 레이어다.

| Profile | 목적 |
| --- | --- |
| `poc` | 아이디어, 기술, 화면, API 가설을 실험하고 결과를 기록 |
| `product` | 실제 사용자와 릴리즈가 있는 제품/업무 앱을 유지 가능한 수준으로 개발 |
| `audit` | 감리, 고객 검수, 공공/SI, 인수인계, 강한 QA 증적 대응 |

Product는 Audit의 축소판이 아니다.
제품 운영에 필요한 의사결정, 계약, 테스트, 릴리즈 근거를 남기는 profile이다.

## 2. 필수 관점

| 관점 | 기준 |
| --- | --- |
| Product Brief | 목표, 사용자, 핵심 시나리오, 비목표, 성공 기준 |
| Product Design | 아키텍처, 주요 컴포넌트, API/DB/UI 계약, ADR |
| Backlog/Release Scope | 이번 릴리즈 범위, 제외 범위, 다음 릴리즈 후보 |
| Test & Release Report | 핵심 회귀 테스트, 주요 화면/API 검증, known issue, release note |
| Traceability | 핵심 요구사항 -> 구현 -> 테스트 -> 릴리즈 근거 연결 |

Audit처럼 모든 ID를 촘촘하게 확장하지 않아도 되지만, 핵심 사용자 시나리오와 릴리즈 판단 근거는 끊기면 안 된다.

## 3. 보안 기준선

Product 보안은 KISA/공공 제출용 매핑을 기본 강제하지 않는다.
대신 일반 제품 개발에서 납득 가능한 보안 기준선을 둔다.

기본 기준:

- OWASP ASVS
- OWASP Top 10
- OWASP API Security Top 10
- CWE
- 프로젝트별 Security Baseline

Product에서 최소 검토할 보안 항목:

| 항목 | 확인 |
| --- | --- |
| 인증/인가 | 로그인, 세션, 토큰, 사용자별 접근통제 |
| 입력값 검증 | API body, query/path parameter, 화면 입력 |
| 오류/로그 | 내부 stack, SQL, token, 개인정보 노출 금지 |
| 데이터 보호 | 개인정보, 인증정보, 민감정보 저장/전송/마스킹 |
| Web/API 위험 | XSS, CSRF, CORS, SQL injection, command injection, SSRF 필요 여부 |
| 의존성 | 알려진 취약 버전, lockfile, upgrade 정책 |
| 파일/외부연계 | 업로드, 다운로드, webhook, 외부 URL 호출 제한 |

KISA, 공공, 고객사 보안 기준은 선택 참고로 둘 수 있다.
다만 Audit으로 전환하면 KISA/SR 또는 고객 기준과 `SEC-ID`, 테스트, 증적을 공식 매핑해야 한다.

## 4. 데이터/단어사전 기준선

Product에서도 단어사전은 필요하다.
목적은 감리 제출이 아니라 팀과 AI 에이전트가 같은 데이터 의미를 쓰게 하는 것이다.

기본 기준:

- 프로젝트 단어사전
- 화면/API/DB 항목명 매핑
- 데이터 도메인과 타입/길이/형식
- 개인정보/인증정보/민감정보/시스템정보 분류
- 필요 시 ISO/IEC 11179 metadata registry 개념 참고
- 필요 시 DAMA Dictionary/DMBOK 용어 참고

공공데이터 공통표준은 공공/SI/Audit에서는 우선 검토 대상이다.
Product에서는 조직 표준이 없거나 공공 데이터와 연계할 때 참고한다.

Product 단어사전의 최소 항목:

| 항목 | 설명 |
| --- | --- |
| TERM-ID | 프로젝트 용어 ID |
| 한글명/영문명 | 사람과 코드가 함께 이해할 수 있는 이름 |
| API 필드명 | 외부/프론트엔드 계약 |
| DB 컬럼명 | 저장소 계약 |
| 도메인 | 타입, 길이, 형식, 허용값 |
| 보안 분류 | 일반, 식별정보, 인증정보, 개인정보, 민감정보, 시스템정보 |
| 관련 ID | REQ, API, DB, PGM, SEC, TEST 중 필요한 연결 |

## 5. Gate 운영

| 단계 | Product 기준 |
| --- | --- |
| Phase 0 | 제품 목표, 사용자, 문제, 범위 후보 |
| Gate 1 | 핵심 요구사항/시나리오와 release scope |
| Gate 2 | Product Design, API/DB/UI 계약, 보안/데이터 기준선 |
| Gate 3 | 핵심 회귀 테스트와 릴리즈 판단 기준 |
| Impl | 기능 단위 worker/subagent 구현과 self-check |
| Gate 4 | 릴리즈 후보 검증, 주요 UI/API/E2E, known issue |
| Gate 5 | release note, backlog, risk, merge/release 판단 |

## 6. Audit 전환 Gap

Product에서 Audit으로 전환할 때 보강할 수 있는 항목:

- 공공데이터 공통표준 준용/변형/신규 사유
- KISA/SR 또는 고객사 보안 기준 공식 매핑
- 상세 요구사항추적표 확장
- SEC-ID별 테스트/증적 1:1 연결
- 화면 상태별 UI 증적 확대
- FIND/CR/ISSUE와 승인 이력 정규화

전환은 단순 profile 값 변경이 아니라 gap을 확인하고 필요한 산출물을 추가하는 작업이다.
