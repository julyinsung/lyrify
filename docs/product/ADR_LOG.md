# ADR Log

---
document_id: PROD-ADR
title: ADR Log
title_ko: 제품 아키텍처 의사결정 기록
project: lyrify
profile: product
gate_scope: gate2-gate5
status: Draft
version: v0.3
owner_role: Product Architect
author: Agent
reviewer: User
approver: User
created_at: 2026-07-08
updated_at: 2026-08-27
related_documents:
  - docs/product/PRODUCT_ARCHITECTURE.md
---

## 1. Decision Index

| ADR ID | 제목 | 상태 | 결정일 | 영향 범위 |
| --- | --- | --- | --- | --- |
| ADR-001 | 로컬 무균성 및 자동화 트레이드오프를 위한 Docker 및 Web Audio/LRCLIB 하이브리드 가사 싱크 아키텍처 채택 | Accepted | 2026-07-08 | CMP-007, API-008, SCN-004 |
| ADR-002 | 상업적 저작권 보호 및 고품질 생성을 위한 Suno AI 유료 음원 파이프라인 채택 | Accepted | 2026-08-27 | CMP-003, API-004, DATA-001, SCN-003 |
| ADR-003 | 2단계 AI 품질 스크리닝(오디오 파형 결함 검사 + LLM 가사 완성도 평가) 기법 채택 | Accepted | 2026-08-27 | CMP-002, API-003, DATA-001, SCN-002 |
| ADR-004 | ACE-Step 음악 생성 자동 트리거를 위한 로컬 REST API 및 CLI 하이브리드 연동 방식 채택 | Accepted | 2026-08-27 | CMP-001, API-001, SCN-001 |
| ADR-005 | Linux 기반 Docker Compose 표준 배포 및 볼륨 마운트 아키텍처 채택 | Accepted | 2026-08-27 | CMP-005, API-006, DATA-002, SCN-004 |

## 2. ADR 작성 기준

| 항목 | 내용 |
| --- | --- |
| 언제 작성하나 | 런타임, 데이터 저장소, 외부 연동, 보안 기준, 배포 방식처럼 후속 구현/운영에 영향을 주는 선택을 했을 때 작성한다. |
| 번호 규칙 | 첫 실제 의사결정은 `ADR-001`부터 시작한다. |
| 상태 | `Proposed`, `Accepted`, `Superseded`, `Rejected` 중 하나를 사용한다. |
| 비어 있을 때 | 실제 의사결정이 없으면 `ADR-NONE` 행을 유지한다. 아직 확정되지 않은 `ADR-001` placeholder 행은 남기지 않는다. |

## 3. ADR 상세 템플릿

새 ADR을 추가할 때 아래 형식을 복사해 사용한다.

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-001 |
| Context | 결정 배경 |
| Decision | 선택한 방향 |
| Alternatives | 검토한 대안 |
| Consequences | 장점, 비용, 후속 작업 |
| Related Scenario / Contract | 관련 SCN/API/DATA/UI/REG |
| Status | Proposed / Accepted / Superseded / Rejected |

## 4. ADR 상세 기록

### ADR-001: Docker 및 Web Audio/LRCLIB 하이브리드 가사 싱크 아키텍처 채택

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-001 |
| Context | AI 기반 오디오 가사 싱크(Forced Alignment)를 위해 로컬 AI 구동(Python, PyTorch 등)이 필요하나, 사용자 로컬 PC에 복잡한 AI 구동 의존성을 강제 설치하는 것은 무겁고 환경을 오염시킬 위험이 있음. 반면 클라우드 API(Google STT)는 인터넷이 필수적이며 사용자의 유료 GCP API 키 등록 등의 번거로운 과정이 동반됨. |
| Decision | 시스템에 Docker 데몬이 실행 중일 경우 로컬 Docker Gentle/Whisper API 컨테이너를 호출하여 AI 싱크 정렬을 처리하고, Docker가 없을 경우 가벼운 Web Audio 기반 비트 감지(세미 오토) 및 무료 온라인 가사 API(LRCLIB)를 백업으로 사용하는 하이브리드 백엔드 처리 방식을 채택함. |
| Alternatives | 1. 로컬 Python/PyTorch 환경 강제 설치 (기각 - 일반 사용자 환경 오염 및 설치 진입 장벽).<br>2. Google GCP Speech-to-Text API 강제 적용 (기각 - 결제 카드 등록 및 유료 사용 거부감, 인터넷 필수 조건 제약). |
| Consequences | - 장점: 로컬 PC의 독립성과 무균성을 보존하며, 사양 및 환경에 맞춤화된 최적의 사용자 경험 제공.<br>- 비용: 백엔드에서 Docker 존재 여부를 검사하고 여러 동기화 흐름을 유연하게 처리하기 위한 분기 개발 공수 발생. |
| Related Scenario / Contract | SCN-004, CMP-006, API-006 |
| Status | Accepted |

### ADR-002: 상업적 저작권 보호 및 고품질 생성을 위한 Suno AI 유료 음원 파이프라인 채택

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-002 |
| Context | 초기 실험용 AI 오디오 모델(예: 구글 릴리아 등)은 상업적 이용 및 소셜 배포 시 저작권 분쟁 및 라이선스 위배 위험이 존재함. 크리에이터가 유튜브 등에 안전하게 수익화/배포하기 위해서는 상업적 권리가 보장되는 상용 AI 음원 서비스가 필요함. |
| Decision | 유료 구독을 통해 상업적 이용 권리가 확보되는 Suno AI를 최종 완성 음원 생성 도구로 공식 채택하고, ACE-Step-1.5의 초안 레시피(가사/스타일)와 Suno AI 음원을 1:1 매핑하여 관리하는 듀얼 파이프라인 구조를 제품의 표준으로 확정함. |
| Alternatives | 1. 오픈소스/실험용 AI 모델 사용 (기각 - 상업적 저작권 불확실성 및 배포 리스크).<br>2. 수동 작곡 음원만 지원 (기각 - AI 크리에이터 자동화 파이프라인 비전에 부합하지 않음). |
| Consequences | - 장점: 크리에이터의 유튜브/소셜 배포 시 저작권 안전성 확보 및 고품질 보컬/음악 결과물 제공.<br>- 비용: 외부 웹에서 생성된 음원을 로컬 감시 디렉토리로 다운로드/임포트하는 매핑 UI 지원 필요. |
| Related Scenario / Contract | SCN-003, CMP-003, API-004, DATA-001 |
| Status | Accepted |

