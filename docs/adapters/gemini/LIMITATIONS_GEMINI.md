# Gemini Limitations (GEMINI Standard)

> 상태: v0.1 (Gemini Runner 한계 및 극복 지침)
> 목적: Gemini 모델의 아키텍처 및 행동적 특징으로 인한 한계점을 명시하고, 이를 프레임워크 수준에서 극복하기 위한 실질적인 우회 규칙을 제공한다.

---

## 1. 모델 한계 및 대응 전략

### ① Rate Limits (분당 요청 및 토큰 제한)
* **현황**: 대량의 컨텍스트를 주입할 때 TPM(Token Per Minute) 또는 RPM(Request Per Minute) 제한에 도달하여 API 호출이 차단될 가능성이 높습니다.
* **대응**: 
  * 런타임 구동 엔진은 API 호출부(Adapter Client)에 지수 백오프(Exponential Backoff) 및 재시도 로직을 필수로 내장해야 합니다.
  * 불필요한 중간 빌드 로그 등은 컨텍스트에서 스트립(Strip)한 후 주입합니다.

### ② 추론 일관성 (Temperature & Top-P 제어)
* **현황**: 창의적인 답변 성향으로 인해 규격화된 코드가 아닌 독자적인 스타일의 코드를 작성할 가능성이 존재합니다.
* **대응**:
  * 코딩 및 검수 작업 수행 시 API 설정의 `temperature` 값을 `0.0`에서 최대 `0.2`로 고정하여 추론의 결정론적(Deterministic) 특성을 강제합니다.
  * UI 개발 시에는 Baseline을 최대한 보존하도록 프롬프트에 `Strict CSS Class conservation rule`을 바인딩합니다.

---

## 2. Gemini 장점 극대화 지침

### ① 대량 파일 병합 참조
* **한계 극복**: 타 모델(Claude 등)은 토큰 및 비용 이슈로 인해 파일 일부만 발췌하여 읽지만, Gemini는 전체 프로젝트의 파일 구조 및 코드를 한 번에 인풋으로 주입받을 수 있습니다.
* **지침**: 
  * 구현 워커 실행 시, `working_documents`에 기술된 주 변경 대상 파일 외에도 의존성이 걸린 전체 모듈(예: 백엔드의 모든 MVC 레이어 파일)을 병합하여 하나의 컨텍스트로 제공합니다.
  * 워커가 의존성이 깨진 코드를 생산하는 실수를 원천적으로 방지합니다.

### ② 구조화된 JSON 반환 활용
* **지침**:
  * 단순 마크다운 텍스트 출력을 요청하는 대신, API의 `responseSchema`를 활용하여 규격화된 아웃풋 구조인 `RUN_OUTPUT_CONTRACT_GEMINI.md` 사양에 부합하는 JSON을 강제 반환하게 합니다.
  * 파싱 오류 및 정합성 검사 오류를 제거합니다.
