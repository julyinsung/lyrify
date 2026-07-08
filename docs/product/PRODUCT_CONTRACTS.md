# Product Contracts

---
document_id: PROD-CONTRACT
title: Product Contracts
title_ko: 제품 구현 계약 인덱스
project: lyrify
profile: product
gate_scope: gate2-impl
status: Draft
version: v0.2
owner_role: Technical Architect
author: Agent
reviewer: User
approver: User
created_at: 2026-07-08
updated_at: 2026-07-08
related_documents:
  - docs/product/PRODUCT_BRIEF.md
  - docs/product/PRODUCT_ARCHITECTURE.md
---

## 1. Contract Policy

이 문서는 상세 설계서 복사본이 아니라 Product profile의 구현 계약 진입점이다.
상세 API/DB/UI/보안 설계가 필요한 경우 `docs/artifacts/02-design/` 산출물로 분리하고, 이 문서에서는 링크와 핵심 계약만 유지한다.

## 2. API Contracts

| API ID | Method | Path / Entry | Request | Response | 관련 Scenario | 상세 문서 / 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| API-001 | GET | `/api/tracks` | None | `JSON` (파싱된 트랙 레시피 리스트, 매핑 경로, 싱크 타임라인 등) | SCN-001 | 트랙 목록 조회 |
| API-002 | POST | `/api/tracks/:id/map` | `JSON` (`{ type: "ace-step" \| "lelia", filePath: "string" }`) | `JSON` (`{ success: true, mappedFiles: { aceStep: string, lelia: string } }`) | SCN-002 | 음원 수동/자동 매핑 저장 |
| API-003 | POST | `/api/tracks/:id/sync` | `JSON` (`{ timeline: [{ part: "string", startSecond: number }] }`) | `JSON` (`{ success: true, updatedTimeline: [...] }`) | SCN-004 | 파트별 타임라인 싱크 저장 |
| API-004 | POST | `/api/tracks/:id/generate-image` | `JSON` (`{ useApi: boolean, textPrompt?: string }`) | `JSON` (`{ success: true, imageUrl: string }`) | SCN-003 | Google API 또는 로컬 템플릿 커버 생성 |
| API-005 | POST | `/api/tracks/:id/export-video` | `JSON` (`{ targetAudio: "ace-step" \| "lelia" }`) | `JSON` (`{ success: true, videoUrl: string, jobId: string }`) | SCN-004 | FFmpeg 비디오 렌더링 요청 |
| API-006 | POST | `/api/tracks/:id/auto-align` | `JSON` (`{ engine: "docker-gentle" \| "google-stt" }`) | `JSON` (`{ success: true, autoTimeline: [...] }`) | SCN-004 | AI 기반 가사 타임라인 자동 정렬 |

## 3. Data Contracts

| DATA/DB ID | 이름 | 주요 필드 | 보안 분류 | 관련 API/Scenario | 상세 문서 / 설명 |
| --- | --- | --- | --- | --- | --- |
| DATA-001 | database.json | `id`, `title`, `bpm`, `keyscale`, `lyricsRaw`, `parts` (문단 배열), `audioPathAceStep`, `audioPathLelia`, `coverImageUrl`, `timeline` | 일반 | API-001, API-002, API-003 | 로컬 트랙 메타데이터 DB |
| DATA-002 | config.json | `watchDirectory` (감시 경로), `exportDirectory` (수출 경로), `googleApiKey` (선택적 구글 API Key) | 인증정보 | API-004, API-005, API-006 | 애플리케이션 로컬 환경 설정 파일 (GCP Key 포함) |

## 4. UI Contracts

| UI/SCR ID | 화면/상호작용 | 주요 상태 | 관련 Scenario | 검증 |
| --- | --- | --- | --- | --- |
| UI-001 | 대시보드 카드 뉴스형 그리드 | Empty / Loading / Success | SCN-001 | 자동/육안 검증 |
| UI-002 | 트랙 상세 정보 및 싱크 에디터 모달 | Success / Syncing / GeneratingImage | SCN-001, SCN-002, SCN-003, SCN-004 | 수동/자동 검증 |
| UI-003 | FFmpeg 인코딩 상태 패널 (프로그레스 바) | Loading (인코딩 중) / Success / Error (부재 또는 실패) | SCN-004 | 자동/인코더 검증 |

## 5. Security And Data Baseline

| 항목 | 기준 | 적용 위치 | 검증 |
| --- | --- | --- | --- |
| Security | docs/core/PRODUCT_PROFILE_BASELINE.md, docs/core/SECURITY_BASELINE.md | GCP API Key 로컬 세팅 격리 (`.env`), 로컬 경로 검증 모듈 | REG-001 |
| Data | docs/core/DATA_STANDARD_RULES.md | database.json 스키마 표준 정의 | REG-001 |

## 6. Contract Gaps

| Gap ID | 내용 | 영향 | 후속 판단 |
| --- | --- | --- | --- |
| GAP-001 | 비디오 인코딩 백엔드 진행 상태 실시간 통신 방식 필요 | HTTP POST의 1회성 응답만으로는 FFmpeg 렌더링 진행률(%)을 대시보드에 실시간 표시하기 어려움 | SSE(Server-Sent Events) 프로토콜 또는 프론트엔드의 1초 주기 주기적 폴링(Polling) API 추가 도입 |
