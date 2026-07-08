# 개발표준정의서

```yaml
---
document_id: DOC-DEV-G2-001
title: Development Standard
title_ko: 개발표준정의서
project: "{PROJECT_NAME}"
gate: G2
status: Draft
version: v0.1
owner_role: Technical Architect
author: "{AUTHOR}"
reviewer: "{REVIEWER}"
approver: "{APPROVER}"
created_at: "{YYYY-MM-DD}"
updated_at: "{YYYY-MM-DD}"
related_ids:
  - REQ-001
  - FUNC-001
  - PGM-001
  - UT-001
change_reason: 최초 초안 작성
---
```

## 1. 문서 목적

본 문서는 프로젝트의 개발 언어, 패키지 구조, 아키텍처 패턴, 코드 컨벤션, 주석 컨벤션, 빌드/실행/테스트 방법, 에이전트 작업 규칙을 정의한다.

에이전트와 개발자는 구현 전에 본 문서와 관련 요구사항/설계/테스트 산출물을 함께 확인해야 한다.

기술스택별 기본 규칙은 `docs/core/TECH_STACK_BASELINES.md`를 기준으로 한다. 본 문서는 해당 베이스라인을 프로젝트 상황에 맞게 구체화한 실행 기준이며, 구현 단계에서는 본 문서가 우선한다.

## 2. 적용 범위

| 항목 | 내용 |
| --- | --- |
| 적용 시스템 |  |
| 적용 모듈 |  |
| 적용 언어 |  |
| 적용 프레임워크 |  |
| 적용 기술스택 베이스라인 | 예: Spring Boot + Spring Security + React |
| 적용 테스트 도구 |  |
| 제외 범위 |  |

## 3. 기술 스택

| 구분 | 표준 | 버전/범위 | 선정 사유 | 비고 |
| --- | --- | --- | --- | --- |
| Language |  |  |  |  |
| Runtime |  |  |  |  |
| Web Framework |  |  |  |  |
| Database |  |  |  |  |
| ORM/Query |  |  |  |  |
| Test |  |  |  |  |
| Build/Package |  |  |  |  |
| Lint/Format |  |  |  |  |

적용 베이스라인:

| 영역 | 선택 | 참조 베이스라인 | 프로젝트 조정사항 |
| --- | --- | --- | --- |
| Backend |  | `TECH_STACK_BASELINES.md` §3 또는 §8 |  |
| Backend Security |  | `TECH_STACK_BASELINES.md` §4 |  |
| Frontend |  | `TECH_STACK_BASELINES.md` §5, §6 또는 §7 |  |
| Test/E2E |  | `TECH_STACK_BASELINES.md` 각 스택 테스트 규칙 |  |

Spring Boot를 사용하는 경우 다음 항목을 반드시 확정한다.

| 항목 | 프로젝트 기준 |
| --- | --- |
| Base Package | 예: `com.example.todo` |
| MVC 적용 방식 | 예: Controller -> Service -> Repository -> Entity |
| 패키지 구조 기준 | 예: feature 우선 `{feature}/...`, `domain` 래퍼 사용 시 사유 기록 |
| JPA 사용 여부 | 예: Spring Data JPA + QueryDSL |
| Entity/DTO 분리 | 예: Entity 직접 응답 금지, Response DTO 사용 |
| Transaction 기준 | 예: Service 계층에서만 `@Transactional` |
| Pagination/Sort 기준 | 예: page/size/sort 허용값과 최대 size |
| Auditing 기준 | 예: createdAt/updatedAt/createdBy/updatedBy |
| DB Pool 기준 | 예: HikariCP 기본, 대체 pool 사용 시 사유 기록 |
| Lombok 기준 | 예: 허용 annotation과 금지 annotation |
| Logging 기준 | 예: SLF4J + Logback, Log4j2 선택 시 사유 기록 |

스택별 실행 정책:

