# Claude Adapter Limitations

> 상태: v0.1
> 목적: Claude Adapter 사용 시 한계와 주의사항을 정의한다.

## 1. 컨텍스트 한계

Claude는 대화 컨텍스트를 누적하지만, 대화가 길어지면 초기 내용이 압축될 수 있다.

Adapter는 Run마다 다음 우선순위로 문서를 제공한다.

1. 현재 Run의 관련 ID가 포함된 추적표
2. 관련 요구사항/설계/테스트 문서
3. 개발표준
4. Core 규칙
5. 참조표준 요약

문서가 길면 전체를 제공하기보다 관련 ID 중심으로 요약한다.

subagent에게 위임할 때는 모든 컨텍스트를 다시 전달하지 않고 `source_documents`(3-tier: `read_first` / `working_documents` / `reference_on_demand`)와 `related_ids`만 전달한다.

## 2. subagent 위임 한계

Claude subagent(`.claude/agents/*.md`)는 각자 독립된 컨텍스트로 시작한다.

- Orchestrator의 이전 대화 내용을 자동으로 공유하지 않는다.
- Run Input Contract에 명시된 문서와 ID만 참조한다.
- 위임 시 scope.writable 밖의 파일을 수정하지 않는다.

## 3. 범위 확장 위험

Claude는 문제를 해결하는 과정에서 주변 코드를 함께 개선하려 할 수 있다.

이를 막기 위해 Run 입력에는 반드시 `scope.writable`과 `scope.excluded`를 둔다.

범위 밖 수정이 필요하면 `Blocked` 또는 `CompletedWithIssues`로 보고한다.

## 4. 테스트 해석 한계

테스트 명령이 실패했거나 실행되지 않았는데 통과로 간주하면 안 된다.

Adapter는 다음 상태를 구분한다.

- `passed`
- `failed`
- `not_run`
- `partial`

테스트를 실행할 수 없는 환경이면 그 이유와 후속 조치를 남긴다.

## 5. 화면 증적 한계

화면 증적의 기준 도구는 Playwright다.
Claude-in-Chrome, CDP, computer-use, 브라우저 수동 캡처는 보조 관찰로만 사용할 수 있고 UI Pass 증거가 될 수 없다.

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
- 뷰포트 크기

Playwright 캡처를 생성하지 못하면 `not_run` 또는 `FIND`로 기록하고, CDP/수동 캡처만으로 Pass 처리하지 않는다.

## 6. 민감정보 제한

Claude Adapter는 다음 경로를 기본 제외한다.

```text
docs/ref-docs/
```

다음 정보는 출력, 로그, 커밋에 포함하지 않는다.

- 실제 개인정보
- 운영 비밀번호
- API 토큰
- 내부망 주소
- 고객사 비공개 문서 원문
- 보안상 민감한 설정값

## 7. 승인 필요 상황

다음은 사용자 승인이 필요하다.

- `docs/ref-docs/` 접근
- 원격 저장소 push
- 패키지 설치 또는 외부 네트워크 접근
- 기존 승인 ID 변경
- 테스트 기준 완화
- 보안 통제 제거
- 대규모 리팩터링
- scope.writable 밖 파일 수정

## 8. Codex/GPT Adapter와의 호환성

Claude Adapter와 Codex/GPT Adapter는 같은 Core 규약을 따르지만 다음 항목이 다르다.

| 항목 | Codex/GPT | Claude |
| --- | --- | --- |
| 진입 문서 | `AGENTS.md` | `.claude/CLAUDE.md` |
| 스킬 참조 방식 | 수동 경로 참조 | `.claude/skills/` 자동 로드 |
| 도구 실행 | 텍스트 명령 출력 | Bash tool 직접 실행 |
| 브라우저 캡처 | Playwright 명령 출력 | Playwright 명령 실행 |
| `adapter` 필드 | `codex-gpt` | `claude` |

두 어댑터가 같은 프로젝트에 공존할 수 있다. Core 규칙은 변경하지 않는다.

## 9. 남은 과제

Claude Adapter v0.1에서 아직 자동화하지 않은 영역:

- Run 입력 YAML 자동 생성 (`vulcan.py run-new` 확장)
- subagent 결과 자동 검증
- Dashboard 연동
- Codex/GPT Adapter와의 호환성 테스트
