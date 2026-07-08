---
paths:
  - "docs/artifacts/04-review/**"
---

# Gate 4: QA 검수 규칙

## 산출물

- 결함/발견: `docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md` (템플릿: `QA_FINDING_TEMPLATE.md`)
- 테스트 결과서: `docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md` 등
- 추적표 최신화: `docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md`
- UI 증적: `docs/artifacts/04-review/screenshots/` (파일명 권장: `{TEST-ID}-{설명}.png`)

## 3단계 진행

Gate 4는 별도 subagent로 단계를 분리한다.

1. **코드 리뷰** — 요구사항 + 설계 + 소스코드 기반. 리뷰 메모 산출.
2. **테스트 실행** — Test-Cases + `ENVIRONMENT.md` 기반. 결과 + 스크린샷.
3. **최종 판정** — 위 결과 종합하여 QA Finding/Review 산출.

각 단계 내에서도 REQ 청크 분할을 적용한다.

## 6개 평가 항목

### Blocker (1개라도 Fail → 전체 Fail)

| ID | 항목 | 기준 |
| --- | --- | --- |
| A | 요구사항 충족 | 모든 `REQ-NNN`이 구현되었는가 |
| B | 설계 준수 | 설계 문서의 아키텍처/API/화면을 따르는가 |
| C | 테스트 결과 | `UT`/`IT`/`PT`/`UI`가 전수 Pass 또는 명시적 Skip 사유 |
| D | 보안 점검 | `SEC-NNN` 대응이 구현·검증되었는가 (security-baseline skill로 보조) |

### Improvement (개선 권고)

| ID | 항목 | 기준 |
| --- | --- | --- |
| E | 주석 표준 | 개발표준정의서(`DOC-DEV-G2-001_Development-Standard`)의 주석 섹션 준수 |
| F | 코드 품질 | 함수 길이, 네이밍, 중복 |

## 발견사항 분류 (`docs/core/CHANGE_CONTROL_PROCESS.md`)

- **FIND** — 승인 범위 안 결함 → 현 Gate에서 QA Fix Loop (`docs/adapters/codex-gpt/skills/qa-fix-loop.md` 참조)
- **CR** — 범위 변경 → `docs/artifacts/05-change/`에 변경요청 작성, 영향 Gate로 재진입
- **ISSUE** — 보류/질문 → `docs/backlog/`로 이월

**Blocker/Major는 백로그 이월 금지.** 현 Gate 안에서 Developer에게 재작업 요청한다.

## 추적표 갱신

`상태`를 `구현완료`/`수정예정`으로, `리뷰 문서` 컬럼을 채운다.

## 완료 조건

`docs/core/AGENT_RUN_PROTOCOL.md` §5: 테스트 결과와 화면/로그 증적이 추적표에 연결되고, 미해결 FIND/CR/ISSUE가 명시적으로 처리(수정/이월/CR 승격)되어 있어야 한다.