| 항목 | 적용 조건 | 프로젝트 기준 | 금지/주의 사항 | 검증 방법 |
| --- | --- | --- | --- | --- |
| 동기/비동기 함수 선언 | Python/FastAPI, Node, Java async, 외부 I/O 사용 시 | 예: 동기 DB driver는 동기 함수, 비동기 I/O library 사용 시에만 async/await | blocking I/O를 async context에 임의 배치 금지 | UT-/IT-/lint |
| 트랜잭션 소유권 | DB write 또는 복수 repository 조합 시 | 예: Service/UseCase가 commit/rollback 또는 `@Transactional` 경계를 소유 | Repository/Adapter의 자의적 commit/rollback 금지 | UT-/IT- |
| 외부 호출 정책 | API client, queue, file, third-party 호출 시 | timeout, retry, idempotency, fallback 기준 작성 | 무한 retry, 민감정보 로그 출력 금지 | UT-/IT-/E2E |
| 환경 설정 | endpoint, DB URL, secret, feature flag 사용 시 | `.env`, application config, secret manager 등 출처 작성 | endpoint/secret의 운영 코드 하드코딩 금지 | config test/build |

## 4. 아키텍처 및 패키지 구조

아키텍처 패턴:

```text
{예: Router -> Service -> Repository -> Database}
```

패키지 구조:

```text
{PROJECT_ROOT}/
  app/
    api/
    services/
    repositories/
    models/
    schemas/
    core/
    resources/
  tests/
    unit/
    integration/
  docs/
```

| 계층 | 책임 | 허용 의존성 | 금지 사항 |
| --- | --- | --- | --- |
| API/Controller | 요청/응답, 인증 확인, 입력 스키마 연결 | Service, Schema | DB 직접 접근 |
| Service | 업무 규칙, 트랜잭션 경계, 권한 판단 | Repository, Model | HTTP 객체 직접 의존 |
| Repository | 데이터 접근 | DB Session, Model | 업무 정책 판단 |
| Model/Entity | 데이터 구조 |  | 외부 API 호출 |
| Schema/DTO | 입출력 데이터 검증 |  | 업무 로직 포함 |

Spring Boot MVC/JPA 패키지 구조 예:

```text
src/main/java/{basePackage}/
  {ApplicationName}Application.java
  config/
  common/
    error/
    message/
    response/
  security/
  auth/
    controller/
    service/
    dto/
  user/
    entity/
    repository/
    service/
    dto/
  {featureName}/
    controller/
    service/
    dto/
    entity/
    repository/
    mapper/
src/main/resources/
  messages_ko.properties
  application.yml
src/test/java/{basePackage}/
  auth/
  user/
  {featureName}/
```

패키지 구조 선택 기준:

- `security/`: Spring Security 설정, 필터, 인증 principal, 보안 공통 컴포넌트
- `auth/`: 로그인, 회원가입, 토큰 발급, 로그아웃 등 인증 기능
- `user/`: 사용자 Entity, Repository, 사용자 상태/조회 도메인
- `{featureName}/`: TODO, 주문, 게시글처럼 업무 기능 단위 패키지
- `domain/{domainName}/...`: DDD 구조를 명시적으로 선택한 경우에만 사용하며 선택 사유를 기록

JPA 기준:

| 항목 | 규칙 | 예외 |
| --- | --- | --- |
| Entity 응답 노출 | 금지, Response DTO로 변환 | 내부 배치/테스트 전용은 사유 기록 |
| Fetch 전략 | 기본 LAZY, 필요한 조회는 fetch join/EntityGraph/projection 사용 |  |
| Cascade/orphanRemoval | 생명주기 종속 시에만 사용 | 사유 기록 |
| Query 방식 | Spring Data JPA, JPQL, QueryDSL, native query 선택 기준 명시 | native query는 DB 종속성 기록 |
| 트랜잭션 | Service 계층에서 관리 | Repository 직접 트랜잭션은 사유 기록 |
| Auditing | 생성/수정 일시와 사용자 기준 명시 |  |
| DB Pool | HikariCP 기본 또는 대체 pool 선택 사유와 설정 위치 명시 | 대체 pool은 검증 방법 기록 |

