# 🎵 ZENION Music Studio (Lyrify)

> **AI 기반 차세대 음악 프로덕션 워크스테이션 & Suno AI 마스터 스튜디오**

---

## 🌟 개요

**ZENION Music Studio (Lyrify)**는 단순한 가사 생성기가 아닙니다.  
프로 작곡가와 음악 프로듀서의 제작 철학을 담아, **"왜 이 악기와 코드를 선택했는지"에 대한 음악적 기획 의도(Rationale)**를 바탕으로 1곡을 완벽하게 다듬어가는 **AI 음악 프로덕션 워크스테이션**입니다.

---

## 🚀 빠른 시작 (Quick Start)

### 1. Docker 환경에서 1초 만에 실행
```bash
# 컨테이너 빌드 및 백그라운드 실행
docker compose up -d

# 웹 스튜디오 접속
# 브라우저에서 http://localhost:3000 열기
```

### 2. 로컬 개발 모드 실행
```bash
npm install
npm run dev
# http://localhost:3000 접속
```

---

## 📚 공식 문서 및 사용자 매뉴얼

* 📖 **[실전 사용자 매뉴얼 (User Manual)](docs/user/USER_MANUAL.md)**  
  * 1곡 심층 기획부터 Suno v3.5/v4/v5 프롬프트 복사, 테이크 브랜치 분기, A/B 청취, 비디오 배포까지 5단계 완벽 가이드
* 🏛️ **[시스템 아키텍처 및 API 흐름도](docs/user/ARCHITECTURE_AND_DATAFLOW.md)**  
  * 브라우저 ➔ Node.js 백엔드 ➔ Google Gemini SDK ➔ SQLite DB & 마스터 볼트 파일 시스템 간의 엔드투엔드 데이터 흐름
* 📑 **[아키텍처 결정 기록 (ADR-004)](docs/adr/ADR-004_music_branching_and_hybrid_sqlite_storage.md)**  
  * 하이브리드 SQLite 스토리지 및 Music Git-Flow 브랜칭 모델 설계 결정서
* 📋 **[제품 설계 및 계약서 (Product Specs)](docs/product/PRODUCT_CONTRACTS.md)**  
  * REST API 명세, 데이터 계약, UI 컴포넌트 인터랙션 계약

---

## ✨ 핵심 기능

1. **사운드 아키텍처 & Rationale 설계**:
   * BPM, 조성(Key), 악기 편성, 보컬 톤 선정의 음악 이론적 이유(Rationale)를 명시.
2. **섹션별 인라인 연주 지시어 타임라인**:
   * `[Intro]`부터 `[Outro]`까지 각 파트별 편곡 의도, 연주 지시어, 가사, 보컬 애드리브를 독립적으로 편집.
3. **Suno AI (v3.5 / v4 / v5) 마스터 패키지**:
   * 3단 구조화 Style of Music Box + 인라인 메타태그 Lyrics Box 원클릭 클립보드 복사.
4. **Music Git-Flow (버전 & 브랜치 관리)**:
   * 원장(Master)을 유지하며 파트별 실험 테이크(Take 1, Take 2)를 분기하고 A/B 비교 후 Master로 승격(Merge).
5. **AI Co-Producer Agent**:
   * 자연어 대화를 통해 가사 및 편곡을 점진적으로 튜닝.
6. **올인원 비디오 렌더링 & SNS 릴리즈 키트**:
   * 한글 자막 16:9 유튜브 롱폼 & 9:16 인스타/틱톡 숏폼 MP4 인코딩 및 플랫폼별 맞춤 설명문 생성.

---

## 🛠️ 기술 스택

* **Frontend**: React 18, HTML5 Web Audio API, Modern Split Console CSS
* **Backend**: Node.js v20 LTS, Express, Fluent-FFmpeg
* **AI & LLM**: Google Gemini 2.0 Flash SDK (`@google/genai`), Structured Outputs
* **Storage Layer**: Hybrid Dual-Layer (Embedded SQLite + `ZENION-MUSIC` Master Vault)
* **Media & Video**: Linux 네이티브 FFmpeg v6.x+, `fonts-noto-cjk`, `libass`
* **Container**: Linux Debian 12 Bookworm Slim (`node:20-bookworm-slim`), Docker Compose
