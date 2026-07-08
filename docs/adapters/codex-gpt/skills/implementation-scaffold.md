# Implementation Scaffold Skill

## 목적

Impl 진입 직후 feature 구현 전에 빌드 가능한 계약 skeleton을 만든다.

이 skill은 업무 로직 구현이 아니라 Program Design의 `PGM/IF/MTH/DTO/Entity/Component` 계약을 실제 파일, class/interface, public method signature, 테스트 골격으로 고정하는 작업이다.

## 입력

- 현재 scaffold Run
- `target_contracts.interface_contract`
- `target_contracts.contract_skeleton`
- 프로그램 설계서
- 개발표준정의서
- Gate 3 테스트케이스

## 절차

1. `AGENTS.md`, `session.json`, 현재 Run 문서를 먼저 읽는다.
2. `target_contracts.interface_contract`의 public signature, DTO/schema, error contract를 확인한다.
3. `target_contracts.contract_skeleton.files`에 지정된 파일만 생성하거나 보강한다.
4. 신규 개발이면 폴더, 빌드 설정, app entrypoint, public class/interface/method, DTO/schema, 테스트 파일 skeleton을 만든다.
5. 고도화이면 기존 코드와 Program Design의 계약을 매핑하고, 누락 skeleton만 보강한다.
6. 업무 로직은 완성하지 않는다. method body는 `TODO`, `NotImplemented`, 최소 wiring, 빈 adapter처럼 빌드가 깨지지 않는 수준으로 둔다.
7. Gate 2/3에서 frontend stack과 도구가 확정되어 있으면 `package.json`, lockfile, lint/build/test script, Playwright 설정을 scaffold 범위에서 고정한다.
8. Node/Playwright 의존성 설치가 필요하면 worker cache(`npm_config_cache`, `PLAYWRIGHT_BROWSERS_PATH`)를 사용해 가능한 범위에서 실행한다.
9. npm registry, 권한, 인증, 네트워크, cache 문제로 설치/검증을 실행하지 못하면 `environment_blocked` 또는 `not_run`으로 기록하고, 실패 명령/cwd/exit code/log path/Orchestrator 재실행 명령을 남긴다.
10. scaffold worker의 Node/Playwright 실행은 skeleton smoke 보조 검증이다. 최종 화면 실행, Playwright 증적, QA Pass는 `workflow.integration_branch` 기준 `QA-000` QA workspace의 Gate 4 QA에서 판정한다.
11. `scaffold_reference_contracts`에 SCR/UI ID가 있으면 화면 구조 참고용으로만 사용한다. UI-001-* Pass, 상태별 캡처, Playwright 증적을 이번 scaffold Run의 직접 완료 조건으로 쓰지 않는다.
12. contract skeleton smoke 명령 또는 Run의 `verification.commands`를 가능한 범위에서 실행한다.
13. 다음 Build Wave가 채워야 할 method, 테스트, 남은 ISSUE/CR 후보를 Run 결과에 남긴다.

## 금지

- 업무 기능 로직 완성
- 전체 E2E 또는 Gate 4 QA Pass 선언
- `session.json`, Gate 상태, wave-complete, sync-session 직접 변경
- `scope.writable` 밖 파일 수정
- Program Design에 없는 class, method, schema 임의 생성

## 완료 조건

- Program Design의 public signature가 실제 skeleton 파일에 존재한다.
- 신규/고도화 모드와 생략 사유가 Run에 기록되어 있다.
- compile/import/build smoke가 통과했거나 Not Run 사유가 명확하다.
- Node/Playwright 설치가 막혔으면 코드 실패와 환경 차단을 분리해 기록하고 Orchestrator 재검증 명령을 남긴다.
- worker worktree에서 화면 서버나 Playwright를 못 띄운 경우에도 최종 UI 검증은 Gate 4 QA 입력으로 분리되어 있다.
- 다음 Build Wave가 구현할 계약 단위가 식별되어 있다.