Lombok 기준:

| 항목 | 규칙 |
| --- | --- |
| 사용 여부 |  |
| 허용 annotation | 예: `@Getter`, `@RequiredArgsConstructor`, `@Builder`, `@NoArgsConstructor(access = AccessLevel.PROTECTED)` |
| Entity 금지 annotation | 예: `@Data`, 무분별한 `@Setter`, 양방향 연관관계가 있는 `@ToString`, 전체 필드 기반 `@EqualsAndHashCode` |
| DTO 사용 기준 | 예: 불변성, validation, 직렬화 기준을 해치지 않는 범위 |
| 예외/조정 사유 |  |

## 5. 코드 컨벤션

| 항목 | 규칙 | 예외 |
| --- | --- | --- |
| 네이밍 |  |  |
| 함수/메서드 크기 |  |  |
| 모듈 분리 |  |  |
| 예외 처리 |  |  |
| 로그 |  |  |
| 설정값 |  |  |
| 외부 의존성 |  |  |
| DB Pool | 예: HikariCP 기본값, pool size/timeouts 설정 위치 |  |
| Lombok | 예: 허용/금지 annotation, Entity 사용 제한 |  |
| Logger | 예: SLF4J facade + Logback, Log4j2 선택 시 사유 |  |

언어/프레임워크별 상세 기준:

| 스택 | 적용 규칙 | 예외/조정 사유 |
| --- | --- | --- |
| Spring Boot |  |  |
| Spring Security |  |  |
| React/Next.js/Vue |  |  |
| Python/FastAPI |  |  |

## 6. 주석 컨벤션

기본 원칙:

- 코드가 그대로 설명하는 내용은 주석으로 반복하지 않는다.
- 요구사항, 보안 기준, 성능 제약, 추적 ID, 복잡한 의사결정은 주석 또는 docstring에 남길 수 있다.
- 임시 우회 처리는 `ISSUE-ID` 또는 `DEC-ID`와 함께 남긴다.
- Java/Spring의 Controller, Service, Security Config, 핵심 Component 클래스에는 책임과 관련 ID를 JavaDoc으로 남긴다.
- public 메서드 중 API/업무 규칙/트랜잭션/권한 판단을 포함하는 메서드는 JavaDoc으로 입력, 출력, 예외, 관련 ID를 남긴다.
- 단순 getter/setter, 단순 CRUD 위임, repository 기본 메서드에는 주석을 쓰지 않는다.

추적 ID 표기 예:

```text
REQ: REQ-001
PGM: PGM-001
SEC: SEC-001
TEST: UT-001
```

스택별 주석 기준:

| 스택 | 기준 |
| --- | --- |
| Java/Spring | 보안 판단, 트랜잭션 경계, 복잡한 도메인 규칙에는 관련 `REQ/SEC/PGM`을 남길 수 있다. 단순 getter/setter, 단순 CRUD 위임에는 주석을 쓰지 않는다. |
| TypeScript/React/Next/Vue | 복잡한 상태 전이, 권한 가드, API 오류 변환, 접근성 예외에는 관련 `REQ/SCR/SEC`을 남길 수 있다. JSX/Template이 그대로 설명하는 내용은 주석으로 반복하지 않는다. |
| Python/FastAPI | 보안 dependency, 권한 판단, repository transaction, 복잡한 validation에는 관련 `REQ/SEC/PGM`을 남길 수 있다. |

Java/Spring 클래스 JavaDoc 예:

