# 개발표준 검토 Skill

## 사용할 때

Gate 2에서 Gate 3로 넘어가기 전, 또는 Gate 4 구현 검수 시 사용한다.

구현 전에 개발표준정의서가 확정되었는지, build persona와 외부 worker가 일관된 방식으로 코딩할 수 있는 기준이 충분한지 검토한다.

## 필수 입력

- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/SECURITY_BASELINE.md`
- `docs/core/TECH_STACK_BASELINES.md`
- `docs/templates/DEVELOPMENT_STANDARD_TEMPLATE.md`
- 관련 개발표준정의서
- 관련 프로그램 설계서
- 관련 테스트케이스

## 절차

1. 개발표준정의서 상태가 Draft 또는 템플릿 플레이스홀더 상태인지 확인한다.
2. 언어, 런타임, 프레임워크, DB, 테스트 도구, 빌드/패키지 방식이 확정되었는지 확인한다.
3. 선택한 기술스택이 `TECH_STACK_BASELINES.md`의 어떤 섹션을 따르는지 확인한다.
4. Spring Boot/Spring Security/React/Next.js/Vue/FastAPI 등 선택 스택별 패키지 구조와 계층 책임이 구현자가 바로 따를 수 있을 만큼 구체적인지 확인한다.
   - Spring Boot라면 base package, MVC 계층, feature 우선 패키지 구조, JPA Entity/DTO 분리, transaction 기준, repository/query 기준이 명시되어야 한다.
   - `domain/{domainName}` 래퍼를 쓰는 경우 DDD 구조 선택 사유가 있어야 한다. 사유가 없으면 base package 바로 아래 `auth/`, `user/`, `{feature}/`, `security/`, `common/` 구조를 기준으로 보완을 요구한다.
5. DB 접근 기준에 JPA, query 방식, pagination, auditing, DB pool 기준이 있는지 확인한다.
   - Spring Boot라면 HikariCP 기본 사용 또는 대체 pool 선택 사유, 설정 위치, 검증 방법이 명시되어야 한다.
6. Lombok 사용 여부, 허용 annotation, Entity 금지 annotation이 있는지 확인한다.
7. 메시지 리소스, 예외 처리, 로그, 설정값, 외부 의존성 규칙이 있는지 확인한다.
   - 로깅은 SLF4J facade, Logback/Log4j2 선택 기준, Log4j 1.x 금지, logger 선언, 로그 레벨, MDC/requestId, 민감정보 로그 금지, `System.out`/`printStackTrace` 금지 기준이 있어야 한다.
8. 선택 스택별 동기/비동기 함수 선언, 트랜잭션 소유권, 외부 호출 정책, 환경 설정 규칙이 있는지 확인한다.
   - Python/FastAPI에서 동기 DB driver를 쓰면 blocking I/O를 `async def`에 임의 배치하지 않는 기준이 있어야 한다.
   - DB write 또는 복수 repository 조합이 있으면 Service/UseCase의 commit/rollback 또는 transaction boundary 소유 기준이 있어야 한다.
   - endpoint, DB URL, secret, feature flag는 environment/config contract로 분리되고 운영 코드 하드코딩 금지 또는 예외 기준이 있어야 한다.
9. 프로그램 설계서의 public method/event contract가 worker 구현에 충분한지 확인한다.
   - signature에는 선택 스택에 맞는 입력, 출력, 오류/예외 타입이 있어야 한다.
   - Frontend/API 연동이 있으면 상태 동기화, rollback/refetch, 사용자 오류 표시 위치가 프로그램 설계서 또는 화면 설계서와 연결되어야 한다.
10. 주석 컨벤션과 추적 ID 표기 규칙이 있는지 확인한다.
   - Java/Spring이라면 주요 클래스와 public 업무 메서드의 JavaDoc 기준, Controller/Service/Security Config 주석 기준, 실제 예시가 있어야 한다.
11. 글로벌 예외 매핑 기준이 있는지 확인한다.
   - Controller/Router마다 동일한 오류 응답 변환을 반복하지 않고, 선택 스택의 global exception handler, middleware, interceptor, filter 중 하나로 공통 오류 포맷을 매핑해야 한다.
12. 보안 구현 기준이 `SECURITY_BASELINE.md`의 관련 항목과 연결되어 있는지 확인한다.
13. 단위/통합/UI/성능 테스트 파일명, 함수명, 필수 검증 명령, 실행 시점, 결과 기록 위치, 증적 기준이 있는지 확인한다.
   - 명령은 실행 위치(cwd), Windows/POSIX 명령, 필수 여부, 성공 기준, 로그/증적 경로, `Not Run`/`Skipped` 처리 기준까지 있어야 한다.
   - Node 기반 frontend가 있으면 lockfile 존재 시 `npm ci` 우선 원칙과 `npm install` 허용 조건이 있어야 한다.
   - Spring Boot + frontend 통합 배포라면 backend 단독 검증과 `gradlew clean build` 같은 통합 배포 빌드 검증이 구분되어야 한다.
14. worker 작업 규칙이 Run 입력 계약 중심인지 확인한다.
   - 모든 문서를 일괄로 읽으라고 하지 않고 `target_contracts`, `source_documents.working`, `reference_on_demand`, `scope.writable` 기준으로 읽기 범위를 제한해야 한다.
   - worker self-check와 Orchestrator 최종 검증 책임이 구분되어야 한다.
15. 베이스라인과 다른 선택이 있으면 사유가 기록되어 있는지 확인한다.
16. 누락이 기존 설계 범위 안이면 `FIND`, 기술스택 또는 범위 변경이면 `CR`로 분류한다.

## 출력

다음을 반환한다.

- 개발표준정의서 상태
- 확정된 기술스택, 적용 베이스라인, 패키지 구조
- 누락된 코딩/주석/테스트/보안 기준
- public method signature, 상태 동기화/rollback, transaction owner, sync/async, config, global error mapping의 충족 여부
- build persona가 구현 가능한지 여부
- `FIND` 또는 `CR` 권고
