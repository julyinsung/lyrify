# Vulcan-Anvil Ex Templates

이 디렉토리는 Vulcan-Anvil Ex Core 규칙을 따르는 공식 산출물 템플릿을 보관한다.

루트의 `templates/` 디렉터리는 `vulcan.py init`이 새 프로젝트 골격을 만들 때 복사하는 시드 파일 영역이다.
이 디렉터리(`docs/templates/`)는 Gate 산출물의 공식 문서 양식만 다룬다.

`docs/templates/poc/`는 PoC profile에서 사용하는 통합 산출물 양식이다.
PoC에서는 audit 문서 전체를 느슨하게 채우는 대신 `docs/poc/`의 3종 문서로 목표, 설계, 검증 결과를 먼저 연결한다.

`0.4.7` 기준 공식 템플릿:

- `PROJECT_BRIEF_TEMPLATE.md`: 프로젝트 개요서
- `STAKEHOLDER_SCOPE_TEMPLATE.md`: 이해관계자 및 범위 정의서
- `AS_IS_TO_BE_TEMPLATE.md`: 현행/개선 방향 정의서
- `RISK_ASSUMPTION_TEMPLATE.md`: 위험 및 가정 정의서
- `REQUIREMENTS_SPEC_TEMPLATE.md`: 요구사항정의서
- `TRACEABILITY_MATRIX_TEMPLATE.md`: 요구사항추적표
- `SW_ARCHITECTURE_TEMPLATE.md`: SW 아키텍처 정의서
- `DEPLOYMENT_INFRASTRUCTURE_ARCHITECTURE_TEMPLATE.md`: 배포·운영 인프라 아키텍처 정의서
- `FUNCTION_SPEC_TEMPLATE.md`: 기능명세서
- `PROJECT_GLOSSARY_TEMPLATE.md`: 프로젝트 단어사전
- `DATABASE_SPEC_TEMPLATE.md`: DB명세서
- `LOGICAL_ERD_DBML_TEMPLATE.dbml`: 논리 ERD DBML 원본
- `PHYSICAL_ERD_DBML_TEMPLATE.dbml`: 물리 ERD DBML 원본
- `API_SPEC_TEMPLATE.md`: API 정의서
- `SECURITY_GUIDE_TEMPLATE.md`: 보안가이드
- `PROGRAM_SPEC_TEMPLATE.md`: 프로그램 설계서
- `SCREEN_SPEC_TEMPLATE.md`: 화면설계서
- `TEST_CASE_TEMPLATE.md`: 테스트케이스 정의서
- `TEST_RESULT_TEMPLATE.md`: Gate 4 QA 테스트 결과서
- `DEVELOPMENT_STANDARD_TEMPLATE.md`: 개발표준정의서
- `CHANGE_REQUEST_TEMPLATE.md`: 변경요청 관리대장
- `CHANGE_REQUEST_DETAIL_TEMPLATE.md`: 개별 변경요청 상세서
- `RELEASE_APPROVAL_TEMPLATE.md`: 릴리즈 승인서
- `QA_FINDING_TEMPLATE.md`: QA 발견사항

템플릿 작성 기준:

- 모든 공식 산출물은 `docs/core/DOCUMENT_METADATA.md`의 메타데이터 필드를 따른다.
- 모든 ID는 `docs/core/ID_SYSTEM.md`의 Prefix 규칙을 따른다.
- 모든 연결 관계는 `docs/core/TRACEABILITY_RULES.md`의 추적성 규칙을 따른다.
- 보안항목은 `docs/core/SECURITY_BASELINE.md`의 기준선을 우선 적용하고, 프로젝트별 구현 규격은 보안가이드에 확정한다.
- 화면설계서, 프로그램 설계서, DB명세서, 테스트케이스는 보안가이드의 `SEC-ID`별 구체 규칙과 연결되어야 한다.
- 데이터 항목은 `docs/core/REFERENCE_STANDARDS.md`와 `docs/core/DATA_STANDARD_RULES.md`의 데이터 표준 규칙을 따른다.
- 프로젝트 데이터 용어는 `docs/core/DATA_STANDARD_RULES.md`의 데이터 표준 규칙을 따른다.
- 개발 언어, 패키지 구조, 코드/주석/테스트 컨벤션은 `docs/core/TECH_STACK_BASELINES.md`를 기준으로 개발표준정의서에 명시하고 구현 전에 확정한다.
- 템플릿은 사람이 빈칸을 채우는 양식이면서, 에이전트가 대화/코드/테스트 결과를 바탕으로 작성할 수 있는 작업 지침이어야 한다.