```java
/**
 * TODO 항목 생성, 조회, 완료 처리 업무 규칙을 담당한다.
 *
 * 관련 ID: FUNC-003, PGM-003, SEC-004
 * 주요 규칙: 로그인한 사용자는 본인 TODO만 조회하거나 변경할 수 있다.
 */
@Service
@RequiredArgsConstructor
public class TodoService {
}
```

Java/Spring 메서드 JavaDoc 예:

```java
/**
 * 로그인 사용자의 TODO를 생성한다.
 *
 * 관련 ID: REQ-003, PGM-003, UT-004
 * 트랜잭션: TODO 저장과 감사 필드 생성을 하나의 쓰기 트랜잭션으로 처리한다.
 *
 * @param userId 인증된 사용자 ID
 * @param request TODO 생성 요청 DTO
 * @return 생성된 TODO 응답 DTO
 */
@Transactional
public TodoResponse createTodo(Long userId, TodoCreateRequest request) {
    // SEC-004: 요청 userId가 인증 principal에서 온 값인지 controller에서 보장한다.
}
```

## 6.1 로깅 컨벤션

| 항목 | 규칙 |
| --- | --- |
| 로깅 API | 예: SLF4J facade |
| 구현체 | 예: Spring Boot 기본 Logback. Log4j2 선택 시 사유와 의존성 충돌 검증 방법 기록 |
| 금지 구현체 | 예: Log4j 1.x |
| Logger 선언 | 예: 클래스별 `private static final Logger` 또는 승인된 Lombok `@Slf4j` |
| 금지 API | 예: 운영 코드에서 `System.out.println`, `printStackTrace` 금지 |
| 로그 레벨 | ERROR/WARN/INFO/DEBUG/TRACE 사용 기준 작성 |
| 민감정보 | 비밀번호, 토큰, 인증 헤더, 세션 식별자, 개인정보 로그 출력 금지 |
| 요청 추적 | requestId/correlationId를 사용할 경우 MDC 생성/전파/삭제 위치 작성 |
| 예외 로그 | 사용자 노출 메시지와 내부 원인 분리, stack trace 노출 금지 |

Logger 예:

```java
private static final Logger log = LoggerFactory.getLogger(AuthService.class);

public void logout(Long userId) {
    log.info("User logout completed. userId={}", userId);
}
```

민감정보 로그 금지 예:

```java
// 금지: 토큰과 비밀번호가 로그에 남는다.
log.debug("login token={}, password={}", token, rawPassword);
```

## 7. API 및 오류 응답 규칙

성공 응답 표준:

```json
{
  "data": {},
  "message": "OK"
}
```

오류 응답 표준:

```json
{
  "error": {
    "code": "ERR-001",
    "message": "요청을 처리할 수 없습니다."
  }
}
```

| 오류 코드 | 의미 | HTTP 상태 | 관련 보안 기준 |
| --- | --- | ---: | --- |
| ERR-001 |  |  |  |

글로벌 예외 매핑 기준:

- Controller/Router마다 동일한 `try/catch`, `try-except` 응답 변환을 반복하지 않고, 선택 스택의 global exception handler, middleware, interceptor, filter 중 하나로 공통 오류 포맷을 매핑한다.
- validation, authentication, authorization, not found, conflict, system error는 공통 오류 코드와 HTTP 상태를 가진다.
- 사용자 노출 메시지와 내부 원인/stack trace는 분리한다.

## 8. 메시지 관리 규칙

기본 원칙:

- 사용자에게 노출되는 메시지는 코드에 직접 하드코딩하지 않는다.
- 사용자 노출 메시지는 메시지 리소스 파일에서 관리한다.
- API 응답은 메시지 코드와 메시지 본문을 함께 반환한다.
- 테스트는 원칙적으로 메시지 본문보다 메시지 코드를 검증한다.
- 인증/권한/보안 오류 메시지는 계정 존재 여부, 내부 구조, 권한 판단 상세를 노출하지 않는다.
- 문구 변경은 코드 변경 없이 메시지 리소스 수정으로 처리할 수 있어야 한다.

