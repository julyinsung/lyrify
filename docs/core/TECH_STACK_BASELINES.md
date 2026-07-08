# 기술스택 베이스라인

> 상태: 초안 v0.1
> 목적: 사용자가 개발 언어와 프레임워크를 선택했을 때, Gate 2 개발표준정의서가 참조해야 할 기본 코딩 규칙, 주석 규칙, 테스트 규칙을 정의한다.

## 1. 원칙

기술스택 베이스라인은 개발표준정의서의 출발점이다.

Orchestrator와 design/development-review persona는 Gate 2에서 다음 순서로 개발표준을 확정한다.

1. 사용자가 원하는 언어, 프레임워크, 배포 형태를 확인한다.
2. 본 문서에서 해당 스택의 베이스라인을 선택한다.
3. 프로젝트 특성에 맞게 패키지 구조, 메시지 리소스, 테스트 명령, 보안 구현 규칙을 조정한다.
4. 조정 결과를 `DOC-DEV-G2-001_Development-Standard_v0.1.md`에 명시한다.
5. 구현 단계에서는 개발표준정의서가 본 문서보다 우선한다.

베이스라인은 에이전트가 매번 임의로 컨벤션을 만들지 않게 하는 기본값이다. 프로젝트에서 다른 규칙을 선택할 수 있지만, 그 경우 개발표준정의서에 선택 사유를 남긴다.

## 2. 공통 규칙

모든 스택에 공통으로 적용한다.

| 구분 | 기준 |
| --- | --- |
| 추적성 | 주요 구현 파일, 테스트, API, 화면, DB 객체는 관련 `REQ/AC/FUNC/SCR/PGM/API/DB/SEC/UT/IT`와 연결한다. |
| 메시지 | 사용자 노출 메시지는 코드에 직접 하드코딩하지 않고 메시지 리소스 또는 i18n 리소스로 관리한다. |
| 설정 | 환경별 값, 비밀값, URL, 토큰, 암호키는 코드에 하드코딩하지 않는다. |
| 보안 | `SECURITY_BASELINE.md`, `KISA_SECURITY_RULES.md`, 프로젝트 보안가이드의 기준을 따른다. |
| 테스트 | 단위테스트와 통합테스트의 경계를 개발표준정의서에 명시한다. |
| 주석 | 코드가 그대로 설명하는 내용은 주석으로 반복하지 않고, 추적 ID, 보안 판단, 복잡한 의사결정, 예외 사유를 남긴다. |
| 예외 | 예외는 삼키지 않고 공통 오류 응답 또는 표준 오류 처리 흐름으로 전환한다. |
| 로그 | 개인정보, 인증정보, 토큰, 비밀번호, 세션 식별자, 내부 상세 오류를 로그에 남기지 않는다. |

## 3. Backend: Spring Boot

### 3.1 패키지명 규칙

Spring Boot 프로젝트는 조직/프로젝트/애플리케이션 성격을 반영한 base package를 먼저 확정한다.

권장 형식:

```text
{기관또는회사}.{프로젝트}.{애플리케이션}
```

예:

```text
kr.go.example.portal
com.example.todo
com.company.product.admin
```

규칙:

- 모두 소문자를 사용한다.
- 하이픈은 사용하지 않는다.
- 업무 도메인 이름은 package depth를 과도하게 늘리지 않는다.
- `controller`, `service`, `repository`, `entity`, `dto` 같은 계층명은 base package 아래에서 일관되게 사용한다.
- `domain` 같은 포괄 래퍼 패키지는 기본값으로 두지 않는다. DDD 계층 분리가 명확한 경우에만 선택 사유를 개발표준정의서에 남긴다.
- 멀티 모듈 프로젝트는 모듈명과 base package 관계를 개발표준정의서에 명시한다.

### 3.2 MVC + Layered Architecture

Spring Boot 기본 구조는 MVC 패턴과 계층형 아키텍처를 함께 사용한다.

- MVC의 Controller는 HTTP 요청/응답과 View/API 경계만 담당한다.
- Service는 업무 규칙, 트랜잭션, 권한 판단을 담당한다.
- Repository는 데이터 접근만 담당한다.
- Entity는 JPA 영속 모델이며 API 응답으로 직접 노출하지 않는다.
- DTO는 API 입출력 계약과 validation을 담당한다.