### ADR-003: 2단계 AI 품질 스크리닝(오디오 파형 결함 검사 + LLM 가사 완성도 평가) 기법 채택

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-003 |
| Context | 10개 이상의 초안을 크리에이터가 일일이 전부 청음하고 비교하는 것은 피로도가 심함. 기계적 오디오 결함과 음악적/가사적 매력도를 사전 채점하여 추천해줄 필요성 대두. |
| Decision | 1단계로 Web Audio/Node 파형 분석을 통해 무음/클리핑/볼륨 레벨을 기술 검사하고, 2단계로 LLM을 통해 가사 운율/구성 및 스타일 매력도를 종합 평가하여 100점 만점 스코어 및 랭킹을 대시보드에 제공함. |
| Alternatives | 1. 완전 수동 청음 (기각 - 시간 낭비 및 피로도 심함).<br>2. 무거운 오디오 딥러닝 모델 단독 사용 (기각 - 로컬 PC 사양 부담). |
| Consequences | - 장점: 크리에이터가 상위 TOP 3 후보만 청음하고 즉시 결정할 수 있어 작업 시간 90% 이상 단축.<br>- 비용: 가사 분석 및 오디오 파형 유효성 검사 로직 개발 필요. |
| Related Scenario / Contract | SCN-002, CMP-002, API-003, DATA-001 |
| Status | Accepted |

### ADR-004: ACE-Step 음악 생성 자동 트리거를 위한 로컬 REST API 및 CLI 하이브리드 연동 방식 채택

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-004 |
| Context | AI 디렉터가 기획한 10종의 음악 스타일 레시피를 ACE-Step 엔진에게 자동으로 전달하여 초안 음원을 일괄 생성하도록 지시하는 입력 인터페이스가 필요함. |
| Decision | ACE-Step의 내장 REST API 서버(`http://127.0.0.1:8001`) 호출을 1순위 표준으로 채택하고, API 서버 미기동 시 `cli.py` 명령어 백그라운드 자식 프로세스 실행을 폴백으로 지원하는 하이브리드 트리거 방식을 채택함. |
| Alternatives | 1. 파일 시스템 단순 텍스트 주입 후 수동 생성 유도 (기각 - 완전 자동화 미흡).<br>2. ACE-Step 소스코드 직접 통합 (기각 - ACE-Step 내부 의존성과의 결합도 증가 및 업데이트 충돌 위험). |
| Consequences | - 장점: Lyrify 백엔드가 ACE-Step과 느슨하게 결합(Loosely Coupled)되어 독립성을 유지하면서도, 원클릭 10곡 자동 생성 트리거를 원활하게 수행 가능.<br>- 비용: ACE API 응답 타임아웃 및 CLI 에러 핸들링 로직 구현 필요. |
| Related Scenario / Contract | SCN-001, CMP-001, API-001 |
| Status | Accepted |

### ADR-005: Linux 기반 Docker Compose 표준 배포 및 볼륨 마운트 아키텍처 채택

| 항목 | 내용 |
| --- | --- |
| ADR ID | ADR-005 |
| Context | Windows 네이티브 환경에서 FFmpeg 구동 시 한글 자막 폰트 경로 이스케이프 오류, 자막 깨짐, 바이너리 PATH 설정 복잡성 문제가 빈번하게 발생함. 또한 로컬 저장소(`ZENION-MUSIC`, `ACE-Step-1.5`)와 안정적으로 실시간 연동하면서 일관된 16:9/9:16 비디오 렌더링 품질을 보장할 표준 배포 아키텍처가 필요함. |
| Decision | Debian 12 Bookworm 기반의 Linux 컨테이너(`node:20-bookworm-slim`)에 FFmpeg 및 `fonts-noto-cjk`(한글 폰트)를 일체화 패키징하고, Docker Compose(`docker-compose.yml`)를 통해 호스트의 `ZENION-MUSIC` 및 `ACE-Step-1.5` 디렉토리를 컨테이너 내부(`/data/...`)로 볼륨 마운트하는 Docker Compose 배포를 제품의 1순위 표준으로 확정함. |
| Alternatives | 1. Windows 네이티브 FFmpeg 바이너리 직접 설치 및 PATH 수동 등록 (기각 - 한글 폰트 깨짐 및 OS 종속적 오류 위험).<br>2. 외부 클라우드 인코딩 위임 (기각 - 대용량 미디어 업로드/다운로드 지연 및 API 비용 발생). |
| Consequences | - 장점: 한글 가사 자막 렌더링 무결성 확보, FFmpeg 무설치 제로 컨피그, 일관된 고품질 비디오 렌더링 보장.<br>- 비용: 사용자 PC에 Docker Desktop 구동 필요 (원클릭 `docker-compose.yml` 및 로컬 폴백 스크립트 함께 제공). |
| Related Scenario / Contract | SCN-004, CMP-005, API-006, DATA-002 |
| Status | Accepted |