메시지 리소스 예:

```text
app/resources/messages.ko.yml
app/resources/messages.en.yml
```

메시지 코드 예:

```yaml
MSG-001: 정상 처리되었습니다.
ERR-001: 요청을 처리할 수 없습니다.
```

| 구분 | 하드코딩 허용 여부 | 관리 방식 | 비고 |
| --- | --- | --- | --- |
| 사용자 오류 메시지 | 금지 | 메시지 리소스 | API `error.message` |
| 사용자 성공/안내 메시지 | 금지 | 메시지 리소스 | API `message` |
| 입력값 검증 메시지 | 금지 | 메시지 리소스 | Validation 응답 |
| 보안 관련 메시지 | 금지 | 메시지 리소스 | 노출 정보 최소화 |
| 로그 내부 메시지 | 허용 | 코드 또는 상수 | 민감정보 출력 금지 |
| 테스트 설명 문자열 | 허용 | 테스트 코드 | 메시지 본문 검증 지양 |
| 개발자 전용 assertion | 허용 | 코드 | 사용자 노출 금지 |

## 9. DB 접근 및 데이터 표준 규칙

- DB 객체와 컬럼은 DB명세서의 `DB-ID`와 연결한다.
- 용어/단어/도메인은 프로젝트 단어사전과 공공데이터 공통표준 검토 상태를 따른다.
- 개인정보 또는 중요정보는 저장/전송/로그 출력 전에 보안항목을 확인한다.

## 10. 보안 구현 규칙

| 보안 영역 | 구현 규칙 | 참조 기준 | 검증 테스트 |
| --- | --- | --- | --- |
| 입력값 검증 |  | KISA-SD-2021 SR1-1, SR1-9 |  |
| 인증 |  | KISA-SD-2021 SR2-1 |  |
| 권한 |  | KISA-SD-2021 SR2-4 |  |
| 비밀번호/암호 |  | KISA-SD-2021 SR2-3, SR2-6, SR2-7 |  |
| 중요정보 전송 |  | KISA-SD-2021 SR2-8 |  |
| 예외처리 |  | KISA-SD-2021 SR3-1 |  |
| 세션통제 |  | KISA-SD-2021 SR4-1 |  |

## 11. 테스트 컨벤션

| 항목 | 규칙 |
| --- | --- |
| 테스트 파일명 |  |
| 테스트 함수명 |  |
| 단위테스트 기준 |  |
| 통합테스트 기준 |  |
| 성능테스트 기준 |  |
| 테스트 데이터 |  |
| 테스트 증적 |  |

테스트 설명 규칙:

- 테스트 메서드명은 `UT/IT/UI/PT` ID를 포함한다.
- 각 테스트는 `@DisplayName`, Given/When/Then 주석, 또는 테스트 상단 설명으로 입력값, 기대값, 확인한 출력/상태를 드러낸다.
- 감리 또는 인수 증적으로 쓰는 테스트는 코드만 보고도 무엇을 검증했는지 알 수 있어야 한다.
- 단순 helper 테스트를 제외하고, 여러 시나리오를 한 테스트에 섞으면 실패 원인과 증적 매핑이 어려우므로 시나리오 단위로 분리한다.

테스트 함수명 예:

```text
test_UT_001_signup_success()
test_IT_001_signup_then_login()
```

## 12. 빌드, 실행, 테스트 명령

구현 및 QA 단계에서 실행해야 하는 명령을 정의한다. 에이전트마다 명령 해석이 달라지지 않도록 실행 위치(cwd), OS별 명령, 필수 여부, 성공 기준, 결과 기록 위치, 로그/증적 경로를 함께 기록한다.

