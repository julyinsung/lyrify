# Profile Gap Check

> 상태: 초안 v0.1
> 목적: `poc -> product -> audit` 전환을 무거운 승격 프로세스가 아니라 가벼운 gap 진단으로 다루기 위한 기준을 정의한다.

## 1. 원칙

Delivery Profile 변경은 프로젝트를 새로 만드는 일이 아니다.
같은 프로젝트 안에서 운영 강도와 산출물 기대치를 바꾸는 것이다.

따라서 profile 전환은 다음처럼 다룬다.

```text
현재 산출물 확인
-> 목표 profile 기준의 부족 항목 확인
-> gap을 backlog 또는 후속 작업으로 기록
-> 사용자가 원하면 profile 값을 변경
```

`profile-gap`은 전환을 차단하거나 자동 승격하지 않는다.
부족한 항목을 알고 넘어가게 하는 진단 도구다.

## 2. 왜 승격 프로세스를 크게 만들지 않는가

PoC의 목적은 빠른 확인이다.
PoC가 끝난 뒤 Product로 이어갈지 말지는 사용자의 제품 판단이며, 프레임워크가 복잡한 승인서나 별도 프로젝트 생성을 강제할 필요는 없다.

필요한 것은 다음 정도다.

- 지금 가진 PoC 결과가 Product 판단에 충분한가
- Product로 계속 개발하려면 어떤 문서와 계약을 보강해야 하는가
- Audit으로 가려면 어떤 공식 추적, 보안, 데이터, QA 증적이 부족한가

## 3. 권장 명령

```powershell
python vulcan.py profile-gap --to product
python vulcan.py profile-gap --to audit
python vulcan.py profile-gap --to product --json
```

`profile-gap`은 읽기 전용 진단이다.
`session.json`, `vulcan.config.json`, 산출물, 코드를 수정하지 않는다.

`profile-gap`은 두 층으로 결과를 나눈다.

- `ok` / `partial` / `missing`: 목표 profile에서 기대하는 문서나 동등 산출물이 있는지
- `content_issues` / `content_warnings`: 현재 Gate에서 판단에 필요한 핵심 내용이 비어 있거나 확인이 필요한지

예를 들어 Product profile을 새로 init하면 `docs/product/` 6종 문서는 모두 있으므로 문서 세트는 `ok`가 될 수 있다.
하지만 `PRODUCT_BRIEF.md`의 목표, 주요 사용자, 성공 기준이 `TBD`라면 `content_issues`가 남고 `status --check`는 Gate 완료를 차단한다.

## 4. PoC -> Product Gap

Product로 이어가기 전에 최소 확인할 항목은 다음이다.

| 항목 | 의미 |
| --- | --- |
| Product brief | 목표, 사용자, 핵심 시나리오, 비목표, 성공 기준이 제품 관점으로 정리되어 있는가 |
| Product architecture | 주요 컴포넌트, 런타임, 배포/운영 경계, 품질속성이 있는가 |
| ADR | 중요한 기술/구조 선택 이유가 남아 있는가 |
| Product contracts | API, DB, UI, 보안, 데이터 계약의 진입점이 있는가 |
| Regression/release report | 반복 실행할 회귀 테스트와 릴리즈 판단 근거가 있는가 |
| Traceability | 핵심 시나리오 -> 계약 -> 구현 -> 테스트 -> 릴리즈 근거가 끊기지 않는가 |

PoC 문서가 이 항목의 일부를 이미 설명하고 있으면 `partial`로 본다.
Product profile에서 계속 개발하려면 `partial` 항목을 Product 산출물 또는 기존 설계 산출물로 보강한다.

Product profile로 새 프로젝트를 시작하면 기본 Product 산출물은 `docs/product/` 아래에 생성된다.
PoC에서 Product로 전환하는 경우에는 `profile-gap --to product` 결과를 보고 필요한 문서부터 채운다.

## 5. Product -> Audit Gap

Audit으로 전환할 때는 다음 항목을 확인한다.

| 항목 | 의미 |
| --- | --- |
| Requirements and AC | 요구사항, 수용기준, 비기능 요구사항이 공식 ID로 분리되어 있는가 |
| Full design artifacts | 아키텍처, 기능, 프로그램, API, 화면, DB, 보안, 개발표준이 존재하는가 |
| Security mapping | KISA/SR, 고객/공공 기준, OWASP/CWE가 SEC-ID와 테스트에 연결되어 있는가 |
| Data standard mapping | 공공데이터 공통표준 준용/변형/신규 사유가 필요한 범위에 남아 있는가 |
| Test plan and QA evidence | UT/IT/UI/PT 계획과 Gate 4 결과/증적이 분리되어 있는가 |
| Traceability matrix | REQ/AC/FUNC/SCR/PGM/API/DB/SEC/UT/IT/UI가 추적표에서 연결되어 있는가 |
| Change/release records | FIND/CR/ISSUE, 릴리즈 승인, 미해결 리스크가 정리되어 있는가 |

Audit 전환은 Product보다 더 엄격하다.
다만 `profile-gap`은 여전히 진단이며, 실제 전환과 보강 범위는 사용자 승인 후 진행한다.

## 6. 결과 해석

`profile-gap` 항목은 다음 상태를 사용한다.

| 상태 | 의미 |
| --- | --- |
| `ok` | 목표 profile 기준의 직접 산출물 또는 동등한 공식 산출물이 있다 |
| `partial` | 현재 profile 산출물에 근거는 있으나 목표 profile 기준으로는 보강이 필요하다 |
| `missing` | 근거 산출물이 보이지 않는다 |
| `review` | 파일은 있으나 내용 판단이나 사용자 결정이 필요하다 |

`missing`이 있어도 profile 변경 자체가 금지되는 것은 아니다.
단, 변경 후에는 해당 항목을 backlog, Run, 또는 다음 Gate 작업으로 남겨야 한다.

`content_issues`는 현재 Gate 전환의 차단 후보로 본다.
`content_warnings`는 전환 가능할 수 있지만 Orchestrator가 사용자에게 남은 판단 항목으로 보고해야 한다.
