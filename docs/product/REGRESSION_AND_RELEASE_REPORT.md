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
| REG-001 | Gate 4 실행 예정 | Planned | `tests/logs/reg-001.log` | Gate 4 검증 대상 |
| REG-002 | Gate 4 실행 예정 | Planned | `tests/logs/reg-002.log` | Gate 4 검증 대상 |
| REG-003 | Gate 4 실행 예정 | Planned | `tests/logs/reg-003.log` | Gate 4 검증 대상 |
| REG-004 | Gate 4 실행 예정 | Planned | `tests/logs/reg-004.log` | Gate 4 검증 대상 |
| REG-005 | Gate 4 실행 예정 | Planned | `tests/logs/reg-005.log` | Gate 4 검증 대상 |
| SEC-REG-001 | Gate 4 실행 예정 | Planned | `tests/logs/sec-reg-001.log` | 보안 smoke 검증 대상 |
| SEC-REG-002 | Gate 4 실행 예정 | Planned | `tests/logs/sec-reg-002.log` | 보안 smoke 검증 대상 |

## 3. Known Issues

| Issue ID | 내용 | 영향 | 릴리즈 판단 |
| --- | --- | --- | --- |
| ISSUE-NONE | 현재 식별된 결함 없음 | 없음 | Accept |

## 4. Gate 5 Release Decision

| 항목 | 내용 |
| --- | --- |
| 릴리즈 후보 | Yes (Release 1 MVP 완료 후 판정 예정) |
| 포함 범위 | Release 1 (MVP: ZENION 자산 자동 구조화, 듀얼 오디오 플레이어, 16:9/9:16 비디오 렌더러, SNS 릴리즈 키트) |
| 제외 범위 | 유튜브/틱톡 직접 API 자동 업로드, Suno 웹 자동 크롤러 (Release 2/3 후보) |
| 남은 리스크 | 고해상도 비디오 렌더링 시 로컬 CPU/GPU 사양에 따른 인코딩 소요 시간 차이 |
| 다음 릴리즈 후보 | Release 2: AI 음악 디렉터(가변 스타일 기획) + AI 1차 퀄리티 스크리닝(100점 채점) 고도화 |