| 목적 | 실행 위치(cwd) | Windows 명령 | POSIX 명령 | 필수 여부 | 실행 시점 | 성공 기준 | 결과 기록 위치 | 로그/증적 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 의존성 설치 |  |  |  | 필수/선택 | 최초 구현 또는 환경 갱신 |  | Run |  |  |
| 개발 서버 실행 |  |  |  | 선택 | 화면 확인 또는 수동 QA |  | Run / Test Result |  |  |
| 단위 테스트 |  |  |  | 필수 | Build Wave 완료 시, Gate 4 전 | exit code 0, 실패 0건 | Run / Test Result |  |  |
| 통합 테스트 |  |  |  | 필수/선택 | Gate 4 전 또는 영향 범위 검증 | exit code 0, 실패 0건 | Run / Test Result |  |  |
| E2E/UI 테스트 |  |  |  | 필수/선택 | 화면 기능 구현 후, Gate 4 | exit code 0, 기대 화면 증적 생성 | Run / Test Result / UI Evidence |  |  |
| 정적 검사 |  |  |  | 필수/선택 | Build Wave 완료 시, Gate 4 전 | exit code 0, 오류 0건 | Run |  |  |
| 빌드 |  |  |  | 필수/선택 | Gate 4 전, 릴리즈 후보 전 | exit code 0, 배포 산출물 생성 | Run / Test Result |  |  |
| 포맷 |  |  |  | 선택 | 구현 중 또는 커밋 전 | exit code 0 또는 변경 없음 | Run |  |  |

기술스택별 명령 예:

| 스택 | 단위 테스트 | 정적 검사 | 빌드 | 비고 |
| --- | --- | --- | --- | --- |
| Spring Boot/Gradle | `./gradlew test` | `./gradlew check` | `./gradlew build` | Windows에서는 `.\gradlew.bat test` 형식 사용 가능 |
| Spring Boot/Maven | `./mvnw test` | `./mvnw verify` | `./mvnw package` | Windows에서는 `.\mvnw.cmd test` 형식 사용 가능 |
| React/Next.js | `npm test` | `npm run lint` | `npm run build` | 프로젝트 스크립트명에 맞게 조정 |
| Vue.js | `npm run test:unit` | `npm run lint` | `npm run build` | Vitest/ESLint 기준 |
| Python/FastAPI | `pytest` | `ruff check .` | 해당 시 작성 | 프로젝트 도구에 맞게 조정 |

Spring Boot + Vue 통합 배포 예:

| 목적 | 실행 위치(cwd) | Windows 명령 | POSIX 명령 | 필수 여부 | 실행 시점 | 성공 기준 | 결과 기록 위치 | 로그/증적 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Backend 테스트 | repository root | `.\gradlew.bat test` | `./gradlew test` | 필수 | Build Wave 완료 시 | exit code 0, 테스트 실패 0건 | Run / Test Result | `build/reports/tests/test/` | 검증 기준 명령은 `gradlew test` |
| Backend 정적검사/빌드 | repository root | `.\gradlew.bat check build` | `./gradlew check build` | 필수 | Gate 4 전 | exit code 0, check/build 성공 | Run / Test Result | `build/reports/` | Vue 통합 전 backend 기준 |
| Frontend 의존성 설치 | `frontend/` | `npm ci` 또는 `npm install` | `npm ci` 또는 `npm install` | 최초 1회 | 구현 시작 또는 환경 갱신 | lockfile 기준 설치 성공 | Run | npm output | `package-lock.json`이 있으면 `npm ci` 우선 |
| Frontend 단위 테스트 | `frontend/` | `npm run test:unit` | `npm run test:unit` | 필수 | UI 구현 후 | exit code 0, 실패 0건 | Run / Test Result | test report | Vitest |
| Frontend 정적검사 | `frontend/` | `npm run lint` | `npm run lint` | 필수 | UI 구현 후 | exit code 0, 오류 0건 | Run | lint output | ESLint |
| Frontend 빌드 | `frontend/` | `npm run build` | `npm run build` | 필수 | 배포 패키지 전 | exit code 0, `dist/` 생성 | Run | build output | 정적 파일 생성 |
| 통합 배포 빌드 | repository root | `.\gradlew.bat clean build` | `./gradlew clean build` | 필수 | 릴리즈 후보 전 | exit code 0, frontend 산출물이 backend static 또는 Gradle copy task에 포함 | Run / Test Result | `build/libs/`, static/copy task 결과 | 단일 배포 패키지 기준 |
| Playwright 설치 확인 | repository root 또는 `frontend/` | `npx playwright --version`; 미설치 시 `npm install -D @playwright/test` 후 `npx playwright install` | `npx playwright --version`; 미설치 시 `npm install -D @playwright/test` 후 `npx playwright install` | 화면 QA 필수 | Gate 4 화면 증적 전 | Playwright 실행 가능, 브라우저 설치 완료 | Run / Test Result | npm/playwright output | CDP 캡처로 대체 금지 |
| E2E/UI 테스트 | repository root 또는 `frontend/` | `npx playwright test` | `npx playwright test` | 화면이 있으면 필수 | Gate 4 화면 증적 | exit code 0, 상태별 screenshot/video/trace 생성 | UI Evidence / Test Result | `docs/artifacts/04-review/evidence/ui/` | Gate 3에서 UI-ID별 확정. CDP/수동 캡처만으로 Pass 금지 |