권장 구조:

```text
src/main/java/{basePackage}/
  {ApplicationName}Application.java
  config/
  common/
    error/
    message/
    response/
    audit/
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
    exception/
src/main/resources/
  messages.properties
  messages_ko.properties
  application.yml
src/test/java/{basePackage}/
  auth/
  user/
  {featureName}/
```

| 계층 | 책임 | 금지 사항 |
| --- | --- | --- |
| Controller | 요청/응답, 인증 principal 연결, 입력 DTO 검증 | Entity 직접 반환, 업무 로직 작성 |
| Service | 업무 규칙, 트랜잭션, 권한 판단, 도메인 조합 | HTTP 요청 객체 직접 의존 |
| Repository | 데이터 접근 | 업무 규칙 판단 |
| Entity | 영속 모델과 도메인 불변조건 | API 응답 모델로 직접 노출 |
| DTO | API 입출력, validation annotation | DB 접근, 복잡한 업무 로직 |
| Mapper | Entity/DTO 변환 | 트랜잭션 처리 |

의존 방향:

```text
Controller -> Service -> Repository -> Entity
Controller -> DTO
Service -> DTO/Entity/Repository
Repository -> Entity
```

금지 방향:

```text
Repository -> Service
Repository -> Controller
Entity -> Controller/Service
DTO -> Repository
```

### 3.3 Package by Feature 우선

기본값은 `{featureName}/controller|service|repository|entity|dto` 형태의 feature 우선 구조다.

```text
todo/
  controller/TodoController.java
  service/TodoService.java
  repository/TodoRepository.java
  entity/Todo.java
  dto/TodoCreateRequest.java
  dto/TodoResponse.java
  mapper/TodoMapper.java
```

단순한 샘플에서는 layer 우선 구조를 허용할 수 있지만, SI/솔루션 프로젝트에서는 feature 우선 구조를 기본으로 한다.

인증/보안 패키지 기준:

- `security/`는 Spring Security 설정, 필터, 인증 principal, 보안 공통 컴포넌트처럼 전역 보안 인프라를 둔다.
- `auth/`는 로그인, 회원가입, 토큰 발급, 로그아웃 같은 인증 기능의 Controller/Service/DTO를 둔다.
- `user/`는 사용자 Entity, Repository, 사용자 조회/상태 변경 같은 사용자 도메인을 둔다.
- `todo/`, `order/`처럼 업무 기능은 base package 바로 아래 feature package로 둔다.
- `domain/auth`, `domain/user`, `domain/todo`처럼 모든 업무를 `domain` 아래 넣는 구조는 프로젝트가 DDD 구조를 명시적으로 선택한 경우에만 사용한다.

### 3.4 JPA 사용 기준

JPA를 사용하는 경우 다음 기준을 개발표준정의서와 DB명세서에 반영한다.

| 항목 | 기준 |
| --- | --- |
| Entity 노출 | Entity를 Controller 응답으로 직접 반환하지 않고 Response DTO로 변환한다. |
| 연관관계 | 양방향 관계는 필요할 때만 사용하고, 무한 순환 직렬화 방지 기준을 명시한다. |
| Fetch 전략 | 기본은 LAZY로 두고, 필요한 조회는 fetch join, EntityGraph, query projection을 명시적으로 사용한다. |
| N+1 방지 | 목록/상세 조회 API는 N+1 가능성을 검토하고 테스트 또는 리뷰 기준에 포함한다. |
| Cascade | cascade, orphanRemoval은 생명주기가 완전히 종속되는 경우에만 사용하고 사유를 남긴다. |
| 변경감지 | 변경감지를 사용할 경우 Service 트랜잭션 경계와 수정 대상 필드를 명확히 한다. |
| Query | 단순 CRUD는 Spring Data JPA, 복잡 조회는 JPQL/QueryDSL/native query 중 선택 사유를 남긴다. |
| Auditing | 생성일시, 수정일시, 생성자, 수정자 정책을 공통 기준으로 정한다. |
| Soft Delete | 사용 여부와 조회 필터링 방식을 DB명세서/API정의서에 연결한다. |
| Pagination | 목록 API는 page/size/sort 허용값과 최대 size를 API정의서에 명시한다. |
| DB Pool | Spring Boot 기본 후보는 HikariCP로 둔다. 다른 pool을 사용하면 선택 사유, 설정 위치, 검증 방법을 개발표준정의서에 기록한다. |

