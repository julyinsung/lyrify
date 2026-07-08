# Vulcan-Anvil Ex Adapters Evaluation & Gemini Standard

> 상태: v0.1 (Gemini & Multi-Worker 관점의 어댑터 검토 의견서)
> 목적: 현재 `docs/adapters/` 하위의 문서 및 폴더 구조가 가진 아키텍처적 유효성을 분석하고, 이를 Gemini 기반으로 고도화하여 실제 프레임워크 런타임에 기계적으로 결합할 수 있는 표준화 방안을 정의한다.

---

## 1. 어댑터(Adapter) 문서 구조의 유효성 평가

현재 `docs/adapters/` 하위의 각 도구별(`claude`, `codex-gpt`) 문서들은 **프레임워크의 확장성과 일관성 통제 측면에서 매우 강력하고 유효한 의미**를 가집니다.

### ① 핵심 가치: 느슨한 결합(Decoupling)을 통한 핵심 통제권 유지

* **의미**: 프로젝트 거버넌스(Gate, Traceability, QA, Security)는 `docs/core/`에 완결된 형태로 존재합니다.
* **효과**: 만약 에이전트 구동에 필요한 프롬프트나 CLI 옵션이 Core에 섞이게 되면, 특정 LLM 엔진을 업그레이드하거나 교체할 때 핵심 비즈니스 로직(Gate 규칙 등)까지 흔들리는 사이드 이펙트가 발생합니다. 어댑터 디렉토리는 이를 방지하는 **방화벽** 역할을 합니다.

### ② 모델별 한계 보완 (`LIMITATIONS.md` 및 `GATE_PROMPTS.md`)

* **의미**: Claude(MCP 기반, XML 태그 친화적), Codex(YAML 및 정적 API 지향), Gemini(대규모 컨텍스트 및 JSON Schema 강제) 등 모델의 핵심 행동 양식과 한계점이 다릅니다.
* **효과**: 모델의 단점을 극복하는 전용 프롬프트 및 예외 지침을 제공하여, 최종 산출물은 Core 표준 규격으로 일관되게 출력되도록 보장합니다.

---

## 2. 한계점 및 실효성 개선 방안 (Gemini 관점)

현재의 문서 구조가 "단순히 워커가 인간적으로 읽는 텍스트 가이드"에 그친다면 유지관리 비용만 커집니다. 어댑터 문서들이 200%의 실효성을 가지기 위해 다음과 같은 표준화 및 개선이 필요합니다.

### 📌 개선 1. 런타임(Automation Engine) 바인딩 구조의 표준화

* **현황**: `GATE_PROMPTS.md` 등이 장문의 프리텍스트(Free-text) 마크다운으로 적혀 있어, `vulcan.py` 같은 프레임워크 구동 코드가 이를 기계적으로 로드하기 어렵습니다.
* **개선**: 프롬프트 문서 내부를 **JSON/YAML 구조 블록**으로 선언하여 런타임 구동 엔진이 API 호출 시 `System Prompt` 또는 `User Content Prefix`로 자동 로드할 수 있도록 파싱 포맷을 표준화해야 합니다.

### 📌 개선 2. Gemini(Antigravity) 어댑터의 신설

* **현황**: Gemini 어댑터 디렉토리와 관련 사양이 비어 있습니다.
* **개선**: Gemini의 강력한 스펙(100만+ Token Context window, 엄격한 JSON Schema 준수)에 특화된 어댑터 스펙을 표준화하여 정의해야 합니다.

---

## 3. [NEW] Gemini Adapter 표준 규격 및 파일 가이드라인

향후 추가될 `docs/adapters/gemini/` 하위의 최소 산출물과 그 구현 스펙은 다음과 같이 구성합니다.

### 1) `docs/adapters/gemini/README.md`

Gemini 엔진을 Vulcan-Anvil Ex 프레임워크의 워커/오케스트레이터로 바인딩할 때의 범위와 연동 구조를 정의합니다.

* **핵심 강점 활용**: Gemini API의 `Structured Outputs` 기능을 강제 설정하여 Core 규약(`RUN_INPUT_CONTRACT_GEMINI.md`)의 YAML/JSON 출력을 100% 무결하게 정형화합니다.

### 2) `docs/adapters/gemini/LIMITATIONS.md`

Gemini의 고유 특성과 한계점을 정의하고 극복 방안을 규약화합니다.

* **컨텍스트 강점 활용**: 코드베이스 전체 및 모든 상류 설계 문서를 한 번에 컨텍스트로 제공해도 성능 저하가 없는 장점을 명시하고, 파일 탐색 횟수를 줄이는 대신 한 번의 컨텍스트 임베딩으로 정확한 코드 일치를 도출하도록 지시합니다.
* **안전 제약**: 멀티 에이전트 환경에서 API 호출 시 발생하는 레이턴시 스파이크 및 동시성 제어 한계를 명시합니다.

### 3) `docs/adapters/gemini/GATE_PROMPTS.md` (기계적 파싱 지원 포맷)

Gemini가 읽어야 할 게이트별 프롬프트 구조입니다. 기계적 파싱이 가능하도록 JSON 블록을 포함합니다.

```json
{
  "adapter": "gemini",
  "gate_prompts": {
    "gate2": {
      "system_reminder": "너는 Vulcan-Anvil Ex Gate 2 설계 검수자다. 반드시 DOC-CORE-G2-002 명세의 Interface Signature가 일치하는지 정적 대조하라.",
      "structured_output_required": true
    },
    "impl": {
      "system_reminder": "너는 Gemini build worker다. target_contracts.interface_contract에 명시된 시그니처와 구현 코드가 한 자의 오차도 없이 일치해야 한다.",
      "structured_output_required": false
    }
  }
}
```

### 4) `docs/adapters/gemini/PERSONA_MAPPING.md`

Core의 `requirements`, `design`, `build`, `review` 페르소나를 Gemini의 각 인스턴스(시스템 인스트럭션 템플릿)와 매핑하는 설정을 정의합니다.
