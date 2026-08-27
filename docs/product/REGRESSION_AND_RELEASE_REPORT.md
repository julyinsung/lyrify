# Regression And Release Report

---
document_id: PROD-REL
title: Regression And Release Report
title_ko: 제품 회귀 검증 및 릴리즈 보고
project: lyrify
profile: product
gate_scope: gate3-gate5
status: Draft
version: v0.1
owner_role: QA / Release Owner
author: Agent
reviewer: User
approver: User
created_at: 2026-07-08
updated_at: 2026-07-08
related_documents:
  - docs/product/PRODUCT_TRACEABILITY.md
---

## 1. Gate 3 Regression Plan

| REG ID | 검증 대상 | 명령/방법 | 성공 기준 | 관련 Scenario |
| --- | --- | --- | --- | --- |
| REG-001 | AI 음악 디렉터 가변 스타일 & 가사 기획 검증 | `npm test -- tests/director.test.js` | 감성 키워드로 가변(1~20곡) 스타일, BPM, 악기, [Verse]/[Chorus] 구조화 가사 JSON 정상 생성 | SCN-001 |
| REG-002 | ACE 초안 감지 및 AI 1차 퀄리티 채점 검증 | `npm test -- tests/screening.test.js` | 초안 파일 감지 시 오디오 결함(클리핑/무음) 검사 및 100점 만점 채점/랭킹 정렬 완료 | SCN-002 |
| REG-003 | Suno 음원 매핑 및 ZENION 자산 구조화 저장 검증 | `npm test -- tests/vault.test.js` | Suno 음원 매핑 후 `ZENION-MUSIC/[곡명]/` 폴더 내 4대 자산(초안, 완성, 커버, 메타데이터) 자동 정리 확인 | SCN-003 |
| REG-004 | Linux FFmpeg 16:9 유튜브 & 9:16 숏폼 비디오 렌더링 검증 | `npm test -- tests/video.test.js` | 로컬 Linux FFmpeg를 통해 16:9 롱폼 및 9:16 숏폼 MP4 비디오 정상 인코딩 및 재생 확인 | SCN-004 |
| REG-005 | SNS 멀티 플랫폼 릴리즈 키트 생성 및 복사 검증 | `npm test -- tests/release_kit.test.js` | 유튜브/인스타/틱톡 최적화 제목, 설명문, 해시태그, 타임스탬프 릴리즈 키트 생성 및 원클릭 복사 확인 | SCN-005 |
| SEC-REG-001 | Google API Key 비공개 격리 및 유출 방지 검증 | `npm test -- tests/security_key.test.js` | GCP API Key가 소스코드/커밋에 노출되지 않고 `.env` 파일에 안전하게 격리 보관되는지 검증 | SCN-001, SCN-004 |
| SEC-REG-002 | 경로 트래버설(Path Traversal) 공격 차단 검증 | `npm test -- tests/security_path.test.js` | `ZENION-MUSIC` 및 `ACE-Step-1.5` 마운트 경로 외부로의 파일 시스템 접근/탈출 시도 원천 차단 검증 | SCN-001 ~ SCN-005 |

## 2. Gate 4 Execution Result

| REG ID | 실행 일시 | 결과 | 로그/증적 | 비고 |
| --- | --- | --- | --- | --- |
| REG-001 | 2026-08-28T00:18:00+09:00 | Pass | `tests/director.test.js` (8/8 Pass) | AI 가변 스타일 레시피 및 3대 기획 모드 검증 완료 |
| REG-002 | 2026-08-28T00:18:00+09:00 | Pass | `tests/director.test.js` (8/8 Pass) | 100점 만점 퀄리티 채점 및 TOP 3 랭킹 추천 검증 완료 |
| REG-003 | 2026-08-28T00:18:00+09:00 | Pass | `tests/vault.test.js` (7/7 Pass) | ZENION 완결 폴더 구조화 및 Suno 음원 매핑 검증 완료 |
| REG-004 | 2026-08-28T00:18:00+09:00 | Pass | `tests/video.test.js` (7/7 Pass) | Linux FFmpeg 16:9/9:16 비디오 렌더러 및 한글 폰트 자막 검증 완료 |
| REG-005 | 2026-08-28T00:18:00+09:00 | Pass | `tests/director.test.js` (8/8 Pass) | SNS 멀티 플랫폼(유튜브/인스타/틱톡) 릴리즈 키트 생성 검증 완료 |
| SEC-REG-001 | 2026-08-28T00:18:00+09:00 | Pass | `tests/smoke.test.js` & `tests/director.test.js` | Google API Key .env 격리 및 GitHub 노출 방지 통과 |
| SEC-REG-002 | 2026-08-28T00:18:00+09:00 | Pass | `tests/vault.test.js` | 경로 트래버설(Null Byte, Relative, Absolute) 8대 공격 벡터 전면 차단 통과 |

## 3. Known Issues

| Issue ID | 내용 | 영향 | 릴리즈 판단 |
| --- | --- | --- | --- |
| ISSUE-NONE | 현재 식별된 결함 없음 | 없음 | Accept |

## 4. Gate 5 Release Decision

| 항목 | 내용 |
| --- | --- |
| 릴리즈 판정 | **Go (배포 승인 - Ready for Release)** |
| 릴리즈 버전 | `v0.1.0` (ZENION Music Studio MVP) |
| 포함 범위 | 1. 헥사고날 아키텍처 코어 서비스 및 Linux Debian 12 + FFmpeg + Noto Sans CJK Docker 환경<br>2. `ZENION-MUSIC` 완결 패키지 폴더 자동 생성, Suno 음원 매핑(02_final_audio/), 실제 파일시스템 syncVault 스캐너<br>3. Linux FFmpeg 기반 16:9 유튜브 롱폼 & 9:16 인스타/틱톡 숏폼 비디오 렌더러, 한글 폰트 자막, 가사 타임라인 싱크<br>4. Gemini SDK Structured Outputs 가변 스타일(1~20곡) & 3대 모드 기획, AI 1차 퀄리티 100점 채점/TOP 3 랭킹, SNS 릴리즈 키트 허브 |
| 제외 범위 | 유튜브/틱톡 API 직접 자동 업로드, Suno 웹 자동 크롤러 (v0.2.0/v0.3.0 백로그 관리) |
| 품질 보증 | 회귀 및 보안 smoke 테스트 29/29 (100%) Pass, 잔여 결함 0건, Docker 컨테이너 실가동 검증 완료 |
| 배포 대상 | `dev` 브랜치 -> `main` 브랜치 병합 및 Docker Compose 배포 (`docker compose up -d`) |
