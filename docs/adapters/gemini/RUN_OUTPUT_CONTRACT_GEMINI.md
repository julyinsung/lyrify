# Gemini Run Output Contract Binding (GEMINI Standard)

> 상태: v0.1 (Gemini Runner 출력 바인딩 사양)
> 목적: Core 공통 출력 계약([RUN_OUTPUT_CONTRACT_GEMINI.md](file:///c:/Users/user/Documents/antig-workspace/vulcan-anvil-ex/docs/core/RUN_OUTPUT_CONTRACT_GEMINI.md))을 Gemini API의 `Structured Outputs` 기능과 결합하기 위한 스키마 매핑 및 기술 규격을 정의한다.

---

## 1. 연동 전략

* Gemini API는 출력 형식(JSON)을 완벽하게 규제할 수 있는 `responseSchema` 설정을 제공합니다.
* Gemini 어댑터는 워커를 기동할 때, Core의 공통 출력 사양을 아래 정의된 OpenAPI-compliant JSON Schema 형태로 API 호출 파라미터에 탑재하여 호출합니다.
* 이를 통해 마크다운 파싱 오류나 JSON 누락 오류 없이 Core 규격을 이행합니다.

---

## 2. Gemini API Structured Response Schema 설정 명세

런타임 구동 엔진이 Gemini Python SDK/REST API 호출 시 `generation_config` 내에 세팅해야 하는 JSON Schema 정의입니다.

```json
{
  "type": "OBJECT",
  "properties": {
    "run_id": { "type": "STRING" },
    "status": { 
      "type": "STRING", 
      "enum": ["Completed", "Blocked", "Failed", "In Progress"] 
    },
    "completed_at": { "type": "STRING" },
    "changed_files": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "file_path": { "type": "STRING" },
          "status": { "type": "STRING", "enum": ["Created", "Modified", "Deleted"] }
        },
        "required": ["file_path", "status"]
      }
    },
    "related_ids": {
      "type": "ARRAY",
      "items": { "type": "STRING" }
    },
    "standard_compliance_report": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "standard_id": { "type": "STRING" },
          "status": { "type": "STRING", "enum": ["Pass", "Fail", "N/A"] },
          "details": { "type": "STRING" }
        },
        "required": ["standard_id", "status"]
      }
    },
    "verification_results": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "command": { "type": "STRING" },
          "result": { "type": "STRING", "enum": ["passed", "failed", "not_run"] },
          "summary": { "type": "STRING" }
        },
        "required": ["command", "result"]
      }
    },
    "delegation_records": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "mode": { "type": "STRING" },
          "delegate": { "type": "STRING" },
          "native_agent": { "type": "BOOLEAN" },
          "task": { "type": "STRING" },
          "scope": {
            "type": "OBJECT",
            "properties": {
              "writable": { "type": "ARRAY", "items": { "type": "STRING" } }
            },
            "required": ["writable"]
          },
          "started_at": { "type": "STRING" },
          "completed_at": { "type": "STRING" },
          "status": { "type": "STRING" },
          "changed_files": { "type": "ARRAY", "items": { "type": "STRING" } },
          "result_summary": { "type": "STRING" },
          "orchestrator_verification": {
            "type": "ARRAY",
            "items": {
              "type": "OBJECT",
              "properties": {
                "command": { "type": "STRING" },
                "result": { "type": "STRING" }
              },
              "required": ["command", "result"]
            }
          }
        },
        "required": ["mode", "delegate", "task", "status", "changed_files", "result_summary"]
      }
    },
    "orchestrator_decision_needed": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "item": { "type": "STRING" },
          "reason": { "type": "STRING" }
        },
        "required": ["item", "reason"]
      }
    },
    "open_issues": { "type": "ARRAY", "items": { "type": "STRING" } },
    "findings": { "type": "ARRAY", "items": { "type": "STRING" } },
    "change_requests": { "type": "ARRAY", "items": { "type": "STRING" } }
  },
  "required": ["run_id", "status", "completed_at", "changed_files", "related_ids"]
}
```