Entity 작성 기준:

- 기본 생성자는 JPA 요구사항 범위에서만 노출한다.
- setter 남용을 피하고 의미 있는 변경 메서드를 둔다.
- `equals/hashCode`는 식별자 생성 시점과 proxy 이슈를 고려해 프로젝트 표준을 정한다.
- Lombok 사용 여부와 허용 annotation을 개발표준정의서에 명시한다.

Lombok 기준:

- Lombok 사용 여부는 개발표준정의서에서 명시적으로 선택한다.
- 허용 기본값은 `@Getter`, `@NoArgsConstructor(access = AccessLevel.PROTECTED)`, `@RequiredArgsConstructor`, `@Builder` 정도로 제한한다.
- Entity에는 `@Data`, 무분별한 `@Setter`, 양방향 연관관계가 있는 `@ToString`, 전체 필드 기반 `@EqualsAndHashCode` 사용을 금지한다.
- DTO에는 `@Getter`, 생성자, builder를 허용하되 validation과 불변성을 해치지 않도록 한다.
- Lombok으로 생성되는 코드 때문에 테스트, 직렬화, JPA proxy 동작이 불명확해지는 경우 명시 코드로 전환한다.

Repository 기준:

- Repository method 이름이 길어져 의미가 흐려지면 JPQL/QueryDSL 등 명시적 쿼리로 전환한다.
- 사용자 입력값을 문자열 결합 방식으로 query에 삽입하지 않는다.
- native query는 DB 종속성과 검증 방법을 기록한다.

### 3.5 코딩 규칙

| 항목 | 기준 |
| --- | --- |
| 언어 | Java 17 이상 또는 프로젝트 표준 LTS |
| 네이밍 | Class `PascalCase`, method/field `camelCase`, constant `UPPER_SNAKE_CASE` |
| 트랜잭션 | 쓰기 Service 메서드에 `@Transactional`, 읽기에는 `@Transactional(readOnly = true)` 적용 |
| Validation | 외부 입력은 DTO에서 Bean Validation으로 1차 검증하고, 업무 규칙은 Service에서 검증 |
| 응답 | 공통 응답/오류 응답 모델을 사용하고 내부 예외 메시지를 그대로 노출하지 않음 |
| 메시지 | `MessageSource`와 `messages_ko.properties` 등 메시지 리소스 사용 |
| 설정 | `application.yml`은 기본값만 두고 환경별 값은 profile/env/secret 관리 |
| JPA | N+1, lazy loading, cascade, orphanRemoval 사용 사유를 설계 또는 코드에 명확히 함 |
| Lombok | 허용 annotation과 금지 annotation을 개발표준정의서에 명시 |
| DB Pool | HikariCP 기본값 또는 대체 pool 선택 사유와 설정 기준 명시 |
| Logging | SLF4J facade를 사용하고 구현체(Logback/Log4j2)는 개발표준정의서에 명시 |

### 3.6 주석 기준

주석 기준:

- Controller, Service, Security Config, 핵심 Component 같은 주요 클래스에는 책임과 관련 `FUNC/PGM/SEC`를 JavaDoc으로 남긴다.
- public API, 복잡한 서비스 규칙, 보안 판단, 트랜잭션 경계에는 관련 ID를 남긴다.
- 단순 getter/setter, 단순 CRUD 위임에는 주석을 쓰지 않는다.
- 보안 예외, 임시 우회, 정책 결정은 `SEC-ID`, `DEC-ID`, `ISSUE-ID`와 함께 남긴다.

클래스 JavaDoc 예:

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

메서드 JavaDoc 예:

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

짧은 주석 예:

```java
// REQ-003, SEC-AUTH-002: 작성자 본인만 TODO를 수정할 수 있다.
```

### 3.6.1 로깅 기준

Spring Boot 로깅 기준:

