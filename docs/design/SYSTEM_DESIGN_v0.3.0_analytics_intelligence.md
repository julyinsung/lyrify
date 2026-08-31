# SYSTEM DESIGN: SNS Performance Analytics & Data-Driven A&R Intelligence (v0.3.0)

## 1. Hexagonal Architecture Extension (헥사고날 확장)

### 1.1 Core Domain Entities & Aggregates
* \TrackAnalytics\: YouTube, Instagram, TikTok 3대 플랫폼의 통합 지표 엔티티
* \CorrelationModel\: 음악 속성(BPM, Instruments, Keywords)과 SNS 반응 간의 통계적 상관 모델
* \AudienceRetentionPoint\: 1초 단위 시청 유지율 및 상대적 되감기 스파이크 포인트

### 1.2 Core Domain Services
* \AnalyticsAggregatorService\: 다채널 데이터 수집, 정규화, database.json 저장
* \CorrelationEngineService\: Pearson 상관계수, 회귀 분석 및 킬링파트 스파이크 감지
* \StrategyAdvisoryService\: 상관 분석 결과를 종합하여 Gemini 기반 차기작 A&R 전략 브리핑 생성

### 1.3 Adapters & Repositories
* \YouTubeAnalyticsAdapter\: YouTube Data/Analytics API 및 수동 JSON/CSV 임포트 어댑터
* \InstagramGraphAdapter\: Instagram Graph API 및 릴스 인사이트 수집 어댑터
* \TikTokAnalyticsAdapter\: TikTok Creator API 및 완독률 데이터 수집 어댑터
* \AnalyticsRepository\: \data/analytics.json\ 안전한 비동기 영속화 및 락 제어

## 2. API Contract Specification (v0.3.0)
* \GET /api/analytics/summary\: 전 채널 통합 지표 (총 조회수, 평균 완독률, 최고 성과 트랙 TOP 3)
* \GET /api/analytics/tracks/:id\: 단일 트랙의 3대 SNS 세부 지표 및 초단위 유지율 시계열 곡선
* \POST /api/analytics/tracks/:id/sync\: 외부 API 또는 지표 JSON을 통한 트랙 성과 동기화
* \GET /api/analytics/correlations\: BPM/악기/키워드 vs 완독률/저장률 상관 분석 매트릭스
* \POST /api/analytics/strategy-brief\: AI A&R의 데이터 기반 차기작 프로덕션 전략 브리핑 요청

## 3. UI/UX 화면 구성 (3대 메인 탭 체제)
* **[TAB 1] 🌟 1곡 심층 프로덕션 스튜디오 (Master Studio)**: 기존 v0.2.0 기능 100% 무손실 유지
* **[TAB 2] 🗄️ AI 탐색 & 트랙 볼트 (Library)**: 기존 v0.2.0 트랙 패키지 관리 및 개별/일괄 삭제 유지
* **[TAB 3] 📊 SNS 퍼포먼스 & A&R 인텔리전스 (Analytics Hub)**:
  * 상단: 3대 채널 종합 스코어카드 (YouTube 조회수, Insta 저장률, TikTok 완독률)
  * 좌측: 음악 피처 vs 반응 상관 분석 인터랙티브 차트 (BPM 산점도, 악기별 저장률 리프트)
  * 우측: 킬링파트 타임라인 오버레이 ([Intro/Verse/Chorus] 위 시청 유지율 곡선)
  * 하단: 🤖 AI A&R 차기작 전략 브리핑 카드 & [💬 대화창으로 전략 전송] 원클릭 버튼
