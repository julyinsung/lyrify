# ADR-005: SNS Performance Analytics & Data-Driven A&R Production Intelligence (v0.3.0)

## 1. Context & Background (배경 및 문제 정의)
v0.2.0까지 구축된 ZENION Music Studio는 1곡 심층 프로덕션(Master Studio), Git-Flow 기반 테이크 분기, 가사/사운드 설계, Linux FFmpeg 비디오 렌더링, SNS 릴리즈 키트 생성 파이프라인을 완비하였다.
그러나 릴리즈 이후 YouTube(롱폼/쇼츠), Instagram(릴스), TikTok(숏폼)에서 발생하는 실제 시청자 반응(조회수, 시청지속률 곡선, 완독률, 저장률)이 음악 프로덕션 파이프라인과 단절되어 있어, 다음 곡의 기획/작사/BPM/사운드 설계가 데이터에 기반하지 못하고 직관에만 의존하는 한계가 존재했다.

## 2. Decision Drivers (의사결정 요인)
1. **기존 v0.2.0 기능 100% 무손실 보존**: 현재 구축된 1곡 심층 스튜디오 및 트랙 볼트 라이브러리 화면을 온전히 유지하면서 3번째 탭([📊 SNS 퍼포먼스 & A&R 인텔리전스])으로 완벽히 통합.
2. **다채널 SNS 성과 데이터 정규화**: YouTube Data/Analytics API, Instagram Graph API, TikTok Creator Analytics의 서로 다른 지표(조회수, 완독률, 저장수, 시청시간, 유지율 곡선)를 단일 스키마로 표준화.
3. **음악 피처 vs SNS 반응 상관 분석 (Correlation Analysis)**: BPM(템포), 장르, 악기 레이어, 가사 키워드, 훅(Hook) 진입 시점과 시청 완독률/저장률 간 상관계수(r) 및 회귀 분석 수행.
4. **타임라인 시청률 & 가사 섹션 오버레이 (Retention vs Lyrics)**: 영상의 초단위 시청 유지율 그래프를 가사 섹션([Intro], [Verse], [Chorus])과 1:1로 매핑하여 킬링파트 스파이크와 이탈 지점을 시각화.
5. **AI A&R 차기작 전략 브리핑 & 1:1 대화형 프로듀싱 연계**: 상관 분석 결과를 토대로 Google Gemini가 차기작 사운드/작사 전략 리포트를 자동 발행하고, 메인 대화창으로 원클릭 전송.

## 3. UI Architecture (3대 메인 탭 구조)
- **[TAB 1] 🌟 1곡 심층 프로덕션 스튜디오 (Master Studio)**: 기존 v0.2.0 유지 (창작 & 실시간 AI 지시)
- **[TAB 2] 🗄️ AI 탐색 & 트랙 볼트 (Library)**: 기존 v0.2.0 유지 (패키지 에셋 및 트랙 관리)
- **[TAB 3] 📊 SNS 퍼포먼스 & A&R 인텔리전스 (Analytics Hub)**: v0.3.0 신규 탑재 (상관 분석 & 전략 리포트)

## 4. Technical Contracts (v0.3.0)
- GET /api/analytics/summary: 전 트랙 다채널 통합 지표 요약
- GET /api/analytics/tracks/:id: 특정 트랙의 SNS 세부 지표 및 초단위 유지율 곡선
- POST /api/analytics/tracks/:id/sync: 특정 트랙의 SNS 성과 데이터 수동/자동 동기화
- GET /api/analytics/correlations: 전 트랙 음악 피처 vs SNS 반응 상관 분석 결과
- POST /api/analytics/strategy-brief: 상관 분석 기반 AI A&R 차기작 기획 리포트 생성
