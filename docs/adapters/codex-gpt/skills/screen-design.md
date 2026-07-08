# 화면 설계 Skill

## 사용할 때

Gate 2에서 화면이 있는 기능을 설계할 때 사용한다.

외부 시안, Figma 캡처, 이미지 생성 시안, 손그림, 기존 시스템 화면 캡처를 가져오거나 새로 만들고, 이를 `SCR-ID`, `UI-ID`, 요구사항, 테스트 기준과 연결한다.

## 필수 입력

- `docs/core/TRACEABILITY_RULES.md`
- `docs/templates/SCREEN_SPEC_TEMPLATE.md`
- 관련 요구사항정의서
- 관련 기능명세서
- 관련 프로그램 설계서
- 관련 요구사항추적표
- 사용자가 제공한 외부 시안 또는 참고 이미지

## 절차

1. 관련 `REQ`, `AC`, `FUNC`, `PGM`, `SEC`를 확인한다.
2. 사용자 흐름을 기준으로 필요한 화면을 식별하고 `SCR-ID`를 부여한다.
3. 각 화면의 기본, 오류, 빈 상태, 권한 제한 상태를 정의한다.
4. 외부 시안이 있으면 출처, 파일/URL, 기준 viewport를 기록한다.
5. 정적 이미지 시안은 `docs/artifacts/02-design/screen/images/`에 둔다.
6. HTML/CSS/JS 화면 퍼블리싱 산출물은 `docs/artifacts/02-design/screen/ui-baseline/UIREF-NNN/` 하위에 둔다.
7. 시안이 없고 사용자가 허용하면 imagegen, 화면 퍼블리싱 산출물, 간단 와이어프레임 중 적절한 방식으로 기준 시안을 만든다.
8. UIREF가 단순 참고자료인지 구현 기준인지 구분한다.
9. 구현 기준이면 UI Implementation Contract에 기준 파일, 기준 CSS/토큰, 필수 유지 요소, 변경 허용 항목, 변경 금지 항목, 비교 방식을 작성한다.
10. 화면설계서에 입력 항목, 출력 항목, 이벤트, 메시지 위치, 보안 적용 방식을 작성한다.
11. Gate 3에서 사용할 `UI-ID`, viewport, 캡처 경로, 비교 기준 후보를 작성한다.
12. 요구사항추적표에 `SCR-ID`, `UIREF-ID`, 관련 `REQ/AC/FUNC/PGM/SEC` 연결을 반영한다.

## 출력

다음을 반환한다.

- 작성 또는 갱신한 `SCR-ID`
- 사용한 시안 출처와 파일/URL
- UI Implementation Contract 적용 여부와 필수 유지/허용 변경/금지 변경
- 기준 viewport
- 화면 상태 목록
- Gate 3로 넘길 `UI-ID` 후보
- 미해결 화면 질문 또는 `FIND/CR` 후보
