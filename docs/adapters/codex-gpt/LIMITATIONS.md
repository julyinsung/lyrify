# Codex/GPT Adapter Limitations

> 상태: 초안 v0.1
> 목적: Codex/GPT Adapter 사용 시 한계와 주의사항을 정의한다.

## 1. 컨텍스트 한계

Codex/GPT는 모든 문서를 항상 완전하게 기억한다고 가정하지 않는다.

Adapter는 Run마다 다음 우선순위로 문서를 제공한다.

1. 현재 Run의 관련 ID가 포함된 추적표
2. 관련 요구사항/설계/테스트 문서
3. 개발표준
4. Core 규칙
5. 참조표준 요약

문서가 길면 전체를 제공하기보다 관련 ID 중심으로 요약한다.

## 2. 범위 확장 위험

Codex/GPT는 문제를 해결하는 과정에서 주변 코드를 함께 개선하려 할 수 있다.

이를 막기 위해 Run 입력에는 반드시 `scope.writable`과 `scope.excluded`를 둔다.

범위 밖 수정이 필요하면 `Blocked` 또는 `CompletedWithIssues`로 보고한다.

## 3. 테스트 해석 한계

테스트 명령이 실패했거나 실행되지 않았는데 통과로 간주하면 안 된다.

Adapter는 다음 상태를 구분한다.

- `passed`
- `failed`
- `not_run`
- `partial`

테스트를 실행할 수 없는 환경이면 그 이유와 후속 조치를 남긴다.

## 4. 화면 증적 한계

화면 증적의 기준 도구는 Playwright다. CDP, 브라우저 수동 캡처, 런타임 Preview 캡처는 보조 관찰로만 사용할 수 있고 UI Pass 증거가 될 수 없다.

Playwright가 설치되어 있지 않으면 먼저 설치하고 다시 실행한다.

```text
npx playwright --version
npm install -D @playwright/test
npx playwright install
npx playwright test
```

화면 증적 Run은 다음을 기록한다.

- Playwright 설치 확인 또는 설치 명령 결과
- Playwright 실행 명령과 exit code
- 캡처 대상 URL
- 캡처 파일 경로
- 콘솔 오류 여부
- 모바일/데스크톱 여부

Playwright 캡처를 생성하지 못하면 `not_run` 또는 `FIND`로 기록하고, CDP/수동 캡처만으로 Pass 처리하지 않는다.

## 5. 민감정보 제한

Codex/GPT Adapter는 다음 경로를 기본 제외한다.

```text
docs/ref-docs/
```

다만 `docs/seed-docs/reference-standards/`는 프로젝트 생성 시 주입할 공개 표준 원문 영역이므로, Run 입력에서 명시된 경우 읽기 전용으로 사용할 수 있다.

다음 정보는 출력, 로그, 커밋에 포함하지 않는다.

- 실제 개인정보
- 운영 비밀번호
- API 토큰
- 내부망 주소
- 고객사 비공개 문서 원문
- 보안상 민감한 설정값

참조문서에서 얻은 내용은 필요한 경우 요약 규칙 문서로만 반영한다.

## 6. 모델 독립성 한계

Codex/GPT Adapter는 Codex/GPT 실행 특성에 맞춘 문서다.

Claude, Cursor, Copilot 등 다른 도구는 같은 Core 규약을 따르되 다음 항목이 달라질 수 있다.

- 파일 접근 방식
- 도구 실행 방식
- 컨텍스트 제공 방식
- 결과 출력 형식
- 브라우저/캡처 가능 여부

따라서 Adapter별 문서는 중복을 허용하되 Core 규칙을 변경하지 않는다.

## 7. 승인 필요 상황

다음은 사용자 승인이 필요하다.

- `docs/ref-docs/` 접근
- 원격 저장소 push
- 패키지 설치 또는 외부 네트워크 접근
- 기존 승인 ID 변경
- 테스트 기준 완화
- 보안 통제 제거
- 대규모 리팩터링

## 8. 남은 과제

Codex/GPT Adapter v0.1에서 아직 자동화하지 않은 영역:

- Run 입력 YAML 자동 생성
- 추적표에서 관련 ID 자동 추출
- Run 출력 YAML 검증
- Dashboard 연동
- Claude Adapter와의 호환성 테스트