명령 실행 기록 기준:

- 실행한 모든 필수 명령은 실행 위치(cwd), 실제 명령, OS, exit code, 결과, 요약, 로그/증적 경로를 기록한다.
- `Pass`는 exit code와 성공 기준, 필수 로그/증적이 모두 충족될 때만 기록한다.
- 실행하지 못한 필수 명령은 `Not Run`으로 기록하고 사유, 영향 범위, 후속 조치를 남긴다.
- 프로젝트 범위상 적용하지 않는 명령은 승인 근거와 함께 `Skipped`로 기록한다.
- 개발표준정의서에서 필수로 지정한 명령은 Gate 4 테스트결과서의 실행 검증 표에 모두 반영한다.
- 화면 QA는 Playwright 설치 확인과 `npx playwright test` 실행 결과를 필수로 기록한다. CDP, 브라우저 수동 캡처, 런타임 Preview 캡처는 보조 관찰로만 기록할 수 있고 UI Pass 증거로 사용하지 않는다.

## 13. 에이전트 작업 규칙

에이전트는 다음 순서를 따른다.

1. Run 입력 계약의 `target_contracts`, `source_documents.working`, `scope.writable`을 먼저 확인한다.
2. 구현 대상의 `REQ/FUNC/PGM/SCR/API/DB/SEC/UT/IT/UI/PT` ID를 확인한다.
3. `reference_on_demand` 문서는 대상 ID와 직접 충돌하거나 세부 기준이 필요할 때만 읽는다.
4. 사용자가 선택한 기술스택에 맞는 `docs/core/TECH_STACK_BASELINES.md` 섹션과 본 개발표준정의서의 패키지 구조, 코드 컨벤션을 따른다.
5. 프로그램 설계서의 public method/event, DTO, error, transaction, config contract를 우선 구현한다.
6. 문서에 없는 기능, API, DB 컬럼, 테스트를 임의로 추가하지 않는다.
7. 필요한 변경이 있으면 먼저 `ISSUE` 또는 `CR` 후보로 기록한다.
8. 사용자 노출 메시지를 코드에 직접 하드코딩하지 않고 메시지 리소스를 사용한다.
9. worker는 자신의 self-check 명령과 결과를 Run에 남기고, Orchestrator가 최종 테스트결과서와 추적표 반영을 재검증한다.

## 14. 변경이력

| 버전 | 일자 | 변경내용 | 작성자 | 검토자 | 승인자 |
| --- | --- | --- | --- | --- | --- |
| v0.1 | {YYYY-MM-DD} | 최초 초안 작성 |  |  |  |
