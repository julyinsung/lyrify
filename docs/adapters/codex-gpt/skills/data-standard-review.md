# 데이터 표준 검토 Skill

## 사용할 때

프로젝트 용어집, DB 명세, 컬럼 명명, 코드/명칭 분리, 공공데이터 표준 정합성을 검토할 때 사용한다.

## 필수 입력

- `docs/core/DATA_STANDARD_RULES.md`
- `docs/core/REFERENCE_STANDARDS.md`
- `docs/templates/PROJECT_GLOSSARY_TEMPLATE.md`
- `docs/templates/DATABASE_SPEC_TEMPLATE.md`
- 필요한 경우 `docs/seed-docs/reference-standards/` 아래 공공데이터 표준 엑셀

## 절차

1. 범위 안의 업무 용어, 테이블명, 컬럼명, 코드값을 식별한다.
2. 용어가 공공데이터 표준에 존재하는지 확인한다.
3. 표준에 없으면 프로젝트 정의 용어로 분류하고 근거를 기록한다.
4. DB 명칭이 프로젝트 용어집과 일관적인지 확인한다.
5. ID, 코드값, 명칭, 설명의 도메인이 명확한지 확인한다.
6. 논리/물리 ERD DBML이 있으면 DB명세서의 테이블, 컬럼, PK/FK, 관계와 일치하는지 확인한다.
7. export 이미지 또는 PDF가 있으면 사람이 검토할 수 있는 최신 산출물인지 확인한다.
8. 매핑 누락이나 명명 불일치는 `FIND` 또는 `ISSUE`로 기록한다.

## 출력

다음을 반환한다.

- 검토한 용어
- 공공 표준 매칭 결과
- 프로젝트 정의 용어
- DB 명명 누락 또는 불일치
- 논리/물리 ERD DBML 작성 여부
- DB명세서와 DBML의 불일치
- ERD export 산출물 존재 여부
- 필요한 용어집 또는 DB 명세 갱신
