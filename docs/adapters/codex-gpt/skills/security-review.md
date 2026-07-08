# 보안 검토 Skill

## 사용할 때

보안 요구사항, 보안 설계, 보안 구현, 보안 테스트 증적을 검토할 때 사용한다.

## 필수 입력

- `docs/core/REFERENCE_STANDARDS.md`
- `docs/core/SECURITY_BASELINE.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/templates/SECURITY_GUIDE_TEMPLATE.md`
- 프로젝트 산출물 `docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md`
- `docs/templates/PROGRAM_SPEC_TEMPLATE.md`
- `docs/templates/SCREEN_SPEC_TEMPLATE.md`
- 관련 `SEC` 항목
- 필요한 경우 `docs/seed-docs/reference-standards/` 아래 공개 보안 표준 문서

## 절차

1. 관련 `REQ`, `NREQ`, `SCR`, `PGM`, `DB`, `SEC` ID를 식별한다.
2. `SECURITY_BASELINE.md`의 기능 유형별 체크리스트로 누락된 `SEC-ID` 후보를 찾는다.
3. 프로젝트 보안가이드에 각 `SEC-ID`의 구체 규칙, 값, 오류 메시지, 적용 위치, 검증 ID가 있는지 확인한다.
4. 각 `SEC-ID`에 `KISA/SR`, `OWASP`, `CWE` 매핑이 있는지 확인한다.
5. 화면설계서, 프로그램 설계서, DB명세서가 보안가이드의 값을 그대로 참조하는지 확인한다.
6. 구현이 승인된 보안가이드를 따르는지 확인한다.
7. 테스트가 보안가이드의 각 규칙을 증명하는지 확인한다.
8. 승인된 범위 안의 미해결 보안 이슈는 `FIND`로 기록한다.
9. 보안 기준선, 보안가이드, 인수기준, 설계 범위가 바뀌어야 하면 `CR`로 승격한다.

## 출력

다음을 반환한다.

- 검토한 보안 ID
- 사용한 보안 가이드 참조(`KISA/SR`, `OWASP`, `CWE`)
- 누락되었거나 약한 통제 항목
- 보안가이드에 없는 암묵 구현/테스트 스펙
- 테스트 커버리지 상태
- `FIND` 또는 `CR` 권고

