# SYSTEM DESIGN: SNS Performance Analytics & Data-Driven A&R Intelligence (v0.3.0)

## 1. UI/UX 메인 아키텍처 (Executive Command Center)
* **접속 시 기본 탭(Default Tab)**: \nalytics\ (SNS & A&R 인텔리전스)
* **화면 레이아웃**:
  1. 최상단: 3대 플랫폼 종합 KPI 스코어카드 (YouTube 조회수, Insta 저장률, TikTok 완독률)
  2. 중앙 좌측: 음악 피처 vs 반응 상관 분석 차트 (BPM 산점도, 악기별 저장률)
  3. 중앙 우측: 킬링파트 타임라인 오버레이 (가사 섹션 위 시청 유지율 곡선)
  4. 하단: 🤖 AI A&R 차기작 전략 브리핑 카드 & [🚀 1곡 스튜디오로 전달] / [💬 대화창 시작] 액션 버튼

## 2. Hexagonal Domain & Services
* \AnalyticsAggregatorService\: 다채널 데이터 수집, 정규화, database.json 저장
* \CorrelationEngineService\: Pearson 상관계수, 회귀 분석 및 킬링파트 스파이크 감지
* \StrategyAdvisoryService\: 상관 분석 결과를 종합하여 Gemini 기반 차기작 A&R 전략 브리핑 생성