- 로깅 API는 SLF4J facade를 사용한다.
- 기본 구현체는 Spring Boot 기본 Logback을 우선한다. Log4j2를 선택할 경우 선택 사유와 의존성 충돌 검증 방법을 개발표준정의서에 기록한다.
- Log4j 1.x는 사용하지 않는다.
- `System.out.println`, `printStackTrace`를 운영 코드에서 사용하지 않는다.
- Logger 선언은 클래스별 `private static final Logger` 또는 프로젝트가 승인한 Lombok `@Slf4j` 중 하나로 통일한다.
- `ERROR`, `WARN`, `INFO`, `DEBUG`, `TRACE` 레벨 사용 기준을 개발표준정의서에 명시한다.
- 비밀번호, 토큰, 인증 헤더, 세션 식별자, 주민등록번호, 전화번호, 이메일 등 개인정보/인증정보를 로그에 남기지 않는다.
- 요청 추적이 필요하면 `requestId` 또는 `correlationId`를 MDC로 관리하고, 생성/전파/삭제 위치를 명시한다.
- 예외 로그는 사용자 메시지와 내부 원인을 분리하고, 사용자에게 노출되는 오류 응답에는 내부 stack trace를 포함하지 않는다.

Logger 예:

```java
private static final Logger log = LoggerFactory.getLogger(AuthService.class);

public void logout(Long userId) {
    log.info("User logout completed. userId={}", userId);
}
```

민감정보 금지 예:

```java
// 금지: 토큰과 비밀번호가 로그에 남는다.
log.debug("login token={}, password={}", token, rawPassword);
```

### 3.7 테스트 기준

테스트 기준:

| 테스트 | 권장 도구 | 기준 |
| --- | --- | --- |
| 단위 | JUnit 5, Mockito, AssertJ | Service 업무 규칙, validator, mapper |
| Web MVC | Spring MVC Test | Controller validation, 인증/인가, 오류 응답 |
| 통합 | Spring Boot Test, Testcontainers 또는 H2 | Repository, transaction, 주요 API flow |
| 보안 | Spring Security Test | 인증 실패, 권한 실패, CSRF/session 정책 |

테스트 설명 기준:

- JUnit 테스트는 추적 ID를 메서드명에 남기고, `@DisplayName` 또는 Given/When/Then 주석으로 입력값, 기대값, 확인한 출력/상태를 설명한다.
- 한 테스트가 여러 API 흐름을 묶는 경우 각 흐름의 입력과 기대 결과를 코드 근처에 드러내거나 테스트를 분리한다.
- 감리 증적으로 쓰는 테스트는 테스트 파일만 읽어도 `UT/IT`가 무엇을 검증했는지 알 수 있어야 한다.

## 4. Backend Security: Spring Security

Spring Security를 사용하는 경우 다음 기준을 개발표준정의서와 보안가이드에 반영한다.

| 항목 | 기준 |
| --- | --- |
| 인증 | Form login, session, JWT/OAuth2 중 선택하고 선택 사유를 ADR 또는 개발표준에 기록 |
| 비밀번호 | `PasswordEncoder` 사용. 개발/테스트 외 평문/단순 해시 금지 |
| 인가 | URL 보안과 method security 중 적용 범위를 명시 |
| 세션 | 세션 고정 보호, timeout, logout, cookie 속성 기준 명시 |
| CSRF | 브라우저 세션 기반이면 기본 활성화. 비활성화 시 API 특성과 대체 통제 기록 |
| CORS | 허용 origin/method/header를 명시하고 wildcard 남용 금지 |
| 오류 | 로그인 실패, 권한 실패 메시지에서 계정 존재 여부나 내부 정책 노출 금지 |
| 테스트 | 인증/인가 실패 케이스를 통합 또는 MVC 테스트에 포함 |

## 5. Frontend: React

권장 구조:

```text
src/
  app/
  pages/ 또는 routes/
  features/{featureName}/
    components/
    hooks/
    api/
    model/
  shared/
    components/
    api/
    lib/
    messages/
  test/
```

| 항목 | 기준 |
| --- | --- |
| 언어 | TypeScript 우선 |
| 컴포넌트 | 함수 컴포넌트와 hooks 사용 |
| 상태 | 로컬 UI 상태와 서버 상태를 구분 |
| API | 화면 컴포넌트에서 fetch를 직접 흩뿌리지 않고 feature/shared api 계층 사용 |
| 메시지 | 사용자 노출 문구는 i18n/messages 리소스 또는 상수로 관리 |
| 입력검증 | 클라이언트 검증은 UX 보조이며 서버 검증을 대체하지 않음 |
| 보안 | `dangerouslySetInnerHTML` 금지. 필요 시 sanitize 근거와 테스트 기록 |
| 접근성 | label, button name, keyboard navigation, focus 상태를 고려 |

