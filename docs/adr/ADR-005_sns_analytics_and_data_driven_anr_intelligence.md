# ADR-005: SNS Performance Analytics & Data-Driven A&R Production Intelligence (v0.3.0)

## 1. Context & Background (배경 및 문제 정의)
ZENION Music Studio는 v0.3.0에서 사용자 중심의 워크플로우를 대폭 혁신한다.
디렉터가 스튜디오에 접속했을 때 가장 먼저 마주하는 화면(Home/Default View)을 **[📊 SNS & A&R 인텔리전스 대시보드]**로 전진 배치(메인 승격)하여, 대중의 반응 데이터와 다음 음악 제작 전략을 먼저 브리핑받고 프로덕션에 착수하도록 설계한다.

## 2. Decision Drivers (의사결정 요인)
1. **SNS & A&R 인텔리전스를 제1메인(Home) 화면으로 승격**: 스튜디오 접속 시 기본 활성화되는 첫 페이지로 배치.
2. **데이터 드리븐 프로덕션 흐름 (Data ➔ Strategy ➔ Production)**:
   - [Home] SNS 성과 및 상관 분석 확인 ➔ AI A&R 차기작 전략 수신 ➔ [1곡 스튜디오] 또는 [1:1 대화창]으로 원클릭 전환 프로듀싱.
3. **기존 v0.2.0 기능 100% 무손실 보존**: 1곡 심층 스튜디오 및 트랙 볼트 라이브러리를 서브 탭으로 온전히 유지.

## 3. UI Architecture (메인 우선순위 탭 구조)
- **[TAB 1 - HOME / 메인 첫 화면] 📊 SNS & A&R 인텔리전스 (Executive Analytics & Strategy Hub)**
- **[TAB 2] 🌟 1곡 심층 프로덕션 스튜디오 (Master Studio)**
- **[TAB 3] 🗄️ AI 탐색 & 트랙 볼트 (Track Vault Library)**

## 4. Technical Contracts (v0.3.0)
- GET /api/analytics/summary: 전 트랙 다채널 통합 지표 요약
- GET /api/analytics/tracks/:id: 특정 트랙의 SNS 세부 지표 및 초단위 유지율 곡선
- POST /api/analytics/tracks/:id/sync: 특정 트랙의 SNS 성과 데이터 수동/자동 동기화
- GET /api/analytics/correlations: 전 트랙 음악 피처 vs SNS 반응 상관 분석 결과
- POST /api/analytics/strategy-brief: 상관 분석 기반 AI A&R 차기작 기획 리포트 생성
