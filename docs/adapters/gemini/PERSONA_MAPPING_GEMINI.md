# Gemini Persona Mapping (GEMINI Standard)

> 상태: v0.1 (Gemini Runner 페르소나 매핑 명세)
> 목적: Core 에이전트 페르소나를 Gemini 모델의 구체적인 API 파라미터, 시스템 인스트럭션 및 Structured Outputs 스키마에 바인딩하는 표준 매핑 규칙을 정의한다.

---

## 1. 페르소나 매핑 매트릭스

Gemini 어댑터는 런타임에서 Core 페르소나를 전달받았을 때, 아래 매트릭스에 기술된 모델 매개변수와 제약을 동적으로 결합하여 최적의 에이전트 인스턴스를 생성합니다.

| Core Persona | 작업 역할 | Gemini API 설정 제약 | 주입되는 스킬 카드 및 규칙 |
| :--- | :--- | :--- | :--- |
| **requirements** | 요구사항 분석가 | `temperature: 0.1`<br>`maxOutputTokens: 8192` | `traceability-review_GEMINI.md`<br>요구사항 정의 표준 규칙 |
| **design** | 시스템 설계자 | `temperature: 0.1`<br>`maxOutputTokens: 16384` | `screen-design_GEMINI.md`<br>프로그램/API/DB/보안 설계 가이드 |
| **build** | 빌드 워커 | `temperature: 0.0`<br>`maxOutputTokens: 16384` | `build-wave_GEMINI.md`<br>`RUN_INPUT_CONTRACT_GEMINI.md` |
| **review** | 독립 검수자 | `temperature: 0.1`<br>`maxOutputTokens: 8192` | `ui-review_GEMINI.md`<br>`development-standard-review_GEMINI.md` |

---

## 2. 런타임 구동 엔진 바인딩 YAML 프로토콜

프레임워크의 구동기(`vulcan.py` 등)가 Gemini API 호출용 Payload를 빌드할 때 사용하는 매핑 정의 파일의 구조입니다.

```yaml
persona_configurations:
  requirements:
    model: "gemini-1.5-pro-latest"
    system_instruction_ref: "docs/adapters/gemini/GATE_PROMPTS_GEMINI.md#gemini_prompts.gate1.system_instruction"
    generation_config:
      temperature: 0.1
      topP: 0.95
      responseMimeType: "application/json"
      # Output 스키마 강제
      responseSchema:
        type: "OBJECT"
        properties:
          requirements_list:
            type: "ARRAY"
            items:
              type: "OBJECT"
              properties:
                id: { type: "STRING" }
                text: { type: "STRING" }
                priority: { type: "STRING" }
        required: ["requirements_list"]

  build:
    model: "gemini-1.5-pro-latest"
    system_instruction_ref: "docs/adapters/gemini/GATE_PROMPTS_GEMINI.md#gemini_prompts.impl.system_instruction"
    generation_config:
      temperature: 0.0 # 코드 구현은 극도의 일관성과 결정론적 추론 필수
      topP: 0.1
      responseMimeType: "text/plain" # 실제 소스코드 출력을 위해 플레인 텍스트 허용
```