| 테스트 | 권장 도구 | 기준 |
| --- | --- | --- |
| 단위/컴포넌트 | Vitest/Jest, Testing Library | 사용자 행동 중심 검증 |
| API mocking | MSW 또는 프로젝트 표준 mock | 성공/실패/권한 오류 |
| E2E | Playwright | 핵심 사용자 flow와 화면 증적 |

## 6. Frontend: Next.js

Next.js는 React 베이스라인을 따른다. 추가로 다음 기준을 적용한다.

| 항목 | 기준 |
| --- | --- |
| 라우팅 | App Router 또는 Pages Router 중 하나를 선택하고 혼용 기준을 명시 |
| Server/Client | Server Component와 Client Component 경계를 명확히 한다 |
| API Route | API Route를 사용할 경우 Backend API와 책임 경계를 문서화 |
| 인증 | cookie/session/token 저장 위치와 서버 검증 위치를 명시 |
| 환경변수 | 서버 전용 env와 `NEXT_PUBLIC_` env를 구분 |
| 캐시 | route cache, fetch cache, revalidation 기준을 명시 |
| 보안 | 서버에서만 알아야 하는 비밀값을 client bundle에 노출하지 않음 |

권장 구조:

```text
app/
  (routes)/
  api/
features/
shared/
  components/
  api/
  lib/
  messages/
tests/
```

## 7. Frontend: Vue.js

권장 구조:

```text
src/
  app/
  router/
  features/{featureName}/
    components/
    composables/
    api/
    model/
  shared/
    components/
    api/
    lib/
    messages/
  stores/
```

| 항목 | 기준 |
| --- | --- |
| 언어 | TypeScript 우선 |
| 컴포넌트 | Composition API와 `<script setup>` 기본 |
| 상태 | Pinia 또는 프로젝트 표준 상태관리 사용 |
| API | composable/api 계층에서 호출하고 컴포넌트에 직접 흩뿌리지 않음 |
| 메시지 | vue-i18n 또는 messages 리소스 사용 |
| 보안 | `v-html` 금지. 필요 시 sanitize 근거와 테스트 기록 |
| 접근성 | label, aria, focus, keyboard navigation 고려 |

| 테스트 | 권장 도구 | 기준 |
| --- | --- | --- |
| 단위/컴포넌트 | Vitest, Vue Test Utils, Testing Library | 사용자 행동 중심 검증 |
| API mocking | MSW 또는 프로젝트 표준 mock | 성공/실패/권한 오류 |
| E2E | Playwright | 핵심 사용자 flow와 화면 증적 |

## 8. Python/FastAPI

기존 샘플과 PoC에서 사용할 수 있는 기본 구조다.

| 항목 | 기준 |
| --- | --- |
| 구조 | Router -> Service -> Repository -> Database |
| 검증 | Pydantic schema로 외부 입력 검증 |
| 메시지 | 메시지 리소스 또는 상수 모듈 사용 |
| 테스트 | pytest, TestClient, repository/service unit test |
| 보안 | dependency 기반 인증/인가, 비밀번호 해시, 출력 인코딩, 민감정보 로그 금지 |

## 9. Gate 2 적용 체크리스트

Gate 2 완료 전 development-review persona는 다음을 확인한다.

| 항목 | 확인 |
| --- | --- |
| 기술스택 선택 | Backend, Frontend, DB, 테스트 도구가 명시되어 있다. |
| 베이스라인 연결 | 본 문서의 적용 섹션이 개발표준정의서에 기록되어 있다. |
| 패키지 구조 | 프로젝트에 맞는 패키지/폴더 구조가 확정되어 있다. |
| 메시지 관리 | 사용자 노출 메시지 관리 방식이 확정되어 있다. |
| 보안 구현 | 인증, 인가, 입력검증, 출력 인코딩, 세션/토큰 기준이 확정되어 있다. |
| 테스트 | 단위/통합/E2E 테스트 도구와 파일명 규칙이 확정되어 있다. |
| 빌드/실행 | 의존성 설치, 실행, 테스트, 정적검사 명령이 명시되어 있다. |
| 예외 | 베이스라인과 다른 선택은 사유가 기록되어 있다. |
