#!/usr/bin/env python3
"""
Vulcan-Anvil Ex - 5-Gate AI 협업 개발 프레임워크

대장장이 신 Vulcan처럼, 에이전트 팀을 단련하여 체계적으로 프로젝트를 완성합니다.
Agent-Forge의 5-Gate 프로세스를 Claude Code 네이티브 하네스(.claude/) 구조로 재구현.

명령어:
  init         새 프로젝트 초기화
  session      Gate 상태 업데이트 + git commit 자동 생성
  check-trace  Gate별 정합성 검사
  export       snapshot.json 생성 (대시보드용)
  upgrade      프레임워크 파일을 최신 버전으로 업데이트
  version      현재 프레임워크 버전 확인

사용법:
  # 초기화 (Vulcan-Anvil 디렉토리에서 실행)
  python vulcan.py init <target-dir> <project-name> [--agent-name NAME] [--remote GIT_URL] [--require-remote]

  # 이하 명령은 프로젝트 디렉토리에서 실행
  python vulcan.py check-trace
  python vulcan.py session --gate gate1 --status awaiting-approval --feature "로그인 기능"
  python vulcan.py session --gate gate1 --status done --approved --approval-evidence "사용자 승인"
  python vulcan.py export [--output snapshot.json]
  python vulcan.py upgrade
"""

import argparse
import ast
import contextlib
import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import date, datetime, timedelta

# Windows 콘솔 UTF-8 출력 보장
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VULCAN_VERSION = "0.4.9"

VULCAN_DIR = os.path.dirname(os.path.abspath(__file__))


CODEX_MODEL_POLICY_DEFAULTS = {
    "enabled": True,
    "fallback": {
        "model": "gpt-5.5",
        "effort": "high",
    },
    "roles": {
        "review": {
            "model": "gpt-5.5",
            "effort": "high",
            "description": "독립 검수, 설계/QA 정합성 검토",
        },
        "critical_judgment": {
            "model": "gpt-5.5",
            "effort": "high",
            "description": "Gate 승인 후보, FIND/CR 분류, 릴리즈 판단 후보",
        },
        "build": {
            "model": "gpt-5.5",
            "effort": "high",
            "description": "일반 구현 worker",
        },
        "build-backend": {
            "model": "gpt-5.5",
            "effort": "high",
            "description": "Backend/API/DB 구현 worker",
        },
        "build-frontend": {
            "model": "gpt-5.5",
            "effort": "high",
            "description": "Frontend/UI 구현 worker",
        },
        "qa-execution": {
            "model": "gpt-5.4",
            "effort": "medium",
            "description": "QA 명령 실행, 로그 수집, 결과 정리",
        },
        "qa-fix-loop": {
            "model": "gpt-5.5",
            "effort": "high",
            "description": "승인된 FIND 범위 안의 QA 수정 worker",
        },
        "run-draft": {
            "model": "gpt-5.4-mini",
            "effort": "medium",
            "description": "Run 초안, trace-context 후보, 문서 정리",
        },
        "evidence-summary": {
            "model": "gpt-5.4-mini",
            "effort": "low",
            "description": "로그/증적 index, 단순 요약",
        },
    },
}

CODEX_MODEL_FALLBACKS = {
    "gpt-5.3-codex": {
        "model": "gpt-5.5",
        "reason": "gpt-5.3-codex is not supported by the current Codex CLI account; using gpt-5.5",
    },
}


def _bootstrap_vulcan_core():
    local_core = os.path.join(VULCAN_DIR, "vulcan_core")
    if os.path.isdir(local_core):
        return
    session_path = os.path.join(VULCAN_DIR, "session.json")
    try:
        with open(session_path, encoding="utf-8") as f:
            session = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    source_root = session.get("vulcan_src")
    if not source_root:
        return
    source_core = os.path.join(source_root, "vulcan_core")
    if os.path.isdir(source_core) and source_root not in sys.path:
        sys.path.insert(0, source_root)


_bootstrap_vulcan_core()

from vulcan_core.runners import (
    EXEC_RUNNERS,
    INDEPENDENT_REVIEW_EXEC_RUNNERS,
    INDEPENDENT_REVIEW_RUNNERS,
    antigravity_executable,
    default_execution_branch,
    default_execution_worktree_path,
    detect_runtime_runners,
    normalize_exec_runner,
    runner_empty_output,
    runner_log_ext,
    runner_log_slug,
    runner_model_source,
    runtime_role_runner,
    runtime_runner_config,
)

TEMPLATES_DIR = os.path.join(VULCAN_DIR, "templates")
PROJECT_DOC_SETS = [
    ".agents",
    ".codex/agents",
    ".gemini/agents",
    "docs/core",
    "docs/templates",
    "docs/adapters",
    "docs/seed-docs",
]
PROJECT_DOC_DIRS = [
    "docs/poc",
    "docs/artifacts/00-discovery",
    "docs/artifacts/01-requirements",
    "docs/artifacts/02-traceability",
    "docs/artifacts/02-design/architecture",
    "docs/artifacts/02-design/function",
    "docs/artifacts/02-design/program",
    "docs/artifacts/02-design/api",
    "docs/artifacts/02-design/screen",
    "docs/artifacts/02-design/screen/images",
    "docs/artifacts/02-design/screen/ui-baseline",
    "docs/artifacts/02-design/data",
    "docs/artifacts/02-design/data/erd",
    "docs/artifacts/02-design/data/erd/logical",
    "docs/artifacts/02-design/data/erd/physical",
    "docs/artifacts/02-design/data/erd/exports",
    "docs/artifacts/02-design/security",
    "docs/artifacts/02-design/development-standard",
    "docs/artifacts/03-test",
    "docs/artifacts/04-review",
    "docs/artifacts/04-review/evidence",
    "docs/artifacts/04-review/evidence/ui",
    "docs/artifacts/05-change",
    "docs/artifacts/07-release",
    "docs/runs",
    "docs/reviews",
    "docs/ref-docs",
]
PROJECT_ARTIFACT_TEMPLATES = [
    ("docs/templates/PROJECT_BRIEF_TEMPLATE.md", "docs/artifacts/00-discovery/DOC-CORE-P0-001_Project-Brief_v0.1.md"),
    ("docs/templates/STAKEHOLDER_SCOPE_TEMPLATE.md", "docs/artifacts/00-discovery/DOC-CORE-P0-002_Stakeholder-And-Scope_v0.1.md"),
    ("docs/templates/AS_IS_TO_BE_TEMPLATE.md", "docs/artifacts/00-discovery/DOC-CORE-P0-003_As-Is-To-Be_v0.1.md"),
    ("docs/templates/RISK_ASSUMPTION_TEMPLATE.md", "docs/artifacts/00-discovery/DOC-CORE-P0-004_Risk-And-Assumption_v0.1.md"),
    ("docs/templates/REQUIREMENTS_SPEC_TEMPLATE.md", "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md"),
    ("docs/templates/TRACEABILITY_MATRIX_TEMPLATE.md", "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md"),
    ("docs/templates/SW_ARCHITECTURE_TEMPLATE.md", "docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md"),
    ("docs/templates/DEPLOYMENT_INFRASTRUCTURE_ARCHITECTURE_TEMPLATE.md", "docs/artifacts/02-design/architecture/DOC-ARCH-G2-002_Deployment-Infrastructure-Architecture_v0.1.md"),
    ("docs/templates/FUNCTION_SPEC_TEMPLATE.md", "docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md"),
    ("docs/templates/PROGRAM_SPEC_TEMPLATE.md", "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md"),
    ("docs/templates/API_SPEC_TEMPLATE.md", "docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md"),
    ("docs/templates/SCREEN_SPEC_TEMPLATE.md", "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md"),
    ("docs/templates/PROJECT_GLOSSARY_TEMPLATE.md", "docs/artifacts/02-design/data/DOC-DATA-G2-001_Project-Glossary_v0.1.md"),
    ("docs/templates/DATABASE_SPEC_TEMPLATE.md", "docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md"),
    ("docs/templates/LOGICAL_ERD_DBML_TEMPLATE.dbml", "docs/artifacts/02-design/data/erd/logical/logical-erd.dbml"),
    ("docs/templates/PHYSICAL_ERD_DBML_TEMPLATE.dbml", "docs/artifacts/02-design/data/erd/physical/physical-erd.dbml"),
    ("docs/templates/SECURITY_GUIDE_TEMPLATE.md", "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md"),
    ("docs/templates/DEVELOPMENT_STANDARD_TEMPLATE.md", "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md"),
    ("docs/templates/TEST_CASE_TEMPLATE.md", "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md"),
    ("docs/templates/QA_FINDING_TEMPLATE.md", "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md"),
    ("docs/templates/TEST_RESULT_TEMPLATE.md", "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md"),
    ("docs/templates/CHANGE_REQUEST_TEMPLATE.md", "docs/artifacts/05-change/DOC-PM-G0-001_Change-Request_v0.1.md"),
    ("docs/templates/RELEASE_APPROVAL_TEMPLATE.md", "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md"),
]
POC_ARTIFACT_TEMPLATES = [
    ("docs/templates/poc/POC_REQUIREMENTS_TEMPLATE.md", "docs/poc/POC_REQUIREMENTS.md"),
    ("docs/templates/poc/POC_SYSTEM_DESIGN_TEMPLATE.md", "docs/poc/POC_SYSTEM_DESIGN.md"),
    ("docs/templates/poc/POC_TEST_REPORT_TEMPLATE.md", "docs/poc/POC_TEST_REPORT.md"),
]
PRODUCT_ARTIFACT_TEMPLATES = [
    ("docs/templates/product/PRODUCT_BRIEF_TEMPLATE.md", "docs/product/PRODUCT_BRIEF.md"),
    ("docs/templates/product/PRODUCT_ARCHITECTURE_TEMPLATE.md", "docs/product/PRODUCT_ARCHITECTURE.md"),
    ("docs/templates/product/ADR_LOG_TEMPLATE.md", "docs/product/ADR_LOG.md"),
    ("docs/templates/product/PRODUCT_CONTRACTS_TEMPLATE.md", "docs/product/PRODUCT_CONTRACTS.md"),
    ("docs/templates/product/PRODUCT_TRACEABILITY_TEMPLATE.md", "docs/product/PRODUCT_TRACEABILITY.md"),
    ("docs/templates/product/REGRESSION_AND_RELEASE_REPORT_TEMPLATE.md", "docs/product/REGRESSION_AND_RELEASE_REPORT.md"),
]
POC_REQUIRED_ARTIFACTS_BY_GATE = {
    "phase0": ["docs/poc/POC_REQUIREMENTS.md"],
    "gate1": ["docs/poc/POC_REQUIREMENTS.md"],
    "gate2": ["docs/poc/POC_REQUIREMENTS.md", "docs/poc/POC_SYSTEM_DESIGN.md"],
    "gate3": ["docs/poc/POC_REQUIREMENTS.md", "docs/poc/POC_SYSTEM_DESIGN.md", "docs/poc/POC_TEST_REPORT.md"],
    "impl": ["docs/poc/POC_REQUIREMENTS.md", "docs/poc/POC_SYSTEM_DESIGN.md", "docs/poc/POC_TEST_REPORT.md"],
    "gate4": ["docs/poc/POC_REQUIREMENTS.md", "docs/poc/POC_SYSTEM_DESIGN.md", "docs/poc/POC_TEST_REPORT.md"],
    "gate5": ["docs/poc/POC_REQUIREMENTS.md", "docs/poc/POC_SYSTEM_DESIGN.md", "docs/poc/POC_TEST_REPORT.md"],
    "completed": ["docs/poc/POC_REQUIREMENTS.md", "docs/poc/POC_SYSTEM_DESIGN.md", "docs/poc/POC_TEST_REPORT.md"],
}
PRODUCT_REQUIRED_ARTIFACTS_BY_GATE = {
    "phase0": ["docs/product/PRODUCT_BRIEF.md"],
    "gate1": ["docs/product/PRODUCT_BRIEF.md"],
    "gate2": [
        "docs/product/PRODUCT_BRIEF.md",
        "docs/product/PRODUCT_ARCHITECTURE.md",
        "docs/product/ADR_LOG.md",
        "docs/product/PRODUCT_CONTRACTS.md",
    ],
    "gate3": [
        "docs/product/PRODUCT_BRIEF.md",
        "docs/product/PRODUCT_ARCHITECTURE.md",
        "docs/product/ADR_LOG.md",
        "docs/product/PRODUCT_CONTRACTS.md",
        "docs/product/PRODUCT_TRACEABILITY.md",
        "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
    ],
    "impl": [
        "docs/product/PRODUCT_BRIEF.md",
        "docs/product/PRODUCT_ARCHITECTURE.md",
        "docs/product/ADR_LOG.md",
        "docs/product/PRODUCT_CONTRACTS.md",
        "docs/product/PRODUCT_TRACEABILITY.md",
        "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
    ],
    "gate4": [
        "docs/product/PRODUCT_BRIEF.md",
        "docs/product/PRODUCT_ARCHITECTURE.md",
        "docs/product/ADR_LOG.md",
        "docs/product/PRODUCT_CONTRACTS.md",
        "docs/product/PRODUCT_TRACEABILITY.md",
        "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
    ],
    "gate5": [
        "docs/product/PRODUCT_BRIEF.md",
        "docs/product/PRODUCT_ARCHITECTURE.md",
        "docs/product/ADR_LOG.md",
        "docs/product/PRODUCT_CONTRACTS.md",
        "docs/product/PRODUCT_TRACEABILITY.md",
        "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
        "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md",
    ],
    "completed": [
        "docs/product/PRODUCT_BRIEF.md",
        "docs/product/PRODUCT_ARCHITECTURE.md",
        "docs/product/ADR_LOG.md",
        "docs/product/PRODUCT_CONTRACTS.md",
        "docs/product/PRODUCT_TRACEABILITY.md",
        "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
        "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md",
    ],
}
PROFILE_GAP_RULES = {
    "product": [
        {
            "id": "product_brief",
            "title": "Product brief",
            "ok_any": [
                "docs/product/PRODUCT_BRIEF.md",
                "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            ],
            "partial_any": ["docs/poc/POC_REQUIREMENTS.md"],
            "recommendation": "목표, 사용자, 핵심 시나리오, 비목표, 성공 기준을 Product 관점으로 정리합니다.",
        },
        {
            "id": "product_architecture",
            "title": "Product architecture",
            "ok_any": [
                "docs/product/PRODUCT_ARCHITECTURE.md",
                "docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md",
            ],
            "partial_any": ["docs/poc/POC_SYSTEM_DESIGN.md"],
            "recommendation": "주요 컴포넌트, 런타임, 배포/운영 경계, 품질속성을 정리합니다.",
        },
        {
            "id": "adr",
            "title": "ADR log",
            "ok_any": [
                "docs/product/ADR_LOG.md",
                "docs/artifacts/02-design/architecture/ADR_LOG.md",
                "docs/artifacts/02-design/architecture/adr/README.md",
            ],
            "partial_any": [
                "docs/product/PRODUCT_ARCHITECTURE.md",
                "docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md",
                "docs/poc/POC_SYSTEM_DESIGN.md",
            ],
            "recommendation": "기술/구조 선택 이유와 대안을 ADR로 남깁니다.",
        },
        {
            "id": "product_contracts",
            "title": "Product contracts",
            "ok_any": ["docs/product/PRODUCT_CONTRACTS.md"],
            "ok_all": [
                "docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md",
                "docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md",
                "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
            ],
            "partial_any": [
                "docs/poc/POC_SYSTEM_DESIGN.md",
                "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
                "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
            ],
            "recommendation": "API/DB/UI/Security/Data 계약의 진입점 또는 상세 설계 링크를 정리합니다.",
        },
        {
            "id": "regression_release",
            "title": "Regression and release report",
            "ok_any": [
                "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
                "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
            ],
            "partial_any": [
                "docs/poc/POC_TEST_REPORT.md",
                "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
            ],
            "recommendation": "반복 실행할 회귀 테스트와 릴리즈 판단 근거를 정리합니다.",
        },
        {
            "id": "traceability",
            "title": "Release traceability",
            "ok_any": [
                "docs/product/PRODUCT_TRACEABILITY.md",
                "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            ],
            "partial_any": ["docs/poc/POC_TEST_REPORT.md"],
            "recommendation": "핵심 시나리오 -> 계약 -> 구현 -> 테스트 -> 릴리즈 근거를 연결합니다.",
        },
    ],
    "audit": [
        {
            "id": "requirements",
            "title": "Requirements and traceability",
            "ok_all": [
                "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
                "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            ],
            "partial_any": ["docs/product/PRODUCT_BRIEF.md", "docs/poc/POC_REQUIREMENTS.md"],
            "recommendation": "REQ/NREQ/AC와 추적표를 공식 산출물로 분리합니다.",
        },
        {
            "id": "design",
            "title": "Full design artifacts",
            "ok_all": [
                "docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md",
                "docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md",
                "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
                "docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md",
                "docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md",
                "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
            ],
            "partial_any": ["docs/product/PRODUCT_ARCHITECTURE.md", "docs/product/PRODUCT_CONTRACTS.md", "docs/poc/POC_SYSTEM_DESIGN.md"],
            "recommendation": "아키텍처, 기능, 프로그램, API, DB, 보안 설계를 Audit 산출물로 확장합니다.",
        },
        {
            "id": "security_mapping",
            "title": "Security standard mapping",
            "ok_any": ["docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md"],
            "partial_any": ["docs/core/SECURITY_BASELINE.md", "docs/core/PRODUCT_PROFILE_BASELINE.md"],
            "recommendation": "KISA/SR, 고객/공공 기준, OWASP/CWE를 SEC-ID와 테스트 증적에 연결합니다.",
        },
        {
            "id": "data_standard",
            "title": "Data standard mapping",
            "ok_all": [
                "docs/artifacts/02-design/data/DOC-DATA-G2-001_Project-Glossary_v0.1.md",
                "docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md",
            ],
            "partial_any": ["docs/core/DATA_STANDARD_RULES.md", "docs/product/PRODUCT_CONTRACTS.md", "docs/poc/POC_SYSTEM_DESIGN.md"],
            "recommendation": "단어사전, 데이터 도메인, 공공데이터 공통표준 준용/변형/신규 사유를 정리합니다.",
        },
        {
            "id": "test_qa",
            "title": "Test plan and QA evidence",
            "ok_all": [
                "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
                "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
                "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
            ],
            "partial_any": ["docs/product/REGRESSION_AND_RELEASE_REPORT.md", "docs/poc/POC_TEST_REPORT.md"],
            "recommendation": "Gate 3 테스트 계획과 Gate 4 결과/증적/FIND를 분리해 정리합니다.",
        },
        {
            "id": "release_control",
            "title": "Change and release records",
            "ok_any": [
                "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md",
                "docs/product/RELEASE_SCOPE.md",
            ],
            "partial_any": ["docs/artifacts/05-change/DOC-PM-G0-001_Change-Request_v0.1.md", "docs/product/REGRESSION_AND_RELEASE_REPORT.md"],
            "recommendation": "FIND/CR/ISSUE, 릴리즈 승인, known issue, 잔여 리스크를 정리합니다.",
        },
    ],
}
PROJECT_ROOT_FILES = [
    "AGENTS.md",
    "GEMINI.md",
]
RUN_SKILLS = {
    "orchestrator-plan": "docs/core/ORCHESTRATOR_PROTOCOL.md",
    "persona-run": "docs/core/AGENT_RUN_PROTOCOL.md",
    "traceability-review": "docs/adapters/codex-gpt/skills/traceability-review.md",
    "screen-design": "docs/adapters/codex-gpt/skills/screen-design.md",
    "security-review": "docs/adapters/codex-gpt/skills/security-review.md",
    "screen-review": "docs/adapters/codex-gpt/skills/screen-review.md",
    "ui-review": "docs/adapters/codex-gpt/skills/ui-review.md",
    "development-standard-review": "docs/adapters/codex-gpt/skills/development-standard-review.md",
    "implementation-plan": "docs/adapters/codex-gpt/skills/implementation-plan.md",
    "implementation-scaffold": "docs/adapters/codex-gpt/skills/implementation-scaffold.md",
    "build-wave": "docs/adapters/codex-gpt/skills/build-wave.md",
    "data-standard-review": "docs/adapters/codex-gpt/skills/data-standard-review.md",
    "qa-execution": "docs/adapters/codex-gpt/skills/qa-execution.md",
    "qa-fix-loop": "docs/adapters/codex-gpt/skills/qa-fix-loop.md",
    "change-impact-analysis": "docs/adapters/codex-gpt/skills/change-impact-analysis.md",
    "handoff": "docs/core/ORCHESTRATOR_PROTOCOL.md",
    "independent-review": "docs/adapters/codex-gpt/skills/independent-review.md",
}
RUN_PERSONAS = {
    "discovery": "배경, 제약, 현행 자료, 질문, 위험을 정리한다.",
    "requirements": "요구사항, 비기능 요구사항, 인수기준을 정리한다.",
    "design": "기능, 화면, 프로그램, DB, 보안 설계를 작성한다.",
    "screen-design": "화면 구조, 시안, 와이어프레임, UI 기준 증적을 설계한다.",
    "security-review": "보안 요구사항, 보안설계, 시큐어코딩 기준 누락을 검토한다.",
    "screen-review": "화면 식별, 화면상태, 와이어프레임, UI 증적 기준 누락을 검토한다.",
    "ui-review": "구현자가 좋은 화면을 만들 수 있을 만큼 UI 기준선이 충분한지 검토한다.",
    "development-review": "개발표준, 패키지 구조, 코딩/주석/테스트 컨벤션 확정 여부를 검토한다.",
    "test-design": "AC, SEC, NREQ를 검증 가능한 테스트로 전개한다.",
    "build-planning": "승인된 설계와 테스트 기준을 구현 가능한 Build Wave로 나눈다.",
    "build": "승인된 설계를 코드, 설정, 테스트 코드로 구현한다.",
    "evidence": "테스트 결과, 화면 캡처, 로그 등 증적을 만든다.",
    "review": "추적성, 보안, 품질, 설계 준수 여부를 검토한다.",
    "release": "승인 후보, 릴리즈 범위, 인수인계 항목을 정리한다.",
    "change-control": "변경요청 영향도와 다시 진행할 Gate를 판단한다.",
    "documentation": "용어, 문서 버전, 산출물 일관성을 정리한다.",
}
RUN_SKILL_DEFAULT_PERSONAS = {
    "orchestrator-plan": "documentation",
    "persona-run": "",
    "traceability-review": "review",
    "screen-design": "screen-design",
    "security-review": "review",
    "screen-review": "screen-review",
    "ui-review": "ui-review",
    "development-standard-review": "development-review",
    "implementation-plan": "build-planning",
    "implementation-scaffold": "build",
    "build-wave": "build",
    "data-standard-review": "review",
    "qa-execution": "evidence",
    "qa-fix-loop": "build",
    "change-impact-analysis": "change-control",
    "handoff": "review",
    "independent-review": "review",
}
GATE_DEFAULT_PERSONAS = {
    "phase0": "discovery",
    "gate1": "requirements",
    "gate2": "design",
    "gate3": "test-design",
    "impl": "build",
    "gate4": "review",
    "gate5": "release",
}
HANDOFF_TARGETS = ["cli", "desktop", "github", "codex-review", "claude", "manual"]
INDEPENDENT_REVIEW_DEFAULT_GATES = ["gate2", "gate4"]
RUN_REQUIRED_KEYS = [
    "run_id",
    "adapter",
    "persona",
    "status",
    "skill",
    "related_ids",
    "verification_results",
    "evidence",
    "traceability_updates",
    "open_issues",
]

GATE_LABELS = {
    "phase0": "Phase 0 Discovery",
    "gate1": "Gate 1 요구사항",
    "gate2": "Gate 2 설계",
    "gate3": "Gate 3 테스트 플랜",
    "impl":  "구현",
    "gate4": "Gate 4 QA 검토",
    "gate5": "Gate 5 최종 승인",
}

GATE_ORDER = ["phase0", "gate1", "gate2", "gate3", "impl", "gate4", "gate5"]
DEFAULT_DELIVERY_PROFILE = "audit"
SUPPORTED_DELIVERY_PROFILES = ("audit", "product", "poc")
DELIVERY_PROFILE_ALIASES = {
    "solution": "product",
}
DELIVERY_PROFILE_RULES = {
    "audit": {
        "gate_approval": "all-gates-explicit",
        "required_artifacts": "full-audit-set",
        "traceability_level": "full",
        "program_contract_level": "class-interface-public-method",
        "security_standard_level": "kisa-public-customer-plus-owasp-cwe",
        "data_standard_level": "public-data-standard-plus-project-glossary",
        "qa_evidence_level": "qa-000-to-qa-003-command-ui-log-finding",
        "independent_review_level": "gate2-gate4-pr-as-needed",
        "run_preflight_strictness": "blocking",
        "release_control": "gate5-release-approval-pr",
    },
    "product": {
        "gate_approval": "major-gates-and-release",
        "required_artifacts": "architecture-api-db-security-release-core",
        "traceability_level": "core-requirement-api-db-security-regression",
        "program_contract_level": "public-api-service-dto",
        "security_standard_level": "owasp-asvs-top10-api-top10-cwe",
        "data_standard_level": "project-glossary-field-domain-security-classification",
        "qa_evidence_level": "release-regression-major-ui-api",
        "independent_review_level": "release-candidate-or-large-change",
        "run_preflight_strictness": "scope-contract-blocking-other-warning",
        "release_control": "release-note-backlog-pr",
    },
    "poc": {
        "gate_approval": "start-checkpoint-finish",
        "required_artifacts": "poc-requirements-system-design-test-report",
        "traceability_level": "hypothesis-to-implementation-to-result",
        "program_contract_level": "main-interface-entrypoint",
        "security_standard_level": "risk-identification-and-productization-gap",
        "data_standard_level": "core-fields-and-sensitive-data-identification",
        "qa_evidence_level": "smoke-demo-log",
        "independent_review_level": "optional",
        "run_preflight_strictness": "warning-first",
        "release_control": "poc-result-summary",
    },
}

RUN_TYPES_BY_GATE = {
    "phase0": "Discovery",
    "gate1": "Requirements",
    "gate2": "Design",
    "gate3": "Test",
    "impl": "Implementation",
    "gate4": "Review",
    "gate5": "Approval",
}

AUDIT_COMMON_READ_FIRST_DOCS = [
    "AGENTS.md",
    "session.json",
    "docs/core/GATE_EXECUTION_CHECKLIST.md",
    "docs/core/TRACEABILITY_RULES.md",
]

ADAPTER_READ_FIRST_DOCS = {
    "codex": ["docs/adapters/codex-gpt/GATE_PROMPTS.md"],
    "codex-cli": ["docs/adapters/codex-gpt/GATE_PROMPTS.md"],
    "codex-gpt": ["docs/adapters/codex-gpt/GATE_PROMPTS.md"],
    "gemini": ["docs/adapters/gemini/GATE_PROMPTS_GEMINI.md"],
    "antigravity": ["docs/adapters/gemini/GATE_PROMPTS_GEMINI.md"],
    "antigravity-cli": ["docs/adapters/gemini/GATE_PROMPTS_GEMINI.md"],
    "agy": ["docs/adapters/gemini/GATE_PROMPTS_GEMINI.md"],
    "claude": ["docs/adapters/claude/GATE_PROMPTS.md"],
    "claude-cli": ["docs/adapters/claude/GATE_PROMPTS.md"],
}

AUDIT_GATE_READ_FIRST_DOCS = {
    "gate2": [
        "docs/core/GATE2_DESIGN_SEQUENCE.md",
    ],
}

AUDIT_COMMON_REFERENCE_DOCS = [
    "docs/core/ID_SYSTEM.md",
    "docs/core/ORCHESTRATOR_PROTOCOL.md",
    "docs/core/AGENT_PERSONAS.md",
    "docs/core/AGENT_RUN_PROTOCOL.md",
    "docs/core/DELIVERY_PROFILES.md",
    "docs/core/RUN_INPUT_CONTRACT.md",
    "docs/core/RUN_OUTPUT_CONTRACT.md",
]

AUDIT_COMMON_READONLY_DOCS = [
    "docs/core/",
    "docs/templates/",
    "docs/seed-docs/reference-standards/",
]

AUDIT_COMMON_EXCLUDED_PATHS = [
    "docs/ref-docs/",
    "**/*.db",
    "**/__pycache__/",
    "**/.ruff_cache/",
]

AUDIT_GATE_ANCHOR_DOCS = {
    "gate1": [
        "docs/artifacts/00-discovery/DOC-CORE-P0-001_Project-Brief_v0.1.md",
        "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
        "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
    ],
    "gate2": [
        "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
        "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
    ],
    "gate3": [
        "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
        "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
        "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
    ],
    "impl": [
        "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
        "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
        "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
    ],
    "gate4": [
        "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
        "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
    ],
    "gate5": [
        "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
        "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
        "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md",
    ],
}

AUDIT_FOCUSED_SOURCE_SKILLS = {
    "traceability-review",
    "independent-review",
    "handoff",
}

AUDIT_DESIGN_SEQUENCE_SKILLS = {
    "screen-design",
    "screen-review",
    "ui-review",
    "development-standard-review",
    "data-standard-review",
    "security-review",
}

AUDIT_UI_POLICY_SKILLS = {
    "screen-design",
    "screen-review",
    "ui-review",
    "implementation-plan",
    "implementation-scaffold",
    "build-wave",
    "qa-execution",
    "qa-fix-loop",
}

AUDIT_GATE_EXIT_POLICY = {
    "stop_required": True,
    "next_gate_requires_user_approval": True,
    "approval_evidence_required": True,
    "allowed_next_action": "현재 Gate 산출물 요약, 미해결 항목, 다음 Gate 진행 승인 질문을 남기고 대기한다.",
    "forbidden_actions": [
        "사용자의 명시 승인 없이 다음 Gate 산출물을 작성하지 않는다.",
        "사용자의 명시 승인 없이 구현, 테스트 실행, QA 승인, 릴리즈 승인을 선언하지 않는다.",
        "대화상 승인 없이 Run 또는 릴리즈 승인서에 User Approved로 기록하지 않는다.",
    ],
}

AUDIT_UI_EVIDENCE_POLICY = {
    "state_level_required": True,
    "id_pattern": "UI-001-01",
    "capture_tool": "Playwright",
    "official_runner": "@playwright/test",
    "official_runner_command": "npx playwright test",
    "official_runner_required_profiles": ["audit", "product"],
    "poc_fallback_allowed": True,
    "install_if_missing": [
        "npx playwright --version",
        "npm install -D @playwright/test",
        "npx playwright install",
    ],
    "required_artifacts": [
        "playwright-report/index.html 또는 동등한 HTML report",
        "test-results/ trace, screenshot, video 중 프로젝트가 선택한 증적",
        "docs/artifacts/04-review/evidence/ui/ 상태별 screenshot",
    ],
    "forbidden_as_pass_evidence": [
        "CDP-only capture",
        "browser manual screenshot without Playwright run",
        "custom Playwright library script without @playwright/test runner in audit/product profile",
    ],
    "fallback_rule": "PoC에서는 커스텀 Playwright script를 smoke/demo 증적으로 허용할 수 있지만, audit/product의 공식 UI Pass는 @playwright/test 실행 결과를 기준으로 한다.",
    "minimum_fields": [
        "UI-ID",
        "관련 SCR",
        "상태/시나리오",
        "입력값",
        "기대 화면",
        "실제 확인",
        "증적 파일",
        "결과",
    ],
    "examples": [
        "UI-001-01 기본 화면 또는 빈 상태",
        "UI-001-02 입력/작성 중 상태",
        "UI-001-03 목록/결과 표시 상태",
        "UI-001-04 완료 또는 상태 변경",
        "UI-001-05 삭제/취소 후 상태",
        "UI-001-06 입력 오류 또는 검증 오류",
    ],
}

AUDIT_UI_IMPLEMENTATION_CONTRACT_POLICY = {
    "required_when": "화면설계서에 UIREF, 이미지 시안, HTML/CSS/JS 화면 퍼블리싱 산출물, Figma, 기존 화면 캡처, ui-baseline 경로가 있는 경우",
    "gate2_required_fields": [
        "기준 파일 또는 URL",
        "기준 CSS 또는 디자인 토큰",
        "필수 유지 요소",
        "변경 허용 항목",
        "변경 금지 항목",
        "구현 비교 방식",
        "차이 발생 시 FIND/CR 판정 기준",
    ],
    "impl_checklist": [
        "구현 전 관련 SCR의 UI Implementation Contract를 확인한다.",
        "화면 퍼블리싱 CSS 또는 동등한 레이아웃/class 구조를 재사용했는지 기록한다.",
        "보안가이드 때문에 바꾼 문구, 필드, 흐름은 DEC/ISSUE/FIND/CR 중 하나로 기록한다.",
        "기본/오류/성공/전환 상태가 Gate 3 UI-ID와 연결되어 있는지 확인한다.",
        "구현 결과 screenshot이 기준 UIREF와 비교 가능한 위치에 저장되는지 확인한다.",
    ],
    "gate4_required_evidence": [
        "기준 UIREF screenshot 또는 ui-baseline 경로",
        "구현 screenshot",
        "차이 목록",
        "허용된 차이 여부",
        "미허용 차이의 FIND 또는 CR",
    ],
}

AUDIT_WORKER_EXECUTION_POLICY = {
    "applies_when": "Run이 subagent, codex-cli, claude-cli, manual worker 등 Orchestrator와 분리된 작업자 runner에게 전달되는 경우",
    "role": "worker-runner",
    "forbidden_actions": [
        "Gate 전환을 수행하지 않는다.",
        "session.json의 current_gate, gate_status, completed를 직접 변경하지 않는다.",
        "사용자 승인, Gate 완료, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 확정하지 않는다.",
        "Run의 scope.writable 밖 파일을 수정하지 않는다.",
        "Orchestrator가 요청하지 않은 신규 Run, PR, 커밋, push를 만들지 않는다.",
        "전역 memory, 과거 세션 요약, 다른 샘플 프로젝트 기억을 현재 Run의 근거로 사용하지 않는다.",
    ],
    "required_outputs": [
        "수행한 변경과 검증 결과를 Run 결과에 남긴다.",
        "Gate 전환, session 변경, 최종 승인 판단이 필요하면 Orchestrator 결정 필요 항목으로 반환한다.",
        "범위 밖 수정이나 기준 충돌이 필요하면 직접 처리하지 않고 open_issues 또는 findings로 남긴다.",
    ],
}

AUDIT_WORKER_RUN_SIZING_POLICY = {
    "primary_split_basis": "기능/계약 단위",
    "time_is_secondary": True,
    "target_duration_minutes": 10,
    "max_duration_minutes": 15,
    "rules": [
        "Run 하나는 FUNC/PGM/API/DB/SEC/TEST ID가 연결된 검증 가능한 완결 단위여야 한다.",
        "Run 하나만 반영해도 빌드 또는 담당 테스트가 깨지지 않아야 한다.",
        "15분을 넘길 것으로 예상되면 개발 중단이 아니라 더 작은 기능/계약 단위로 다시 분리한다.",
        "시간이 끝났다는 이유로 컴파일/테스트가 깨진 반쪽 구현을 완료 처리하지 않는다.",
        "파일/메소드 개수 제한은 시간 판단을 돕는 보조 기준이며 1차 기준이 아니다.",
    ],
}

ORCHESTRATOR_DIRECT_EDIT_LIMITS = {
    "max_files": 2,
    "max_loc": 30,
    "split_files": 3,
    "split_loc": 100,
    "split_minutes": 15,
}

AUDIT_DEVELOPMENT_STANDARDS_APPLIED = [
    {
        "standard_id": "DEV-LOG-001",
        "rule": "표준 logger를 사용하고 민감정보, 토큰, 비밀번호, 내부 stack trace를 로그에 남기지 않는다.",
    },
    {
        "standard_id": "DEV-COMMENT-001",
        "rule": "주요 class와 public 업무 method에는 책임, 입력, 출력, 예외, 관련 ID를 JavaDoc/docstring/주석으로 남긴다.",
    },
    {
        "standard_id": "DEV-TEST-001",
        "rule": "테스트는 UT/IT/UI ID와 사람이 읽을 수 있는 입력값, 기대값, 출력값 또는 Given/When/Then 설명을 가진다.",
    },
]

AUDIT_DEVELOPMENT_STANDARD_CHECKLIST = {
    "logging": {
        "required": True,
        "targets": ["Controller", "Service", "SecurityFilter", "ControllerAdvice", "CoreComponent"],
        "rule": "SLF4J LoggerFactory 또는 프로젝트 표준 logger를 선언하고 민감정보를 로그에 남기지 않는다.",
    },
    "comments": {
        "required": True,
        "targets": ["주요 class", "public 업무 method", "보안/트랜잭션/권한 판단 method"],
        "rule": "책임, 입력, 출력, 예외, 관련 REQ/FUNC/PGM/SEC/UT/IT ID를 JavaDoc/docstring/주석으로 남긴다.",
    },
    "tests": {
        "required": True,
        "targets": ["@Test", "단위 테스트", "통합 테스트", "UI/E2E 테스트"],
        "rule": "테스트 이름의 추적 ID만으로 끝내지 않고 @DisplayName 또는 Given/When/Then으로 입력값, 기대값, 출력값을 설명한다.",
    },
}

AUDIT_QA_EXECUTION_POLICY = {
    "worker_can_run_tests": True,
    "worker_can_write_evidence": True,
    "worker_can_modify_source": False,
    "result_statuses": ["Pass", "Fail", "Not Run", "Skipped", "environment_blocked"],
    "qa_workspace_policy": [
        "QA-000은 workflow.integration_branch의 현재 작업공간을 Gate 4 전체에서 재사용할 QA workspace로 기록한다.",
        "QA worktree는 선택 옵션이며, 명시적으로 활성화한 경우에만 사용한다.",
        "QA-001, QA-002, QA-003은 QA-000이 기록한 동일 QA workspace에서 실행한다.",
        "QA-000 workspace가 없거나 차단되면 후속 QA Run은 새 공간을 임의로 만들지 않고 Orchestrator 결정 필요 항목으로 반환한다.",
        "QA 중 결함 수정은 테스트 실행 중 즉시 수행하지 않고 workflow.integration_branch 통합 브랜치의 qa-fix-loop로 분리한다.",
    ],
    "qa000_required_checks": [
        "`python vulcan.py doctor --json`을 실행하고 JSON 결과를 QA-000 환경 증적으로 저장한다.",
        "Gradle wrapper 또는 backend 빌드 도구가 로컬 캐시/권한 기준으로 실행 가능한지 확인한다.",
        "backend 최소 smoke test 또는 test discovery가 실행 가능한지 확인한다.",
        "frontend 의존성이 설치되어 있거나 npm ci/npm install을 실행할 수 있는지 확인한다.",
        "Playwright package와 browser cache가 있거나 npx playwright install을 실행할 수 있는지 확인한다.",
        "backend/frontend 개발 포트(예: 8080, 5173 또는 프로젝트 지정 포트)가 사용 가능한지 확인한다.",
        "SQLite 또는 프로젝트 지정 DB 파일을 생성/접근할 수 있는지 확인한다.",
        "필수 환경변수, test profile, 임시 디렉터리, 로그/증적 출력 디렉터리를 확인한다.",
    ],
    "qa000_doctor_evidence": {
        "command": "python vulcan.py doctor --json",
        "json_evidence_path": "docs/artifacts/04-review/evidence/qa-000/QA-000-doctor.json",
        "log_evidence_path": "docs/artifacts/04-review/evidence/qa-000/QA-000-doctor.log",
        "interpretation": [
            "summary.fail > 0이면 제품 결함으로 단정하지 않고 environment_blocked 또는 ISSUE 후보로 분리한다.",
            "summary.warn > 0이면 QA-000 Run 결과에 경고와 후속 판단을 남긴다.",
            "doctor 결과만으로 테스트 Pass/Fail을 대신 판정하지 않는다.",
        ],
    },
    "stages": [
        "QA-000 환경 준비/스모크: 통합된 소스, 의존성, DB/포트/환경변수, backend/frontend 기동 가능성, Playwright 설치/브라우저 캐시를 확인하고 후속 QA Run이 재사용할 QA workspace 경로를 기록한다.",
        "QA-001 명령 기반 검증: QA-000 workspace에서 backend/frontend test, lint, build, check-contract, check-trace, run-check를 실행하고 로그 증적을 남긴다.",
        "QA-002 UI/E2E 증적: QA-000 workspace에서 서버를 띄우고 UI-ID별 Playwright screenshot/log/trace를 수집한다.",
        "QA-003 결과 정리/판정 후보: QA Finding, Test Result, traceability 반영 후보, FIND/CR/ISSUE, Gate4 완료 판단 필요 항목을 정리한다.",
    ],
    "on_failure": [
        "코드를 직접 수정하지 않는다.",
        "원인 가설, 재현 명령, 로그 경로, 영향 ID를 남긴다.",
        "승인된 설계 범위 안의 결함이면 FIND 후보로 남긴다.",
        "요구사항/API/DB/보안/화면 계약 변경이 필요하면 CR 후보로 남긴다.",
    ],
    "failure_report_contract": {
        "required_when": ["Fail", "Not Run", "environment_blocked"],
        "required_fields": [
            "qa_stage",
            "failing_command",
            "cwd",
            "exit_code",
            "observed_error",
            "log_path",
            "reproduction_command",
            "impact_ids",
            "candidate_classification",
            "orchestrator_decision_needed",
        ],
        "candidate_classification_values": ["FIND", "CR", "ISSUE", "environment_blocked"],
        "forbidden_actions": [
            "source_code_edit",
            "new_api_or_method_creation",
            "qa_fix_loop_execution",
            "gate_pass_decision",
        ],
    },
}

AUDIT_GATE2_DESIGN_SEQUENCE = [
    "G2-01 Kickoff / 설계 범위 고정: Gate 1 요구사항, AC, 미결 질문, 보류 항목을 확인한다.",
    "G2-02 SW Architecture Draft: 전체 구조, 주요 CNT, ADR 후보, 보안/데이터/배포 경계, Pending을 먼저 잡는다.",
    "G2-03 Screen / User Flow: SCR, UIREF, 화면 상태, 메시지 위치, 사용자 흐름을 확정한다.",
    "G2-04 Function Spec: 화면과 요구사항을 FUNC, 기능 흐름, 예외 흐름으로 전개한다.",
    "G2-05 Program Design / API Spec: FUNC를 PGM, 컴포넌트, 인터페이스, public method contract, API, DTO, 오류코드로 내린다.",
    "G2-06 Data / DB Spec: TERM, WORD, DOMAIN, DB, ERD/DBML, 제약조건을 확정한다.",
    "G2-07 Security Guide: SEC별 정책값, 적용 위치, 오류 메시지, 검증 후보를 확정한다.",
    "G2-08 Development Standard: 패키지 구조, 레이어 규칙, DTO/Entity, 빌드/테스트 명령을 확정한다.",
    "G2-09 SW Architecture Baseline 보강: 상세 설계 결정을 CMP, FLOW, 품질속성, ADR 상태로 되돌려 반영한다.",
    "G2-10 Design Review / Gate 3 승인 대기: 설계 검수 결과, FIND/ISSUE/CR, Gate 3 승인 질문을 남긴다.",
]

AUDIT_GATE_PRESETS = {
    "phase0": {
        "sample": "docs/core/run-input-samples/phase0-discovery.sample.md",
        "required": [
            "docs/templates/PROJECT_BRIEF_TEMPLATE.md",
            "docs/templates/STAKEHOLDER_SCOPE_TEMPLATE.md",
            "docs/templates/AS_IS_TO_BE_TEMPLATE.md",
            "docs/templates/RISK_ASSUMPTION_TEMPLATE.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-001_Project-Brief_v0.1.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-002_Stakeholder-And-Scope_v0.1.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-003_As-Is-To-Be_v0.1.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-004_Risk-And-Assumption_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/00-discovery/",
            "docs/runs/",
        ],
        "completion_criteria": [
            "프로젝트 목적, 사용자, 범위, 비목표가 실제 프로젝트 값으로 정리되어 있다.",
            "이해관계자와 승인자, 주요 제약, 참고문서 출처가 식별되어 있다.",
            "As-Is/To-Be와 주요 리스크/가정이 Gate 1 질문으로 이어진다.",
            "Phase 0에서 구현, 테스트 코드, 화면 증적을 만들지 않는다.",
        ],
    },
    "gate1": {
        "sample": "docs/core/run-input-samples/gate1-requirements-review.sample.md",
        "required": [
            "docs/templates/REQUIREMENTS_SPEC_TEMPLATE.md",
            "docs/templates/TRACEABILITY_MATRIX_TEMPLATE.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-001_Project-Brief_v0.1.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-002_Stakeholder-And-Scope_v0.1.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-003_As-Is-To-Be_v0.1.md",
            "docs/artifacts/00-discovery/DOC-CORE-P0-004_Risk-And-Assumption_v0.1.md",
            "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "REQ, NREQ, AC가 실제 기능/품질 요구로 작성되어 있다.",
            "각 요구사항에 출처, 우선순위, 승인 상태, 관련 리스크가 연결되어 있다.",
            "보안, 데이터, 화면, 인터페이스 후보가 Gate 2 설계 입력으로 넘어간다.",
            "요구사항과 인수기준이 추적표에 연결되어 있다.",
        ],
    },
    "gate2": {
        "sample": "docs/core/run-input-samples/gate2-design-review.sample.md",
        "required": [
            "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md",
            "docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md",
            "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
            "docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md",
            "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
            "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
            "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/02-design/",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "REQ/AC가 FUNC, SCR, PGM, API, DB, SEC 설계 ID로 전개되어 있다.",
            "설계 산출물 간 화면, API, 프로그램, 데이터, 보안 연결이 모순되지 않는다.",
            "Gate 2 산출 순서와 현재 Run 위치가 Run 기록에 남아 있다.",
            "SW 아키텍처 Draft/Baseline Candidate/Baseline 성숙도와 Pending/ADR 상태가 기록되어 있다.",
            "화면 퍼블리싱 산출물 또는 외부 시안이 있으면 UI Implementation Contract로 기준 파일, 필수 유지, 변경 허용/금지, 비교 방식을 확정한다.",
            "개발표준과 아키텍처 기준이 구현자가 사용할 수 있을 만큼 구체적이다.",
            "Gate 3 테스트 설계에 넘길 검증 후보가 식별되어 있다.",
        ],
        "design_sequence": AUDIT_GATE2_DESIGN_SEQUENCE,
    },
    "gate3": {
        "sample": "docs/core/run-input-samples/gate3-test-design.sample.md",
        "required": [
            "docs/templates/TEST_CASE_TEMPLATE.md",
            "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md",
            "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
            "docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md",
            "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
            "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "AC, SEC, NREQ가 UT, IT, UI, PT 후보로 전개되어 있다.",
            "요구사항정의서의 모든 상세 REQ-NNN-NN이 테스트케이스 문서의 상세 REQ별 테스트 매핑에 포함되어 있다.",
            "각 상세 REQ-NNN-NN은 하나 이상의 UT, IT, UI, PT 또는 승인된 검토 테스트와 연결되어 있다.",
            "각 테스트케이스에 입력, 절차, 기대결과, 증적 방식이 있다.",
            "UI 테스트는 화면 단위가 아니라 상태/시나리오 단위로 UI-001-01처럼 분리되어 있다.",
            "각 UI 테스트는 기대 화면, 실제 확인 방법, 캡처 증적 파일 경로가 1:1로 연결되어 있다.",
            "화면 퍼블리싱 기반 화면은 UI Implementation Contract의 필수 유지/변경 허용/금지 항목을 테스트 기대결과에 반영한다.",
            "자동화 가능 테스트와 수동 검수 테스트가 구분되어 있다.",
            "구현 전에 필요한 테스트 데이터와 환경 제약이 식별되어 있다.",
        ],
    },
    "impl": {
        "sample": "docs/core/run-input-samples/impl-build-wave.sample.md",
        "required": [
            "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md",
            "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        ],
        "writable": [
            "docs/runs/",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/artifacts/04-review/evidence/",
        ],
        "completion_criteria": [
            "승인된 Gate 2/3 범위 안에서만 구현 또는 구현 계획을 작성한다.",
            "Implementation Plan은 feature 구현 Wave 전에 scaffold 필요 여부를 판단하고, 필요하면 BW-000 implementation-scaffold를 첫 Wave로 둔다.",
            "scaffold가 불필요하면 contract_skeleton.mode: not-required와 확인한 파일/명령 근거를 남긴다.",
            "작은 기능이라도 실제 코드/테스트/UI/API 구현은 Orchestrator 직접 구현이 아니라 native worker(subagent/thread/native branch agent)에게 위임한다.",
            "agent-run --mode work와 run-exec는 필수 실행 경로가 아니라 별도 CLI 프로세스, worktree 격리, watchdog/timeout 증적, cross-runner 실행이 필요할 때 선택하는 옵션이다.",
            "사용자가 worker 사용을 명시하지 않았다는 점은 Orchestrator 직접 구현 사유가 아니며, 구현 진행 승인이 있으면 별도 요청이 없어도 native worker 위임을 기본 절차로 둔다.",
            "직접 구현 예외는 worker/subagent/thread 실행 불가, worker 결과 통합 중 충돌 해결에 필요한 최소 수정, 긴급한 1~2줄 연결 수정, 사용자의 명시적 직접 구현 승인에 한해 허용한다.",
            "Orchestrator 직접 수정 예외가 있으면 orchestrator_direct_edit_reason, direct_edit_scope.files, direct_edit_scope.estimated_loc, direct_edit_scope.contract_changed, 실행 검증, 후속 검수 필요 여부를 Run에 기록한다.",
            "직접 구현 예외는 2개 이하 파일, 약 30 LOC 이하, public API/PGM/IF/MTH/DTO/schema/DB/security/SCR/UI contract 변경 없음, 기존 테스트 또는 작은 테스트 보정으로 검증 가능한 경우로 제한한다.",
            "3개 이상 파일, 약 100 LOC 이상, 15분 이상 예상, backend/frontend 동시 변경, 새 계약 추가, 테스트 본문 대량 추가가 보이면 Build Wave로 분리한다.",
            "화면 구현은 관련 SCR의 UI Implementation Contract와 Gate 3 UI 테스트 기준을 먼저 확인한다.",
            "Build Wave와 worker Run은 기능/계약 단위로 나뉘며 target_contracts의 FUNC/PGM/API/DB/SEC/TEST 묶음이 명확하다.",
            "Build Wave 범위, 소유 파일, 관련 ID, 검증 명령이 명확하다.",
            "시간 기준은 10분 내외/최대 15분 권장 보조 기준이며, 미완성 중간 구현을 완료 처리하지 않는다.",
            "구현 변경은 테스트 코드, 테스트 결과, 추적표 갱신 필요 항목과 연결되며, 추적표 Implemented/Verified 상태는 Orchestrator 재검증 후 반영한다.",
            "동시에 active 상태인 Build Wave가 하나만 유지된다.",
        ],
        "verification_commands": [
            "python vulcan.py sync-session",
        ],
    },
    "gate4": {
        "sample": "docs/core/run-input-samples/gate4-qa-review.sample.md",
        "required": [
            "docs/templates/QA_FINDING_TEMPLATE.md",
            "docs/templates/TEST_RESULT_TEMPLATE.md",
            "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
            "docs/artifacts/04-review/evidence/",
        ],
        "writable": [
            "docs/artifacts/04-review/",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "실행한 테스트 명령과 결과가 테스트 결과서에 기록되어 있다.",
            "화면/UI 증적 또는 로그 증적이 관련 UI/UT/IT/PT ID와 1:1로 연결되어 있다.",
            "회원가입, 로그인, TODO 같은 UI 흐름은 기본/오류/성공/전환 상태별 캡처가 분리되어 있다.",
            "화면 캡처 증적은 Playwright로 생성되어 있으며, Playwright 미설치 시 설치 명령과 재실행 결과가 기록되어 있다.",
            "CDP, 브라우저 수동 캡처, 런타임 Preview 캡처만으로 UI Pass를 확정하지 않는다.",
            "화면 퍼블리싱 기반 화면은 기준 UIREF와 구현 screenshot의 차이 목록 및 허용 여부가 기록되어 있다.",
            "증적 파일이 기대 화면을 실제로 보여주지 못하면 Pass가 아니라 Fail 또는 Not Run으로 기록되어 있다.",
            "결함은 FIND로 기록하고, 범위 변경은 CR로 승격한다.",
            "Gate 4 QA 실행은 가능하면 qa-execution/evidence worker Run으로 분리하고, Orchestrator는 결과 판정과 사용자 협의를 맡는다.",
            "QA 실행 중 실패가 나오면 Orchestrator가 즉시 코드를 수정하지 않고 원인, 재현 명령, 로그, 영향 ID를 먼저 기록한다.",
            "수정 완료 결함은 qa-fix-loop Run과 재검증 결과가 연결되어 있다.",
        ],
        "verification_commands": [
            "python vulcan.py sync-session",
        ],
    },
    "gate5": {
        "sample": "docs/core/run-input-samples/gate5-release-approval.sample.md",
        "required": [
            "docs/templates/RELEASE_APPROVAL_TEMPLATE.md",
            "docs/templates/CHANGE_REQUEST_TEMPLATE.md",
            "docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
            "docs/artifacts/05-change/",
            "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md",
            "docs/artifacts/05-change/",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "릴리즈 범위, 제외 범위, 승인자, 잔여 리스크가 명확하다.",
            "미해결 FIND/CR/ISSUE의 처리 상태와 승인 조건이 기록되어 있다.",
            "요구사항, 테스트 결과, 증적, 릴리즈 승인서가 추적표로 연결되어 있다.",
            "인수인계와 운영/롤백 고려사항이 남아 있다.",
        ],
    },
}

AUDIT_GATE_SKILL_PRESETS = {
    ("gate2", "data-standard-review"): {
        "sample": "docs/core/run-input-samples/gate2-data-standard-review.sample.md",
        "required": [
            "docs/core/DATA_STANDARD_RULES.md",
            "docs/core/REFERENCE_STANDARDS.md",
            "docs/templates/PROJECT_GLOSSARY_TEMPLATE.md",
            "docs/templates/DATABASE_SPEC_TEMPLATE.md",
            "docs/artifacts/02-design/data/DOC-DATA-G2-001_Project-Glossary_v0.1.md",
            "docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md",
            "docs/artifacts/02-design/data/erd/logical/logical-erd.dbml",
            "docs/artifacts/02-design/data/erd/physical/physical-erd.dbml",
            "docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md",
            "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/02-design/data/DOC-DATA-G2-001_Project-Glossary_v0.1.md",
            "docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md",
            "docs/artifacts/02-design/data/erd/logical/logical-erd.dbml",
            "docs/artifacts/02-design/data/erd/physical/physical-erd.dbml",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "프로젝트 단어사전에 TERM, WORD, DOMAIN 섹션이 실제 프로젝트 값으로 채워져 있다.",
            "공공데이터 공통표준 또는 프로젝트 신규 용어 여부와 등록 사유가 기록되어 있다.",
            "화면 항목명, API 필드명, DB 컬럼명, DOMAIN-ID 매핑이 작성되어 있다.",
            "개인정보/인증정보/시스템정보 등 보안 분류와 관련 SEC-ID가 연결되어 있다.",
            "DB명세서와 논리/물리 DBML의 테이블, 컬럼, PK/FK, 코드 도메인이 일치한다.",
            "미정 또는 작성 전 상태의 placeholder가 남아 있지 않다.",
        ],
    },
    ("gate2", "development-standard-review"): {
        "sample": "docs/core/run-input-samples/gate2-development-standard-review.sample.md",
        "required": [
            "docs/core/TECH_STACK_BASELINES.md",
            "docs/core/SECURITY_BASELINE.md",
            "docs/templates/DEVELOPMENT_STANDARD_TEMPLATE.md",
            "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md",
            "docs/artifacts/02-design/architecture/DOC-ARCH-G2-001_SW-Architecture_v0.1.md",
            "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
            "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "언어, 런타임, 프레임워크, DB, 빌드, 테스트 도구와 선택 근거가 작성되어 있다.",
            "TECH_STACK_BASELINES.md 중 어떤 기준을 준용하고 어떤 점을 프로젝트에 맞게 조정했는지 기록되어 있다.",
            "패키지 구조, 계층 책임, 금지 의존성, DTO/Entity 분리, 트랜잭션 기준이 구현자가 따를 수 있을 만큼 구체적이다.",
            "메시지, 예외, 로그, 설정값, 외부 의존성, 주석/추적 ID 표기 규칙이 있다.",
            "보안 구현 기준이 SECURITY_BASELINE과 SEC-ID에 연결되어 있다.",
            "필수 검증 명령과 증적 위치가 Gate 3/구현 단계로 전달 가능하다.",
        ],
    },
    ("gate2", "security-review"): {
        "required": [
            "docs/core/SECURITY_BASELINE.md",
            "docs/core/KISA_SECURITY_RULES.md",
            "docs/templates/SECURITY_GUIDE_TEMPLATE.md",
            "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
            "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
            "docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md",
            "docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "SEC-ID별 정책값, 적용 위치, 구현 규칙, 오류 메시지, 검증 방향이 작성되어 있다.",
            "KISA/SR, OWASP, CWE 근거가 필요한 보안 항목에 연결되어 있다.",
            "비밀번호, 토큰, 접근제어, 입력검증, 정보노출 제한이 프로그램/API/DB/화면 설계와 모순되지 않는다.",
            "Gate 3에서 UT/IT/UI로 전개할 보안 검증 후보가 식별되어 있다.",
        ],
    },
    ("gate2", "screen-review"): {
        "required": [
            "docs/templates/SCREEN_SPEC_TEMPLATE.md",
            "docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md",
            "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
            "docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "필수 화면과 상태가 SCR-ID로 식별되어 있다.",
            "각 화면에 입력 항목, 이벤트, 메시지, 호출 API/프로그램, 관련 SEC-ID가 연결되어 있다.",
            "와이어프레임, 이미지, HTML/CSS/JS 화면 퍼블리싱 산출물, 또는 동등한 화면 구조 증적이 있다.",
            "UIREF가 참고자료인지 구현 기준인지 구분되고, 구현 기준이면 필수 유지/변경 허용/금지 항목이 정의되어 있다.",
            "Gate 3 UI 테스트와 Gate 4 캡처 증적 기준이 작성되어 있다.",
        ],
    },
    ("gate2", "ui-review"): {
        "required": [
            "docs/templates/SCREEN_SPEC_TEMPLATE.md",
            "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
            "docs/artifacts/02-design/screen/ui-baseline/",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        ],
        "writable": [
            "docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
            "docs/runs/",
        ],
        "completion_criteria": [
            "구현자가 화면 밀도, 레이아웃, 상태, 메시지, 반응형 기준을 판단할 수 있다.",
            "desktop/mobile viewport와 비교 기준이 명시되어 있다.",
            "화면 퍼블리싱 산출물 또는 외부 시안이 구현 계약으로 전환되어 필수 유지 요소와 허용 차이가 명확하다.",
            "빈 상태, 오류 상태, 인증 필요 상태, 성공 상태의 UI 기준이 상태/시나리오별 UI-ID로 분리되어 있다.",
            "실제 캡처 증적 경로와 UI-ID 후보가 Gate 3/4로 1:1 전달된다.",
        ],
    },
    ("impl", "implementation-plan"): {
        "writable": [
            "docs/runs/",
            "session.json",
        ],
        "completion_criteria": [
            "Build Wave 후보와 각 Wave의 소유 파일, 관련 ID, 검증 명령이 나뉘어 있다.",
            "화면 구현 Wave는 UI Implementation Contract 준수 체크와 screenshot 비교 증적 위치가 정의되어 있다.",
            "구현 착수 전 사용자 승인 또는 명시적인 진행 지시가 필요한 항목이 식별되어 있다.",
        ],
    },
    ("impl", "implementation-scaffold"): {
        "run_type": "ImplementationScaffold",
        "worker_run": True,
        "working": [
            "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md",
            "docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        ],
        "writable": [
            "docs/runs/",
            "docs/artifacts/04-review/evidence/",
            "TBD: scaffold 대상 코드/테스트 경로를 Program Design의 Contract Skeleton 기준으로 구체화",
        ],
        "completion_criteria": [
            "신규 개발이면 빌드 가능한 프로젝트 골격과 contract skeleton을 먼저 만든다.",
            "고도화이면 기존 코드와 Program Design의 PGM/IF/MTH/DTO 계약 매핑을 확인하고 누락 skeleton만 보강한다.",
            "target_contracts.interface_contract와 contract_skeleton의 public signature, DTO/schema, error contract가 실제 파일에 존재한다.",
            "업무 로직은 TODO/stub/NotImplemented 또는 최소 wiring만 포함하고 feature 구현을 완료 처리하지 않는다.",
            "compile/import/build smoke 명령을 실행하거나 Not Run 사유를 남긴다.",
            "다음 Build Wave가 구현할 method와 테스트 stub를 Orchestrator 결정 필요 항목으로 반환한다.",
        ],
    },
    ("impl", "build-wave"): {
        "worker_run": True,
        "working": [
            "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        ],
        "writable": [
            "docs/runs/",
            "docs/artifacts/04-review/evidence/",
        ],
        "completion_criteria": [
            "Wave 하나의 범위만 수정하고 다른 Wave 범위는 건드리지 않는다.",
            "Wave는 기능/계약 단위로 검증 가능한 완결 조각이며, 시간은 쪼개기 보조 기준으로만 사용한다.",
            "target_contracts.interface_contract의 public signature, schema, error contract를 다른 이름이나 타입으로 대체하지 않는다.",
            "화면 구현은 UI Implementation Contract의 필수 유지 요소, 허용 변경, 금지 변경을 준수한다.",
            "구현 결과, 작성/갱신한 테스트케이스, Orchestrator가 재실행할 검증 명령, 추적표 갱신 필요 항목이 같은 Run에 기록되어 있다.",
        ],
    },
    ("gate4", "qa-fix-loop"): {
        "run_type": "QAFix",
        "worker_run": True,
        "required": [
            "docs/adapters/codex-gpt/skills/qa-fix-loop.md",
        ],
        "working": [
            "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
        ],
        "writable": [
            "docs/runs/",
            "docs/artifacts/04-review/evidence/",
        ],
        "completion_criteria": [
            "승인된 설계 범위 안의 결함만 FIND로 수정한다.",
            "요구사항 또는 범위 변경이 필요한 항목은 CR로 승격한다.",
            "재검증 명령과 결과가 테스트 결과서에 반영되어 있다.",
            "수정은 native worker(subagent/thread/native branch agent)에게 위임하고 Orchestrator는 결과 통합과 재검증을 담당한다. 외부 CLI 실행 증적이 필요할 때만 agent-run/run-exec를 선택한다.",
        ],
    },
    ("gate4", "qa-execution"): {
        "sample": "docs/core/run-input-samples/gate4-qa-review.sample.md",
        "run_type": "Evidence",
        "worker_run": True,
        "required": [
            "docs/adapters/codex-gpt/skills/qa-execution.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
        ],
        "working": [
            "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
        ],
        "writable": [
            "docs/runs/",
            "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
            "docs/artifacts/04-review/evidence/",
        ],
        "completion_criteria": [
            "Gate 4 전체 QA를 한 번에 수행하지 않는다. QA-000 환경 준비, QA-001 명령 검증, QA-002 UI/E2E 증적, QA-003 결과 정리 중 현재 Run 범위를 명시한다.",
            "QA-000에서 통합된 소스, 의존성, 실행 포트, DB/환경변수, Playwright 설치 상태를 먼저 확인하고 차단되면 이후 QA 실행을 진행하지 않는다.",
            "Gate 3 테스트케이스와 개발표준정의서의 필수 검증 명령을 실행하거나 Not Run/environment_blocked로 사유를 기록한다.",
            "각 검증 결과에는 cwd, command, exit code, success criteria, result, log/evidence path가 있다.",
            "Playwright 화면 검증은 상태/시나리오별 UI-ID와 screenshot/log/trace 증적을 1:1로 연결한다.",
            "실패나 이상 동작은 즉시 수정하지 않고 원인 가설, 재현 명령, 영향 ID, 후보 FIND/CR/ISSUE를 기록한다.",
            "새 API, 새 메소드, 요구사항/설계 변경이 필요해 보이면 코드를 만들지 않고 CR 후보로 반환한다.",
            "worker는 QA Pass, Gate 완료, 수정 완료를 확정하지 않고 Orchestrator 결정 필요 항목으로 반환한다.",
        ],
    },
    ("gate5", "change-impact-analysis"): {
        "completion_criteria": [
            "릴리즈 전 변경요청의 영향 Gate, 영향 산출물, 승인 조건이 정리되어 있다.",
            "릴리즈 보류/승인/조건부 승인 판단 근거가 남아 있다.",
        ],
    },
}


# ── 공통 유틸 ──────────────────────────────────────────────────────────────

def render(text, variables):
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def read_template(rel_path):
    path = os.path.join(TEMPLATES_DIR, rel_path)
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_file(target_dir, rel_path, content):
    full_path = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  생성: {rel_path}")


def copy_file(target_dir, rel_path, src_rel_path=None):
    import shutil
    src = os.path.join(TEMPLATES_DIR, src_rel_path or rel_path)
    dst = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  생성: {rel_path}")


def copy_tree(src_dir, dst_dir):
    """디렉토리 트리를 재귀적으로 복사합니다."""
    import shutil
    for root, dirs, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        for f in files:
            src = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f) if rel_root != "." else f
            dst = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def copy_source_tree(target_dir, rel_dir, variables=None, overwrite=True, source_root=None):
    """Copy a repository directory into the target project.

    Markdown and JSON files are rendered with project variables; binary files are copied as-is.
    """
    import shutil

    src_dir = os.path.join(source_root or VULCAN_DIR, rel_dir)
    if not os.path.isdir(src_dir):
        return 0

    copied = 0
    render_exts = {".md", ".json", ".txt", ".yml", ".yaml"}
    for root, dirs, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        for f in files:
            src = os.path.join(root, f)
            child_rel = os.path.join(rel_root, f) if rel_root != "." else f
            dst_rel = os.path.join(rel_dir, child_rel)
            dst = os.path.join(target_dir, dst_rel)

            if os.path.exists(dst) and not overwrite:
                continue

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            ext = os.path.splitext(f)[1].lower()
            if variables is not None and ext in render_exts:
                with open(src, encoding="utf-8") as fp:
                    content = render(fp.read(), variables)
                with open(dst, "w", encoding="utf-8") as fp:
                    fp.write(content)
            else:
                shutil.copy2(src, dst)
            copied += 1
    return copied


def install_project_doc_framework(target_dir, variables, overwrite=True, source_root=None):
    """Install audit/agent document framework files into a project."""
    source_root = source_root or VULCAN_DIR

    for rel_path in PROJECT_ROOT_FILES:
        src = os.path.join(source_root, rel_path)
        dst = os.path.join(target_dir, rel_path)
        if not os.path.isfile(src):
            continue
        if os.path.exists(dst) and not overwrite:
            continue
        with open(src, encoding="utf-8") as fp:
            content = render(fp.read(), variables)
        with open(dst, "w", encoding="utf-8") as fp:
            fp.write(content)
        print(f"  install/update: {rel_path}")

    for rel_dir in PROJECT_DOC_SETS:
        copied = copy_source_tree(
            target_dir,
            rel_dir,
            variables=variables,
            overwrite=overwrite,
            source_root=source_root,
        )
        if copied:
            print(f"  install/update: {rel_dir}/ ({copied} files)")

    for rel_dir in PROJECT_DOC_DIRS:
        write_file(target_dir, os.path.join(rel_dir, ".gitkeep"), "")


def install_project_artifacts(target_dir, variables, overwrite=False, source_root=None):
    """Install official Ex artifact working documents into docs/artifacts/."""
    source_root = source_root or VULCAN_DIR

    for src_rel, dst_rel in PROJECT_ARTIFACT_TEMPLATES:
        src = os.path.join(source_root, src_rel)
        dst = os.path.join(target_dir, dst_rel)
        if not os.path.isfile(src):
            continue
        if os.path.exists(dst) and not overwrite:
            continue
        with open(src, encoding="utf-8") as fp:
            content = render(fp.read(), variables)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fp:
            fp.write(content)
        print(f"  install/update: {dst_rel}")


def install_poc_artifacts(target_dir, variables, overwrite=False, source_root=None):
    """Install PoC profile integrated working documents into docs/poc/."""
    source_root = source_root or VULCAN_DIR
    for src_rel, dst_rel in POC_ARTIFACT_TEMPLATES:
        src = os.path.join(source_root, src_rel)
        dst = os.path.join(target_dir, dst_rel)
        if not os.path.isfile(src):
            continue
        if os.path.exists(dst) and not overwrite:
            continue
        with open(src, encoding="utf-8") as fp:
            content = render(fp.read(), variables)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fp:
            fp.write(content)
        print(f"  install/update: {dst_rel}")


def install_product_artifacts(target_dir, variables, overwrite=False, source_root=None):
    """Install Product profile working documents into docs/product/."""
    source_root = source_root or VULCAN_DIR
    for src_rel, dst_rel in PRODUCT_ARTIFACT_TEMPLATES:
        src = os.path.join(source_root, src_rel)
        dst = os.path.join(target_dir, dst_rel)
        if not os.path.isfile(src):
            continue
        if os.path.exists(dst) and not overwrite:
            continue
        with open(src, encoding="utf-8") as fp:
            content = render(fp.read(), variables)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fp:
            fp.write(content)
        print(f"  install/update: {dst_rel}")


def ensure_gitignore_entry(project_dir, entry):
    path = os.path.join(project_dir, ".gitignore")
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = f.read()

    lines = {line.strip() for line in existing.splitlines()}
    if entry.strip() in lines:
        return

    suffix = "" if not existing or existing.endswith("\n") else "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(existing + suffix + entry.rstrip() + "\n")
    print(f"  update: .gitignore ({entry})")


def slugify(value):
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-zA-Z가-힣_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "run"


def split_csv(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def runs_rel_dir(project_dir="."):
    docs_runs = os.path.join(project_dir, "docs", "runs")
    root_runs = os.path.join(project_dir, "runs")
    if os.path.isdir(docs_runs):
        return os.path.join("docs", "runs")
    if os.path.isdir(root_runs):
        return "runs"
    return os.path.join("docs", "runs")


def next_run_id(project_dir="."):
    runs_dir = os.path.join(project_dir, runs_rel_dir(project_dir))
    max_num = 0
    if os.path.isdir(runs_dir):
        for name in os.listdir(runs_dir):
            match = re.match(r"RUN-(\d+)", name)
            if match:
                max_num = max(max_num, int(match.group(1)))
    return f"RUN-{max_num + 1:03d}"


def acquire_run_generation_lock(project_dir=".", timeout_seconds=10):
    runs_dir = os.path.join(project_dir, runs_rel_dir(project_dir))
    os.makedirs(runs_dir, exist_ok=True)
    lock_path = os.path.join(runs_dir, ".run-new.lock")
    deadline = time.monotonic() + timeout_seconds

    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            payload = f"pid={os.getpid()} created_at={datetime.now().isoformat()}\n"
            os.write(fd, payload.encode("utf-8", errors="replace"))
            return lock_path, fd
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(lock_path)
                if age > 600:
                    os.remove(lock_path)
                    continue
            except OSError:
                pass
            if time.monotonic() >= deadline:
                print("오류: 다른 run-new 작업이 실행 중이어서 Run ID를 생성할 수 없습니다.")
                print(f"  lock: {lock_path}")
                sys.exit(1)
            time.sleep(0.2)


def release_run_generation_lock(lock):
    lock_path, fd = lock
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        os.remove(lock_path)
    except OSError:
        pass


def reviews_rel_dir(project_dir="."):
    docs_reviews = os.path.join(project_dir, "docs", "reviews")
    if os.path.isdir(docs_reviews):
        return os.path.join("docs", "reviews")
    return os.path.join("docs", "reviews")


def next_review_id(project_dir="."):
    reviews_dir = os.path.join(project_dir, reviews_rel_dir(project_dir))
    max_num = 0
    if os.path.isdir(reviews_dir):
        for name in os.listdir(reviews_dir):
            match = re.match(r"RV-(\d+)", name)
            if match:
                max_num = max(max_num, int(match.group(1)))
    return f"RV-{max_num + 1:03d}"


def find_review_file(project_dir, review_id, suffix):
    reviews_dir = os.path.join(project_dir, reviews_rel_dir(project_dir))
    if not os.path.isdir(reviews_dir):
        return ""
    for name in sorted(os.listdir(reviews_dir)):
        if name.startswith(f"{review_id}_") and name.endswith(suffix):
            return os.path.join(reviews_rel_dir(project_dir), name)
    return ""


def find_independent_review_run_file(project_dir, review_id):
    runs_dir = os.path.join(project_dir, runs_rel_dir(project_dir))
    if not os.path.isdir(runs_dir):
        return ""
    for name in sorted(os.listdir(runs_dir)):
        if not name.endswith(".md") or "independent-review" not in name:
            continue
        path = os.path.join(runs_dir, name)
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        if re.search(rf"^\s*review_id\s*:\s*{re.escape(review_id)}\s*$", content, re.MULTILINE):
            return os.path.join(runs_rel_dir(project_dir), name)
    return ""


def format_yaml_list(items):
    if not items:
        return "[]"
    return "[" + ", ".join(items) + "]"


def format_yaml_scalar(value):
    return json.dumps(value, ensure_ascii=False)


def classify_related_ids(ids):
    groups = {
        "req": [],
        "nreq": [],
        "ac": [],
        "func": [],
        "scr": [],
        "pgm": [],
        "api": [],
        "db": [],
        "sec": [],
        "test": [],
        "ui": [],
        "other": [],
    }
    for item in ids or []:
        value = item.strip()
        if not value:
            continue
        prefix = value.split("-", 1)[0].lower()
        if prefix in ("ut", "it", "pt", "tst"):
            groups["test"].append(value)
        elif prefix in groups:
            groups[prefix].append(value)
        else:
            groups["other"].append(value)
    return groups


def format_yaml_mapping_sequences(mapping, indent=0):
    lines = []
    spaces = " " * indent
    for key, values in mapping.items():
        lines.append(f"{spaces}{key}: {format_yaml_list(values)}")
    return "\n".join(lines)


def file_sha256(path):
    if not os.path.exists(path):
        return ""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_yaml_sequence(items, indent=0):
    spaces = " " * indent
    if not items:
        return f"{spaces}[]"
    return "\n".join(f"{spaces}- {format_yaml_scalar(item)}" for item in items)


def format_development_standards_applied(items, indent=0):
    spaces = " " * indent
    child = " " * (indent + 2)
    if not items:
        return f"{spaces}[]"
    lines = []
    for item in items:
        lines.append(f"{spaces}- standard_id: {format_yaml_scalar(item.get('standard_id', 'DEV-TBD'))}")
        lines.append(f"{child}source: \"docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md\"")
        lines.append(f"{child}rule: {format_yaml_scalar(item.get('rule', 'TBD'))}")
    return "\n".join(lines)


def format_development_standard_checklist(policy, indent=0):
    spaces = " " * indent
    child = " " * (indent + 2)
    lines = []
    for key, item in policy.items():
        lines.append(f"{spaces}{key}:")
        lines.append(f"{child}required: {str(bool(item.get('required'))).lower()}")
        lines.append(f"{child}targets:")
        lines.append(format_yaml_sequence(item.get("targets", []), indent + 4))
        lines.append(f"{child}rule: {format_yaml_scalar(item.get('rule', 'TBD'))}")
    return "\n".join(lines)


def merge_unique(*item_lists):
    merged = []
    seen = set()
    for items in item_lists:
        for item in items or []:
            if item not in seen:
                merged.append(item)
                seen.add(item)
    return merged


def compact_reference_documents_for_profile(profile, paths, limit=None):
    normalized_profile = normalize_delivery_profile(profile)
    unique_paths = merge_unique(paths)
    if normalized_profile != "poc":
        return unique_paths
    unique_paths = [
        path
        for path in unique_paths
        if normalize_repo_path(path).lower() not in POC_REFERENCE_EXCLUDED_DOCS
    ]
    limit = POC_REFERENCE_DOC_LIMIT if limit is None else max(0, int(limit))
    if not unique_paths or limit == 0:
        return []

    priority_tokens = [
        "/program/",
        "/api/",
        "/data/",
        "/security/",
        "/function/",
        "/screen/",
        "/03-test/",
        "/01-requirements/",
        "/00-discovery/",
        "docs/core/",
    ]

    def priority(path):
        normalized = normalize_repo_path(path)
        for index, token in enumerate(priority_tokens):
            if token in normalized:
                return index
        return len(priority_tokens)

    ranked = sorted(unique_paths, key=lambda item: (priority(item), unique_paths.index(item)))
    return ranked[:limit]


def is_orchestrator_only_command(command):
    normalized = command.strip().lower()
    return any(
        token in normalized
        for token in (
            "check-trace",
            "sync-session",
            "wave-start",
            "wave-complete",
            "session ",
            "gate-start",
        )
    )


def is_working_document(path):
    normalized = path.replace("\\", "/")
    return normalized.startswith("docs/artifacts/")


def is_run_working_document(path):
    normalized = path.replace("\\", "/")
    if normalized in ("session.json",):
        return False
    if normalized.startswith("docs/runs/"):
        return False
    if normalized.startswith("TBD:"):
        return False
    return normalized.startswith(("docs/artifacts/", "docs/backlog/"))


def working_documents_from_scope(*scopes):
    docs = []
    for scope in scopes:
        for path in scope or []:
            if is_run_working_document(path):
                docs.append(path)
    return merge_unique(docs)


def split_working_and_reference(paths):
    working = []
    reference = []
    for path in paths:
        if is_working_document(path):
            working.append(path)
        else:
            reference.append(path)
    return working, reference


def normalize_delivery_profile(profile):
    normalized = str(profile or DEFAULT_DELIVERY_PROFILE).strip().lower()
    normalized = DELIVERY_PROFILE_ALIASES.get(normalized, normalized)
    if normalized not in SUPPORTED_DELIVERY_PROFILES:
        return DEFAULT_DELIVERY_PROFILE
    return normalized


def delivery_profile_rules(profile):
    normalized = normalize_delivery_profile(profile)
    return dict(DELIVERY_PROFILE_RULES.get(normalized, DELIVERY_PROFILE_RULES[DEFAULT_DELIVERY_PROFILE]))


def load_delivery_profile(project_dir="."):
    path = os.path.join(project_dir, "session.json")
    config_path = os.path.join(project_dir, "vulcan.config.json")

    session = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                session = json.load(f)
        except (OSError, json.JSONDecodeError):
            session = {}

    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError):
            config = {}

    profile = (
        session.get("profile")
        or session.get("delivery_profile")
        or config.get("delivery_profile")
        or DEFAULT_DELIVERY_PROFILE
    )
    return normalize_delivery_profile(profile)


def load_primary_runner(project_dir="."):
    config_path = os.path.join(project_dir, "vulcan.config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
                return config.get("runtime", {}).get("primary")
        except (OSError, json.JSONDecodeError):
            pass
    return None


def normalize_adapter_name(adapter=""):
    normalized = str(adapter or "").strip().lower()
    aliases = {
        "codex_cli": "codex-cli",
        "claude_cli": "claude-cli",
        "antigravity_cli": "antigravity-cli",
        "codex-gpt": "codex-gpt",
    }
    return aliases.get(normalized, normalized)


def adapter_read_first_docs(adapter=""):
    normalized = normalize_adapter_name(adapter)
    return ADAPTER_READ_FIRST_DOCS.get(normalized, [])


def adapter_family(adapter=""):
    normalized = normalize_adapter_name(adapter)
    if normalized in ("codex", "codex-cli", "codex-gpt"):
        return "codex"
    if normalized in ("gemini", "antigravity", "antigravity-cli", "agy"):
        return "gemini"
    if normalized in ("claude", "claude-cli"):
        return "claude"
    return ""


def adapter_doc_family(path):
    normalized = str(path or "").replace("\\", "/").lower()
    if normalized.startswith("docs/adapters/codex-gpt/"):
        return "codex"
    if normalized.startswith("docs/adapters/gemini/"):
        return "gemini"
    if normalized.startswith("docs/adapters/claude/"):
        return "claude"
    if normalized.startswith("docs/core/") and normalized.endswith("_gemini.md"):
        return "gemini"
    return ""


def filter_adapter_specific_docs(paths, adapter=""):
    family = adapter_family(adapter)
    filtered = []
    for path in paths or []:
        doc_family = adapter_doc_family(path)
        if doc_family and family and doc_family != family:
            continue
        filtered.append(path)
    return filtered


def is_gemini_long_context_mode(project_dir="."):
    config_path = os.path.join(project_dir, "vulcan.config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
                return bool(config.get("runtime", {}).get("gemini_long_context_mode", False))
        except (OSError, json.JSONDecodeError):
            pass
    return False


def effective_trace_depth(project_dir=".", trace_depth=None):
    if trace_depth is not None:
        return trace_depth
    profile = load_delivery_profile(project_dir)
    if profile == "poc":
        return POC_TRACE_DEPTH_DEFAULT
    return 2


POC_COMMON_READ_FIRST_DOCS = [
    "AGENTS.md",
    "session.json",
    "docs/core/GATE_EXECUTION_CHECKLIST.md",
    "docs/core/DELIVERY_PROFILES.md",
]

POC_TRACE_DEPTH_DEFAULT = 1
POC_REFERENCE_DOC_LIMIT = 5
POC_REFERENCE_EXCLUDED_DOCS = {
    "docs/core/agent_run_protocol.md",
    "docs/core/agent_run_protocol_gemini.md",
    "docs/core/run_input_contract.md",
    "docs/core/run_input_contract_gemini.md",
    "docs/core/run_output_contract.md",
    "docs/core/run_output_contract_gemini.md",
}

POC_COMMON_READONLY_DOCS = [
    "docs/core/",
    "docs/templates/",
]

POC_COMMON_EXCLUDED_PATHS = [
    "docs/ref-docs/",
    "**/*.db",
    "**/__pycache__/",
    "**/.ruff_cache/",
    "**/node_modules/",
    "**/.next/",
]

POC_GATE_WORKING_DOCUMENTS = {
    "phase0": [
        "docs/poc/POC_REQUIREMENTS.md",
    ],
    "gate1": [
        "docs/poc/POC_REQUIREMENTS.md",
    ],
    "gate2": [
        "docs/poc/POC_SYSTEM_DESIGN.md",
    ],
    "gate3": [
        "docs/poc/POC_TEST_REPORT.md",
    ],
    "impl": [
        "docs/runs/",
        "app/",
        "static/",
        "tests/",
        "requirements.txt",
    ],
    "gate4": [
        "docs/poc/POC_TEST_REPORT.md",
        "docs/poc/evidence/",
    ],
    "gate5": [
        "docs/poc/POC_TEST_REPORT.md",
        "docs/artifacts/07-release/",
        "docs/backlog/",
    ],
}

POC_GATE_REFERENCES = {
    "phase0": [
        "docs/core/ORCHESTRATOR_PROTOCOL.md",
    ],
    "gate1": [
        "docs/core/TRACEABILITY_RULES.md",
        "docs/poc/POC_REQUIREMENTS.md",
    ],
    "gate2": [
        "docs/poc/POC_REQUIREMENTS.md",
    ],
    "gate3": [
        "docs/poc/POC_REQUIREMENTS.md",
        "docs/poc/POC_SYSTEM_DESIGN.md",
    ],
    "impl": [
        "docs/poc/POC_REQUIREMENTS.md",
        "docs/poc/POC_SYSTEM_DESIGN.md",
        "docs/poc/POC_TEST_REPORT.md",
    ],
    "gate4": [
        "docs/poc/POC_TEST_REPORT.md",
        "docs/runs/",
    ],
    "gate5": [
        "docs/poc/POC_TEST_REPORT.md",
        "docs/runs/",
    ],
}

POC_GATE_COMPLETION_CRITERIA = {
    "phase0": [
        "PoC 목표, 가설, 성공 기준, 비목표가 짧게 정리되어 있다.",
        "불확실한 정보와 다음 질문이 open_issues에 남아 있다.",
        "PoC 종료 시 제품화/감리 전환 여부를 판단할 기준이 적혀 있다.",
    ],
    "gate1": [
        "핵심 요구사항 또는 가설이 검증 가능한 문장으로 정리되어 있다.",
        "각 요구사항은 최소 한 개의 성공 기준 또는 관찰 기준과 연결되어 있다.",
        "PoC 범위를 넘는 요구는 backlog 또는 open_issues로 분리되어 있다.",
    ],
    "gate2": [
        "핵심 아키텍처, 데이터, API 또는 화면 결정이 구현자가 이해할 수준으로 정리되어 있다.",
        "실험 코드의 주요 진입점, public interface, smoke 검증 기준이 식별되어 있다.",
        "제품화 또는 audit 전환 시 보강해야 할 설계 항목이 남아 있다.",
    ],
    "gate3": [
        "PoC 가설을 확인할 smoke, demo, 핵심 회귀 테스트가 정의되어 있다.",
        "미실행 또는 수동 확인 항목은 Pass로 기록하지 않고 Not Run 또는 open_issues로 남긴다.",
    ],
    "impl": [
        "PoC 목표를 확인하는 최소 코드와 빠른 self-check가 가능하다.",
        "구현 worker는 README, 최종 테스트 결과서, browser smoke/screenshot, release/backlog 정리를 직접 완료 조건으로 삼지 않는다.",
        "Browser smoke/screenshot, 결과서 정규화, 제품화 전환 후보 정리는 Gate 4/5에서 수행한다.",
        "실패한 실험은 구현 성공처럼 포장하지 않고 원인과 다음 판단 필요 항목으로 반환한다.",
    ],
    "gate4": [
        "PoC smoke/demo 검증 결과와 로그 또는 캡처 증적이 남아 있다.",
        "실패, 차단, 미실행 항목은 원인과 다음 판단 기준으로 분류되어 있다.",
    ],
    "gate5": [
        "PoC 결과 요약, 성공/실패 판단, 계속 진행/중단/전환 제안이 기록되어 있다.",
        "제품화 또는 audit 전환 시 보강해야 할 산출물과 기술부채가 분리되어 있다.",
    ],
}

POC_GATE_EXIT_POLICY = {
    "stop_required": True,
    "next_gate_requires_user_approval": True,
    "approval_evidence_required": False,
    "allowed_next_action": "PoC 결과와 다음 선택지를 짧게 정리하고 사용자 확인을 받는다.",
    "forbidden_actions": [
        "PoC smoke 결과를 운영 또는 감리 수준 검증 완료로 표현하지 않는다.",
        "실제로 실행하지 않은 테스트를 Pass로 기록하지 않는다.",
        "제품화 또는 audit 전환 보강 항목을 완료된 것으로 처리하지 않는다.",
    ],
}

POC_WORKER_EXECUTION_POLICY = {
    "forbidden_actions": [
        "Gate 전환을 수행하지 않는다.",
        "session.json의 current_gate, gate_status, completed를 직접 변경하지 않는다.",
        "사용자 승인, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 확정하지 않는다.",
        "scope.writable 밖 파일을 수정하지 않는다.",
        "PoC 구현 worker라면 README, 최종 테스트 결과서, browser smoke/screenshot, release/backlog 정리를 직접 완료 조건으로 삼지 않는다.",
    ],
    "required_outputs": [
        "수행한 변경과 빠른 self-check 결과를 Run 결과에 남긴다.",
        "실패 또는 미실행 항목은 원인과 다음 판단 필요 항목으로 반환한다.",
        "native 위임이면 delegation_records에 시작/종료 시각, duration_seconds, heartbeat/status probe 횟수, self-check와 Orchestrator 재검증 명령을 남긴다.",
    ],
}


def build_poc_run_input_preset(gate, skill, skill_path, run_rel_path, adapter=""):
    gate_working = POC_GATE_WORKING_DOCUMENTS.get(gate, ["docs/runs/"])
    gate_reference = compact_reference_documents_for_profile("poc", POC_GATE_REFERENCES.get(gate, []))
    run_rel_path = run_rel_path.replace("\\", "/")
    worker_run = skill in ("implementation-scaffold", "build-wave", "qa-execution", "qa-fix-loop")
    working_documents = merge_unique([run_rel_path], gate_working)
    source_read_first = filter_adapter_specific_docs(
        merge_unique(POC_COMMON_READ_FIRST_DOCS, adapter_read_first_docs(adapter), [skill_path] if skill_path else []),
        adapter,
    )
    verification_commands = [
        f"python vulcan.py run-check {run_rel_path}",
        "python vulcan.py profile-status",
    ]
    if gate in ("gate3", "gate4"):
        verification_commands.append("python vulcan.py check-trace")
    output_include = [
        "changed_files",
        "related_ids",
        "verification_results",
        "evidence",
        "delegation_records",
        "open_issues",
        "next_run_suggestion",
    ]
    if gate in ("gate4", "gate5"):
        output_include.extend(["findings", "change_requests"])
    return {
        "profile": "poc",
        "adapter": adapter or "codex-gpt",
        "skill": skill,
        "run_type": RUN_TYPES_BY_GATE.get(gate, "Review"),
        "worker_run": worker_run,
        "focused_source": False,
        "source_documents": {
            "read_first": source_read_first,
            "working_documents": working_documents,
            "reference_on_demand": filter_adapter_specific_docs(merge_unique(gate_reference), adapter),
            "optional": [],
        },
        "scope": {
            "writable": working_documents,
            "readonly": POC_COMMON_READONLY_DOCS,
            "excluded": POC_COMMON_EXCLUDED_PATHS,
        },
        "completion_criteria": POC_GATE_COMPLETION_CRITERIA.get(gate, POC_GATE_COMPLETION_CRITERIA["phase0"]),
        "design_sequence": [],
        "include_ui_policies": False,
        "verification": {
            "commands": verification_commands,
            "evidence": {
                "required": gate in ("gate4", "gate5"),
                "target_documents": merge_unique([run_rel_path], gate_working[:1]),
            },
        },
        "gate_exit_policy": POC_GATE_EXIT_POLICY,
        "ui_evidence_policy": AUDIT_UI_EVIDENCE_POLICY,
        "ui_implementation_contract_policy": AUDIT_UI_IMPLEMENTATION_CONTRACT_POLICY,
        "qa_execution_policy": {},
        "worker_execution_policy": POC_WORKER_EXECUTION_POLICY,
        "development_standards_applied": [],
        "development_standard_checklist": {},
        "output_requirements": {
            "format": "RUN_OUTPUT_CONTRACT.md",
            "include": merge_unique(output_include),
        },
        "question_policy": {
            "ask_when": [
                "PoC 목표, 가설, 성공 기준이 불명확하다.",
                "scope.writable 밖의 파일 수정이 필요하다.",
                "PoC 범위를 넘어 제품화 또는 audit 수준 결정이 필요하다.",
            ],
        },
        "security_policy": {
            "forbidden_paths": ["docs/ref-docs/"],
            "allowed_reference_paths": [],
            "forbidden_actions": [
                "토큰, 비밀번호, 개인식별정보를 커밋하지 않는다.",
                "민감문서 내용을 출력에 원문 인용하지 않는다.",
                "PoC 편의를 이유로 보안 위험을 완료 상태로 숨기지 않는다.",
            ],
        },
    }


def build_run_input_preset(profile, gate, skill, skill_path, run_rel_path, adapter=""):
    if profile == "poc":
        return build_poc_run_input_preset(gate, skill, skill_path, run_rel_path, adapter=adapter)

    if profile != "audit":
        return None

    gate_preset = AUDIT_GATE_PRESETS.get(gate)
    if not gate_preset:
        return None

    skill_preset = AUDIT_GATE_SKILL_PRESETS.get((gate, skill), {})
    gate_sample = gate_preset.get("sample")
    skill_sample = skill_preset.get("sample")
    skill_required = skill_preset.get("required", [])
    worker_run = bool(skill_preset.get("worker_run"))
    skill_has_working_docs = any(is_working_document(path) for path in skill_required)
    focused_source = skill in AUDIT_FOCUSED_SOURCE_SKILLS
    preset_working_documents = skill_preset.get("working") or gate_preset.get("working", [])
    if preset_working_documents:
        scoped_working_documents = merge_unique(preset_working_documents)
    elif focused_source:
        scoped_working_documents = []
    elif skill_preset.get("writable"):
        scoped_working_documents = working_documents_from_scope(skill_preset.get("writable", []))
    else:
        scoped_working_documents = working_documents_from_scope(gate_preset.get("writable", []))
    if skill_has_working_docs:
        source_candidates = merge_unique(AUDIT_GATE_ANCHOR_DOCS.get(gate, []), skill_required)
    elif focused_source:
        source_candidates = merge_unique(AUDIT_GATE_ANCHOR_DOCS.get(gate, []), skill_required)
    else:
        source_candidates = merge_unique(gate_preset.get("required", []), skill_required)
    run_rel_path = run_rel_path.replace("\\", "/")
    if worker_run:
        working_documents = merge_unique([run_rel_path], scoped_working_documents)
        reference_documents = [
            path for path in source_candidates
            if path not in working_documents and path not in scoped_working_documents
        ]
    elif scoped_working_documents:
        working_documents = scoped_working_documents
        reference_documents = [
            path for path in source_candidates
            if path not in working_documents and path not in scoped_working_documents
        ]
    else:
        working_documents, reference_documents = split_working_and_reference(source_candidates)
    source_read_first = merge_unique(
        AUDIT_COMMON_READ_FIRST_DOCS,
        adapter_read_first_docs(adapter),
        AUDIT_GATE_READ_FIRST_DOCS.get(gate, []),
        [skill_path],
    )
    source_read_first = filter_adapter_specific_docs(source_read_first, adapter)
    source_reference = merge_unique(
        AUDIT_COMMON_REFERENCE_DOCS,
        [gate_sample] if gate_sample else [],
        [skill_sample] if skill_sample else [],
        reference_documents,
    )
    source_reference = [path for path in source_reference if path not in source_read_first]
    source_reference = filter_adapter_specific_docs(source_reference, adapter)
    base_verification_commands = [f"python vulcan.py run-check {run_rel_path}"]
    if not worker_run:
        base_verification_commands.append("python vulcan.py check-trace")
    verification_commands = merge_unique(
        base_verification_commands,
        gate_preset.get("verification_commands", []),
        skill_preset.get("verification_commands", []),
    )
    if worker_run:
        verification_commands = [
            command for command in verification_commands
            if not is_orchestrator_only_command(command)
        ]
    base_evidence_targets = [run_rel_path]
    if not worker_run:
        base_evidence_targets.append("docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md")
    evidence_targets = merge_unique(
        base_evidence_targets,
        gate_preset.get("evidence_targets", []),
        skill_preset.get("evidence_targets", []),
    )
    writable_scope = skill_preset.get("writable") or gate_preset.get("writable", [])
    if worker_run and skill == "qa-execution":
        writable_scope = merge_unique(
            [run_rel_path],
            [path for path in writable_scope if path.replace("\\", "/") != "docs/runs/"],
        )
    completion_criteria = (
        skill_preset.get("completion_criteria", [])
        if skill_has_working_docs and skill_preset.get("completion_criteria")
        else merge_unique(gate_preset.get("completion_criteria", []), skill_preset.get("completion_criteria", []))
    )
    return {
        "profile": profile,
        "adapter": adapter or "codex-gpt",
        "skill": skill,
        "run_type": skill_preset.get("run_type", RUN_TYPES_BY_GATE.get(gate, "Review")),
        "worker_run": worker_run,
        "focused_source": focused_source,
        "source_documents": {
            "read_first": source_read_first,
            "working_documents": working_documents,
            "reference_on_demand": source_reference,
            "optional": merge_unique(gate_preset.get("optional", []), skill_preset.get("optional", [])),
        },
        "scope": {
            "writable": merge_unique(writable_scope),
            "readonly": merge_unique(AUDIT_COMMON_READONLY_DOCS, gate_preset.get("readonly", []), skill_preset.get("readonly", [])),
            "excluded": merge_unique(AUDIT_COMMON_EXCLUDED_PATHS, gate_preset.get("excluded", []), skill_preset.get("excluded", [])),
        },
        "completion_criteria": completion_criteria,
        "design_sequence": (
            merge_unique(gate_preset.get("design_sequence", []), skill_preset.get("design_sequence", []))
            if gate != "gate2" or skill in AUDIT_DESIGN_SEQUENCE_SKILLS
            else []
        ),
        "include_ui_policies": gate in ("gate3", "impl", "gate4") or skill in AUDIT_UI_POLICY_SKILLS,
        "verification": {
            "commands": verification_commands,
            "evidence": {
                "required": True,
                "target_documents": evidence_targets,
            },
        },
        "gate_exit_policy": AUDIT_GATE_EXIT_POLICY,
        "ui_evidence_policy": AUDIT_UI_EVIDENCE_POLICY,
        "ui_implementation_contract_policy": AUDIT_UI_IMPLEMENTATION_CONTRACT_POLICY,
        "qa_execution_policy": AUDIT_QA_EXECUTION_POLICY if skill == "qa-execution" else {},
        "worker_execution_policy": AUDIT_WORKER_EXECUTION_POLICY,
        "worker_run_sizing_policy": AUDIT_WORKER_RUN_SIZING_POLICY,
        "development_standards_applied": AUDIT_DEVELOPMENT_STANDARDS_APPLIED if worker_run and skill in ("build-wave", "implementation-scaffold") else [],
        "development_standard_checklist": AUDIT_DEVELOPMENT_STANDARD_CHECKLIST if worker_run and skill in ("build-wave", "implementation-scaffold") else {},
        "output_requirements": {
            "format": "RUN_OUTPUT_CONTRACT.md",
            "include": [
                "changed_files",
                "related_ids",
                "verification_results",
                "evidence",
                "delegation_records",
                *(
                    [
                        "failure_reports",
                    ]
                    if skill == "qa-execution"
                    else []
                ),
                "traceability_updates",
                "gate_exit_summary",
                "approval_request",
                "open_issues",
                "next_run_suggestion",
            ],
        },
        "question_policy": {
            "ask_when": [
                "요구사항, 설계문서, 기준 문서가 서로 충돌한다.",
                "scope.writable 밖의 파일 수정이 필요하다.",
                "프로젝트 도메인 정보가 부족해 실제 값을 채울 수 없다.",
                "보안 또는 감리 기준을 낮추는 선택이 필요하다.",
            ],
        },
        "security_policy": {
            "forbidden_paths": ["docs/ref-docs/"],
            "allowed_reference_paths": ["docs/seed-docs/reference-standards/"],
            "forbidden_actions": [
                "민감문서 내용을 출력에 원문 인용하지 않는다.",
                "토큰, 비밀번호, 개인식별정보를 커밋하지 않는다.",
                "승인 없이 외부 네트워크로 프로젝트 파일을 전송하지 않는다.",
            ],
        },
    }


def render_run_input_preset(preset, ids, persona, gate, trace_info=None):
    source = preset["source_documents"]
    scope = preset["scope"]
    verification = preset["verification"]
    evidence = verification["evidence"]
    output = preset["output_requirements"]
    question = preset["question_policy"]
    security = preset["security_policy"]
    gate_exit = preset["gate_exit_policy"]
    ui_evidence = preset["ui_evidence_policy"]
    ui_contract = preset["ui_implementation_contract_policy"]
    qa_execution = preset.get("qa_execution_policy", {})
    worker_policy = preset["worker_execution_policy"]
    sizing_policy = preset.get("worker_run_sizing_policy")
    dev_standards_applied = preset.get("development_standards_applied", [])
    dev_standard_checklist = preset.get("development_standard_checklist", {})
    target_contracts = classify_related_ids(ids)
    worker_run = bool(preset.get("worker_run"))
    skill = preset.get("skill", "")
    design_sequence = preset.get("design_sequence", [])
    design_sequence_block = ""
    design_sequence_instruction = ""
    if design_sequence:
        design_sequence_block = f"""
design_sequence:
{format_yaml_sequence(design_sequence, 2)}"""
        design_sequence_instruction = """
   - Gate 2 Run이면 `design_sequence`에서 현재 위치를 확인하고, 필요한 이전 단계 누락과 다음 Gate 2 Run 제안을 기록한다."""
    ui_evidence_block = ""
    ui_contract_block = ""
    qa_execution_block = ""
    qa_execution_instruction = ""
    if qa_execution:
        qa_execution_block = f"""
qa_execution_policy:
  worker_can_run_tests: {str(qa_execution["worker_can_run_tests"]).lower()}
  worker_can_write_evidence: {str(qa_execution["worker_can_write_evidence"]).lower()}
  worker_can_modify_source: {str(qa_execution["worker_can_modify_source"]).lower()}
  result_statuses: {format_yaml_list(qa_execution["result_statuses"])}
  qa_workspace_policy:
{format_yaml_sequence(qa_execution.get("qa_workspace_policy", []), 4)}
  qa000_required_checks:
{format_yaml_sequence(qa_execution.get("qa000_required_checks", []), 4)}
  qa000_doctor_evidence:
    command: {format_yaml_scalar(qa_execution.get("qa000_doctor_evidence", {}).get("command", "python vulcan.py doctor --json"))}
    json_evidence_path: {format_yaml_scalar(qa_execution.get("qa000_doctor_evidence", {}).get("json_evidence_path", "docs/artifacts/04-review/evidence/qa-000/QA-000-doctor.json"))}
    log_evidence_path: {format_yaml_scalar(qa_execution.get("qa000_doctor_evidence", {}).get("log_evidence_path", "docs/artifacts/04-review/evidence/qa-000/QA-000-doctor.log"))}
    interpretation:
{format_yaml_sequence(qa_execution.get("qa000_doctor_evidence", {}).get("interpretation", []), 6)}
  stages:
{format_yaml_sequence(qa_execution.get("stages", []), 4)}
  on_failure:
{format_yaml_sequence(qa_execution["on_failure"], 4)}
qa_failure_report_contract:
  required_when: {format_yaml_list(qa_execution["failure_report_contract"]["required_when"])}
  required_fields:
{format_yaml_sequence(qa_execution["failure_report_contract"]["required_fields"], 4)}
  candidate_classification_values: {format_yaml_list(qa_execution["failure_report_contract"]["candidate_classification_values"])}
  forbidden_actions:
{format_yaml_sequence(qa_execution["failure_report_contract"]["forbidden_actions"], 4)}"""
        qa_execution_instruction = """
- QA 실행 worker이면 테스트 실패 또는 이상 동작을 발견해도 소스코드를 수정하지 않는다.
- QA 실패는 `qa_failure_report_contract` 필드에 맞춰 원인 가설, 재현 명령, 로그 경로, 영향 ID, 후보 FIND/CR/ISSUE 또는 environment_blocked를 기록하고 Orchestrator 결정 필요 항목으로 반환한다.
- Gate 4 전체 QA를 한 Run에서 모두 수행하지 않는다. QA-000 환경 준비, QA-001 명령 검증, QA-002 UI/E2E 증적, QA-003 결과 정리 중 현재 Run의 범위를 명시한다.
- QA-000은 후속 QA-001/QA-002/QA-003이 재사용할 QA workspace 경로를 남긴다. 기본값은 workflow.integration_branch의 현재 작업공간이다.
- QA-000은 `python vulcan.py doctor --json` 결과를 `docs/artifacts/04-review/evidence/qa-000/QA-000-doctor.json`에 남기고, 환경 차단과 제품 결함을 분리한다.
- QA-001/QA-002/QA-003은 QA-000이 기록한 같은 QA workspace에서 실행한다.
- QA-000 환경 준비가 통과하지 않으면 QA-001/QA-002를 진행하지 않고 environment_blocked 또는 Not Run으로 반환한다."""
    if preset.get("include_ui_policies", True):
        ui_evidence_block = f"""
ui_evidence_policy:
  state_level_required: {str(ui_evidence["state_level_required"]).lower()}
  id_pattern: {format_yaml_scalar(ui_evidence["id_pattern"])}
  official_runner: {format_yaml_scalar(ui_evidence.get("official_runner", "@playwright/test"))}
  official_runner_command: {format_yaml_scalar(ui_evidence.get("official_runner_command", "npx playwright test"))}
  official_runner_required_profiles: {format_yaml_list(ui_evidence.get("official_runner_required_profiles", ["audit", "product"]))}
  poc_fallback_allowed: {str(ui_evidence.get("poc_fallback_allowed", True)).lower()}
  fallback_rule: {format_yaml_scalar(ui_evidence.get("fallback_rule", "PoC에서는 커스텀 Playwright script를 smoke/demo 증적으로 허용할 수 있지만, audit/product의 공식 UI Pass는 @playwright/test 실행 결과를 기준으로 한다."))}
  required_artifacts:
{format_yaml_sequence(ui_evidence.get("required_artifacts", []), 4)}
  minimum_fields:
{format_yaml_sequence(ui_evidence["minimum_fields"], 4)}
  examples:
{format_yaml_sequence(ui_evidence["examples"], 4)}"""
        ui_contract_block = f"""
ui_implementation_contract_policy:
  required_when: {format_yaml_scalar(ui_contract["required_when"])}
  gate2_required_fields:
{format_yaml_sequence(ui_contract["gate2_required_fields"], 4)}
  impl_checklist:
{format_yaml_sequence(ui_contract["impl_checklist"], 4)}
  gate4_required_evidence:
{format_yaml_sequence(ui_contract["gate4_required_evidence"], 4)}"""
        gate_finish_instruction = (
            "- 작업자 runner이면 Gate 진행 승인 질문을 사용자에게 직접 하지 말고 Orchestrator 결정 필요 항목으로 반환한다."
            if worker_run
            else "- Gate 산출물 완료 후에는 다음 Gate로 진행하지 말고 사용자 승인 질문을 남긴 뒤 대기한다."
        )
        ui_instruction_block = f"""
- UI 검증이 포함되면 `ui_evidence_policy`에 따라 상태/시나리오별 UI-ID와 증적 파일을 1:1로 연결한다.
- UIREF, 화면 퍼블리싱 산출물, 외부 시안이 있으면 `ui_implementation_contract_policy`에 따라 설계-구현-증적 비교 기준을 남긴다.
- subagent, CLI, 별도 worktree에서 작업자 runner로 실행 중이면 `worker_execution_policy`를 따른다.
- 기준 충돌, 범위 초과, 도메인 정보 부족은 임의로 통과시키지 말고 `open_issues`에 남기거나 사용자에게 질문한다.
{gate_finish_instruction}"""
    else:
        gate_finish_instruction = (
            "- 작업자 runner이면 Gate 진행 승인 질문을 사용자에게 직접 하지 말고 Orchestrator 결정 필요 항목으로 반환한다."
            if worker_run
            else "- Gate 산출물 완료 후에는 다음 Gate로 진행하지 말고 사용자 승인 질문을 남긴 뒤 대기한다."
        )
        ui_instruction_block = f"""
- subagent, CLI, 별도 worktree에서 작업자 runner로 실행 중이면 `worker_execution_policy`를 따른다.
- 기준 충돌, 범위 초과, 도메인 정보 부족은 임의로 통과시키지 말고 `open_issues`에 남기거나 사용자에게 질문한다.
{gate_finish_instruction}"""

    read_first_docs = source.get("read_first", [])
    working_docs = source.get("working_documents", [])
    reference_docs = source.get("reference_on_demand", [])
    optional_docs = source.get("optional", [])
    contract_detail_block = ""
    implementation_worker = worker_run and skill in ("build-wave", "implementation-scaffold")
    if implementation_worker:
        contract_detail_block = """
  interface_contract:
    language: "TBD: Program Design 기준 언어/런타임"
    signatures:
      - "TBD: PGM/IF/MTH public signature를 Program Design에서 복사"
    schemas:
      - "TBD: DTO/Entity/State schema를 Program Design에서 복사"
    error_contracts:
      - "TBD: 오류 코드/예외/사용자 메시지 계약을 Program Design/API/Security에서 복사"
"""
        if skill == "implementation-scaffold":
            contract_detail_block += """  contract_skeleton:
    mode: "new|existing-alignment|not-required"
    files:
      - path: "TBD: skeleton 파일 경로"
        create: "TBD: 생성/확인할 class/interface/method/DTO"
    forbidden:
      - "업무 로직 완성"
      - "전체 E2E 또는 Gate 4 QA Pass 선언"
    smoke_commands:
      - "TBD: compile/import/build smoke 명령"
"""
    if worker_run:
        if skill == "qa-execution":
            completion_action_line = "- `completion_criteria`를 모두 만족하도록 테스트 실행 결과, 로그/화면 증적, 후보 FIND/CR/ISSUE, 자기 Run 기록을 갱신한다."
        else:
            completion_action_line = "- `completion_criteria`를 모두 만족하도록 담당 코드, 테스트, 증적, 자기 Run 기록을 갱신한다."
        if skill == "qa-execution":
            completion_policy_section = """## 5. QA Worker 완료 및 Orchestrator 반환

Run을 완료할 때 다음 항목을 반드시 남긴다.

| 항목 | 작성 기준 |
| --- | --- |
| 실행 검증 요약 | 실행한 명령, cwd, exit code, 성공 기준, 결과 |
| 증적 | 로그, screenshot, trace, report 파일 경로와 관련 UT/IT/UI ID |
| 실패/차단 분류 | `Fail`, `Not Run`, `Skipped`, `environment_blocked` 사유 |
| 원인 가설 | 실패 재현 명령, 영향 ID, 관련 로그 위치 |
| 후보 분류 | 승인된 설계 범위 안이면 FIND 후보, 범위 변경이면 CR 후보, 판단 보류면 ISSUE 후보 |
| Orchestrator 결정 필요 | 수정 여부, 재실행 여부, CR 승격 여부, Gate 완료 판단 필요 항목 |

QA 실행 worker는 소스코드를 수정하지 않고, 사용자 승인 질문, Gate 완료 선언, QA Pass, 릴리즈 승인, merge 가능 판단을 직접 하지 않는다."""
        else:
            completion_policy_section = """## 5. Worker 완료 및 Orchestrator 반환

Run을 완료할 때 다음 항목을 반드시 남긴다.

| 항목 | 작성 기준 |
| --- | --- |
| 담당 Wave 산출물 요약 | 담당 범위에서 작성/수정한 코드, 테스트, 증적과 관련 ID |
| Worker self-check | 가능하면 실행한 담당 영역 테스트, 빌드, 린트, Run check와 결과 |
| Orchestrator 재검증 명령 | 구현 에이전트가 작성/갱신한 테스트케이스를 메인 에이전트가 재실행할 명령 |
| Orchestrator 결정 필요 | 추적표 갱신, session 갱신, wave-complete, check-trace, Gate 진행 판단 필요 항목 |
| 미해결 항목 | `open_issues`, `findings`, `change_requests` |
| 범위 밖 요청 | `scope.writable` 밖 수정이 필요한 이유와 후보 경로 |

작업자 runner는 사용자 승인 질문, Gate 완료 선언, QA Pass, 릴리즈 승인, merge 가능 판단을 직접 하지 않는다."""
    else:
        completion_action_line = "- `completion_criteria`를 모두 만족하도록 문서, 추적표, Run 기록을 갱신한다."
        completion_policy_section = """## 5. Gate 종료 및 승인 대기

Run을 완료할 때 다음 항목을 반드시 남긴다.

| 항목 | 작성 기준 |
| --- | --- |
| 현재 Gate 산출물 요약 | 이번 Gate에서 작성/수정한 산출물과 관련 ID |
| 미해결 항목 | `open_issues`, `findings`, `change_requests` |
| 다음 Gate 제안 | 다음 Gate에서 수행할 Run 후보 |
| 사용자 승인 질문 | "다음 Gate로 진행해도 되는지"를 명시적으로 질문 |
| 승인 증적 | 대화에서 사용자가 명시 승인한 문구 또는 승인 보류 사유 |

사용자 승인 전에는 다음 Gate 산출물 작성, 구현 착수, QA Pass, Gate 5 승인 선언을 하지 않는다."""
    if implementation_worker and (dev_standards_applied or dev_standard_checklist):
        development_standard_block = f"""
development_standards_applied:
{format_development_standards_applied(dev_standards_applied, 2)}
development_standard_checklist:
{format_development_standard_checklist(dev_standard_checklist, 2)}"""
    elif implementation_worker:
        development_standard_block = ""
    else:
        development_standard_block = ""
    if implementation_worker:
        run_scope_instruction = "- worker Run은 기능/계약 단위로 끝나는 완결 조각이어야 하며, 시간은 10분 내외/최대 15분 권장 보조 기준으로만 사용한다."
        verification_instruction = "- 구현 worker Run이면 테스트케이스와 Orchestrator가 재실행할 `verification.commands`를 남긴다. 가능하면 self-check로 실행하되 최종 검증은 Orchestrator가 재실행한다."
    elif skill == "qa-execution":
        run_scope_instruction = "- QA 실행 worker Run은 테스트 실행/증적 수집/원인 분류 단위로 끝나는 완결 조각이어야 한다."
        verification_instruction = "- QA 실행 worker Run이면 실행한 명령과 Orchestrator가 재실행할 `verification.commands`를 결과 문서에 남긴다."
    else:
        run_scope_instruction = "- Run은 현재 Gate와 related_ids 범위 안에서 완료 가능한 산출물 또는 검토 단위로 끝나야 한다."
        verification_instruction = "- 실행하거나 확인한 검증 명령과 결과를 Run 기록에 남긴다."
    return f"""## 3. Run 입력 계약

```yaml
profile: {format_yaml_scalar(preset["profile"])}
adapter: {format_yaml_scalar(preset.get("adapter", "codex-gpt"))}
run_type: {format_yaml_scalar(preset["run_type"])}
gate: {format_yaml_scalar(gate)}
related_ids: {format_yaml_list(ids)}
{format_trace_context_metadata(trace_info)}
target_contracts:
{format_yaml_mapping_sequences(target_contracts, 2)}{contract_detail_block}
persona: {format_yaml_scalar(persona)}
source_documents:
  read_first:
{format_yaml_sequence(read_first_docs, 4)}
  working_documents:
{format_yaml_sequence(working_docs, 4)}
  reference_on_demand:
{format_yaml_sequence(reference_docs, 4)}
  optional:
{format_yaml_sequence(optional_docs, 4)}{design_sequence_block}
scope:
  writable:
{format_yaml_sequence(scope["writable"], 4)}
  readonly:
{format_yaml_sequence(scope["readonly"], 4)}
  excluded:
{format_yaml_sequence(scope["excluded"], 4)}
completion_criteria:
{format_yaml_sequence(preset["completion_criteria"], 2)}
{development_standard_block}
{qa_execution_block}
verification:
  commands:
{format_yaml_sequence(verification["commands"], 4)}
  evidence:
    required: {str(evidence["required"]).lower()}
    target_documents:
{format_yaml_sequence(evidence["target_documents"], 6)}
{f'''worker_run_sizing_policy:
  primary_split_basis: {format_yaml_scalar(sizing_policy["primary_split_basis"])}
  time_is_secondary: {str(sizing_policy["time_is_secondary"]).lower()}
  target_duration_minutes: {sizing_policy["target_duration_minutes"]}
  max_duration_minutes: {sizing_policy["max_duration_minutes"]}
  rules:
{format_yaml_sequence(sizing_policy["rules"], 4)}''' if implementation_worker and sizing_policy else ""}
output_requirements:
  format: {format_yaml_scalar(output["format"])}
  include:
{format_yaml_sequence(output["include"], 4)}
```

## 4. 수행 지시

- `source_documents.read_first`만 먼저 읽고 현재 Gate, skill, 관련 ID를 확인한다.
{"  - 구현 worker Run이면 `target_contracts`의 FUNC/PGM/API/DB/SEC/TEST 묶음을 먼저 확인한다." if implementation_worker else ""}
{"- 구현 worker Run이면 `target_contracts.interface_contract`의 public signature, schema, error contract를 먼저 구현 경계로 삼는다." if implementation_worker else ""}
{"- scaffold Run이면 `target_contracts.contract_skeleton`의 파일과 smoke 검증을 먼저 확인하고 업무 로직 구현을 완료 처리하지 않는다." if skill == "implementation-scaffold" else ""}
{"- 구현 worker Run이면 `development_standards_applied`와 `development_standard_checklist`를 코드/테스트 작성 체크리스트로 사용하고 결과 보고에 준수/예외를 남긴다." if implementation_worker else ""}
- `source_documents.working_documents`를 중심으로 실제 산출물을 작성하거나 검토한다.
- `source_documents.reference_on_demand`는 기준 충돌, 작성 규칙 확인, 상세 판단이 필요할 때만 참고한다.
- 전역 memory, 과거 세션 요약, 다른 샘플 프로젝트 기억은 현재 Run의 근거로 사용하지 않는다.
- `scope.writable` 안에서만 산출물을 수정한다.{design_sequence_instruction}
{completion_action_line}
{run_scope_instruction}
- 실제 프로젝트 값으로 작성하고 placeholder를 완료 산출물에 남기지 않는다.
{verification_instruction}
{qa_execution_instruction}
{ui_instruction_block}

{completion_policy_section}"""


def default_persona_for_run(gate, skill):
    skill_persona = RUN_SKILL_DEFAULT_PERSONAS.get(skill)
    if skill_persona:
        return skill_persona

    return GATE_DEFAULT_PERSONAS.get(gate, "review")


def load_session(project_dir="."):
    path = os.path.join(project_dir, "session.json")
    if not os.path.exists(path):
        print("오류: session.json을 찾을 수 없습니다. 프로젝트 디렉토리에서 실행하세요.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_session(session, project_dir="."):
    path = os.path.join(project_dir, "session.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def refresh_session_stats(session, project_dir="."):
    stats = compute_stats(project_dir)
    implementation = stats.get("implementation") or compute_implementation_progress(project_dir, session=session)
    session["implementation"] = implementation
    session["stats"] = stats
    session["stats"]["implementation"] = implementation
    return session


def git_commit(message, project_dir=".", include_source=False, paths=None):
    try:
        if paths is None:
            paths = ["session.json", "docs/"]
        for path in paths:
            subprocess.run(["git", "add", path], cwd=project_dir, check=True, capture_output=True)
        if include_source:
            # 구현/QA 이후: .gitignore가 관리하는 범위 내에서 모든 변경 포함
            subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True, capture_output=True)

        staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=project_dir)
        if staged.returncode == 0:
            print(f"  커밋 생략: 변경 없음 ({message})")
            return False

        subprocess.run(["git", "commit", "-m", message], cwd=project_dir, check=True, capture_output=True)
        print(f"  커밋 완료: {message}")
        return True
    except subprocess.CalledProcessError as e:
        # git commit 실패는 경고만 출력하고 계속 진행 (git_push와 다른 동작)
        stdout = e.stdout.decode(errors="replace").strip() if e.stdout else ""
        stderr = e.stderr.decode(errors="replace").strip() if e.stderr else ""
        detail = "\n".join(part for part in [stderr, stdout] if part).strip()
        print(f"  경고: git commit 실패 - {detail or '상세 메시지 없음'}")
        return False


def git_push(project_dir="."):
    """현재 프로젝트 디렉토리에서 git push를 실행합니다.

    git commit과 달리 push 실패는 프로세스를 즉시 중단합니다 (REQ-006-02).

    Args:
        project_dir: git push를 실행할 프로젝트 디렉토리 경로.
    """
    try:
        result = subprocess.run(
            ["git", "push"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        print(f"  푸시 완료")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace").strip()
        if "has no upstream branch" in stderr:
            try:
                subprocess.run(
                    ["git", "push", "-u", "origin", "HEAD"],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                )
                print("  푸시 완료: origin HEAD")
                return
            except subprocess.CalledProcessError as retry_error:
                stderr = retry_error.stderr.decode(errors="replace").strip()
        print(f"git push 실패: {stderr}")
        sys.exit(1)


def has_git_remote(project_dir=".", remote="origin"):
    result = subprocess.run(
        ["git", "remote", "get-url", remote],
        cwd=project_dir,
        capture_output=True,
    )
    return result.returncode == 0


def version_run_document(rel_path, message, project_dir="."):
    committed = git_commit(message, project_dir, paths=[rel_path])
    if not committed:
        return
    git_push_if_remote(project_dir)


def git_push_if_remote(project_dir="."):
    if has_git_remote(project_dir):
        git_push(project_dir)
        return True
    print("  푸시 생략: git remote origin 없음")
    return False


# ── check-trace ────────────────────────────────────────────────────────────

def count_docs(project_dir="."):
    """docs/ 하위 4개 디렉토리의 .md 파일 수를 카운트한다.

    서브디렉토리 내 .md 파일도 포함한다. 디렉토리가 없거나 권한 오류 시
    해당 카테고리를 0으로 처리하고 계속 진행한다 (graceful).

    Args:
        project_dir: 프로젝트 루트 디렉토리 경로.

    Returns:
        requirements, design, test_plan, review 카테고리별 .md 파일 수와
        total 합계를 담은 dict.
    """
    categories = {
        "discovery": [
            os.path.join(project_dir, "docs", "artifacts", "00-discovery"),
            os.path.join(project_dir, "docs", "00-discovery"),
        ],
        "requirements": [
            os.path.join(project_dir, "docs", "artifacts", "01-requirements"),
            os.path.join(project_dir, "docs", "01-requirements"),
        ],
        "design": [
            os.path.join(project_dir, "docs", "artifacts", "02-design"),
            os.path.join(project_dir, "docs", "02-design"),
        ],
        "test_plan": [
            os.path.join(project_dir, "docs", "artifacts", "03-test"),
            os.path.join(project_dir, "docs", "03-test-plan"),
        ],
        "review": [
            os.path.join(project_dir, "docs", "artifacts", "04-review"),
            os.path.join(project_dir, "docs", "04-review"),
        ],
        "release": [
            os.path.join(project_dir, "docs", "artifacts", "07-release"),
        ],
        "backlog": [
            os.path.join(project_dir, "docs", "artifacts", "05-change"),
            os.path.join(project_dir, "docs", "backlog"),
        ],
        "runs": [
            os.path.join(project_dir, "docs", "runs"),
        ],
    }
    counts = {}
    for key, dir_paths in categories.items():
        count = 0
        existing_dirs = [dir_path for dir_path in dir_paths if os.path.isdir(dir_path)]
        dirs_to_count = existing_dirs[:1]
        for dir_path in dirs_to_count:
            try:
                for root, _dirs, files in os.walk(dir_path):
                    count += sum(1 for f in files if f.endswith(".md"))
            except OSError:
                # 디렉토리 미존재 또는 권한 오류 — 0으로 처리하고 계속 진행
                continue
        counts[key] = count
    counts["total"] = sum(counts.values())
    return counts


def find_first_existing(project_dir, candidates):
    for rel_path in candidates:
        path = os.path.join(project_dir, rel_path)
        if os.path.exists(path):
            return path
    return None


def find_artifact_file(project_dir, rel_dir, name_pattern):
    base = os.path.join(project_dir, rel_dir)
    if not os.path.isdir(base):
        return None
    for root, _dirs, files in os.walk(base):
        for filename in files:
            if re.search(name_pattern, filename, re.IGNORECASE):
                return os.path.join(root, filename)
    return None


def compute_stats(project_dir="."):
    """check-trace에서 수집한 파싱 결과를 조합하여 stats 딕셔너리를 조립한다.

    parse_requirements, parse_test_plan_status, count_docs, parse_traceability를
    호출하여 요구사항/테스트/문서 통계를 단일 dict로 반환한다. 파싱 실패 시
    해당 섹션을 0 기본값으로 채우고 예외를 전파하지 않는다.

    Args:
        project_dir: 프로젝트 루트 디렉토리 경로.

    Returns:
        requirements, tests, docs 섹션과 updated_at을 포함한 stats dict.
    """
    profile = load_delivery_profile(project_dir)
    if profile == "poc":
        return compute_poc_stats(project_dir)
    if profile in {"product", "solution"}:
        return compute_product_stats(project_dir)

    # requirements 섹션
    try:
        group_reqs, detail_reqs, defined_acs, ac_delegates = parse_requirements(project_dir)
        traceability = parse_traceability(project_dir)
        implemented = sum(
            1 for info in traceability.values()
            if info.get("status") in ("구현완료", "완료", "Implemented", "Verified")
        )
        total_reqs = len(detail_reqs)
        # ac가 있는 REQ: defined_acs에 해당 AC-ID가 있거나 ac_delegates에 위임 참조가 있는 경우
        ac_covered = sum(
            1 for req in detail_reqs
            if req.replace("REQ-", "") in defined_acs
            or req.replace("REQ-", "") in ac_delegates
        )
        requirements_stats = {
            "groups":      len(group_reqs),
            "total":       total_reqs,
            "implemented": implemented,
            "pending":     total_reqs - implemented,
            "ac_defined":  ac_covered,
            "ac_missing":  total_reqs - ac_covered,
        }
    except Exception:
        requirements_stats = {
            "groups": 0, "total": 0, "implemented": 0,
            "pending": 0, "ac_defined": 0, "ac_missing": 0,
        }

    # tests 섹션
    try:
        tst_results, _source = parse_effective_test_status(project_dir)
        tests_stats = {
            "total":   len(tst_results),
            "passed":  sum(1 for _, s in tst_results if s == "pass"),
            "failed":  sum(1 for _, s in tst_results if s == "fail"),
            "skipped": sum(1 for _, s in tst_results if s == "skip"),
            "pending": sum(1 for _, s in tst_results if s in ("not_executed", "environment_blocked")),
        }
    except Exception:
        tests_stats = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "pending": 0}

    # docs 섹션
    try:
        docs_stats = count_docs(project_dir)
    except Exception:
        docs_stats = {"requirements": 0, "design": 0, "test_plan": 0, "review": 0, "total": 0}

    # backlog 섹션
    try:
        backlog_stats = compute_backlog_stats(project_dir)
    except Exception:
        backlog_stats = {
            "active": 0, "done": 0, "rejected": 0,
            "by_level": {"trivial": 0, "small": 0, "major": 0},
            "by_priority": {"p0": 0, "p1": 0, "p2": 0, "p3": 0},
        }

    try:
        implementation_stats = compute_implementation_progress(project_dir)
    except Exception:
        implementation_stats = {
            "requirements": {"total": 0, "implemented": 0, "pending": 0, "completed_ids": []},
            "waves": {"total": 0, "completed": 0, "current": "", "items": []},
        }

    return {
        "requirements": requirements_stats,
        "implementation": implementation_stats,
        "tests":        tests_stats,
        "docs":         docs_stats,
        "backlog":      backlog_stats,
        "updated_at":   date.today().isoformat(),
    }


def _ids_from_text(pattern, content):
    return sorted(set(re.findall(pattern, content or "")))


def parse_product_trace_rows(project_dir="."):
    path = os.path.join(project_dir, "docs", "product", "PRODUCT_TRACEABILITY.md")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return []

    rows = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "SCN-" not in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 8 or not re.fullmatch(r"SCN-\d{3}", cells[0]):
            continue
        req_ids = sorted(set(re.findall(r"\bREQ-\d{3}\b", cells[1])))
        rows.append(
            {
                "scenario": cells[0],
                "requirements": req_ids,
                "implementation": cells[4],
                "regression": cells[5],
                "release_evidence": cells[6],
                "status": cells[7],
            }
        )
    return rows


def _product_row_is_implemented(row):
    implementation = (row.get("implementation") or "").strip()
    status = (row.get("status") or "").strip()
    if not implementation or re.fullmatch(r"(?i)(tbd|planned|not run|n/a|-)", implementation):
        return False
    implemented_status = re.search(
        r"(?i)\b(impl self-check passed|implemented|verified|done|pass|passed)\b",
        status,
    )
    return bool(implemented_status or re.search(r"`[^`]+`", implementation))


def _product_test_status_counts(project_dir="."):
    path = os.path.join(project_dir, "docs", "product", "REGRESSION_AND_RELEASE_REPORT.md")
    if not os.path.exists(path):
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "pending": 0}
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        content = ""
    counts = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "pending": 0}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "REG-" not in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"REG-\d{3}", cells[0]):
            continue
        counts["total"] += 1
        result_text = " ".join(cells[1:4]).lower()
        if re.search(r"\bpass(?:ed)?\b|verified", result_text):
            counts["passed"] += 1
        elif re.search(r"\bfail(?:ed)?\b", result_text):
            counts["failed"] += 1
        elif re.search(r"\bskip(?:ped)?\b", result_text):
            counts["skipped"] += 1
        else:
            counts["pending"] += 1
    return counts


def compute_product_stats(project_dir="."):
    rows = parse_product_trace_rows(project_dir)
    req_ids = sorted({req_id for row in rows for req_id in row.get("requirements", [])})
    implemented_req_ids = sorted({
        req_id
        for row in rows
        if _product_row_is_implemented(row)
        for req_id in row.get("requirements", [])
    })
    try:
        docs_stats = count_docs(project_dir)
    except Exception:
        docs_stats = {"requirements": 0, "design": 0, "test_plan": 0, "review": 0, "total": 0}
    try:
        backlog_stats = compute_backlog_stats(project_dir)
    except Exception:
        backlog_stats = {
            "active": 0,
            "done": 0,
            "rejected": 0,
            "by_level": {"trivial": 0, "small": 0, "major": 0},
            "by_priority": {"p0": 0, "p1": 0, "p2": 0, "p3": 0},
        }
    try:
        implementation_stats = compute_implementation_progress(project_dir)
    except Exception:
        implementation_stats = {
            "requirements": {"total": 0, "implemented": 0, "pending": 0, "completed_ids": []},
            "waves": {"total": 0, "completed": 0, "current": "", "items": []},
        }
    implementation_stats = dict(implementation_stats)
    implementation_stats["requirements"] = {
        "total": len(req_ids),
        "implemented": len(implemented_req_ids),
        "pending": max(0, len(req_ids) - len(implemented_req_ids)),
        "completed_ids": implemented_req_ids,
    }
    requirements_stats = {
        "groups": len(rows),
        "total": len(req_ids),
        "implemented": len(implemented_req_ids),
        "pending": max(0, len(req_ids) - len(implemented_req_ids)),
        "ac_defined": len(req_ids),
        "ac_missing": 0,
    }
    return {
        "requirements": requirements_stats,
        "implementation": implementation_stats,
        "tests": _product_test_status_counts(project_dir),
        "docs": docs_stats,
        "backlog": backlog_stats,
        "updated_at": date.today().isoformat(),
        "product": {
            "scenarios": {"total": len(rows), "ids": [row["scenario"] for row in rows]},
            "requirements": {"total": len(req_ids), "implemented": len(implemented_req_ids), "ids": req_ids, "implemented_ids": implemented_req_ids},
        },
    }


def _poc_test_status_counts(test_content):
    rank = {"pending": 0, "skipped": 1, "passed": 2, "failed": 3}
    seen = {}
    for line in (test_content or "").splitlines():
        if "|" not in line:
            continue
        ids = re.findall(r"\bT-(?:[A-Z]+-)?\d{3}\b", line)
        if not ids:
            continue
        lowered = line.lower()
        if "fail" in lowered:
            status = "failed"
        elif "environment_blocked" in lowered or "environment blocked" in lowered:
            status = "pending"
        elif "not run" in lowered or "not_run" in lowered or "skipped" in lowered:
            status = "skipped"
        elif "planned" in lowered or "tbd" in lowered:
            status = "pending"
        elif "pass" in lowered or "통과" in lowered:
            status = "passed"
        else:
            status = "pending"
        for test_id in ids:
            previous = seen.get(test_id)
            if previous is None or rank[status] > rank[previous]:
                seen[test_id] = status
    counts = {"total": len(seen), "passed": 0, "failed": 0, "skipped": 0, "pending": 0}
    for status in seen.values():
        counts[status] += 1
    return counts


def _poc_existing_pass_evidence_paths(project_dir, test_content):
    paths = []
    for line in (test_content or "").splitlines():
        if "|" not in line or not re.search(r"\bEV-(?:[A-Z]+-)?\d{3}\b", line):
            continue
        lowered = line.lower()
        if not ("pass" in lowered or "통과" in lowered or "observed" in lowered):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        candidate = cells[2].strip()
        if not candidate or re.search(r"(?i)\b(TBD|미정|확정필요|not\s+run|planned)\b", candidate):
            continue
        link_match = re.search(r"\]\(([^)]+)\)", candidate)
        if link_match:
            candidate = link_match.group(1)
        candidate = candidate.split("<br>")[0].strip().strip("`")
        if re.match(r"^[a-zA-Z]+://", candidate):
            paths.append(candidate)
            continue
        abs_path = candidate if os.path.isabs(candidate) else os.path.join(project_dir, candidate)
        if os.path.exists(abs_path):
            paths.append(candidate)
    return paths


def compute_poc_stats(project_dir="."):
    req_content = read_project_text(project_dir, "docs/poc/POC_REQUIREMENTS.md")
    design_content = read_project_text(project_dir, "docs/poc/POC_SYSTEM_DESIGN.md")
    test_content = read_project_text(project_dir, "docs/poc/POC_TEST_REPORT.md")

    hyp_ids = _ids_from_text(r"\bHYP-\d{3}\b", req_content)
    req_ids = _ids_from_text(r"\bREQ-\d{3}\b", req_content)
    nreq_ids = _ids_from_text(r"\bNREQ-\d{3}\b", req_content)
    ac_ids = _ids_from_text(r"\bAC-(?:NREQ-)?\d{3}-\d{2}\b", req_content)
    test_link_text = test_content or ""
    has_pass_evidence = bool(_poc_existing_pass_evidence_paths(project_dir, test_content))
    implemented_req_ids = [
        req_id
        for req_id in req_ids
        if has_pass_evidence and req_id in test_link_text and re.search(r"\bPass\b", test_link_text, re.IGNORECASE)
    ]
    api_ids = _ids_from_text(r"\bAPI-\d{3}\b", design_content)
    data_ids = _ids_from_text(r"\bDATA-\d{3}\b", design_content)
    scr_ids = _ids_from_text(r"\bSCR-\d{3}\b", design_content)
    app_ids = _ids_from_text(r"\bAPP-\d{3}\b", design_content)
    evidence_ids = _ids_from_text(r"\bEV-(?:[A-Z]+-)?\d{3}\b", test_content)

    tests_stats = _poc_test_status_counts(test_content)
    requirements_stats = {
        "groups": len(hyp_ids),
        "total": len(req_ids),
        "implemented": len(implemented_req_ids),
        "pending": max(0, len(req_ids) - len(implemented_req_ids)),
        "ac_defined": len(ac_ids),
        "ac_missing": 0,
        "nreq_total": len(nreq_ids),
    }

    try:
        docs_stats = count_docs(project_dir)
    except Exception:
        docs_stats = {"requirements": 0, "design": 0, "test_plan": 0, "review": 0, "total": 0}
    try:
        backlog_stats = compute_backlog_stats(project_dir)
    except Exception:
        backlog_stats = {
            "active": 0, "done": 0, "rejected": 0,
            "by_level": {"trivial": 0, "small": 0, "major": 0},
            "by_priority": {"p0": 0, "p1": 0, "p2": 0, "p3": 0},
        }
    try:
        implementation_stats = compute_implementation_progress(project_dir)
    except Exception:
        implementation_stats = {
            "requirements": {"total": 0, "implemented": 0, "pending": 0, "completed_ids": []},
            "waves": {"total": 0, "completed": 0, "current": "", "items": []},
        }
    implementation_stats = dict(implementation_stats)
    implementation_stats["requirements"] = {
        "total": len(req_ids),
        "implemented": len(implemented_req_ids),
        "pending": max(0, len(req_ids) - len(implemented_req_ids)),
        "completed_ids": implemented_req_ids,
    }

    return {
        "requirements": requirements_stats,
        "implementation": implementation_stats,
        "tests": tests_stats,
        "docs": docs_stats,
        "backlog": backlog_stats,
        "poc": {
            "hypotheses": {"total": len(hyp_ids), "ids": hyp_ids},
            "requirements": {"total": len(req_ids), "implemented": len(implemented_req_ids), "ids": req_ids, "implemented_ids": implemented_req_ids},
            "nreq": {"total": len(nreq_ids), "ids": nreq_ids},
            "design": {
                "api": {"total": len(api_ids), "ids": api_ids},
                "data": {"total": len(data_ids), "ids": data_ids},
                "screen": {"total": len(scr_ids), "ids": scr_ids},
                "app": {"total": len(app_ids), "ids": app_ids},
            },
            "tests": {"total": tests_stats["total"]},
            "evidence": {"total": len(evidence_ids), "ids": evidence_ids},
        },
        "updated_at": date.today().isoformat(),
    }


WAVE_DONE_STATUSES = {"Implemented", "Verified", "Completed", "Done"}
WAVE_ACTIVE_STATUSES = {"InProgress", "In Progress", "Running", "Review Requested"}
WAVE_KNOWN_STATUSES = WAVE_DONE_STATUSES | WAVE_ACTIVE_STATUSES | {"Planned", "Blocked", "CompletedWithIssues", "Rolled Back"}
WAVE_STATUS_RANK = {
    "Planned": 0,
    "InProgress": 1,
    "In Progress": 1,
    "Running": 1,
    "Review Requested": 2,
    "Blocked": 2,
    "CompletedWithIssues": 2,
    "Implemented": 3,
    "Verified": 4,
    "Completed": 4,
    "Done": 4,
    "Rolled Back": 4,
}

BUILD_WAVE_RELATED_ID_RE = re.compile(
    r"\b(?:"
    r"SCN|REQ|AC|FUNC|SCR|UIREF|UICON|PGM|API|DB|DATA|SEC|UT|IT|PT|UI|REG"
    r")-\d{3}(?:-\d{2})?\b",
    re.IGNORECASE,
)


def find_run_files(project_dir="."):
    runs_dir = os.path.join(project_dir, runs_rel_dir(project_dir))
    if not os.path.isdir(runs_dir):
        return []
    return [
        os.path.join(runs_dir, name)
        for name in sorted(os.listdir(runs_dir))
        if name.lower().endswith(".md")
    ]


def find_wave_run_file(project_dir, bw_id):
    pattern = re.compile(rf"\b{re.escape(bw_id)}\b", re.IGNORECASE)
    for path in find_run_files(project_dir):
        basename = os.path.basename(path)
        if not pattern.search(basename):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            content = ""
        metadata = parse_simple_yaml_block(content)
        if str(metadata.get("bw_id", "")).lower() == bw_id.lower() or re.search(
            r"build-wave|implementation-scaffold",
            basename,
            re.IGNORECASE,
        ):
            return path

    for path in find_run_files(project_dir):
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        metadata = parse_simple_yaml_block(content)
        if str(metadata.get("bw_id", "")).lower() == bw_id.lower():
            return path
    return None


def find_run_file(project_dir, run_id):
    target = run_id.lower()
    for path in find_run_files(project_dir):
        stem = os.path.splitext(os.path.basename(path))[0].lower()
        if stem == target or stem.startswith(f"{target}_") or stem.startswith(f"{target}-"):
            return path

    for path in find_run_files(project_dir):
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        metadata = parse_simple_yaml_block(content)
        if metadata.get("run_id", "").lower() == target:
            return path
    return None


def parse_simple_yaml_text(yaml_text):
    result = {}
    current_list_key = None
    for raw_line in yaml_text.splitlines():
        if raw_line.startswith((" ", "\t", "-")):
            if current_list_key and re.match(r"^\s*-\s+", raw_line):
                item = re.sub(r"^\s*-\s+", "", raw_line).strip().strip('"').strip("'")
                if item:
                    result.setdefault(current_list_key, []).append(item)
            continue
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            current_list_key = None
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            result[key] = value.strip('"').strip("'")
            current_list_key = None
        else:
            result[key] = []
            current_list_key = key
    return result


def parse_simple_yaml_block(content):
    match = re.search(r"```yaml\s*(.*?)```", content, re.DOTALL | re.IGNORECASE)
    if not match:
        return {}
    return parse_simple_yaml_text(match.group(1))


def parse_run_input_contract_yaml(content):
    match = re.search(
        r"(?is)##\s*3\.\s*(?:Run|Worker)\s+입력\s+계약.*?```yaml\s*(.*?)```",
        content,
    )
    if not match:
        return {}
    return parse_simple_yaml_text(match.group(1))


def collect_build_wave_records(project_dir="."):
    records = {}

    for path in find_run_files(project_dir):
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        rel_path = os.path.relpath(path, project_dir)
        metadata = parse_simple_yaml_block(content)
        ids = set(re.findall(r"\bBW-\d{3}\b", content))
        if metadata.get("bw_id"):
            ids.add(metadata["bw_id"])

        for bw_id in sorted(ids):
            record = records.setdefault(
                bw_id,
                {"id": bw_id, "status": "Planned", "run": "", "related_ids": []},
            )

            if metadata.get("bw_id") == bw_id or bw_id.lower() in os.path.basename(path).lower():
                status = metadata.get("status")
                if status in WAVE_KNOWN_STATUSES:
                    record["status"] = status
                    record["run"] = rel_path

            related = [item.upper() for item in BUILD_WAVE_RELATED_ID_RE.findall(content)]
            record["related_ids"] = sorted(set(record.get("related_ids", []) + related))

        for line in content.splitlines():
            if not line.strip().startswith("|"):
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cols or re.fullmatch(r"[-: ]+", cols[0] or ""):
                continue
            bw_cols = [c for c in cols if re.fullmatch(r"BW-\d{3}", c)]
            if not bw_cols:
                continue
            bw_id = bw_cols[0]
            record = records.setdefault(
                bw_id,
                {"id": bw_id, "status": "Planned", "run": "", "related_ids": []},
            )
            for col in cols:
                if col in WAVE_KNOWN_STATUSES:
                    record["status"] = col
                    break
            related = [
                item
                for col in cols
                for item in BUILD_WAVE_RELATED_ID_RE.findall(col)
            ]
            related = [item.upper() for item in related]
            record["related_ids"] = sorted(set(record.get("related_ids", []) + related))

    return [records[key] for key in sorted(records)]


def merge_session_wave_records(session, discovered):
    merged = {item["id"]: dict(item) for item in discovered}
    session_impl = session.get("implementation", {}) if session else {}
    session_waves = session_impl.get("waves", {}) if isinstance(session_impl, dict) else {}
    for item in session_waves.get("items", []) if isinstance(session_waves, dict) else []:
        bw_id = item.get("id")
        if not bw_id:
            continue
        base = merged.setdefault(
            bw_id,
            {"id": bw_id, "status": "Planned", "run": "", "related_ids": []},
        )
        session_status = item.get("status")
        base_status = base.get("status")
        session_rank = WAVE_STATUS_RANK.get(session_status, -1)
        base_rank = WAVE_STATUS_RANK.get(base_status, -1)
        if session_status and session_rank >= base_rank:
            base["status"] = session_status
            if item.get("run"):
                base["run"] = item["run"]
        elif not base.get("run") and item.get("run"):
            base["run"] = item["run"]
        base["related_ids"] = sorted(set(base.get("related_ids", []) + item.get("related_ids", [])))
    return [merged[key] for key in sorted(merged)]


def update_wave_run_status(project_dir, bw_id, status):
    path = find_wave_run_file(project_dir, bw_id)
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return ""

    def replace_status(match):
        block = match.group(1)
        if not re.search(rf"^\s*bw_id:\s*{re.escape(bw_id)}\s*$", block, re.MULTILINE):
            return match.group(0)
        if re.search(r"^\s*status:\s*.+$", block, re.MULTILINE):
            block = re.sub(r"^(\s*status:\s*).+$", rf"\1{status}", block, count=1, flags=re.MULTILINE)
        else:
            block = block.rstrip() + f"\nstatus: {status}\n"
        return f"```yaml\n{block}```"

    updated = re.sub(r"```yaml\s*(.*?)```", replace_status, content, count=1, flags=re.DOTALL | re.IGNORECASE)
    if updated != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
    return os.path.relpath(path, project_dir)


def wave_completion_blockers(project_dir, bw_id, requested_status):
    blockers = []
    if requested_status not in {"Verified", "Completed", "Done"}:
        return blockers

    path = find_wave_run_file(project_dir, bw_id)
    if not path:
        return blockers

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return [f"Wave Run 문서를 읽을 수 없습니다: {e}"]

    metadata = parse_simple_yaml_block(content)
    run_status = metadata.get("status", "")
    if run_status in {"Blocked", "Failed", "CompletedWithIssues"}:
        blockers.append(
            f"{bw_id} Run 상태가 {run_status}입니다. {requested_status}로 닫기 전에 이슈를 해소하거나 Wave 상태를 낮추세요."
        )

    if yaml_field_has_nonempty_items(content, "open_issues"):
        blockers.append(
            f"{bw_id} Run에 open_issues가 남아 있습니다. Verified/Completed 처리 전 이슈를 닫거나 CompletedWithIssues/Blocked로 남기세요."
        )

    return blockers


def compute_implementation_progress(project_dir=".", session=None):
    try:
        _group_reqs, detail_reqs, _defined_acs, _ac_delegates = parse_requirements(project_dir)
    except Exception:
        detail_reqs = set()

    try:
        traceability = parse_traceability(project_dir)
    except Exception:
        traceability = {}

    completed_ids = {
        req_id
        for req_id, info in traceability.items()
        if re.fullmatch(r"REQ-\d{3}-\d{2}", req_id)
        and info.get("status") in ("구현완료", "완료", "Implemented", "Verified", "Done")
    }

    if session:
        session_impl = session.get("implementation", {})
        reqs = session_impl.get("requirements", {}) if isinstance(session_impl, dict) else {}
        completed_ids.update(reqs.get("completed_ids", []))

    wave_records = merge_session_wave_records(session or {}, collect_build_wave_records(project_dir))
    current = ""
    for item in wave_records:
        if item.get("status") in WAVE_ACTIVE_STATUSES:
            current = item["id"]
            break
    if session:
        session_current = (
            session.get("implementation", {})
            .get("waves", {})
            .get("current", "")
        )
        if session_current:
            current = session_current

    return {
        "requirements": {
            "total": len(detail_reqs),
            "implemented": len(completed_ids),
            "pending": max(len(detail_reqs) - len(completed_ids), 0),
            "completed_ids": sorted(completed_ids),
        },
        "waves": {
            "total": len(wave_records),
            "completed": sum(1 for item in wave_records if item.get("status") in WAVE_DONE_STATUSES),
            "current": current,
            "items": wave_records,
        },
    }


def implementation_display_counts(implementation):
    """Return normalized implementation counts for status display."""
    implementation = implementation or {}
    reqs = implementation.get("requirements", {}) if isinstance(implementation, dict) else {}
    waves = implementation.get("waves", {}) if isinstance(implementation, dict) else {}
    implemented = reqs.get("implemented", implementation.get("implemented", 0) if isinstance(implementation, dict) else 0)
    total = reqs.get("total", implementation.get("total", 0) if isinstance(implementation, dict) else 0)
    percent = implementation.get("percent", 0) if isinstance(implementation, dict) else 0
    if not percent and total:
        percent = int((implemented / total) * 100)
    return {
        "implemented": implemented,
        "total": total,
        "percent": percent,
        "waves_completed": waves.get("completed", implementation.get("waves_completed", 0) if isinstance(implementation, dict) else 0),
        "waves_total": waves.get("total", implementation.get("waves_total", 0) if isinstance(implementation, dict) else 0),
        "waves_current": waves.get("current", ""),
    }


def parse_requirements(project_dir="."):
    """REQUIREMENTS.md에서 REQ-ID 및 AC 정보를 파싱합니다."""
    path = find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "01-requirements"),
        r"requirements.*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "01-requirements", "REQUIREMENTS.md"),
    ])
    if not path:
        return {}, {}, {}, {}

    with open(path, encoding="utf-8") as f:
        content = f.read()

    group_reqs = {}
    detail_reqs = {}

    for idx, line in enumerate(content.splitlines()):
        line_num = idx + 1
        stripped = line.strip()
        if stripped.startswith("|"):
            cols = [c.strip() for c in stripped.strip("|").split("|")]
            if not cols or set(cols[0]) <= {"-"}:
                continue
            if re.fullmatch(r"REQ-\d{3}", cols[0]):
                name = cols[1] if len(cols) > 1 else ""
                description = cols[2] if len(cols) > 2 else ""
                if name or description:
                    if cols[0] not in group_reqs:
                        group_reqs[cols[0]] = line_num
            elif re.fullmatch(r"REQ-\d{3}-\d{2}", cols[0]):
                name = cols[1] if len(cols) > 1 else ""
                description = cols[2] if len(cols) > 2 else ""
                if name or description:
                    if cols[0] not in detail_reqs:
                        detail_reqs[cols[0]] = line_num
            continue

        detail_match = re.match(r"^#{3,6}\s+(REQ-\d{3}-\d{2})\s+(.+)$", stripped)
        if detail_match and detail_match.group(2).strip():
            req_id = detail_match.group(1)
            if req_id not in detail_reqs:
                detail_reqs[req_id] = line_num

    defined_acs = {}
    for idx, line in enumerate(content.splitlines()):
        line_num = idx + 1
        stripped = line.strip()

        # Check header pattern ### AC-XXX-XX
        ac_header_match = re.search(r'###\s+AC-(\d{3}-\d{2})', stripped)
        if ac_header_match:
            ac_id = ac_header_match.group(1)
            if ac_id not in defined_acs:
                defined_acs[ac_id] = line_num

        # Check table pattern | AC-XXX-XX | ...
        if stripped.startswith("|"):
            cols = [c.strip() for c in stripped.strip("|").split("|")]
            if not cols or set(cols[0]) <= {"-"}:
                continue
            ac_match = re.fullmatch(r"AC-(\d{3}-\d{2})", cols[0])
            if ac_match:
                ac_id = ac_match.group(1)
                if ac_id not in defined_acs:
                    defined_acs[ac_id] = line_num

    # AC 위임 관계 파싱: REQ-XXX-XX 행에 자기 AC는 없지만 다른 AC-ID가 참조되면 위임
    ac_delegates = {}
    for line in content.splitlines():
        m_req = re.search(r'\bREQ-(\d{3}-\d{2})\b', line)
        if m_req:
            req_id = m_req.group(1)
            if req_id not in defined_acs:
                refs = re.findall(r'\bAC-(\d{3}-\d{2})\b', line)
                for ref in refs:
                    if ref != req_id:
                        ac_delegates[req_id] = ref
                        break

    return group_reqs, detail_reqs, defined_acs, ac_delegates


def parse_traceability(project_dir="."):
    """TRACEABILITY.md를 파싱하여 REQ-ID별 추적 정보를 반환합니다.
    Returns: dict[req_id] = {"design": str, "tst_ids": list, "review": str, "status": str}
    TRACEABILITY.md가 없으면 빈 dict 반환 (하위 호환성 유지).
    """
    path = find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-traceability"),
        r"traceability.*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "TRACEABILITY.md"),
    ])
    if not path:
        return {}
    result = {}
    headers = []
    with open(path, encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            if not line.strip().startswith('|'):
                continue
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cols) < 5:
                continue
            if "REQ-ID" in cols:
                headers = cols
                continue
            if all(re.fullmatch(r"[-: ]+", c or "") for c in cols):
                continue

            header_idx = {name: idx for idx, name in enumerate(headers)}

            def cell(name, default=""):
                idx = header_idx.get(name)
                if idx is None or idx >= len(cols):
                    return default
                return cols[idx]

            req_id = cell("REQ-ID", cols[0])
            if not re.match(r'REQ-\d{3}(?:-\d{2})?$', req_id):
                continue
            ac_value = cell("AC-ID", cols[1] if len(cols) > 1 else "")
            is_ex_matrix_row = bool(headers) and re.match(r'AC-\d{3}-\d{2}$', ac_value)
            if is_ex_matrix_row:
                design = ", ".join(
                    c
                    for c in [
                        cell("FUNC-ID"),
                        cell("SCR-ID"),
                        cell("PGM-ID"),
                        cell("DB-ID"),
                        cell("IF-ID"),
                        cell("API-ID"),
                        cell("SEC-ID"),
                    ]
                    if c and c not in ("-", "미정", "해당없음")
                )
                test_columns = {
                    "UT-ID": cell("UT-ID"),
                    "IT-ID": cell("IT-ID"),
                    "PT-ID": cell("PT-ID"),
                }
                if "UI-ID" in header_idx:
                    test_columns["UI-ID"] = cell("UI-ID")
                tst_raw = ", ".join(c for c in test_columns.values() if c and c not in ("-", "미정", "해당없음"))
                review = cell("증적") or cell("검토")
                if review in ("-", "미정", "해당없음"):
                    review = ""
                status = cell("상태")
            elif req_id in result:
                continue
            else:
                design  = cols[1] if len(cols) > 1 and cols[1] != '-' else ''
                tst_raw = cols[2] if len(cols) > 2 and cols[2] != '-' else ''
                review  = cols[3] if len(cols) > 3 and cols[3] != '-' else ''
                status  = cols[4] if len(cols) > 4 else ''
                test_columns = {"TST-ID": tst_raw}
            tst_ids = [t.strip() for t in tst_raw.split(',') if t.strip() and t.strip() != '-']
            result[req_id] = {
                "design": design,
                "tst_ids": tst_ids,
                "review": review,
                "status": status,
                "test_columns": test_columns,
                "__line_num__": line_idx + 1,
            }
    return result


TRACE_ID_PATTERN = re.compile(
    r"\b(?:"
    r"REQ-\d{3}(?:-\d{2})?|NREQ-\d{3}(?:-\d{2})?|AC-\d{3}-\d{2}|"
    r"FUNC-\d{3}|SCR-\d{3}|UIREF-\d{3}|UICON-\d{3}|"
    r"API-\d{3}|PGM-\d{3}|IF-\d{3}|MTH-\d{3}|DB-\d{3}|SEC-\d{3}|"
    r"UT-\d{3}|IT-\d{3}|PT-\d{3}|UI-\d{3}(?:-\d{2})?|EV-[A-Z0-9-]+|"
    r"FIND-\d{3}|CR-\d{3}|DEC-\d{3}|BL-\d{3}|ISSUE-[A-Z0-9-]+|"
    r"RUN-\d{3}|RV-\d{3}"
    r")\b",
    re.IGNORECASE,
)

TRACE_TEST_PREFIXES = {"UT", "IT", "PT"}
TRACE_UNRESOLVED_VALUES = {"", "-", "미정", "확인필요", "해당없음", "tbd", "todo", "n/a", "na"}
TRACE_EXCLUDED_STATUSES = {"deferred", "rejected"}
TRACE_LABEL_HIGH_PRIORITY_COLUMNS = [
    "요구사항명",
    "상세 요구사항명",
    "요구사항",
    "상세 요구사항",
    "인수기준",
    "기능명",
    "프로그램/컴포넌트",
    "화면명",
    "프로그램명",
    "API명",
    "테이블명",
    "인터페이스명",
    "보안항목",
    "검증항목",
    "검증 대상",
    "테스트명",
    "제목",
    "명칭",
    "이름",
    "Name",
    "Title",
    "Description",
]
TRACE_LABEL_LOW_PRIORITY_COLUMNS = ["비고", "Note", "Notes", "Remark", "Remarks"]


def trace_find_ids(value):
    ids = []
    for match in TRACE_ID_PATTERN.finditer(value or ""):
        item = match.group(0).upper()
        if item not in ids:
            ids.append(item)
    return ids


def trace_id_prefix(trace_id):
    return (trace_id or "").split("-", 1)[0].upper()


def trace_cell_ids(row, candidates):
    return trace_find_ids(table_cell(row, candidates))


def trace_clean_label(value):
    label = clean_contract_cell(value or "")
    if not label:
        return ""
    if label.strip().lower() in TRACE_UNRESOLVED_VALUES:
        return ""
    label = re.sub(r"`([^`]+)`", r"\1", label)
    label = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", label)
    label = re.sub(r"\s+", " ", label).strip()
    return label


def trace_table_cell_exact(row, candidates, default=""):
    normalized = {normalize_md_header(key): value for key, value in row.items()}
    for candidate in candidates:
        key = normalize_md_header(candidate)
        if key in normalized:
            return clean_contract_cell(normalized[key])
    return default


def trace_row_label(row):
    label = trace_clean_label(trace_table_cell_exact(row, TRACE_LABEL_HIGH_PRIORITY_COLUMNS))
    if label:
        return label, 2
    label = trace_clean_label(trace_table_cell_exact(row, TRACE_LABEL_LOW_PRIORITY_COLUMNS))
    if label:
        return label, 1
    return "", 0


def trace_primary_ids_for_row(row):
    for header, value in row.items():
        normalized_header = normalize_md_header(header)
        if any(token in normalized_header for token in ["관련", "영향", "증적", "참조", "evidence", "source", "run"]):
            continue
        ids = trace_find_ids(value)
        if ids:
            return ids
    return []


def trace_add_node(nodes, trace_id, status="", source="", label="", label_priority=0):
    if not trace_id:
        return
    node = nodes.setdefault(trace_id, {"id": trace_id, "status": "", "label": "", "label_priority": 0, "sources": set()})
    if status and not node.get("status"):
        node["status"] = status
    clean_label = trace_clean_label(label)
    current_priority = int(node.get("label_priority") or 0)
    if clean_label and (label_priority > current_priority or not node.get("label")):
        node["label"] = clean_label
        node["label_priority"] = label_priority
    if source:
        node["sources"].add(source)


def trace_add_edge(edges, nodes, source_id, target_id, edge_type, status="", source=""):
    if not source_id or not target_id or source_id == target_id:
        return
    trace_add_node(nodes, source_id, status=status, source=source)
    trace_add_node(nodes, target_id, status=status, source=source)
    key = (source_id, target_id, edge_type)
    edge = edges.setdefault(key, {"source": source_id, "target": target_id, "type": edge_type, "sources": set()})
    if source:
        edge["sources"].add(source)


def traceability_matrix_path(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-traceability"),
        r"traceability.*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "TRACEABILITY.md"),
    ])


def build_trace_graph(project_dir="."):
    path = traceability_matrix_path(project_dir)
    nodes = {}
    edges = {}
    rows_processed = 0
    if not path:
        return {"nodes": nodes, "edges": [], "source": "", "rows": 0}

    rel_source = normalize_repo_path(os.path.relpath(path, project_dir))
    with open(path, encoding="utf-8") as f:
        content = f.read()

    for _headers, rows in parse_markdown_tables(content):
        for row in rows:
            row_ids = []
            for value in row.values():
                row_ids.extend(trace_find_ids(value))
            if not row_ids:
                continue
            rows_processed += 1
            status = table_cell(row, ["상태", "Status"])
            label, label_priority = trace_row_label(row)
            for trace_id in row_ids:
                trace_add_node(nodes, trace_id, status=status, source=rel_source)
            if label:
                label_ids = trace_primary_ids_for_row(row) if label_priority > 1 else row_ids
                for trace_id in label_ids:
                    trace_add_node(nodes, trace_id, status=status, source=rel_source, label=label, label_priority=label_priority)

            req_ids = trace_cell_ids(row, ["REQ-ID", "관련 REQ", "관련 REQ/NREQ", "영향받는 REQ"])
            nreq_ids = trace_cell_ids(row, ["NREQ-ID", "관련 NREQ", "관련 REQ/NREQ"])
            ac_ids = trace_cell_ids(row, ["AC-ID", "인수기준"])
            func_ids = trace_cell_ids(row, ["FUNC-ID", "기능"])
            scr_ids = trace_cell_ids(row, ["SCR-ID", "화면"])
            uiref_ids = trace_cell_ids(row, ["UIREF-ID", "UIREF"])
            uicon_ids = trace_cell_ids(row, ["UICON-ID", "UICON"])
            pgm_ids = trace_cell_ids(row, ["PGM-ID", "프로그램", "적용 대상", "영향받는 설계"])
            api_ids = trace_cell_ids(row, ["API-ID", "API", "PGM-ID", "적용 대상", "영향받는 설계"])
            db_ids = trace_cell_ids(row, ["DB-ID", "데이터", "영향받는 설계"])
            if_ids = trace_cell_ids(row, ["IF-ID", "Interface-ID", "영향받는 설계"])
            sec_ids = trace_cell_ids(row, ["SEC-ID", "보안", "보안항목", "적용 대상"])
            ut_ids = trace_cell_ids(row, ["UT-ID", "검증 테스트", "영향받는 테스트"])
            it_ids = trace_cell_ids(row, ["IT-ID", "검증 테스트", "영향받는 테스트"])
            pt_ids = trace_cell_ids(row, ["PT-ID", "검증 테스트", "영향받는 테스트"])
            ui_ids = trace_cell_ids(row, ["UI-ID", "검증 테스트", "영향받는 테스트"])
            ev_ids = trace_cell_ids(row, ["증적", "Evidence"])
            issue_ids = trace_cell_ids(row, ["결함 ID", "FIND-ID", "CR-ID", "ISSUE-ID", "Backlog-ID"])
            run_ids = trace_cell_ids(row, ["증적", "Run", "RUN-ID"])

            upstream_ids = req_ids + nreq_ids
            if ac_ids:
                for upstream_id in upstream_ids:
                    for ac_id in ac_ids:
                        trace_add_edge(edges, nodes, upstream_id, ac_id, "decomposes", status, rel_source)
            elif upstream_ids:
                ac_ids = upstream_ids

            for ac_id in ac_ids:
                for func_id in func_ids:
                    trace_add_edge(edges, nodes, ac_id, func_id, "satisfies", status, rel_source)
                for sec_id in sec_ids:
                    trace_add_edge(edges, nodes, ac_id, sec_id, "implements", status, rel_source)

            design_ids = scr_ids + uiref_ids + uicon_ids + api_ids + pgm_ids + db_ids + if_ids + sec_ids
            for func_id in func_ids:
                for design_id in design_ids:
                    trace_add_edge(edges, nodes, func_id, design_id, "implements", status, rel_source)
            if not func_ids:
                for upstream_id in ac_ids or upstream_ids:
                    for design_id in design_ids:
                        trace_add_edge(edges, nodes, upstream_id, design_id, "implements", status, rel_source)

            test_ids = ut_ids + it_ids + pt_ids + ui_ids
            test_sources = design_ids or func_ids or ac_ids or upstream_ids
            for source_id in test_sources:
                for test_id in test_ids:
                    trace_add_edge(edges, nodes, source_id, test_id, "verifies", status, rel_source)

            for test_id in test_ids:
                for ev_id in ev_ids:
                    if trace_id_prefix(ev_id) in {"RUN", "RV"}:
                        trace_add_edge(edges, nodes, ev_id, test_id, "documents", status, rel_source)
                    else:
                        trace_add_edge(edges, nodes, test_id, ev_id, "evidence_of", status, rel_source)

            for issue_id in issue_ids:
                for related_id in row_ids:
                    if related_id != issue_id:
                        trace_add_edge(edges, nodes, issue_id, related_id, "impacts", status, rel_source)

            for run_id in run_ids:
                if trace_id_prefix(run_id) == "RUN":
                    for related_id in row_ids:
                        if related_id != run_id:
                            trace_add_edge(edges, nodes, run_id, related_id, "documents", status, rel_source)

    edge_items = []
    for edge in edges.values():
        item = dict(edge)
        item["sources"] = sorted(item.get("sources", []))
        edge_items.append(item)
    for node in nodes.values():
        node["sources"] = sorted(node.get("sources", []))
        node.pop("label_priority", None)
    return {
        "nodes": nodes,
        "edges": sorted(edge_items, key=lambda item: (item["source"], item["target"], item["type"])),
        "source": rel_source,
        "rows": rows_processed,
    }


def trace_bfs(graph, seed_id, depth=2, direction="downstream", edge_types=None, include_excluded=False):
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    allowed_edge_types = set(edge_types or [])
    forward = {}
    backward = {}
    for edge in edges:
        if allowed_edge_types and edge.get("type") not in allowed_edge_types:
            continue
        forward.setdefault(edge["source"], []).append(edge)
        backward.setdefault(edge["target"], []).append(edge)

    seed_id = seed_id.upper()
    visited = {seed_id: 0}
    kept_edges = []
    queue = [(seed_id, 0)]
    while queue:
        current, current_depth = queue.pop(0)
        if current_depth >= depth:
            continue
        candidates = []
        if direction in ("downstream", "both"):
            candidates.extend(forward.get(current, []))
        if direction in ("upstream", "both"):
            for edge in backward.get(current, []):
                candidates.append({"source": edge["target"], "target": edge["source"], "type": edge["type"], "sources": edge.get("sources", [])})

        for edge in candidates:
            target = edge["target"]
            status = (nodes.get(target, {}).get("status") or "").strip().lower()
            if not include_excluded and status in TRACE_EXCLUDED_STATUSES:
                continue
            kept_edges.append(edge)
            if target not in visited:
                visited[target] = current_depth + 1
                queue.append((target, current_depth + 1))
    return visited, kept_edges


def trace_related_documents(project_dir, ids, limit=12):
    search_dirs = [
        os.path.join(project_dir, "docs", "artifacts"),
        os.path.join(project_dir, "docs", "runs"),
        os.path.join(project_dir, "docs", "reviews"),
    ]
    id_set = set(ids or [])
    matches = []
    for base in search_dirs:
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs.sort()
            files.sort()
            dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", "__pycache__"}]
            for filename in files:
                if not filename.lower().endswith(".md"):
                    continue
                path = os.path.join(root, filename)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    continue
                found = id_set.intersection(trace_find_ids(content))
                if not found:
                    continue
                rel_path = normalize_repo_path(os.path.relpath(path, project_dir))
                matches.append((rel_path, sorted(found)))
    return [{"path": path, "ids": found} for path, found in sorted(matches)[:limit]]


def trace_document_label_index(project_dir, ids):
    id_set = set(ids or [])
    labels = {}
    search_dirs = [
        os.path.join(project_dir, "docs", "artifacts"),
    ]
    for base in search_dirs:
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs.sort()
            files.sort()
            dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", "__pycache__"}]
            for filename in files:
                if not filename.lower().endswith(".md"):
                    continue
                path = os.path.join(root, filename)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    continue
                if not id_set.intersection(trace_find_ids(content)):
                    continue
                rel_path = normalize_repo_path(os.path.relpath(path, project_dir))
                for _headers, rows in parse_markdown_tables(content):
                    for row in rows:
                        primary_ids = [item for item in trace_primary_ids_for_row(row) if item in id_set]
                        if not primary_ids:
                            continue
                        label, priority = trace_row_label(row)
                        if not label or priority < 2:
                            continue
                        for trace_id in primary_ids:
                            current = labels.get(trace_id)
                            if current and current.get("priority", 0) >= priority:
                                continue
                            labels[trace_id] = {"label": label, "source": rel_path, "priority": priority}
    return labels


def trace_context_yaml(context):
    lines = [
        f"seed_id: {context['seed_id']}",
        f"depth: {context['depth']}",
        f"direction: {context['direction']}",
        f"traceability_source: {format_yaml_scalar(context.get('traceability_source', ''))}",
        "related_ids:",
        format_yaml_sequence(context["related_ids"], 2),
        "nodes:",
    ]
    if context.get("nodes"):
        for node_id, node in context["nodes"].items():
            lines.append(f"  {format_yaml_scalar(node_id)}:")
            if node.get("label"):
                lines.append(f"    label: {format_yaml_scalar(node['label'])}")
            if node.get("status"):
                lines.append(f"    status: {format_yaml_scalar(node['status'])}")
    else:
        lines.append("  {}")
    lines.extend([
        "target_contracts:",
        format_yaml_mapping_sequences(context["target_contracts"], 2),
        "edges:",
    ])
    if context["edges"]:
        for edge in context["edges"]:
            lines.append(f"  - source: {format_yaml_scalar(edge['source'])}")
            lines.append(f"    target: {format_yaml_scalar(edge['target'])}")
            lines.append(f"    type: {format_yaml_scalar(edge['type'])}")
    else:
        lines.append("  []")

    lines.append("source_documents:")
    lines.append("  orchestrator_reference:")
    if context.get("traceability_source"):
        lines.append(f"    - {format_yaml_scalar(context['traceability_source'])}")
    else:
        lines.append("    []")
    lines.append("  reference_on_demand:")
    if context["related_documents"]:
        for doc in context["related_documents"]:
            lines.append(f"    - path: {format_yaml_scalar(doc['path'])}")
            lines.append(f"      ids: {format_yaml_list(doc['ids'])}")
    else:
        lines.append("    []")
    lines.append("warnings:")
    for warning in context["warnings"]:
        lines.append(f"  - {format_yaml_scalar(warning)}")
    return "\n".join(lines)


def trace_context(project_dir, seed_id, depth=2, direction="downstream", edge_types=None, include_excluded=False):
    graph = build_trace_graph(project_dir)
    seed_id = (seed_id or "").strip().upper()
    if seed_id not in graph.get("nodes", {}):
        return {
            "seed_id": seed_id,
            "depth": depth,
            "direction": direction,
            "traceability_source": graph.get("source", ""),
            "related_ids": [seed_id] if seed_id else [],
            "nodes": {},
            "target_contracts": classify_related_ids([seed_id] if seed_id else []),
            "edges": [],
            "related_documents": [],
            "warnings": [
                f"seed ID를 traceability graph에서 찾지 못했습니다: {seed_id}",
                "scope.writable은 trace graph가 확정하지 않는다. Orchestrator가 Run 생성 전 직접 좁혀야 한다.",
                "interface_contract는 Program Design에서 별도 확인해야 한다.",
            ],
        }
    visited, edges = trace_bfs(graph, seed_id, depth=depth, direction=direction, edge_types=edge_types, include_excluded=include_excluded)
    related_ids = sorted(visited, key=lambda item: (visited[item], item))
    related_nodes = {
        trace_id: dict(graph.get("nodes", {}).get(trace_id, {"id": trace_id, "label": "", "status": "", "sources": []}))
        for trace_id in related_ids
    }
    document_labels = trace_document_label_index(project_dir, related_ids)
    for trace_id, label_info in document_labels.items():
        if trace_id in related_nodes:
            related_nodes[trace_id]["label"] = label_info.get("label", related_nodes[trace_id].get("label", ""))
            related_nodes[trace_id]["label_source"] = label_info.get("source", "")
    related_documents = trace_related_documents(project_dir, related_ids)
    warnings = [
        "scope.writable은 trace graph가 확정하지 않는다. Orchestrator가 Run 생성 전 직접 좁혀야 한다.",
        "interface_contract는 Program Design에서 별도 확인해야 한다.",
        "target_contracts는 추천값이며 Orchestrator가 확정해야 한다.",
    ]
    return {
        "seed_id": seed_id,
        "depth": depth,
        "direction": direction,
        "traceability_source": graph.get("source", ""),
        "related_ids": related_ids,
        "nodes": related_nodes,
        "target_contracts": classify_related_ids(related_ids),
        "edges": sorted(edges, key=lambda item: (item["source"], item["target"], item["type"])),
        "related_documents": related_documents,
        "warnings": warnings,
    }


def trace_context_run_enrichment(project_dir, trace_seed="", related_ids=None, depth=2, direction="both"):
    seeds = split_csv(trace_seed)
    base_ids = split_csv(",".join(related_ids or [])) if isinstance(related_ids, list) else split_csv(related_ids or "")
    if not seeds:
        return {
            "seeds": [],
            "depth": depth,
            "direction": direction,
            "related_ids": base_ids,
            "target_contracts": classify_related_ids(base_ids),
            "reference_on_demand": [],
            "warnings": [],
        }

    merged_ids = list(base_ids)
    reference_paths = []
    warnings = []
    for seed in seeds:
        context = trace_context(
            project_dir,
            seed_id=seed,
            depth=max(0, int(depth)),
            direction=direction,
            edge_types=None,
            include_excluded=False,
        )
        merged_ids = merge_unique(merged_ids, context.get("related_ids", []))
        warnings = merge_unique(warnings, context.get("warnings", []))
        for doc in context.get("related_documents", []):
            path = normalize_repo_path(doc.get("path", ""))
            if not path:
                continue
            if path.startswith("docs/runs/") or path.startswith("docs/reviews/"):
                continue
            if "/02-traceability/" in path or path.startswith("docs/artifacts/02-traceability/"):
                continue
            reference_paths.append(path)

    return {
        "seeds": seeds,
        "depth": depth,
        "direction": direction,
        "related_ids": merged_ids,
        "target_contracts": classify_related_ids(merged_ids),
        "reference_on_demand": merge_unique(reference_paths),
        "warnings": warnings,
    }


def format_trace_context_metadata(trace_info, indent=0):
    if not trace_info or not trace_info.get("seeds"):
        return ""
    prefix = " " * indent
    child = " " * (indent + 2)
    return "\n".join([
        f"{prefix}trace_context:",
        f"{child}seeds: {format_yaml_list(trace_info.get('seeds', []))}",
        f"{child}depth: {trace_info.get('depth', 2)}",
        f"{child}direction: {format_yaml_scalar(trace_info.get('direction', 'both'))}",
        f"{child}source: \"trace-context\"",
    ])


def cmd_trace_context(seed_id, depth=2, direction="downstream", emit="yaml", edge_types="", include_excluded=False, project_dir="."):
    if not seed_id:
        print("오류: --id 값이 필요합니다.")
        sys.exit(1)
    edge_type_list = split_csv(edge_types)
    context = trace_context(
        os.path.abspath(project_dir),
        seed_id=seed_id,
        depth=max(0, int(depth)),
        direction=direction,
        edge_types=edge_type_list,
        include_excluded=include_excluded,
    )
    if emit == "json":
        print(json.dumps(context, ensure_ascii=False, indent=2))
    else:
        print(trace_context_yaml(context))


class TestResultTuple(tuple):
    def __new__(cls, tst_id, status, line_num=None):
        return super(TestResultTuple, cls).__new__(cls, (tst_id, status))

    def __init__(self, tst_id, status, line_num=None):
        self.line_num = line_num


def parse_test_plan(project_dir="."):
    """Gate 3 테스트케이스 문서에서 상세 REQ-ID 매핑을 파싱합니다."""
    path = find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "03-test"),
        r"(test.*case|test.*plan|test.*cases).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "03-test-plan", "Test-Plan.md"),
    ])
    if not path:
        return {}

    with open(path, encoding="utf-8") as f:
        content = f.read()

    req_to_line = {}
    for idx, line in enumerate(content.splitlines()):
        line_num = idx + 1
        for match in re.finditer(r'\b(REQ-\d{3}-\d{2})\b', line):
            req_id = match.group(1)
            if req_id not in req_to_line:
                req_to_line[req_id] = line_num
    return req_to_line


def parse_test_plan_status(project_dir="."):
    """Test-Plan.md에서 TST-ID별 실행 상태를 파싱합니다.
    테스트 케이스 목록 형식의 마크다운 테이블 행만 파싱합니다.
    보안 기준표처럼 테스트 ID를 참조만 하는 표는 집계하지 않습니다.
    Returns: list of TestResultTuple
    """
    path = find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "03-test"),
        r"(test.*case|test.*plan|test.*cases).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "03-test-plan", "Test-Plan.md"),
    ])
    if not path:
        return []

    with open(path, encoding="utf-8") as f:
        content = f.read()

    results = {}
    line_nums = {}
    for idx, line in enumerate(content.splitlines()):
        line_num = idx + 1
        # 마크다운 테이블 행만 대상 (|로 시작)
        if not line.strip().startswith('|'):
            continue
        if re.search(r'\b(?:REQ|NREQ|AC|SEC|PGM|SCR)-\s*(?:/|\||$)', line):
            continue
        cols = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cols) < 9:
            continue
        # 구체적인 TST-ID만 매칭 (TST-NNN-NN 또는 TST-SEC-NN 형식)
        # TST-ID, TST-NNN-NN 같은 템플릿/플레이스홀더는 제외
        tst_match = re.search(r'\|\s*((?:TST|UT|IT|PT|UI)-(?:\d{3}(?:-\d{2})?|SEC-\d{2}))\s*\|', line)
        if not tst_match:
            continue
        tst_id = tst_match.group(1)

        # 상태 판별: Pass/Fail/Skip/미실행
        status_cell = cols[-1].lower()
        if re.search(r'\bpass\b', status_cell):
            status = 'pass'
        elif re.search(r'\bfail\b', status_cell):
            status = 'fail'
        elif re.search(r'\bskip\b', status_cell):
            status = 'skip'
        else:
            status = 'not_executed'

        results[tst_id] = status
        line_nums[tst_id] = line_num

    return [TestResultTuple(tst_id, status, line_nums.get(tst_id)) for tst_id, status in results.items()]


def normalize_test_execution_status(value):
    status_cell = clean_contract_cell(value or "").lower()
    if not status_cell:
        return None
    if re.search(r"pass\s*/\s*fail|fail\s*/\s*not\s*run|pass\s*/\s*fail\s*/\s*not\s*run|pass\s*/\s*find|find\s*/\s*cr", status_cell):
        return None
    if re.search(r"environment[_ -]?blocked|환경\s*차단|blocked", status_cell):
        return "environment_blocked"
    if re.search(r"not[_ -]?run|미실행", status_cell):
        return "not_executed"
    if re.search(r"\bskip(?:ped)?\b|생략", status_cell):
        return "skip"
    if re.search(r"\bfail(?:ed)?\b|실패", status_cell):
        return "fail"
    if re.search(r"\bpass(?:ed)?\b|성공|통과", status_cell):
        return "pass"
    return None


def find_qa_test_result_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "04-review"),
        r"(test.*result|qa.*result|테스트.*결과).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "04-review", "Test-Result.md"),
    ])


def is_test_execution_result_id(trace_id):
    item = (trace_id or "").upper()
    if re.fullmatch(r"UI-\d{3}-\d{2}", item):
        return True
    if re.fullmatch(r"(?:UT|IT|PT)-\d{3}", item):
        return True
    if re.fullmatch(r"TST-(?:\d{3}(?:-\d{2})?|SEC-\d{2})", item):
        return True
    return False


def parse_qa_test_result_status(project_dir="."):
    """Gate 4 QA 결과서에서 실제 테스트 실행 상태를 파싱한다.

    Gate 3 테스트케이스 문서는 계획/기준이고, Gate 4의 실제 Pass/Fail/Not Run
    원본은 QA Test Result다. 이 함수는 QA 결과서의 요구사항 검증 요약,
    실행 검증, 화면 증적 표에서 UT/IT/PT/UI ID와 결과를 수집한다.
    """
    path = find_qa_test_result_file(project_dir)
    if not path:
        return []

    with open(path, encoding="utf-8") as f:
        content = f.read()

    results = {}
    line_nums = {}
    for headers, rows in parse_markdown_tables(content):
        header_text = " ".join(headers).lower()
        if re.search(r"비교|comparison|uicmp|contract", header_text):
            continue
        for row in rows:
            row_text = " ".join(row.values())
            if re.search(r"\bUICMP-\d{3}\b", row_text, re.IGNORECASE):
                continue
            test_ids = [
                item for item in trace_find_ids(row_text)
                if is_test_execution_result_id(item)
            ]
            if not test_ids:
                continue

            status_text = table_cell(row, ["결과", "상태", "처리", "판정"])
            status = normalize_test_execution_status(status_text)
            if status is None:
                continue

            line_num = row.get("__line_num__")
            for test_id in test_ids:
                results[test_id] = status
                line_nums[test_id] = line_num

    return [TestResultTuple(tst_id, status, line_nums.get(tst_id)) for tst_id, status in results.items()]


def parse_effective_test_status(project_dir="."):
    qa_results = parse_qa_test_result_status(project_dir)
    if qa_results:
        return qa_results, "QA Test Result"
    return parse_test_plan_status(project_dir), "Gate 3 Test Cases"


def find_development_standard_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "development-standard"),
        r"development.*standard.*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "development-standard.md"),
        os.path.join("docs", "02-design", "Development-Standard.md"),
    ])


def find_project_glossary_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "data"),
        r"(project.*glossary|glossary|단어.*사전|용어.*사전).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "project-glossary.md"),
        os.path.join("docs", "02-design", "Project-Glossary.md"),
        os.path.join("docs", "02-design", "glossary.md"),
    ])


def find_program_spec_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "program"),
        r"(program.*(design|spec)|프로그램.*(설계|명세)).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "program-design.md"),
        os.path.join("docs", "02-design", "Program-Design.md"),
        os.path.join("docs", "02-design", "program-spec.md"),
        os.path.join("docs", "02-design", "Program-Spec.md"),
    ])


def find_api_spec_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "api"),
        r"(api.*spec|api.*정의).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "api-spec.md"),
        os.path.join("docs", "02-design", "API-Spec.md"),
    ])


def find_security_guide_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "security"),
        r"(security.*guide|보안.*가이드).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "security-guide.md"),
        os.path.join("docs", "02-design", "Security-Guide.md"),
    ])


def find_screen_spec_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "screen"),
        r"(screen.*spec|화면.*설계).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "screen-spec.md"),
        os.path.join("docs", "02-design", "Screen-Spec.md"),
    ])


def find_architecture_spec_file(project_dir="."):
    return find_first_existing(project_dir, [
        os.path.join("docs", "artifacts", "02-design", "architecture", "DOC-ARCH-G2-001_SW-Architecture_v0.1.md"),
    ]) or find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "architecture"),
        r"(sw.*architecture|아키텍처).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "architecture.md"),
        os.path.join("docs", "02-design", "Architecture.md"),
        os.path.join("docs", "02-design", "SW-Architecture.md"),
    ])


def find_deployment_infrastructure_architecture_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-design", "architecture"),
        r"(deployment.*infrastructure|infrastructure.*architecture|인프라.*아키텍처|배포.*인프라).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "02-design", "deployment-infrastructure-architecture.md"),
        os.path.join("docs", "02-design", "Infrastructure-Architecture.md"),
    ])


def find_risk_assumption_file(project_dir="."):
    return find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "00-discovery"),
        r"(risk.*assumption|위험.*가정).*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "00-discovery", "risk-and-assumption.md"),
        os.path.join("docs", "00-discovery", "Risk-And-Assumption.md"),
    ])


def split_trace_values(value):
    return [
        item.strip().strip("`")
        for item in re.split(r",|\n|\s+/\s+", value or "")
        if item.strip() and item.strip() not in ("-", "미정", "해당없음")
    ]


def is_probable_source_path(value):
    normalized = value.replace("\\", "/")
    source_exts = (
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go", ".rs",
        ".cs", ".php", ".rb", ".html", ".css", ".scss", ".vue", ".svelte",
    )
    if not normalized.lower().endswith(source_exts):
        return False
    return "/" in normalized or normalized.startswith(("app", "src", "tests", "test"))


def is_probable_text_file(path):
    text_exts = (
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go", ".rs",
        ".cs", ".php", ".rb", ".html", ".css", ".scss", ".vue", ".svelte",
        ".md", ".json", ".yml", ".yaml", ".txt",
    )
    return path.lower().endswith(text_exts)


HARD_TEMPLATE_PLACEHOLDER_RE = re.compile(r"\{PROJECT_NAME\}|\{AUTHOR\}|\{YYYY-MM-DD\}")
SOFT_TBD_PLACEHOLDER_RE = re.compile(r"\bTBD\b|확정필요", re.IGNORECASE)
POC_TBD_REASON_RE = re.compile(r"사유|이유|근거|reason|why", re.IGNORECASE)
POC_TBD_DECISION_RE = re.compile(r"후속|판단|결정|전환|시점|decide_when|next|when", re.IGNORECASE)


def unresolved_template_placeholder_issue(rel_path, content, project_dir="."):
    if HARD_TEMPLATE_PLACEHOLDER_RE.search(content):
        return f"{rel_path}에 템플릿 플레이스홀더가 남아 있음"

    if not SOFT_TBD_PLACEHOLDER_RE.search(content):
        return None

    if load_delivery_profile(project_dir) == "poc":
        return None

    return f"{rel_path}에 템플릿 플레이스홀더가 남아 있음"


def poc_tbd_decision_context_present(content):
    return bool(POC_TBD_REASON_RE.search(content) and POC_TBD_DECISION_RE.search(content))


def collect_poc_tbd_warnings(project_dir="."):
    if load_delivery_profile(project_dir) != "poc":
        return []

    warnings = []
    artifact_dir = os.path.join(project_dir, "docs", "poc")
    if not os.path.isdir(artifact_dir):
        return warnings

    for root, _dirs, files in os.walk(artifact_dir):
        for file_name in files:
            if not file_name.lower().endswith(".md"):
                continue
            path = os.path.join(root, file_name)
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            if not SOFT_TBD_PLACEHOLDER_RE.search(content):
                continue
            rel_path = os.path.relpath(path, project_dir)
            if poc_tbd_decision_context_present(content):
                warnings.append(f"{rel_path}에 PoC TBD/확정필요가 남아 있음 - 사유와 후속 판단 시점 확인 필요")
            else:
                warnings.append(f"{rel_path}에 PoC TBD/확정필요가 있으나 사유 또는 후속 판단 시점이 부족함")
    return warnings


def poc_required_artifacts_for_gate(gate):
    return POC_REQUIRED_ARTIFACTS_BY_GATE.get(gate, POC_REQUIRED_ARTIFACTS_BY_GATE["phase0"])


def product_required_artifacts_for_gate(gate):
    return PRODUCT_REQUIRED_ARTIFACTS_BY_GATE.get(gate, PRODUCT_REQUIRED_ARTIFACTS_BY_GATE["phase0"])


def read_project_text(project_dir, rel_path):
    path = os.path.join(project_dir, rel_path)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def table_value_is_tbd(content, label):
    escaped = re.escape(label)
    return bool(re.search(rf"(?m)^\|\s*{escaped}\s*\|\s*(?:TBD|미정|확정필요)\b", content, re.IGNORECASE))


def mostly_placeholder_row(content, id_pattern):
    pattern = rf"(?m)^\|\s*{id_pattern}\s*\|\s*(?:TBD|미정|확정필요)\b"
    return bool(re.search(pattern, content, re.IGNORECASE))


def collect_poc_profile_findings(project_dir=".", gate=None):
    if load_delivery_profile(project_dir) != "poc":
        return [], []

    session = load_session(project_dir)
    gate = gate or session.get("current_gate", "phase0")
    issues = []
    warnings = []
    required = poc_required_artifacts_for_gate(gate)

    for rel_path in required:
        abs_path = os.path.join(project_dir, rel_path)
        if not os.path.isfile(abs_path):
            issues.append(f"PoC 필수 산출물 없음: {rel_path}")

    req_content = read_project_text(project_dir, "docs/poc/POC_REQUIREMENTS.md")
    if "docs/poc/POC_REQUIREMENTS.md" in required and req_content:
        if HARD_TEMPLATE_PLACEHOLDER_RE.search(req_content):
            issues.append("docs/poc/POC_REQUIREMENTS.md에 치환되지 않은 템플릿 값이 남아 있습니다.")
        if table_value_is_tbd(req_content, "목표"):
            issues.append("docs/poc/POC_REQUIREMENTS.md의 PoC 목표가 TBD입니다.")
        if table_value_is_tbd(req_content, "성공 기준"):
            issues.append("docs/poc/POC_REQUIREMENTS.md의 성공 기준이 TBD입니다.")
        if not re.search(r"\bHYP-\d{3}\b", req_content):
            issues.append("docs/poc/POC_REQUIREMENTS.md에 HYP-ID가 없습니다.")
        if not re.search(r"\bREQ-\d{3}\b", req_content):
            issues.append("docs/poc/POC_REQUIREMENTS.md에 핵심 REQ-ID가 없습니다.")
        if mostly_placeholder_row(req_content, r"HYP-\d{3}") or mostly_placeholder_row(req_content, r"REQ-\d{3}"):
            warnings.append("docs/poc/POC_REQUIREMENTS.md에 placeholder 중심의 HYP/REQ 행이 남아 있습니다.")
        if gate in ("gate4", "gate5", "completed") and re.search(r"(?im)^\s*status\s*:\s*Draft\s*$", req_content):
            warnings.append("docs/poc/POC_REQUIREMENTS.md가 PoC 완료 구간에서도 status: Draft입니다. 실제 상태에 맞게 Completed/Accepted 등으로 정리하세요.")

    design_content = read_project_text(project_dir, "docs/poc/POC_SYSTEM_DESIGN.md")
    if "docs/poc/POC_SYSTEM_DESIGN.md" in required and design_content:
        if HARD_TEMPLATE_PLACEHOLDER_RE.search(design_content):
            issues.append("docs/poc/POC_SYSTEM_DESIGN.md에 치환되지 않은 템플릿 값이 남아 있습니다.")
        if not re.search(r"\b(?:API|DATA|SCR)-\d{3}\b", design_content):
            issues.append("docs/poc/POC_SYSTEM_DESIGN.md에 API/DATA/SCR 중 하나 이상의 설계 ID가 없습니다.")
        if mostly_placeholder_row(design_content, r"(?:API|DATA|SCR)-\d{3}"):
            warnings.append("docs/poc/POC_SYSTEM_DESIGN.md에 placeholder 중심의 설계 행이 남아 있습니다.")
        if gate in ("gate4", "gate5", "completed") and re.search(r"(?im)^\s*status\s*:\s*Draft\s*$", design_content):
            warnings.append("docs/poc/POC_SYSTEM_DESIGN.md가 PoC 완료 구간에서도 status: Draft입니다. 실제 상태에 맞게 Designed/Completed 등으로 정리하세요.")

    test_content = read_project_text(project_dir, "docs/poc/POC_TEST_REPORT.md")
    if "docs/poc/POC_TEST_REPORT.md" in required and test_content:
        if HARD_TEMPLATE_PLACEHOLDER_RE.search(test_content):
            issues.append("docs/poc/POC_TEST_REPORT.md에 치환되지 않은 템플릿 값이 남아 있습니다.")
        if not re.search(r"\bT-(?:[A-Z]+-)?\d{3}\b", test_content):
            issues.append("docs/poc/POC_TEST_REPORT.md에 테스트 ID(T-*, 예: T-001/T-API-001/T-UI-001)가 없습니다.")
        if gate in ("gate4", "gate5", "completed"):
            if not re.search(r"\bEV-(?:[A-Z]+-)?\d{3}\b", test_content):
                issues.append("docs/poc/POC_TEST_REPORT.md에 증적 ID(EV-*, 예: EV-001/EV-API-001/EV-UI-001)가 없습니다.")
            if re.search(r"(?im)^\s*status\s*:\s*Draft\s*$", test_content):
                warnings.append("docs/poc/POC_TEST_REPORT.md가 Gate 4 이후에도 status: Draft입니다. 실제 실행 결과에 맞게 QA Completed/Completed 등으로 정리하세요.")
            if table_value_is_tbd(test_content, "최종 판단"):
                issues.append("docs/poc/POC_TEST_REPORT.md의 최종 판단이 TBD입니다.")
            if table_value_is_tbd(test_content, "근거"):
                issues.append("docs/poc/POC_TEST_REPORT.md의 판단 근거가 TBD입니다.")
            if re.search(r"\|\s*T-(?:[A-Z]+-)?\d{3}\s*\|[^\n]*\|\s*(?:Planned|TBD)\s*\|", test_content, re.IGNORECASE):
                issues.append("docs/poc/POC_TEST_REPORT.md에 Gate 4 이후에도 Planned/TBD 테스트 결과가 남아 있습니다.")
        if gate in ("impl", "gate4", "gate5", "completed"):
            tests_stats = _poc_test_status_counts(test_content)
            if tests_stats.get("passed", 0) > 0 and not _poc_existing_pass_evidence_paths(project_dir, test_content):
                issues.append("docs/poc/POC_TEST_REPORT.md에 Pass/Smoke Pass 결과가 있으나 실제 증적 파일을 찾을 수 없습니다.")
        else:
            if mostly_placeholder_row(test_content, r"T-\d{3}"):
                warnings.append("docs/poc/POC_TEST_REPORT.md에 placeholder 중심의 테스트 계획 행이 남아 있습니다.")

    return issues, warnings


def collect_product_profile_findings(project_dir=".", gate=None):
    if load_delivery_profile(project_dir) != "product":
        return [], []

    session = load_session(project_dir)
    gate = gate or session.get("current_gate", "phase0")
    issues = []
    warnings = []
    required = product_required_artifacts_for_gate(gate)

    for rel_path in required:
        abs_path = os.path.join(project_dir, rel_path)
        if not os.path.isfile(abs_path):
            issues.append(f"Product 필수 산출물 없음: {rel_path}")
            continue
        content = read_project_text(project_dir, rel_path)
        if HARD_TEMPLATE_PLACEHOLDER_RE.search(content):
            issues.append(f"{rel_path}에 치환되지 않은 템플릿 값이 남아 있습니다.")
        elif SOFT_TBD_PLACEHOLDER_RE.search(content):
            warnings.append(f"{rel_path}에 TBD/확정필요 항목이 남아 있습니다. Product 판단에 필요한 항목인지 확인하세요.")

    brief_content = read_project_text(project_dir, "docs/product/PRODUCT_BRIEF.md")
    if "docs/product/PRODUCT_BRIEF.md" in required and brief_content:
        for label in ("목표", "주요 사용자", "성공 기준"):
            if table_value_is_tbd(brief_content, label):
                issues.append(f"docs/product/PRODUCT_BRIEF.md의 {label} 항목이 TBD입니다.")
        if mostly_placeholder_row(brief_content, r"SCN-\d{3}"):
            warnings.append("docs/product/PRODUCT_BRIEF.md에 placeholder 중심의 Scenario 행이 남아 있습니다.")

    architecture_content = read_project_text(project_dir, "docs/product/PRODUCT_ARCHITECTURE.md")
    if "docs/product/PRODUCT_ARCHITECTURE.md" in required and architecture_content:
        if gate in ("gate2", "gate3", "impl", "gate4", "gate5", "completed"):
            for label in ("Runtime", "Data Store"):
                if table_value_is_tbd(architecture_content, label):
                    issues.append(f"docs/product/PRODUCT_ARCHITECTURE.md의 {label}가 TBD입니다.")
        if mostly_placeholder_row(architecture_content, r"CMP-\d{3}") or mostly_placeholder_row(architecture_content, r"GAP-\d{3}"):
            warnings.append("docs/product/PRODUCT_ARCHITECTURE.md에 placeholder 중심의 Component/Gap 행이 남아 있습니다.")

    adr_content = read_project_text(project_dir, "docs/product/ADR_LOG.md")
    if "docs/product/ADR_LOG.md" in required and adr_content:
        if gate in ("gate2", "gate3", "impl", "gate4", "gate5", "completed") and mostly_placeholder_row(adr_content, r"ADR-\d{3}"):
            warnings.append("docs/product/ADR_LOG.md에 placeholder 중심의 ADR 행이 남아 있습니다.")

    contracts_content = read_project_text(project_dir, "docs/product/PRODUCT_CONTRACTS.md")
    if "docs/product/PRODUCT_CONTRACTS.md" in required and contracts_content:
        if gate in ("gate2", "gate3", "impl", "gate4", "gate5", "completed"):
            if mostly_placeholder_row(contracts_content, r"API-\d{3}") and mostly_placeholder_row(contracts_content, r"(?:DATA|DB)-\d{3}") and mostly_placeholder_row(contracts_content, r"(?:UI|SCR)-\d{3}"):
                issues.append("docs/product/PRODUCT_CONTRACTS.md의 API/Data/UI 계약 행이 모두 placeholder입니다.")
        if mostly_placeholder_row(contracts_content, r"GAP-\d{3}"):
            warnings.append("docs/product/PRODUCT_CONTRACTS.md에 placeholder 중심의 Contract Gap 행이 남아 있습니다.")

    trace_content = read_project_text(project_dir, "docs/product/PRODUCT_TRACEABILITY.md")
    if "docs/product/PRODUCT_TRACEABILITY.md" in required and trace_content:
        if gate in ("gate3", "impl", "gate4", "gate5", "completed"):
            if mostly_placeholder_row(trace_content, r"SCN-\d{3}"):
                issues.append("docs/product/PRODUCT_TRACEABILITY.md의 Scenario Trace가 placeholder입니다.")
            if re.search(r"\|\s*SCN-\d{3}\s*\|[^\n]*\|\s*Planned\s*\|", trace_content, re.IGNORECASE) and gate in ("gate4", "gate5", "completed"):
                warnings.append("docs/product/PRODUCT_TRACEABILITY.md에 Gate 4 이후에도 Planned 추적 상태가 남아 있습니다.")

    release_content = read_project_text(project_dir, "docs/product/REGRESSION_AND_RELEASE_REPORT.md")
    if "docs/product/REGRESSION_AND_RELEASE_REPORT.md" in required and release_content:
        if gate in ("gate3", "impl", "gate4", "gate5", "completed") and mostly_placeholder_row(release_content, r"REG-\d{3}"):
            issues.append("docs/product/REGRESSION_AND_RELEASE_REPORT.md의 Regression Plan이 placeholder입니다.")
        if gate in ("gate4", "gate5", "completed") and re.search(
            r"\|\s*REG-\d{3}\s*\|\s*(?:TBD|Not\s+run\s+yet|Gate\s*4\s*예정|Gate\s*4\s*planned|예정)[^|]*\|\s*(?:Planned|TBD|Not\s+Run)\b",
            release_content,
            re.IGNORECASE,
        ):
            issues.append("docs/product/REGRESSION_AND_RELEASE_REPORT.md에 Gate 4 이후에도 Planned/TBD 회귀 실행 결과가 남아 있습니다.")
        if gate in ("gate5", "completed"):
            for label in ("포함 범위", "남은 리스크"):
                if table_value_is_tbd(release_content, label):
                    issues.append(f"docs/product/REGRESSION_AND_RELEASE_REPORT.md의 {label}가 TBD입니다.")

    return issues, warnings


def validate_poc_trace(project_dir=".", gate=None):
    issues, warnings = collect_poc_profile_findings(project_dir, gate=gate)
    if load_delivery_profile(project_dir) != "poc":
        return issues, warnings

    req_content = read_project_text(project_dir, "docs/poc/POC_REQUIREMENTS.md")
    design_content = read_project_text(project_dir, "docs/poc/POC_SYSTEM_DESIGN.md")
    test_content = read_project_text(project_dir, "docs/poc/POC_TEST_REPORT.md")

    req_ids = set(re.findall(r"\bREQ-\d{3}\b", req_content))
    hyp_ids = set(re.findall(r"\bHYP-\d{3}\b", req_content))
    linked_text = "\n".join([design_content, test_content])
    for req_id in sorted(req_ids):
        if linked_text and req_id not in linked_text:
            warnings.append(f"PoC trace warning: {req_id}가 설계/테스트 문서에 연결되지 않았습니다.")
    for hyp_id in sorted(hyp_ids):
        if test_content and hyp_id not in test_content:
            warnings.append(f"PoC trace warning: {hyp_id}가 테스트 결과서에 연결되지 않았습니다.")
    return issues, warnings


def validate_product_trace(project_dir=".", gate=None):
    issues, warnings = collect_product_profile_findings(project_dir, gate=gate)
    if load_delivery_profile(project_dir) != "product":
        return issues, warnings

    brief_content = read_project_text(project_dir, "docs/product/PRODUCT_BRIEF.md")
    contracts_content = read_project_text(project_dir, "docs/product/PRODUCT_CONTRACTS.md")
    trace_content = read_project_text(project_dir, "docs/product/PRODUCT_TRACEABILITY.md")
    release_content = read_project_text(project_dir, "docs/product/REGRESSION_AND_RELEASE_REPORT.md")

    scenario_ids = set(re.findall(r"\bSCN-\d{3}\b", brief_content))
    req_ids = set(re.findall(r"\bREQ-\d{3}(?:-\d{2})?\b", brief_content))
    downstream_scenario_ids = set(re.findall(r"\bSCN-\d{3}\b", "\n".join([contracts_content, trace_content, release_content])))

    if gate in ("phase0", "gate1") and not scenario_ids:
        issues.append("docs/product/PRODUCT_BRIEF.md에 SCN-ID가 없습니다.")
    if gate in ("phase0", "gate1") and not req_ids:
        warnings.append("docs/product/PRODUCT_BRIEF.md에 REQ-ID가 없습니다. Product에서는 허용되지만 이후 계약/회귀 연결 전에 보강하세요.")

    if gate in ("gate3", "impl", "gate4", "gate5", "completed"):
        linked_text = "\n".join([contracts_content, trace_content, release_content])
        for scenario_id in sorted(downstream_scenario_ids - scenario_ids):
            warnings.append(f"Product trace warning: {scenario_id}가 downstream 문서에는 있지만 PRODUCT_BRIEF.md 시나리오에 없습니다.")
        for scenario_id in sorted(scenario_ids):
            if linked_text and scenario_id not in linked_text:
                warnings.append(f"Product trace warning: {scenario_id}가 계약/회귀/릴리즈 문서에 연결되지 않았습니다.")
        for req_id in sorted(req_ids):
            if trace_content and req_id not in trace_content:
                warnings.append(f"Product trace warning: {req_id}가 PRODUCT_TRACEABILITY.md에 연결되지 않았습니다.")

    return issues, warnings


def is_markdown_separator_row(line):
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def collect_artifact_completion_findings(project_dir="."):
    profile = load_delivery_profile(project_dir)
    issues = []
    warnings = []
    artifact_dir = os.path.join(project_dir, "docs", "artifacts")
    if not os.path.isdir(artifact_dir):
        return issues, warnings

    final_statuses = {"designed", "verified", "completed", "approved", "done", "awaitingapproval"}
    id_like_re = re.compile(r"\b(?:REQ|NREQ|AC|FUNC|SCR|UIREF|UICON|PGM|API|DB|IF|SEC|UT|IT|PT|UI|FIND|CR|ISSUE|TERM|DOMAIN)-\d{3}(?:-\d{2})?\b")

    for root, _dirs, files in os.walk(artifact_dir):
        for file_name in files:
            if not file_name.lower().endswith(".md"):
                continue
            path = os.path.join(root, file_name)
            rel_path = os.path.relpath(path, project_dir)
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            status_match = re.search(r"(?m)^\s*status\s*:\s*([A-Za-z0-9_-]+)\s*$", content)
            if not status_match:
                continue
            if status_match.group(1).strip().lower() not in final_statuses:
                continue

            placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
            if placeholder_issue:
                if profile == "poc":
                    warnings.append(placeholder_issue)
                else:
                    issues.append(placeholder_issue)

            if re.search(r"작성자\s*또는\s*에이전트|\{PROJECT_NAME\}|\{AUTHOR\}|\{YYYY-MM-DD\}", content):
                issues.append(f"{rel_path}에 템플릿 기본 문구 또는 치환되지 않은 값이 남아 있음")

            body = run_body_without_yaml(content)
            for line_no, line in enumerate(body.splitlines(), start=1):
                if "|" not in line or is_markdown_separator_row(line):
                    continue
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) < 3:
                    continue
                meaningful = [cell for cell in cells if cell]
                non_id_meaningful = [cell for cell in cells[1:] if cell and cell not in {"-", "N/A", "n/a"}]
                if not meaningful:
                    issues.append(f"{rel_path}:{line_no}에 빈 Markdown 표 행이 남아 있음")
                elif id_like_re.search(cells[0] or "") and not non_id_meaningful:
                    issues.append(f"{rel_path}:{line_no}에 ID만 있고 내용이 비어 있는 Markdown 표 행이 남아 있음")
    return issues, warnings


def validate_development_standard(project_dir="."):
    issues = []
    path = find_development_standard_file(project_dir)
    if not path:
        return [], ["개발표준정의서 없음"]

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    if re.search(r"(?m)^status:\s*Draft\s*$", content):
        issues.append(f"{rel_path} 상태가 Draft")
    placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
    if placeholder_issue:
        issues.append(placeholder_issue)

    required_terms = [
        ("언어/런타임", r"Language|Runtime|적용 언어|적용 프레임워크|Java|TypeScript|Python|Node|Vue|React|Spring Boot"),
        ("패키지 구조", r"패키지 구조|app/|src/"),
        ("기술 선택 근거", r"선정 사유|선택 근거|선정 근거"),
        ("기술스택 베이스라인 조정 근거", r"TECH_STACK_BASELINES|참조 베이스라인|프로젝트 조정사항"),
        ("메시지 관리", r"메시지|message"),
        ("주석/코딩 컨벤션", r"주석|JavaDoc|Javadoc|코드 컨벤션|네이밍"),
        ("로깅 기준", r"SLF4J|Logback|Log4j2|Logger|MDC|requestId|correlationId|System\.out|printStackTrace|로그 레벨"),
        ("DB Pool 기준", r"HikariCP|DB Pool|connection pool|커넥션 풀"),
        ("Lombok 기준", r"Lombok|@Getter|@RequiredArgsConstructor|@Data|@Setter"),
        ("테스트 명령", r"python -m unittest|pytest|npm test|pnpm test|mvn test|gradle test|gradlew test|go test|cargo test|dotnet test"),
        ("검증 명령 실행 기준", r"cwd|실행 위치|성공 기준|exit code|종료 코드|Not Run|Skipped|증적|로그/증적"),
        ("보안 구현 기준", r"SECURITY_BASELINE|KISA|SR2-|SR1-|보안 구현|보안 영역|Spring Security|SEC-\d{3}|JWT"),
    ]
    for label, pattern in required_terms:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"{rel_path}에 {label} 기준 없음")

    critical_blank_rows = [
        ("적용 언어", r"\|\s*적용 언어\s*\|\s*\|"),
        ("적용 프레임워크", r"\|\s*적용 프레임워크\s*\|\s*\|"),
        ("Base Package", r"\|\s*Base Package\s*\|\s*(?:예:\s*)?\|"),
        ("패키지 구조 기준", r"\|\s*패키지 구조 기준\s*\|\s*(?:예:\s*)?\|"),
        ("Lombok 사용 여부", r"\|\s*사용 여부\s*\|\s*\|"),
        ("Lombok 허용 annotation", r"\|\s*허용 annotation\s*\|\s*(?:예:\s*)?\|"),
        ("로깅 API", r"\|\s*로깅 API\s*\|\s*(?:예:\s*)?\|"),
        ("로깅 구현체", r"\|\s*(?:로깅\s*)?구현체\s*\|\s*(?:예:\s*)?\|"),
        ("로그 레벨 기준", r"\|\s*로그 레벨\s*(?:기준)?\s*\|\s*(?:예:\s*)?\|"),
    ]
    for label, pattern in critical_blank_rows:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"{rel_path}에 {label} 값이 비어 있음")

    if re.search(r"Spring Boot|Spring Security|JPA|gradlew", content, re.IGNORECASE):
        spring_required_terms = [
            ("Spring Boot base package", r"Base Package.+`?[a-z]+(?:\.[a-z][a-z0-9_]*)+`?|base package"),
            ("feature 우선 패키지 구조", r"feature 우선|auth/|user/|\{featureName\}|domain/\{domainName\}|DDD"),
            ("domain 래퍼 선택 사유", r"domain/\{domainName\}|domain 래퍼|DDD 구조 선택 사유"),
            ("JavaDoc 적용 대상", r"JavaDoc|Javadoc|public 업무 메서드|Controller, Service, Security Config"),
            ("logger 선언 기준", r"private static final Logger|LoggerFactory|getLogger|@Slf4j|logger 선언"),
            ("System.out 금지", r"System\.out|printStackTrace"),
        ]
        for label, pattern in spring_required_terms:
            if not re.search(pattern, content, re.IGNORECASE):
                issues.append(f"{rel_path}에 {label} 기준 없음")

    return [rel_path], issues


def validate_project_glossary(project_dir="."):
    issues = []
    path = find_project_glossary_file(project_dir)
    if not path:
        return [], ["프로젝트 단어사전 없음"]

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    if re.search(r"(?m)^status:\s*Draft\s*$", content):
        issues.append(f"{rel_path} 상태가 Draft")
    placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
    if placeholder_issue:
        issues.append(placeholder_issue)

    required_terms = [
        ("참조 표준", r"PUBLIC-DATA-STD|공공데이터 공통표준|reference-standards"),
        ("용어 ID", r"TERM-\d{3}"),
        ("단어 ID", r"WORD-\d{3}"),
        ("도메인 ID", r"DOMAIN-\d{3}"),
        ("표준 준용 상태", r"표준 준용 상태|표준 검토|표준 후보|프로젝트 신규|프로젝트 정의"),
        ("등록 사유", r"등록 사유|등록사유|사유"),
        ("화면/API/DB 항목 매핑", r"화면/API/DB|화면 항목명|API 필드명|DB 컬럼명"),
        ("보안/개인정보 분류", r"보안 분류|개인정보|인증정보|민감정보|로그 출력"),
    ]
    for label, pattern in required_terms:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"{rel_path}에 {label} 기준 없음")

    return [rel_path], issues


def validate_program_spec(project_dir="."):
    issues = []
    path = find_program_spec_file(project_dir)
    if not path:
        return [], ["프로그램 설계서 없음"]

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    if re.search(r"(?m)^status:\s*Draft\s*$", content):
        issues.append(f"{rel_path} 상태가 Draft")
    placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
    if placeholder_issue:
        issues.append(placeholder_issue)

    required_terms = [
        ("PGM-ID", r"PGM-\d{3}"),
        ("컴포넌트 책임", r"Class / Component Responsibility|주요 책임|책임 제외"),
        ("인터페이스 계약", r"Interface Contract|IF-\d{3}|interface"),
        ("public method 계약", r"Public Method Contract|MTH-\d{3}|시그니처"),
        ("DTO/Entity/Data 계약", r"DTO|Entity|Data Contract|Contract-ID"),
        ("입력/출력", r"입력|출력|Request|Response|TERM-"),
        ("처리/정책", r"검증/정책|처리 흐름|처리 내용|Policy|Validator"),
        ("예외/오류", r"ERR-\d{3}|오류 ID|예외"),
        ("트랜잭션/보안/로깅", r"Transaction|트랜잭션|SEC-\d{3}|보안|로그|감사|KISA|SR-"),
        ("테스트 연결", r"UT-\d{3}|IT-\d{3}|Test Mapping|AC-|NREQ-"),
        ("Worker Run 분할 기준", r"Worker Run 분할 기준|기능/계약 단위|10분|15분"),
        ("상세 SW 설계 다이어그램 판단", r"상세 SW 설계 다이어그램|복잡도|상태 전이|생략 사유"),
    ]
    for label, pattern in required_terms:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"{rel_path}에 {label} 기준 없음")

    diagram_markers = [
        r"```mermaid\s*\n\s*classDiagram",
        r"```mermaid\s*\n\s*stateDiagram",
        r"```mermaid\s*\n\s*sequenceDiagram",
        r"```mermaid\s*\n\s*flowchart",
        r"```mermaid\s*\n\s*graph",
    ]
    has_detail_diagram = any(re.search(pattern, content, re.IGNORECASE) for pattern in diagram_markers)
    has_skip_reason = bool(re.search(r"생략 사유\s*\|[^\n]*\S|불필요\s*\|[^\n]*\S", content))
    has_need_marker = bool(re.search(r"\|\s*PGM-\d{3}\s*\|[^\n]*\|\s*필요\s*\|", content))
    if has_need_marker and not has_detail_diagram:
        issues.append(f"{rel_path}에 상세 SW 설계 다이어그램 필요 표시가 있으나 Mermaid 다이어그램 없음")
    if not has_detail_diagram and not has_skip_reason:
        issues.append(f"{rel_path}에 상세 SW 설계 다이어그램 또는 생략 사유 없음")

    return [rel_path], issues


def normalize_md_header(value):
    return re.sub(r"\s+", "", (value or "").strip().lower())


def clean_contract_cell(value):
    cleaned = (value or "").strip()
    cleaned = cleaned.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*후보\s*$", "", cleaned)
    return cleaned.strip()


def extract_markdown_section(content, section_title_pattern):
    extracted_content, _ = extract_markdown_section_with_start_line(content, section_title_pattern)
    return extracted_content

def extract_markdown_section_with_start_line(content, section_title_pattern):
    lines = content.splitlines()
    section_lines = []
    in_section = False
    start_level = None
    start_line_idx = 0
    title_re = re.compile(section_title_pattern, re.IGNORECASE)
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

    for i, line in enumerate(lines):
        heading = heading_re.match(line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2)
            if in_section and start_level is not None and level <= start_level:
                break
            if not in_section and title_re.search(title):
                in_section = True
                start_level = level
                start_line_idx = i + 1
                continue
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines), start_line_idx


def parse_markdown_tables(section_content, start_line_offset=0):
    tables = []
    headers = None
    rows = []
    in_fence = False

    def flush():
        nonlocal headers, rows
        if headers and rows:
            tables.append((headers, rows))
        headers = None
        rows = []

    for idx, raw_line in enumerate(section_content.splitlines()):
        current_line_num = start_line_offset + idx + 1
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.startswith("|") or not line.endswith("|"):
            flush()
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", cell or "") for cell in cells):
            continue
        if headers is None:
            headers = cells
            continue
        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))

        row_dict = {headers[c_idx]: cells[c_idx] for c_idx in range(min(len(headers), len(cells)))}
        row_dict["__line_num__"] = str(current_line_num)
        rows.append(row_dict)

    flush()
    return tables


def table_cell(row, candidates, default=""):
    normalized = {normalize_md_header(key): value for key, value in row.items()}
    for candidate in candidates:
        key = normalize_md_header(candidate)
        for header, value in normalized.items():
            if key in header:
                return clean_contract_cell(value)
    return default


def split_contract_ids(value, prefix):
    ids = []
    for match in re.finditer(rf"\b{re.escape(prefix)}-\d{{3}}(?:-\d{{2}})?\b", value or "", re.IGNORECASE):
        item = match.group(0).upper()
        if item not in ids:
            ids.append(item)
    return ids


def pgm_matches(interface_pgm_value, method_pgm_value):
    method_ids = split_contract_ids(method_pgm_value, "PGM")
    if not method_ids:
        return False
    text = (interface_pgm_value or "").upper()
    direct_ids = split_contract_ids(text, "PGM")
    if any(method_id in direct_ids for method_id in method_ids):
        return True
    range_match = re.search(r"PGM-(\d{3})\s*~\s*(?:PGM-)?(\d{3})", text)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        for method_id in method_ids:
            num = int(method_id.split("-")[1])
            if start <= num <= end:
                return True
    return False


def parse_contract_method_name(signature):
    text = clean_contract_cell(signature)
    match = re.search(r"(?:[A-Za-z_]\w*\.)?([A-Za-z_]\w*)\s*\(", text)
    if match:
        return match.group(1)
    return ""


def parse_program_contracts(program_design_path):
    with open(program_design_path, encoding="utf-8") as f:
        content = f.read()

    interface_section = extract_markdown_section(content, r"Interface Contract|인터페이스")
    method_section = extract_markdown_section(content, r"Public Method Contract|public method|메소드")
    interfaces = []
    methods = []

    for headers, rows in parse_markdown_tables(interface_section):
        if not any(re.search(r"IF-ID|Interface-ID", header, re.IGNORECASE) for header in headers):
            continue
        for row in rows:
            if_id = table_cell(row, ["Interface-ID", "IF-ID"])
            if not re.match(r"IF-\d{3}$", if_id or "", re.IGNORECASE):
                continue
            interfaces.append({
                "if_id": if_id.upper(),
                "pgm": table_cell(row, ["PGM-ID", "PGM"]),
                "name": table_cell(row, ["인터페이스명", "Interface", "이름"]),
                "path": table_cell(row, ["패키지/경로", "경로", "Path"]),
                "implementation": table_cell(row, ["구현체", "Implementation"]),
            })

    for headers, rows in parse_markdown_tables(method_section):
        if not any(re.search(r"Method-ID|시그니처|이벤트", header, re.IGNORECASE) for header in headers):
            continue
        for row in rows:
            signature = table_cell(row, ["시그니처/이벤트", "시그니처", "Method", "Event"])
            method_name = parse_contract_method_name(signature)
            if not method_name:
                continue
            methods.append({
                "method_id": table_cell(row, ["Method-ID", "MTH-ID"]),
                "if_id": table_cell(row, ["IF-ID", "Interface-ID"]).upper(),
                "pgm": table_cell(row, ["PGM-ID", "PGM"]),
                "signature": signature,
                "method_name": method_name,
                "input": table_cell(row, ["입력", "Input"]),
                "output": table_cell(row, ["출력", "Output"]),
            })

    return {
        "program_design": program_design_path,
        "interfaces": interfaces,
        "methods": methods,
    }


def extract_contract_paths(path_cell):
    paths = []
    for match in re.finditer(r"`([^`]+)`", path_cell or ""):
        paths.append(match.group(1).strip())
    if not paths and path_cell:
        for chunk in re.split(r"[,，]|\s+또는\s+|\s+and\s+", path_cell):
            chunk = clean_contract_cell(chunk)
            if chunk:
                paths.append(chunk)
    return paths


def resolve_contract_path(project_dir, path_cell):
    for rel_path in extract_contract_paths(path_cell):
        normalized = rel_path.replace("/", os.sep).replace("\\", os.sep)
        if not normalized.lower().endswith(".py"):
            continue
        candidate = os.path.join(project_dir, normalized)
        if os.path.exists(candidate):
            return normalized, candidate
        if normalized.startswith("backend" + os.sep):
            continue
        backend_candidate = os.path.join(project_dir, "backend", normalized)
        if os.path.exists(backend_candidate):
            return os.path.join("backend", normalized), backend_candidate
    return "", ""


def resolve_contract_file(project_dir, path_cell):
    supported_exts = (".py", ".java")
    for rel_path in extract_contract_paths(path_cell):
        normalized = rel_path.replace("/", os.sep).replace("\\", os.sep)
        lower = normalized.lower()
        if not lower.endswith(supported_exts):
            continue
        candidates = [normalized]
        if not normalized.startswith("backend" + os.sep):
            candidates.append(os.path.join("backend", normalized))
        if not normalized.startswith(os.path.join("src", "main", "java") + os.sep):
            candidates.append(os.path.join("src", "main", "java", normalized))
        if not normalized.startswith(os.path.join("backend", "src", "main", "java") + os.sep):
            candidates.append(os.path.join("backend", "src", "main", "java", normalized))
        for candidate_rel in candidates:
            candidate_abs = os.path.join(project_dir, candidate_rel)
            if os.path.exists(candidate_abs):
                return candidate_rel, candidate_abs, os.path.splitext(candidate_abs)[1].lower().lstrip(".")
    return "", "", ""


def parse_python_classes(file_path):
    with open(file_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    classes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            classes[node.name] = methods
    return classes


def strip_java_comments(content):
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r"//.*", "", content)
    return content


def find_matching_brace(content, open_index):
    depth = 0
    for idx in range(open_index, len(content)):
        char = content[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return idx
    return -1


def parse_java_types(file_path):
    with open(file_path, encoding="utf-8") as f:
        content = strip_java_comments(f.read())

    types = {}
    type_pattern = re.compile(
        r"\b(?:(?:public|protected|private|abstract|final|sealed|non-sealed|static)\s+)*"
        r"(class|interface|record|enum)\s+([A-Za-z_]\w*)\b"
    )
    method_pattern = re.compile(
        r"(?:^|[;\n{}])\s*"
        r"(?:(?:public|protected|private|static|final|abstract|default|synchronized|native|strictfp)\s+)*"
        r"(?:<[^>{};]+>\s*)?"
        r"[A-Za-z_$][\w$<>\[\], ?.&]*\s+"
        r"([A-Za-z_$][\w$]*)\s*\([^;{}]*\)\s*(?:throws\s+[^{;]+)?\s*[;{]",
        re.MULTILINE,
    )

    for match in type_pattern.finditer(content):
        kind = match.group(1)
        name = match.group(2)
        brace_index = content.find("{", match.end())
        if brace_index == -1:
            types[name] = set()
            continue
        end_index = find_matching_brace(content, brace_index)
        body = content[brace_index + 1:end_index if end_index != -1 else len(content)]
        methods = set()
        for method_match in method_pattern.finditer(body):
            method_name = method_match.group(1)
            if method_name in {"if", "for", "while", "switch", "catch", "return", "new"}:
                continue
            if method_name == name:
                continue
            methods.add(method_name)
        types[name] = methods
    return types


def parse_contract_classes(file_path, language):
    if language == "py":
        return parse_python_classes(file_path)
    if language == "java":
        return parse_java_types(file_path)
    return {}


def write_json_file(path, payload):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def cmd_check_contract(program_design="", report="", emit_contract="", project_dir="."):
    program_path = program_design or find_program_spec_file(project_dir)
    if not program_path:
        print("오류: 프로그램 설계서를 찾을 수 없습니다.")
        return 1
    if not os.path.isabs(program_path):
        program_path = os.path.join(project_dir, program_path)
    if not os.path.exists(program_path):
        print(f"오류: 프로그램 설계서 파일이 없습니다: {program_path}")
        return 1

    contract = parse_program_contracts(program_path)
    results = []
    interface_by_id = {item["if_id"]: item for item in contract["interfaces"]}
    class_cache = {}

    def add_result(level, contract_id, target, message, path=""):
        results.append({
            "level": level,
            "contract_id": contract_id,
            "target": target,
            "message": message,
            "path": path,
        })

    for interface in contract["interfaces"]:
        if_id = interface["if_id"]
        rel_path, abs_path, language = resolve_contract_file(project_dir, interface.get("path", ""))
        if not rel_path:
            add_result("info", if_id, interface.get("name", ""), "지원 대상 파일(.py/.java)이 아니어서 1차 정적검사에서 제외", interface.get("path", ""))
            continue
        if not os.path.exists(abs_path):
            add_result("fail", if_id, interface.get("name", ""), "파일 없음", rel_path)
            continue
        try:
            classes = class_cache.setdefault(abs_path, parse_contract_classes(abs_path, language))
        except SyntaxError as exc:
            add_result("fail", if_id, interface.get("name", ""), f"Python AST 파싱 실패: {exc}", rel_path)
            continue
        except UnicodeDecodeError as exc:
            add_result("fail", if_id, interface.get("name", ""), f"파일 읽기 실패: {exc}", rel_path)
            continue
        name = interface.get("name", "")
        if name and name in classes:
            add_result("pass", if_id, name, "interface/class 확인", rel_path)
        elif name:
            add_result("fail", if_id, name, "interface/class 없음", rel_path)
        implementation = interface.get("implementation", "")
        if implementation and implementation not in {"-", "해당없음"}:
            if implementation in classes:
                add_result("pass", if_id, implementation, "구현체 class 확인", rel_path)
            else:
                add_result("warn", if_id, implementation, "구현체 class를 같은 Python 파일에서 찾지 못함", rel_path)

    for method in contract["methods"]:
        if_id = method.get("if_id", "")
        interface = interface_by_id.get(if_id)
        if not interface and not if_id:
            candidates = [item for item in contract["interfaces"] if pgm_matches(item.get("pgm", ""), method.get("pgm", ""))]
            matching_candidates = []
            for candidate in candidates:
                _rel_path, candidate_abs_path, candidate_language = resolve_contract_file(project_dir, candidate.get("path", ""))
                if not candidate_abs_path:
                    continue
                try:
                    candidate_classes = class_cache.setdefault(candidate_abs_path, parse_contract_classes(candidate_abs_path, candidate_language))
                except SyntaxError:
                    continue
                candidate_class_names = [
                    name for name in [candidate.get("implementation"), candidate.get("name")]
                    if name and name not in {"-", "해당없음"}
                ]
                if any(method["method_name"] in candidate_classes.get(name, set()) for name in candidate_class_names):
                    matching_candidates.append(candidate)
            if len(matching_candidates) == 1:
                interface = matching_candidates[0]
                if_id = interface["if_id"]
                add_result("warn", method.get("method_id", "") or method["method_name"], method["method_name"], f"Public Method Contract에 IF-ID가 없어 {if_id}로 코드 기준 추정", "")
            elif len(candidates) == 1:
                interface = candidates[0]
                if_id = interface["if_id"]
                add_result("warn", method.get("method_id", "") or method["method_name"], method["method_name"], f"Public Method Contract에 IF-ID가 없어 {if_id}로 추정", "")
            elif candidates:
                add_result("warn", method.get("method_id", "") or method["method_name"], method["method_name"], "Public Method Contract에 IF-ID가 없어 대상 interface가 모호함", "")
                continue
        if not interface:
            add_result("warn", method.get("method_id", "") or method["method_name"], method["method_name"], f"IF-ID를 Interface Contract에서 찾지 못함: {if_id or '미기재'}", "")
            continue
        rel_path, abs_path, language = resolve_contract_file(project_dir, interface.get("path", ""))
        if not rel_path:
            add_result("info", method.get("method_id", "") or f"{if_id}.{method['method_name']}", method["method_name"], "지원 대상 파일(.py/.java)이 아니어서 method 검사 제외", interface.get("path", ""))
            continue
        if not os.path.exists(abs_path):
            add_result("fail", method.get("method_id", "") or f"{if_id}.{method['method_name']}", method["method_name"], "파일 없음", rel_path)
            continue
        try:
            classes = class_cache.setdefault(abs_path, parse_contract_classes(abs_path, language))
        except SyntaxError as exc:
            add_result("fail", method.get("method_id", "") or f"{if_id}.{method['method_name']}", method["method_name"], f"Python AST 파싱 실패: {exc}", rel_path)
            continue
        except UnicodeDecodeError as exc:
            add_result("fail", method.get("method_id", "") or f"{if_id}.{method['method_name']}", method["method_name"], f"파일 읽기 실패: {exc}", rel_path)
            continue
        class_names = [
            name for name in [interface.get("implementation"), interface.get("name")]
            if name and name not in {"-", "해당없음"}
        ]
        found_in = [name for name in class_names if method["method_name"] in classes.get(name, set())]
        target_id = method.get("method_id", "") or f"{if_id}.{method['method_name']}"
        if found_in:
            add_result("pass", target_id, method["method_name"], f"public method 확인 ({', '.join(found_in)})", rel_path)
        else:
            add_result("fail", target_id, method["method_name"], f"public method 없음: {method['method_name']}", rel_path)

    summary = {
        "pass": sum(1 for item in results if item["level"] == "pass"),
        "warn": sum(1 for item in results if item["level"] == "warn"),
        "fail": sum(1 for item in results if item["level"] == "fail"),
        "info": sum(1 for item in results if item["level"] == "info"),
    }
    output = {
        "program_design": os.path.relpath(program_path, project_dir),
        "summary": summary,
        "results": results,
    }

    if emit_contract:
        write_json_file(emit_contract, contract)
    if report:
        write_json_file(report, output)

    print(f"\n[check-contract] {os.path.relpath(program_path, project_dir)}")
    print(f"  PASS {summary['pass']} / WARN {summary['warn']} / FAIL {summary['fail']} / INFO {summary['info']}\n")
    for item in results:
        marker = {"pass": "O", "warn": "!", "fail": "X", "info": "-"}[item["level"]]
        path_suffix = f" ({item['path']})" if item.get("path") else ""
        print(f"  {marker} {item['contract_id']} {item['target']} - {item['message']}{path_suffix}")
    if report:
        print(f"\n  report: {report}")
    if emit_contract:
        print(f"  extracted contract: {emit_contract}")
    return 1 if summary["fail"] else 0


def program_spec_requires_api_spec(project_dir="."):
    path = find_program_spec_file(project_dir)
    if not path:
        return False, None

    with open(path, encoding="utf-8") as f:
        content = f.read()

    effective_lines = [
        line for line in content.splitlines()
        if not re.search(r"API\s*/\s*Batch\s*/\s*Module|REST\s*/\s*GraphQL|GET\s*/\s*POST|API가 없으면|API 관련 칸", line, re.IGNORECASE)
    ]
    effective_content = "\n".join(effective_lines)

    api_patterns = [
        r"\|\s*PGM-\d{3}\s*\|[^|\n]*\|\s*(?:API|REST|GraphQL)\b",
        r"\|\s*호출 방식\s*\|\s*(?:REST|GraphQL)\s*\|",
        r"\|\s*Method\s*\|\s*(?:GET|POST|PUT|PATCH|DELETE)\s*\|",
        r"`/api/[^`]+`",
        r"\|\s*[^|\n]*/api/[^|\n]*\|",
    ]
    return any(re.search(pattern, effective_content, re.IGNORECASE) for pattern in api_patterns), path


def validate_api_spec(project_dir="."):
    issues = []
    required, program_path = program_spec_requires_api_spec(project_dir)
    if not required:
        return [], issues

    path = find_api_spec_file(project_dir)
    program_rel = os.path.relpath(program_path, project_dir) if program_path else "프로그램 설계서"
    if not path:
        return [], [f"{program_rel}에 API가 정의되어 있으나 API 정의서 없음"]

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    if re.search(r"(?m)^status:\s*Draft\s*$", content):
        issues.append(f"{rel_path} 상태가 Draft")
    placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
    if placeholder_issue:
        issues.append(placeholder_issue)

    required_terms = [
        ("API-ID", r"API-\d{3}"),
        ("Method/Path", r"\b(GET|POST|PUT|PATCH|DELETE)\b.*(/|Path)|Path.*\b(GET|POST|PUT|PATCH|DELETE)\b"),
        ("Request", r"Request|요청|Body|Query|Path|Header"),
        ("Response", r"Response|응답|상태코드|HTTP Status"),
        ("Error", r"Error|오류|error\.code|ERR-"),
        ("인증/권한", r"인증|권한|401|403|SEC-"),
        ("예시", r"요청 예시|응답 예시|```json"),
        ("테스트 연결", r"UT-|IT-|테스트 ID|검증"),
    ]
    for label, pattern in required_terms:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"{rel_path}에 {label} 기준 없음")

    return [rel_path], issues


def validate_architecture_spec(project_dir=".", level="baseline"):
    issues = []
    path = find_architecture_spec_file(project_dir)
    if not path:
        return [], ["SW 아키텍처 정의서 없음"]

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    normalized_level = (level or "baseline").lower()
    if normalized_level not in {"draft", "baseline"}:
        normalized_level = "baseline"

    if normalized_level == "baseline" and re.search(r"(?m)^status:\s*Draft\s*$", content):
        issues.append(f"{rel_path} 상태가 Draft")
    placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
    if placeholder_issue:
        issues.append(placeholder_issue)

    draft_required_terms = [
        ("아키텍처 성숙도", r"성숙도|Draft|Baseline Candidate|Baseline|Pending"),
        ("아키텍처 개요", r"아키텍처 개요|시스템 목적|주요 사용자|아키텍처 범위"),
        ("논리 아키텍처", r"논리 아키텍처|프론트엔드|백엔드|인증/권한|배치/비동기"),
        ("C1/C2 구조", r"C1|C2|시스템 컨텍스트|컨테이너|CNT-\d{3}"),
        ("아키텍처 결정 후보", r"ADR-\d{3}|아키텍처 결정|ADR 후보|Architecture Decision"),
    ]
    baseline_required_terms = [
        ("물리 아키텍처", r"물리 아키텍처|PHY-\d{3}|서버|네트워크|배포 단위|런타임"),
        ("모듈/컴포넌트 구조", r"모듈/컴포넌트 구조|C3|컴포넌트|CMP-\d{3}"),
        ("데이터 흐름", r"데이터 흐름|FLOW-\d{3}|sequenceDiagram|오류 처리 흐름"),
        ("보안 아키텍처", r"SEC-\d{3}|보안 아키텍처|인증|인가|세션|암호화|KISA|OWASP|CWE"),
        ("품질속성", r"NREQ-\d{3}|QA-\d{3}|품질속성"),
        ("기술 스택 및 선택 근거", r"기술 스택|선택 근거|언어|프레임워크|DB|배포 방식"),
        ("아키텍처 결정", r"ADR-\d{3}|아키텍처 결정|Architecture Decision"),
        ("추적성 및 상세 설계 연결", r"추적성|상세 설계 연결|프로그램 설계서|API정의서|DB명세서|화면설계서|추적표"),
    ]
    required_terms = draft_required_terms
    if normalized_level == "baseline":
        required_terms += baseline_required_terms
    for label, pattern in required_terms:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"{rel_path}에 {label} 기준 없음")

    mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)```", content, re.IGNORECASE | re.DOTALL)
    flow_blocks = [
        block for block in mermaid_blocks
        if re.search(r"^\s*(?:flowchart|graph)\s+", block, re.IGNORECASE | re.MULTILINE)
    ]
    c1_c2_blocks = flow_blocks[:2]
    missing_boundary_count = sum(
        1 for block in c1_c2_blocks
        if not re.search(r"\bsubgraph\b", block, re.IGNORECASE)
    )
    if c1_c2_blocks and missing_boundary_count:
        issues.append(f"{rel_path}의 C1/C2 아키텍처 다이어그램에 subgraph 경계 표현 없음")

    file_name_node_count = 0
    for block in flow_blocks:
        file_name_node_count += len(re.findall(r"\b[\w.-]+\.(?:py|ts|tsx|js|jsx|java|kt|go|cs|php|rb)\b", block, re.IGNORECASE))
    if file_name_node_count >= 3:
        issues.append(
            f"{rel_path}의 아키텍처 다이어그램이 파일명 나열 중심입니다 "
            "(C1/C2는 CNT/CMP/FLOW와 실행 경계 중심으로 작성)"
        )

    if normalized_level == "baseline":
        if len(flow_blocks) < 2:
            issues.append(f"{rel_path}에 C1/C2 Mermaid 경계 다이어그램이 부족함")

        required_link_targets = [
            "DOC-CORE-G2-001",
            "DOC-CORE-G2-002",
            "DOC-API-G2-001",
            "DOC-DATA-G2-002",
            "DOC-CORE-G2-003",
            "DOC-SEC-G2-001",
            "DOC-DEV-G2-001",
            "DOC-QA-G3-001",
            "DOC-CORE-G4-001",
        ]
        missing_links = [target for target in required_link_targets if target not in content]
        if missing_links:
            issues.append(f"{rel_path}의 상세 설계/추적 연결 문서 누락: {', '.join(missing_links)}")

    return [rel_path], issues


def validate_deployment_infrastructure_architecture(project_dir=".", level="baseline"):
    warnings = []
    path = find_deployment_infrastructure_architecture_file(project_dir)
    if not path:
        if (level or "baseline").lower() == "baseline":
            warnings.append(
                "배포·운영 인프라 아키텍처 문서 없음 "
                "(audit/SI에서는 DOC-ARCH-G2-002_Deployment-Infrastructure-Architecture_v0.1.md 권장)"
            )
        return [], warnings

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    required_terms = [
        ("인프라 구성 개요", r"인프라 구성 개요|배포 환경|주요 Zone|L4|WAS|DB"),
        ("배포·운영 구성도", r"배포.*운영.*구성도|```mermaid|L4|WAS|DB"),
        ("확인 질문", r"확인 질문|Q-INFRA|미확정 영향"),
        ("이중화와 장애 대응", r"이중화|장애|Failover|health check|Health Check"),
        ("포트/프로토콜", r"포트|프로토콜|Port|Protocol|FLOW-INFRA"),
        ("SW 설계/구현 영향", r"SW.*영향|Health Check|Session|DB Connection|TLS|Logging"),
        ("로그/모니터링/백업", r"로그|모니터링|백업|Monitoring|Backup"),
    ]
    for label, pattern in required_terms:
        if not re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"{rel_path}에 {label} 기준 없음")

    if re.search(r"\bTBD\b", content, re.IGNORECASE):
        has_questions = re.search(r"확인 질문|Q-INFRA|미확정 영향|확인 책임|목표 시점", content)
        if not has_questions:
            warnings.append(f"{rel_path}에 TBD가 있으나 확인 질문/영향/책임 기준이 없음")

    if re.search(r"L4|WAS|DB|TLS|health check|Health Check", content, re.IGNORECASE):
        if not re.search(r"DOC-ARCH-G2-001|DOC-SEC-G2-001|DOC-DEV-G2-001|DOC-DATA-G2-002", content):
            warnings.append(f"{rel_path}에 SW/보안/개발표준/DB 문서 연결이 부족함")

    return [rel_path], warnings


def validate_security_guide(project_dir="."):
    issues = []
    path = find_security_guide_file(project_dir)
    if not path:
        return [], ["보안가이드 없음"]

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    if re.search(r"(?m)^status:\s*Draft\s*$", content):
        issues.append(f"{rel_path} 상태가 Draft")
    placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
    if placeholder_issue:
        issues.append(placeholder_issue)

    required_terms = [
        ("SEC-ID", r"SEC-\d{3}|SEC-[A-Z]+"),
        ("참조 표준", r"KISA|SR\d+-\d+|OWASP|CWE"),
        ("구현 규격", r"구현 규격|값 또는 규칙|적용 위치"),
        ("화면/프로그램/DB 반영 기준", r"화면설계서|프로그램 설계서|DB명세서|Screen Spec|Program Design|Database Spec"),
        ("검증 ID", r"UT-|IT-|PT-|UI-|검증 ID|테스트 ID"),
    ]
    for label, pattern in required_terms:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"{rel_path}에 {label} 기준 없음")

    return [rel_path], issues


def validate_screen_spec(project_dir="."):
    issues = []
    path = find_screen_spec_file(project_dir)
    if not path:
        return [], ["화면설계서 없음"]

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    if re.search(r"(?m)^status:\s*Draft\s*$", content):
        issues.append(f"{rel_path} 상태가 Draft")
    placeholder_issue = unresolved_template_placeholder_issue(rel_path, content, project_dir)
    if placeholder_issue:
        issues.append(placeholder_issue)

    has_screen = bool(re.search(r"SCR-\d{3}", content))
    has_uiref = bool(re.search(r"UIREF-\d{3}", content))
    has_ui_test = bool(re.search(r"UI-\d{3}", content))
    has_viewport = bool(re.search(r"Desktop\s+\d+x\d+|Mobile\s+\d+x\d+|viewport", content, re.IGNORECASE))
    has_visual_evidence = bool(re.search(
        r"!\[[^\]]*\]\([^)]+\)|docs/artifacts/02-design/screen/(?:images|ui-baseline)/|figma|imagegen|html\s+mockup|화면 퍼블리싱|mermaid|```(?:text|mermaid|html)",
        content,
        re.IGNORECASE,
    ))
    has_ui_baseline_or_external_design = bool(re.search(
        r"docs/artifacts/02-design/screen/(?:images|ui-baseline)/|figma|imagegen|html\s+mockup|화면 퍼블리싱|외부 시안|기존 시스템 캡처|UIREF-\d{3}",
        content,
        re.IGNORECASE,
    ))
    has_ui_contract = bool(re.search(
        r"UI Implementation Contract|구현 계약|필수 유지|변경 허용|변경 금지|허용 차이|비교 방식",
        content,
        re.IGNORECASE,
    ))

    if has_screen and not has_uiref:
        issues.append(f"{rel_path}에 UIREF 기준 시안/와이어프레임 ID 없음")
    if has_screen and not has_ui_test:
        issues.append(f"{rel_path}에 UI 테스트 ID 없음")
    if has_screen and not has_viewport:
        issues.append(f"{rel_path}에 기준 viewport 없음")
    if has_screen and not has_visual_evidence:
        issues.append(f"{rel_path}에 실제 화면 구조 증적 없음(Text Wireframe fenced block, Mermaid, 화면 퍼블리싱 산출물, 이미지/Figma 등)")
    if has_screen and has_ui_baseline_or_external_design and not has_ui_contract:
        issues.append(f"{rel_path}에 UIREF/ui-baseline을 구현 계약으로 전환한 UI Implementation Contract 없음")

    text_wireframe_rows = [
        line for line in content.splitlines()
        if "Text Wireframe" in line and re.search(r"UIREF-\d{3}", line)
    ]
    if text_wireframe_rows and not re.search(r"```(?:text|mermaid|html)", content, re.IGNORECASE):
        issues.append(f"{rel_path}에 Text Wireframe 표기는 있으나 실제 와이어프레임 코드 블록 없음")

    if re.search(r"UI 기준선 판정\s*\|\s*Minimal", content) and not has_visual_evidence:
        issues.append(f"{rel_path} UI 기준선이 Minimal인데 보강 가능한 화면 구조 증적 없음")

    return [rel_path], issues


def is_resolved_discovery_status(status):
    normalized = (status or "").strip().lower()
    return normalized in {
        "closed", "resolved", "confirmed", "accepted", "done", "n/a", "na",
        "완료", "확정", "해결", "수용", "해당없음",
    }


def detect_due_gate(text):
    value = text or ""
    if re.search(r"Gate\s*1|게이트\s*1|G1", value, re.IGNORECASE):
        return "gate1"
    if re.search(r"Gate\s*2|게이트\s*2|G2", value, re.IGNORECASE):
        return "gate2"
    if re.search(r"Gate\s*3|게이트\s*3|G3", value, re.IGNORECASE):
        return "gate3"
    if re.search(r"구현|impl|Gate\s*4|게이트\s*4|G4", value, re.IGNORECASE):
        return "impl"
    return None


def is_empty_table_value(value):
    normalized = (value or "").strip()
    return normalized in {"", "-", "미정", "확인필요", "TBD", "TODO"}


def find_header_index(headers, candidates):
    for idx, header in enumerate(headers):
        normalized = header.replace(" ", "").lower()
        for candidate in candidates:
            if candidate.replace(" ", "").lower() in normalized:
                return idx
    return None


def validate_discovery_open_items(project_dir=".", current_gate="phase0"):
    issues = []
    path = find_risk_assumption_file(project_dir)
    if not path:
        return issues

    with open(path, encoding="utf-8") as f:
        content = f.read()

    rel_path = os.path.relpath(path, project_dir)
    current_idx = GATE_ORDER.index(current_gate) if current_gate in GATE_ORDER else 0
    registry_counts = {"RISK": 0, "ASM": 0, "Q": 0}
    registry_labels = {
        "RISK": "위험 목록",
        "ASM": "가정 목록",
        "Q": "미결 질문",
    }
    registry_content_headers = {
        "RISK": ["위험 내용"],
        "ASM": ["가정 내용"],
        "Q": ["질문"],
    }

    section = ""
    headers = []
    for line in content.splitlines():
        section_match = re.match(r"^#{2,}\s*(.+?)\s*$", line.strip())
        if section_match:
            section = section_match.group(1)
            headers = []
            continue

        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cols = [c.strip() for c in stripped.strip("|").split("|")]
        if not cols:
            continue
        if cols[0] in {"---", ":---", "---:"} or all(re.match(r"^:?-{3,}:?$", col) for col in cols):
            continue
        if cols[0] in {"RISK-ID", "ASM-ID", "Q-ID"}:
            headers = cols
            continue

        item_id = cols[0]
        if not re.match(r"^(RISK|ASM|Q)-\d{3}$", item_id):
            continue

        item_type = item_id.split("-", 1)[0]
        content_idx = find_header_index(headers, registry_content_headers[item_type]) if headers else None
        content_value = cols[content_idx] if content_idx is not None and content_idx < len(cols) else ""
        status_idx = find_header_index(headers, ["상태"]) if headers else None
        status = cols[status_idx] if status_idx is not None and status_idx < len(cols) else cols[-1]

        if is_empty_table_value(content_value):
            if current_idx >= GATE_ORDER.index("gate1"):
                issues.append(
                    f"  X {rel_path}의 {item_id}는 ID만 있고 내용이 비어 있습니다 "
                    "(삭제하거나 실제 내용/해당없음 사유를 작성)"
                )
                continue
        else:
            registry_counts[item_type] += 1

        due_idx = None
        if item_id.startswith("Q-"):
            due_idx = find_header_index(headers, ["기한"]) if headers else None
        elif item_id.startswith("ASM-"):
            due_idx = find_header_index(headers, ["확인 방법", "확인방법"]) if headers else None
        elif item_id.startswith("RISK-"):
            due_idx = find_header_index(headers, ["대응 방향", "대응방향"]) if headers else None
        if due_idx is None:
            due_idx = 4 if len(cols) > 4 else None
        due_source = cols[due_idx] if due_idx is not None and due_idx < len(cols) else ""

        due_gate = detect_due_gate(due_source)
        due_idx_order = GATE_ORDER.index(due_gate) if due_gate in GATE_ORDER else None

        if is_resolved_discovery_status(status):
            if due_idx_order is None or current_idx < due_idx_order:
                continue
            result_idx = find_header_index(headers, [
                "결정/처리 결과", "확인/처리 결과", "답변/결정 내용", "처리 결과", "결정 내용",
            ]) if headers else None
            basis_idx = find_header_index(headers, ["결정 근거", "연결 ID", "연결ID"]) if headers else None
            decided_at_idx = find_header_index(headers, ["결정일시", "결정 일시", "변경일시", "변경 일시"]) if headers else None
            decider_idx = find_header_index(headers, ["결정자", "확인자"]) if headers else None
            required_resolution_fields = [
                ("결정/처리 결과", result_idx),
                ("결정 근거/연결 ID", basis_idx),
                ("결정일시", decided_at_idx),
                ("결정자", decider_idx),
            ]
            for label, idx in required_resolution_fields:
                if idx is None or idx >= len(cols) or is_empty_table_value(cols[idx]):
                    issues.append(f"  X {rel_path}의 {item_id}는 상태가 {status}이지만 {label}가 비어 있습니다")
            continue

        if due_idx_order is not None and current_idx >= due_idx_order:
            issues.append(
                f"  X {rel_path}의 {item_id}가 {due_source}까지 정리되어야 하지만 상태가 {status or '미정'}입니다"
            )

    if current_idx >= GATE_ORDER.index("gate1"):
        for item_type, count in registry_counts.items():
            if count == 0:
                issues.append(
                    f"  X {rel_path}의 {registry_labels[item_type]}에 유효한 {item_type} 행이 없습니다 "
                    f"(최소 1건 작성하거나 {item_type}-001에 해당없음 사유를 명시)"
                )

    return issues


def has_completed_run(project_dir=".", gate=None, skill=None, persona=None):
    runs_dir = os.path.join(project_dir, "docs", "runs")
    if not os.path.isdir(runs_dir):
        return False

    for root, _, files in os.walk(runs_dir):
        for filename in files:
            if not filename.lower().endswith(".md"):
                continue
            path = os.path.join(root, filename)
            with open(path, encoding="utf-8") as f:
                content = f.read()

            if gate and not re.search(rf'(?m)^gate:\s*{re.escape(gate)}\s*$', content):
                continue
            if skill and not re.search(rf'(?m)^skill:\s*{re.escape(skill)}\s*$', content):
                continue
            if persona and not re.search(rf'(?m)^persona:\s*{re.escape(persona)}\s*$', content):
                continue
            if re.search(r'(?m)^status:\s*(Completed|Verified)\s*$', content):
                run_issues, _warnings = check_run_file(path)
                if run_issues:
                    continue
                return True
    return False


def collect_run_gate_records(project_dir="."):
    runs_dir = os.path.join(project_dir, "docs", "runs")
    records = []
    if not os.path.isdir(runs_dir):
        return records

    for root, _, files in os.walk(runs_dir):
        for filename in files:
            if not filename.lower().endswith(".md"):
                continue
            if filename == ".gitkeep":
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue
            gate_match = re.search(r'(?m)^gate:\s*([A-Za-z0-9_-]+)\s*$', content)
            status_match = re.search(r'(?m)^status:\s*(.+?)\s*$', content)
            records.append({
                "path": os.path.relpath(path, project_dir),
                "gate": gate_match.group(1).lower() if gate_match else "",
                "status": status_match.group(1).strip() if status_match else "",
            })
    return records


def has_open_run_for_gate(project_dir=".", gate=None):
    open_statuses = {"draft", "inprogress", "in progress", "running"}
    for record in collect_run_gate_records(project_dir):
        if gate and record["gate"] != gate:
            continue
        if record["status"].strip().lower() in open_statuses:
            return True
    return False


def detect_early_implementation_files(project_dir="."):
    candidates = [
        "app",
        "src",
        "tests",
        "test",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "pom.xml",
        "build.gradle",
    ]
    found = []
    for rel_path in candidates:
        path = os.path.join(project_dir, rel_path)
        if not os.path.exists(path):
            continue
        if os.path.isdir(path):
            has_real_file = False
            for _root, _dirs, files in os.walk(path):
                if any(filename != ".gitkeep" for filename in files):
                    has_real_file = True
                    break
            if has_real_file:
                found.append(rel_path)
        else:
            found.append(rel_path)
    return found


def validate_gate_progression(project_dir=".", current_gate="phase0"):
    issues = []
    if current_gate not in GATE_ORDER:
        return issues

    current_idx = GATE_ORDER.index(current_gate)
    run_records = collect_run_gate_records(project_dir)
    future_runs = [
        record for record in run_records
        if record["gate"] in GATE_ORDER and GATE_ORDER.index(record["gate"]) > current_idx
    ]
    for record in future_runs:
        issues.append(
            f"  X 프로세스 위반: 현재 Gate는 {current_gate}인데 앞선 Gate Run이 존재합니다 "
            f"({record['gate']}, {record['path']})"
        )

    if current_idx < GATE_ORDER.index("impl"):
        early_files = detect_early_implementation_files(project_dir)
        for rel_path in early_files:
            issues.append(
                f"  X 프로세스 위반: 현재 Gate는 {current_gate}인데 구현/테스트 파일 후보가 존재합니다 ({rel_path})"
            )

    return issues


def validate_artifact_content_boundaries(project_dir="."):
    issues = []
    artifact_dir = os.path.join(project_dir, "docs", "artifacts")
    if not os.path.isdir(artifact_dir):
        return issues

    operational_patterns = [
        r"현재\s*Gate\s*는\s*[A-Za-z0-9_-]+",
        r"현재\s*게이트\s*는\s*[A-Za-z0-9_-]+",
        r"current\s+gate\s+is\s+[A-Za-z0-9_-]+",
    ]
    target_sections = ("주요 제약", "요구사항", "성공 기준", "비목표")

    for root, _, files in os.walk(artifact_dir):
        if os.path.basename(root).lower() == "evidence":
            continue
        for filename in files:
            if not filename.lower().endswith(".md"):
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, encoding="utf-8") as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                continue

            current_section = ""
            for idx, line in enumerate(lines, start=1):
                section_match = re.match(r"^#{2,}\s*(.+?)\s*$", line)
                if section_match:
                    current_section = section_match.group(1)
                if not any(section in current_section for section in target_sections):
                    continue
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in operational_patterns):
                    rel_path = os.path.relpath(path, project_dir)
                    issues.append(
                        f"  X 문서 경계 위반: {rel_path}:{idx}에 운영 상태가 업무 산출물 본문에 기록되었습니다 "
                        "(현재 Gate/Run 상태는 session.json 또는 docs/runs에 기록)"
                    )
    return issues


def is_unresolved_trace_value(value):
    normalized = value.strip().lower()
    return normalized in {"", "-", "미정", "확인필요", "tbd", "todo"}


def traceability_completion_required(session, current_gate):
    gate4_status = str(session.get("gate_status", {}).get("gate4", "")).lower()
    return current_gate == "gate5" or gate4_status in {"done", "completed", "awaiting-approval"}


def is_incomplete_trace_status(value):
    normalized = clean_contract_cell(value).lower()
    return normalized in {"draft", "defined", "designed", "planned", "implemented", "초안", "계획됨", "구현완료"}


def validate_traceability_completion_status(project_dir=".", session=None, current_gate="phase0"):
    session = session or load_session(project_dir)
    if not traceability_completion_required(session, current_gate):
        return []

    path = find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-traceability"),
        r"traceability.*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "TRACEABILITY.md"),
    ])
    if not path:
        return []

    with open(path, encoding="utf-8") as f:
        content = f.read()

    issues = []
    summary_section, summary_start_line = extract_markdown_section_with_start_line(content, r"요구사항별\s*검증\s*요약")
    for _headers, rows in parse_markdown_tables(summary_section, start_line_offset=summary_start_line):
        for row in rows:
            req_id = table_cell(row, ["REQ-ID"])
            status = table_cell(row, ["검증 상태", "상태"])
            if re.match(r"^(REQ|NREQ)-", req_id) and is_incomplete_trace_status(status):
                line_num = row.get("__line_num__", "?")
                filename = os.path.basename(path)
                issues.append(
                    f"  X {filename}:{line_num}\n"
                    f"    요구사항별 검증 요약에 Gate 4 이후 미완료 상태가 남아 있습니다: {req_id} 상태가 '{status}'입니다.\n"
                    f"    Suggested: 모든 테스트 및 확인이 완료되었다면 해당 상태를 'Verified' 또는 '완료'로 갱신하십시오."
                )

    security_section, sec_start_line = extract_markdown_section_with_start_line(content, r"보안항목\s*추적")
    for _headers, rows in parse_markdown_tables(security_section, start_line_offset=sec_start_line):
        for row in rows:
            sec_id = table_cell(row, ["SEC-ID"])
            status = table_cell(row, ["상태"])
            if sec_id.startswith("SEC-") and is_incomplete_trace_status(status):
                line_num = row.get("__line_num__", "?")
                filename = os.path.basename(path)
                issues.append(
                    f"  X {filename}:{line_num}\n"
                    f"    보안항목 추적에 Gate 4 이후 미완료 상태가 남아 있습니다: {sec_id} 상태가 '{status}'입니다.\n"
                    f"    Suggested: 보안 점검이 완료되었다면 상태를 'Verified' 또는 '완료'로 갱신하십시오."
                )

    return issues


def check_trace(project_dir=".", exit_on_error=True):
    session = load_session(project_dir)
    current_gate = session.get("current_gate", "phase0")
    profile = load_delivery_profile(project_dir)
    issues = []
    warnings = []

    print(f"\n[check-trace] {session.get('project', '프로젝트')} - {GATE_LABELS.get(current_gate, current_gate)}\n")
    if profile == "poc":
        print("  Profile: poc (누락/TBD 일부는 가설 검증 경고로 처리)")
        warnings.extend(collect_poc_tbd_warnings(project_dir))
    elif profile == "product":
        print("  Profile: product (docs/product 원장 기준으로 핵심 시나리오와 릴리즈 추적을 확인)")

    progression_issues = validate_gate_progression(project_dir, current_gate)
    if progression_issues:
        print("  Gate 진행 상태 검사: 위반 감지")
        issues.extend(progression_issues)
    else:
        print("  Gate 진행 상태 검사: OK")

    if profile == "poc":
        print("  PoC profile 검사: 필수 산출물과 최소 trace 연결 확인")
        poc_issues, poc_warnings = validate_poc_trace(project_dir, gate=current_gate)
        issues.extend(poc_issues)
        warnings.extend(poc_warnings)
        if poc_issues:
            print(f"  PoC profile 검사: 이슈 {len(poc_issues)}건")
        elif poc_warnings:
            print(f"  PoC profile 검사: 경고 {len(poc_warnings)}건")
        else:
            print("  PoC profile 검사: OK")

        try:
            stats = compute_stats(project_dir)
            session["stats"] = stats
            save_session(session, project_dir)
        except Exception as e:
            print(f"  [경고] stats 계산 실패: {e}")

        print()
        if warnings:
            print(f"경고 {len(warnings)}건:\n")
            for warning in warnings:
                print(f"  {warning}")
            print()
        if issues:
            print(f"이슈 {len(issues)}건 발견 - Gate 완료 불가:\n")
            for issue in issues:
                print(f"  {issue}")
            if exit_on_error:
                sys.exit(1)
        else:
            print("이슈 0건 - Gate 완료 가능합니다.")
        return issues, warnings

    if profile == "product":
        print("  Product profile 검사: Product 문서 세트와 핵심 trace 연결 확인")
        product_issues, product_warnings = validate_product_trace(project_dir, gate=current_gate)
        issues.extend(product_issues)
        warnings.extend(product_warnings)
        if product_issues:
            print(f"  Product profile 검사: 이슈 {len(product_issues)}건")
        elif product_warnings:
            print(f"  Product profile 검사: 경고 {len(product_warnings)}건")
        else:
            print("  Product profile 검사: OK")

        try:
            stats = compute_stats(project_dir)
            session["stats"] = stats
            save_session(session, project_dir)
        except Exception as e:
            print(f"  [경고] stats 계산 실패: {e}")

        print()
        if warnings:
            print(f"경고 {len(warnings)}건:\n")
            for warning in warnings:
                print(f"  {warning}")
            print()
        if issues:
            print(f"이슈 {len(issues)}건 발견 - Gate 완료 불가:\n")
            for issue in issues:
                print(f"  {issue}")
            if exit_on_error:
                sys.exit(1)
        else:
            print("이슈 0건 - Gate 완료 가능합니다.")
        return issues, warnings

    boundary_issues = validate_artifact_content_boundaries(project_dir)
    if boundary_issues:
        print("  문서 내용 경계 검사: 위반 감지")
        issues.extend(boundary_issues)
    else:
        print("  문서 내용 경계 검사: OK")

    discovery_validation_gate = "gate1" if current_gate == "phase0" else current_gate
    discovery_issues = validate_discovery_open_items(project_dir, discovery_validation_gate)
    if discovery_issues:
        print("  Phase 0 미결 항목 검사: 위반 감지")
        issues.extend(discovery_issues)
    else:
        print("  Phase 0 미결 항목 검사: OK")

    if current_gate in ("gate3", "impl", "gate4", "gate5"):
        print("  Gate 2 산출물 유지 검사")
        prior_design_checks = [
            ("SW 아키텍처 정의서", validate_architecture_spec),
            ("프로그램 설계서", validate_program_spec),
            ("보안가이드", validate_security_guide),
            ("화면설계서", validate_screen_spec),
            ("API 정의서", validate_api_spec),
            ("개발표준정의서", validate_development_standard),
            ("프로젝트 단어사전", validate_project_glossary),
        ]
        for label, validator in prior_design_checks:
            _files, prior_issues = validator(project_dir)
            if prior_issues:
                issues.extend(f"  X {issue}" for issue in prior_issues)
            else:
                print(f"  O {label} 확인")

    group_reqs, detail_reqs, defined_acs, ac_delegates = parse_requirements(project_dir)

    # ── Gate 1: REQ-ID별 AC 존재 여부 + TRACEABILITY.md 행 등록 여부
    if current_gate == "gate1":
        print("  Gate 1 검사 (1): 인수 기준(AC) 정의 여부")
        if not detail_reqs:
            issues.append("REQUIREMENTS.md에 REQ-NNN-NN 형식의 요구사항이 없습니다.")
        for req in sorted(detail_reqs):
            ac_id = req.replace("REQ-", "")
            if ac_id in defined_acs:
                print(f"  O {req} - AC 확인")
            elif ac_id in ac_delegates and ac_delegates[ac_id] in defined_acs:
                print(f"  O {req} - AC-{ac_delegates[ac_id]} 위임 확인")
            else:
                req_line = detail_reqs.get(req)
                line_suffix = f":{req_line}" if req_line is not None else ""
                req_path = find_artifact_file(
                    project_dir,
                    os.path.join("docs", "artifacts", "01-requirements"),
                    r"requirements.*\.md$",
                ) or find_first_existing(project_dir, [
                    os.path.join("docs", "01-requirements", "REQUIREMENTS.md"),
                ])
                req_file = os.path.relpath(req_path, project_dir) if req_path else "REQUIREMENTS.md"
                issues.append(
                    f"  X {req} - AC 미정의\n"
                    f"    Path: {req_file}{line_suffix}\n"
                    f"    Suggested: {req_file} 파일에 '### AC-{ac_id}' 등의 인수 기준(AC) 섹션 또는 테이블 항목을 추가하십시오."
                )

        print("\n  Gate 1 검사 (2): TRACEABILITY.md 행 등록 여부")
        traceability = parse_traceability(project_dir)
        if not traceability:
            issues.append("  X TRACEABILITY.md 없음 — PM이 작성해야 합니다")
        else:
            for req in sorted(detail_reqs):
                if req in traceability:
                    print(f"  O {req} - TRACEABILITY.md 행 확인")
                else:
                    req_line = detail_reqs.get(req)
                    line_suffix = f":{req_line}" if req_line is not None else ""
                    req_path = find_artifact_file(
                        project_dir,
                        os.path.join("docs", "artifacts", "01-requirements"),
                        r"requirements.*\.md$",
                    ) or find_first_existing(project_dir, [
                        os.path.join("docs", "01-requirements", "REQUIREMENTS.md"),
                    ])
                    req_file = os.path.relpath(req_path, project_dir) if req_path else "REQUIREMENTS.md"

                    trace_path = find_artifact_file(
                        project_dir,
                        os.path.join("docs", "artifacts", "02-traceability"),
                        r"traceability.*\.md$",
                    ) or find_first_existing(project_dir, [
                        os.path.join("docs", "TRACEABILITY.md"),
                    ])
                    trace_file = os.path.relpath(trace_path, project_dir) if trace_path else "TRACEABILITY.md"

                    issues.append(
                        f"  X TRACEABILITY.md에 {req} 행 미등록\n"
                        f"    Path: {req_file}{line_suffix}\n"
                        f"    Suggested: {trace_file} 파일의 요구사항 추적 테이블에 '{req}' 행을 추가하십시오."
                    )

    # ── Gate 2: 설계 파일 내 REQ-ID 포함 여부 (TRACEABILITY.md 우선, 없으면 그룹 파일 fallback)
    if current_gate == "gate2":
        design_dir = find_first_existing(project_dir, [
            os.path.join("docs", "artifacts", "02-design"),
            os.path.join("docs", "02-design"),
        ])
        traceability = parse_traceability(project_dir)

        if traceability:
            print("  Gate 2 검사: TRACEABILITY.md 기반 설계 파일 내 REQ-ID 포함 확인")
            design_docs = []
            if design_dir and os.path.isdir(design_dir):
                for root, _dirs, files in os.walk(design_dir):
                    for file_name in files:
                        if file_name.endswith(".md"):
                            design_docs.append(os.path.join(root, file_name))
            for req in sorted(detail_reqs):
                info = traceability.get(req)
                if info and re.search(r'통합|삭제됨', info.get("status", "")):
                    print(f"  - {req} - {info['status']} (검사 제외)")
                    continue
                if not info or not info["design"]:
                    line_num = info.get("__line_num__", "?") if info else "?"
                    issues.append(f"  X TRACEABILITY.md:{line_num} (참조 행)\n    {req} 설계 문서 미등록\n    Suggested: TRACEABILITY.md 해당 행의 설계 문서(예: docs/02-design/api-design.md) 항목을 기입하십시오.")
                    continue
                # 쉼표 구분된 복수 설계 파일 지원
                design_files = [f.strip() for f in info["design"].split(',') if f.strip()]
                found_in_any = False
                missing_files = []
                for df in design_files:
                    if not df.endswith(".md"):
                        continue
                    filepath = os.path.join(design_dir or "", df)
                    if not os.path.exists(filepath):
                        missing_files.append(df)
                        continue
                    with open(filepath, encoding="utf-8") as f:
                        content = f.read()
                    if req in content:
                        found_in_any = True
                        break
                if not found_in_any and design_docs:
                    for filepath in design_docs:
                        with open(filepath, encoding="utf-8") as f:
                            content = f.read()
                        if req in content:
                            found_in_any = True
                            break
                if missing_files and not found_in_any:
                    line_num = info.get("__line_num__", "?")
                    issues.append(f"  X TRACEABILITY.md:{line_num} (참조 행)\n    {req} - {', '.join(missing_files)} 파일 없음\n    Suggested: 해당 설계 파일을 생성하거나, TRACEABILITY.md의 '설계 문서' 항목을 올바른 파일명으로 수정하십시오.")
                elif found_in_any:
                    print(f"  O {req} - 설계 산출물 내 ID 확인")
                else:
                    line_num = info.get("__line_num__", "?")
                    issues.append(f"  X TRACEABILITY.md:{line_num} (참조 행)\n    설계 산출물 안에 {req} 텍스트 없음\n    Suggested: 지정된 설계 문서 안에 '{req}' 문자열을 명시적으로 기입하여 추적성을 연결하십시오.")
        else:
            print("  Gate 2 검사: REQ 그룹별 설계 파일 존재 여부 (TRACEABILITY.md 없음 — fallback)")
            for group in sorted(group_reqs):
                filename = f"{group.lower()}-design.md"
                filepath = os.path.join(design_dir or "", filename)
                if os.path.exists(filepath):
                    print(f"  O {group} - {filename} 확인")
                else:
                    issues.append(f"  X {group} - docs/02-design/{filename} 없음")

        print("\n  Gate 2 검사: SW 아키텍처 정의서 확정 여부")
        architecture_files, architecture_issues = validate_architecture_spec(project_dir)
        if architecture_files and not architecture_issues:
            print(f"  O SW 아키텍처 정의서 확인 ({', '.join(architecture_files)})")
        for issue in architecture_issues:
            issues.append(f"  X {issue}")

        print("\n  Gate 2 검사: 보안가이드 확정 여부")
        security_guide_files, security_guide_issues = validate_security_guide(project_dir)
        if security_guide_files and not security_guide_issues:
            print(f"  O 보안가이드 확인 ({', '.join(security_guide_files)})")
        for issue in security_guide_issues:
            issues.append(f"  X {issue}")

        print("\n  Gate 2 검사: 프로그램 설계서 상세 SW 설계 여부")
        program_spec_files, program_spec_issues = validate_program_spec(project_dir)
        if program_spec_files and not program_spec_issues:
            print(f"  O 프로그램 설계서 확인 ({', '.join(program_spec_files)})")
        for issue in program_spec_issues:
            issues.append(f"  X {issue}")

        print("\n  Gate 2 검사: 화면설계 기준 증적 여부")
        screen_spec_files, screen_spec_issues = validate_screen_spec(project_dir)
        if screen_spec_files and not screen_spec_issues:
            print(f"  O 화면설계서 기준 증적 확인 ({', '.join(screen_spec_files)})")
        for issue in screen_spec_issues:
            issues.append(f"  X {issue}")

        print("\n  Gate 2 검사: API 정의서 상세 여부")
        api_spec_files, api_spec_issues = validate_api_spec(project_dir)
        if api_spec_files and not api_spec_issues:
            print(f"  O API 정의서 확인 ({', '.join(api_spec_files)})")
        elif not api_spec_files and not api_spec_issues:
            print("  - API 정의서 검사 제외 (프로그램 설계서에 API 없음)")
        for issue in api_spec_issues:
            issues.append(f"  X {issue}")

        print("\n  Gate 2 검사: 개발표준정의서 근거 여부")
        dev_standard_files, dev_standard_issues = validate_development_standard(project_dir)
        if dev_standard_files and not dev_standard_issues:
            print(f"  O 개발표준정의서 확인 ({', '.join(dev_standard_files)})")
        for issue in dev_standard_issues:
            issues.append(f"  X {issue}")

        print("\n  Gate 2 검사: 프로젝트 단어사전/도메인 여부")
        glossary_files, glossary_issues = validate_project_glossary(project_dir)
        if glossary_files and not glossary_issues:
            print(f"  O 프로젝트 단어사전 확인 ({', '.join(glossary_files)})")
        for issue in glossary_issues:
            issues.append(f"  X {issue}")

        print("\n  Gate 2 검사: Gate 3 진입 전 설계 검수 Run 완료 여부")
        required_review_runs = [
            ("security-review", "보안 검토"),
            ("screen-review", "화면 검토"),
            ("ui-review", "UI 품질 검토"),
            ("development-standard-review", "개발표준 검토"),
        ]
        for skill_name, label in required_review_runs:
            if has_completed_run(project_dir, gate="gate2", skill=skill_name):
                print(f"  O {label} Run 완료 확인 ({skill_name})")
            else:
                issues.append(f"  X {label} Run 미완료 - Gate 3 진입 전 {skill_name} 완료 필요")

    # ── Gate 3: 모든 REQ-NNN-NN에 TST-ID 매핑 여부 + TRACEABILITY.md tst_ids 등록 여부
    if current_gate == "gate3":
        print("  Gate 3 검사 (1): REQ-ID별 TST-ID 커버리지")
        covered = parse_test_plan(project_dir)
        traceability = parse_traceability(project_dir)
        for req in sorted(detail_reqs):
            req_status = traceability.get(req, {}).get("status", "")
            if req_status == "삭제됨" or re.search(r'통합', req_status):
                print(f"  - {req} - {req_status} (검사 제외)")
                continue
            if req in covered:
                print(f"  O {req} - TST 매핑 확인")
            else:
                trace_info = traceability.get(req, {})
                trace_line = trace_info.get("__line_num__")
                trace_path = find_artifact_file(
                    project_dir,
                    os.path.join("docs", "artifacts", "02-traceability"),
                    r"traceability.*\.md$",
                ) or find_first_existing(project_dir, [
                    os.path.join("docs", "TRACEABILITY.md"),
                ])
                trace_file = os.path.relpath(trace_path, project_dir) if trace_path else "TRACEABILITY.md"
                line_suffix = f":{trace_line}" if trace_line is not None else ""

                message = (
                    f"  X {req} - 테스트케이스 문서에 상세 REQ-ID 테스트 매핑 없음\n"
                    f"    Path: {trace_file}{line_suffix}\n"
                    f"    Suggested: Test-Plan.md 등의 테스트케이스 계획서 문서에 '{req}'에 대응하는 테스트케이스(TST-ID 등)를 작성하고, 해당 REQ-ID가 기재된 테스트 테이블 행을 추가하십시오."
                )
                if profile == "poc":
                    warnings.append(message.replace("  X ", "  ! ", 1))
                else:
                    issues.append(message)

        print("\n  Gate 3 검사 (2): TRACEABILITY.md tst_ids 컬럼 등록 여부")
        for req in sorted(detail_reqs):
            info = traceability.get(req, {})
            req_status2 = info.get("status", "")
            if req_status2 == "삭제됨" or re.search(r'통합', req_status2):
                continue
            unresolved_columns = [
                label for label, value in info.get("test_columns", {}).items()
                if is_unresolved_trace_value(value)
            ]
            if unresolved_columns:
                trace_line = info.get("__line_num__")
                trace_path = find_artifact_file(
                    project_dir,
                    os.path.join("docs", "artifacts", "02-traceability"),
                    r"traceability.*\.md$",
                ) or find_first_existing(project_dir, [
                    os.path.join("docs", "TRACEABILITY.md"),
                ])
                trace_file = os.path.relpath(trace_path, project_dir) if trace_path else "TRACEABILITY.md"
                line_suffix = f":{trace_line}" if trace_line is not None else ""

                message = (
                    f"  X {req} - TRACEABILITY.md 테스트 컬럼 미정: {', '.join(unresolved_columns)}\n"
                    f"    Path: {trace_file}{line_suffix}\n"
                    f"    Suggested: {trace_file} 파일의 '{req}' 행에서 {', '.join(unresolved_columns)} 컬럼에 구체적인 테스트 ID(예: UT-001, IT-001, UI-001) 또는 '해당없음'을 기재하십시오."
                )
                if profile == "poc":
                    warnings.append(message.replace("  X ", "  ! ", 1))
                else:
                    issues.append(message)
                continue
            tst_ids = info.get("tst_ids", [])
            if tst_ids:
                print(f"  O {req} - TST-ID {', '.join(tst_ids)} 등록 확인")
            else:
                trace_line = info.get("__line_num__")
                trace_path = find_artifact_file(
                    project_dir,
                    os.path.join("docs", "artifacts", "02-traceability"),
                    r"traceability.*\.md$",
                ) or find_first_existing(project_dir, [
                    os.path.join("docs", "TRACEABILITY.md"),
                ])
                trace_file = os.path.relpath(trace_path, project_dir) if trace_path else "TRACEABILITY.md"
                line_suffix = f":{trace_line}" if trace_line is not None else ""

                message = (
                    f"  X {req} - TRACEABILITY.md에 tst_ids 미등록\n"
                    f"    Path: {trace_file}{line_suffix}\n"
                    f"    Suggested: {trace_file} 파일의 '{req}' 행에 테스트 ID(TST-ID 또는 UT/IT/UI-ID)를 올바르게 명시하십시오."
                )
                if profile == "poc":
                    warnings.append(message.replace("  X ", "  ! ", 1))
                else:
                    issues.append(message)

    # ── Impl: 개발표준 확정 + 구현 파일/테스트 연결 확인
    if current_gate == "impl":
        print("  Impl 검사 (0): Implementation Plan Run 여부")
        if has_completed_run(project_dir, gate="impl", skill="implementation-plan"):
            print("  O Implementation Plan Run 완료 확인")
        else:
            print("  ! Implementation Plan Run 없음 - 작은 구현은 Wave 분할 생략 가능하지만 native worker 위임 기록 필요")

        print("\n  Impl 검사 (1): 개발표준정의서 확정 여부")
        dev_standard_files, dev_standard_issues = validate_development_standard(project_dir)
        if dev_standard_files and not dev_standard_issues:
            print(f"  O 개발표준정의서 확인 ({dev_standard_files[0]})")
        for issue in dev_standard_issues:
            issues.append(f"  X {issue}")

        print("\n  Impl 검사 (2): TRACEABILITY.md 구현 증적 파일 존재 및 ID 포함 여부")
        traceability = parse_traceability(project_dir)
        if not traceability:
            issues.append("  X TRACEABILITY.md 없음 - 구현 파일 연결 확인 불가")
        for req in sorted(detail_reqs):
            info = traceability.get(req, {})
            req_status = info.get("status", "")
            if req_status == "삭제됨" or re.search(r'통합', req_status):
                continue

            evidence_paths = [
                item for item in split_trace_values(info.get("review", ""))
                if is_probable_source_path(item)
            ]
            if not evidence_paths:
                issues.append(f"  X {req} - 추적표 증적에 구현 파일 경로 없음")
                continue

            existing_paths = []
            id_found = False
            related_ids = [req] + info.get("tst_ids", [])
            for evidence_path in evidence_paths:
                full_path = os.path.join(project_dir, evidence_path)
                if not os.path.exists(full_path):
                    issues.append(f"  X {req} - 구현 증적 파일 없음: {evidence_path}")
                    continue
                existing_paths.append(evidence_path)
                if is_probable_text_file(full_path):
                    try:
                        with open(full_path, encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        content = ""
                    if any(related_id and related_id in content for related_id in related_ids):
                        id_found = True

            if existing_paths:
                print(f"  O {req} - 구현 파일 존재 확인 ({', '.join(existing_paths[:3])})")
                if id_found:
                    print(f"  O {req} - 구현/테스트 파일 내 관련 ID 확인")
                else:
                    issues.append(f"  X {req} - 구현/테스트 파일 안에 관련 REQ 또는 TEST ID 없음")

        print("\n  Impl 검사 (3): 테스트케이스 실행 상태")
        tst_results = parse_test_plan_status(project_dir)
        if not tst_results:
            issues.append("  X 테스트케이스 실행 상태 없음")
        else:
            not_passed = [(tid, status) for tid, status in tst_results if status != "pass"]
            passed = [(tid, status) for tid, status in tst_results if status == "pass"]
            print(
                f"  출처: Gate 3 테스트 계획 / 총 {len(tst_results)}건: "
                f"Pass {len(passed)}, Gate 4 예정 {len(not_passed)}"
            )
            print("  ! Impl 단계에서는 Gate 3 테스트케이스를 실행 결과 원본으로 보지 않습니다.")
            print("  ! 실제 Pass/Fail/Not Run 판정은 Gate 4 QA 결과서와 증적으로 확정합니다.")
            for tid, _ in passed:
                print(f"  O {tid} - Pass")
            for tid, status in not_passed:
                print(f"  - {tid} - Gate 4 예정 ({status})")

    # ── Gate 4: 리뷰 파일 내 REQ-ID 포함 여부 + TST-ID 실행 상태
    if current_gate == "gate4":
        review_dirs = [
            os.path.join(project_dir, "docs", "artifacts", "04-review"),
            os.path.join(project_dir, "docs", "04-review"),
        ]
        review_files = []
        for review_dir in review_dirs:
            if os.path.isdir(review_dir):
                for root, _, files in os.walk(review_dir):
                    if os.path.basename(root).lower() == "evidence":
                        continue
                    for filename in files:
                        if filename.lower().endswith(".md"):
                            review_files.append(os.path.join(root, filename))
        traceability = parse_traceability(project_dir)

        if traceability:
            print("  Gate 4 검사 (1): TRACEABILITY.md 기반 리뷰 파일 내 REQ-ID 포함 확인")
            file_contents = {}
            for filepath in review_files:
                with open(filepath, encoding="utf-8") as f:
                    file_contents[filepath] = f.read()
            for req in sorted(detail_reqs):
                info = traceability.get(req, {})
                status = info.get("status", "")
                if status in ("미구현", "삭제됨"):
                    print(f"  - {req} - {status} (리뷰 검사 제외)")
                    continue
                matched = [
                    os.path.relpath(path, project_dir)
                    for path, content in file_contents.items()
                    if req in content
                ]
                if matched:
                    print(f"  O {req} - 리뷰 문서 내 ID 확인 ({matched[0]})")
                else:
                    issues.append(f"  X {req} - docs/artifacts/04-review 리뷰 문서 안에 {req} 없음")
        else:
            print("  Gate 4 검사 (1): REQ 그룹별 리뷰 파일 존재 여부 (TRACEABILITY.md 없음 — fallback)")
            if not review_files:
                for group in sorted(group_reqs):
                    issues.append(f"  X {group} - docs/artifacts/04-review 리뷰 문서 없음")
                    continue
            file_contents = {}
            for filepath in review_files:
                if filepath not in file_contents:
                    with open(filepath, encoding="utf-8") as f:
                        file_contents[filepath] = f.read()
            for group in sorted(group_reqs):
                if any(group in content for content in file_contents.values()):
                    print(f"  O {group} - 리뷰 문서 내 ID 확인")
                else:
                    issues.append(f"  X {group} - docs/artifacts/04-review 리뷰 문서 안에 {group} 없음")

        print("\n  Gate 4 검사 (2): TST-ID 실행 상태")
        qa_results = parse_qa_test_result_status(project_dir)
        if qa_results:
            tst_results = qa_results
            source_label = "QA 결과서"
            qa_path = find_qa_test_result_file(project_dir)
            tst_file = os.path.relpath(qa_path, project_dir) if qa_path else "QA-Test-Result.md"
        else:
            tst_results = parse_test_plan_status(project_dir)
            source_label = "Gate 3 테스트케이스 fallback"
            test_plan_path = find_artifact_file(
                project_dir,
                os.path.join("docs", "artifacts", "03-test"),
                r"(test.*case|test.*plan|test.*cases).*\.md$",
            ) or find_first_existing(project_dir, [
                os.path.join("docs", "03-test-plan", "Test-Plan.md"),
            ])
            tst_file = os.path.relpath(test_plan_path, project_dir) if test_plan_path else "Test-Plan.md"
            message = "  X QA 결과서(DOC-QA-G4-002)에 실제 테스트 실행 결과가 없습니다."
            if profile == "poc":
                warnings.append(message.replace("  X ", "  ! ", 1))
            else:
                issues.append(message)
        if not tst_results:
            message = "Test-Plan.md 또는 QA 결과서에 TST/UT/IT/PT/UI 실행 상태가 없습니다."
            if profile == "poc":
                warnings.append(f"  ! {message}")
            else:
                issues.append(message)
        else:
            tst_lines = {item[0]: getattr(item, "line_num", None) for item in tst_results}
            not_executed = [(tid, s) for tid, s in tst_results if s == 'not_executed']
            environment_blocked = [(tid, s) for tid, s in tst_results if s == 'environment_blocked']
            failed = [(tid, s) for tid, s in tst_results if s == 'fail']
            passed = [(tid, s) for tid, s in tst_results if s == 'pass']
            skipped = [(tid, s) for tid, s in tst_results if s == 'skip']

            print(
                f"  출처: {source_label} / 총 {len(tst_results)}건: "
                f"Pass {len(passed)}, Fail {len(failed)}, Skip {len(skipped)}, "
                f"미실행 {len(not_executed)}, 환경차단 {len(environment_blocked)}"
            )

            for tid, _ in passed:
                print(f"  O {tid} - Pass")
            for tid, _ in skipped:
                print(f"  - {tid} - Skip")
            for tid, _ in failed:
                line_num = tst_lines.get(tid)
                line_suffix = f":{line_num}" if line_num is not None else ""
                issues.append(
                    f"  X {tid} - Fail\n"
                    f"    Path: {tst_file}{line_suffix}\n"
                    f"    Suggested: 테스트 실행 결과가 실패(Fail) 상태입니다. 구현을 수정하거나 해당 테스트를 통과시킨 후 결과를 '{tst_file}'에 'Pass'로 업데이트하십시오."
                )
                print(f"  X {tid} - Fail")
            for tid, _ in not_executed:
                line_num = tst_lines.get(tid)
                line_suffix = f":{line_num}" if line_num is not None else ""
                msg = (
                    f"  X {tid} - 미실행\n"
                    f"    Path: {tst_file}{line_suffix}\n"
                    f"    Suggested: 테스트가 아직 실행되지 않았습니다. 테스트를 수행하고 결과를 '{tst_file}'에 'Pass'로 업데이트하십시오."
                )
                if profile == "poc":
                    warnings.append(msg.replace("  X ", "  ! ", 1))
                else:
                    issues.append(msg)
                print(f"  X {tid} - 미실행")
            for tid, _ in environment_blocked:
                line_num = tst_lines.get(tid)
                line_suffix = f":{line_num}" if line_num is not None else ""
                msg = (
                    f"  X {tid} - environment_blocked\n"
                    f"    Path: {tst_file}{line_suffix}\n"
                    f"    Suggested: 테스트 실행 환경이 차단(Blocked)되었습니다. 차단 원인을 해결하고 테스트를 완료하여 '{tst_file}'에 결과를 업데이트하십시오."
                )
                if profile == "poc":
                    warnings.append(msg.replace("  X ", "  ! ", 1))
                else:
                    issues.append(msg)
                print(f"  X {tid} - environment_blocked")

    completion_status_issues = validate_traceability_completion_status(project_dir, session, current_gate)
    if completion_status_issues:
        print("\n  추적표 완료 상태 검사: 위반 감지")
        if profile == "poc":
            warnings.extend(issue.replace("  X ", "  ! ", 1) for issue in completion_status_issues)
        else:
            issues.extend(completion_status_issues)
    elif traceability_completion_required(session, current_gate):
        print("\n  추적표 완료 상태 검사: OK")

    # stats 계산 및 session.json 업데이트 — 이슈 유무와 무관하게 항상 실행
    try:
        stats = compute_stats(project_dir)
        session["stats"] = stats
        save_session(session, project_dir)
    except Exception as e:
        print(f"  [경고] stats 계산 실패: {e}")

    print()
    if warnings:
        print(f"경고 {len(warnings)}건:\n")
        for warning in warnings:
            print(f"  {warning}")
        print()
    if issues:
        print(f"이슈 {len(issues)}건 발견 - Gate 완료 불가:\n")
        for issue in issues:
            print(f"  {issue}")
        if exit_on_error:
            sys.exit(1)
    else:
        print("이슈 0건 - Gate 완료 가능합니다.")
    return issues, warnings


# ── architecture check ─────────────────────────────────────────────────────

def cmd_check_architecture(level="baseline", project_dir="."):
    files, issues = validate_architecture_spec(project_dir, level=level)
    infra_files, infra_warnings = validate_deployment_infrastructure_architecture(project_dir, level=level)
    label = "Draft" if level == "draft" else "Baseline"

    print(f"\n[check-architecture] SW 아키텍처 {label} 검사\n")
    if files:
        for rel_path in files:
            print(f"  대상: {rel_path}")
    else:
        print("  대상: 없음")
    for rel_path in infra_files:
        print(f"  참고: {rel_path}")

    if issues:
        print(f"\n이슈 {len(issues)}건 발견:\n")
        for issue in issues:
            print(f"  X {issue}")
        sys.exit(1)

    if infra_warnings:
        print(f"\n경고 {len(infra_warnings)}건:\n")
        for warning in infra_warnings:
            print(f"  ! {warning}")

    print("\n이슈 0건 - SW 아키텍처 기준을 만족합니다.")


# ── gate preflight ─────────────────────────────────────────────────────────

def validate_gate_start_prerequisites(project_dir=".", target_gate="phase0"):
    """Gate 전환 직전에 이전 단계의 완료 조건만 검사한다."""
    if target_gate not in GATE_ORDER:
        return []

    issues = []
    target_idx = GATE_ORDER.index(target_gate)
    if target_idx >= GATE_ORDER.index("gate1"):
        issues.extend(validate_discovery_open_items(project_dir, current_gate="gate1"))
    return issues


def require_gate_start_prerequisites(project_dir=".", target_gate="phase0"):
    issues = validate_gate_start_prerequisites(project_dir, target_gate)
    if not issues:
        return

    print(f"\n[gate-start] {target_gate} 진입 전 완료 조건 위반:\n")
    for issue in issues:
        print(f"  {issue}")
    print("\n이슈를 정리한 뒤 다시 Gate 전환을 실행하세요.")
    sys.exit(1)


def cmd_prepare_transition(project_dir="."):
    session = load_session(project_dir)
    current_gate = session.get("current_gate", "phase0")
    profile = load_delivery_profile(project_dir)

    if current_gate == "completed":
        print("==================================================")
        print(" [prepare-transition] Gate 전환 준비 진단")
        print("==================================================")
        print(" 현재 프로젝트는 모든 Gate를 마쳤습니다 (Completed).")
        print(" 추가적인 Gate 전환이 필요하지 않습니다.")
        print("==================================================")
        return

    if current_gate not in GATE_ORDER:
        print(f"오류: session.json의 current_gate가 유효하지 않습니다: {current_gate}")
        sys.exit(1)

    current_idx = GATE_ORDER.index(current_gate)
    next_gate = GATE_ORDER[current_idx + 1] if current_idx + 1 < len(GATE_ORDER) else "completed"

    print("==================================================")
    print(" [prepare-transition] Gate 전환 준비 진단")
    print("==================================================")
    print(f" 현재 Gate: {current_gate} ({GATE_LABELS.get(current_gate, current_gate)})")
    print(f" 목표 Gate: {next_gate} ({GATE_LABELS.get(next_gate, next_gate)})")
    print()

    overall_pass = True

    # [1] Traceability & 정합성 검사 (check-trace)
    print("[1] Traceability & 정합성 검사 (check-trace)")
    trace_issues, trace_warnings = check_trace(project_dir, exit_on_error=False)
    if trace_issues:
        overall_pass = False
        print(f"  -> 결과: ❌ {len(trace_issues)}건의 이슈 발견 (완료 불가)")
    else:
        print("  -> 결과: ✨ 0건의 이슈 발견 (통과)")
    print()

    # [2] 현재 Gate 진행 중인 Run 검사
    print("[2] 현재 Gate 진행 중인 Run 검사")
    active_runs = []
    open_statuses = {"draft", "inprogress", "in progress", "running"}
    for record in collect_run_gate_records(project_dir):
        if record["gate"] == current_gate and record["status"].strip().lower() in open_statuses:
            active_runs.append(record)

    if active_runs:
        overall_pass = False
        print(f"  -> 결과: ❌ {len(active_runs)}건의 미완료 Run 발견 (완료 불가)")
        for run in active_runs:
            print(f"     - {run['path']} ({run['status']})")
    else:
        print("  -> 결과: ✨ 0건의 미완료 Run 발견 (통과)")
    print()

    # [3] 현재 Gate worker Run preflight 사후 점검
    print("[3] 현재 Gate worker Run preflight 사후 점검")
    preflight_records = []
    preflight_skills = {"build-wave", "implementation-scaffold", "qa-execution", "qa-fix-loop"}
    preflight_statuses = {"completed", "verified", "completedwithissues"}
    for record in collect_run_gate_records(project_dir):
        if record["gate"] != current_gate:
            continue
        if record["status"].strip().lower() not in preflight_statuses:
            continue
        run_abs = os.path.join(project_dir, record["path"])
        try:
            with open(run_abs, encoding="utf-8") as f:
                run_content = f.read()
        except OSError:
            continue
        run_metadata = parse_simple_yaml_block(run_content)
        if run_metadata.get("skill") not in preflight_skills:
            continue
        blockers, warnings = run_preflight_file(run_abs)
        if blockers or warnings:
            preflight_records.append((record["path"], blockers, warnings))

    preflight_blocker_count = sum(len(blockers) for _, blockers, _ in preflight_records)
    preflight_warning_count = sum(len(warnings) for _, _, warnings in preflight_records)
    if preflight_blocker_count:
        overall_pass = False
        print(f"  -> 결과: ❌ preflight 차단 {preflight_blocker_count}건 발견 (완료 불가)")
        for path, blockers, warnings in preflight_records:
            if blockers:
                print(f"     - {path}")
                for blocker in blockers:
                    print(f"       X {blocker}")
            elif warnings:
                print(f"     - {path}: 경고 {len(warnings)}건")
    elif preflight_warning_count:
        print(f"  -> 결과: ! preflight 경고 {preflight_warning_count}건 발견 (전환 가능, 확인 권장)")
        for path, _blockers, warnings in preflight_records:
            if warnings:
                print(f"     - {path}")
                for warning in warnings:
                    print(f"       ! {warning}")
    else:
        print("  -> 결과: ✨ preflight 차단/경고 없음 (통과)")
    print()

    # [4] 산출물 내용 완성도 검사
    print("[4] 산출물 내용 완성도 검사")
    if profile == "poc":
        artifact_issues, artifact_warnings = collect_poc_profile_findings(project_dir, gate=current_gate)
    elif profile == "product":
        artifact_issues, artifact_warnings = collect_product_profile_findings(project_dir, gate=current_gate)
    else:
        artifact_issues, artifact_warnings = collect_artifact_completion_findings(project_dir)
    if artifact_issues:
        overall_pass = False
        print(f"  -> 결과: ❌ 산출물 완성도 이슈 {len(artifact_issues)}건 발견 (완료 불가)")
        for issue in artifact_issues[:20]:
            print(f"     - {issue}")
        if len(artifact_issues) > 20:
            print(f"     ... 외 {len(artifact_issues) - 20}건")
    elif artifact_warnings:
        print(f"  -> 결과: ! 산출물 완성도 경고 {len(artifact_warnings)}건 발견 (전환 가능, 확인 권장)")
        for warning in artifact_warnings[:20]:
            print(f"     - {warning}")
        if len(artifact_warnings) > 20:
            print(f"     ... 외 {len(artifact_warnings) - 20}건")
    else:
        print("  -> 결과: ✨ 산출물 완성도 차단/경고 없음 (통과)")
    print()

    # [5] Gate 전환 필수 요구사항 검사
    print("[5] Gate 전환 필수 요구사항 검사")
    transition_issues = []

    if profile == "poc":
        required_poc_docs = poc_required_artifacts_for_gate(current_gate)
        missing_poc_docs = [rel_path for rel_path in required_poc_docs if not os.path.isfile(os.path.join(project_dir, rel_path))]
        for rel_path in missing_poc_docs:
            transition_issues.append(f"PoC 필수 산출물 없음: {rel_path}")

        if current_gate == "impl":
            wave_records = collect_build_wave_records(project_dir)
            active_waves = [w for w in wave_records if w.get("status") not in ("Verified", "Completed", "Done")]
            for w in active_waves:
                run_file_str = f" ({w['run']})" if w['run'] else ""
                transition_issues.append(f"진행 중인 Build Wave 존재: 완료되지 않은 Build Wave {w['id']} ({w['status']}){run_file_str}가 있습니다.")

    elif profile == "product":
        required_product_docs = product_required_artifacts_for_gate(current_gate)
        missing_product_docs = [rel_path for rel_path in required_product_docs if not os.path.isfile(os.path.join(project_dir, rel_path))]
        for rel_path in missing_product_docs:
            transition_issues.append(f"Product 필수 산출물 없음: {rel_path}")

        if current_gate == "impl":
            wave_records = collect_build_wave_records(project_dir)
            active_waves = [w for w in wave_records if w.get("status") not in ("Verified", "Completed", "Done")]
            for w in active_waves:
                run_file_str = f" ({w['run']})" if w['run'] else ""
                transition_issues.append(f"진행 중인 Build Wave 존재: 완료되지 않은 Build Wave {w['id']} ({w['status']}){run_file_str}가 있습니다.")

    elif current_gate == "phase0":
        discovery_issues = validate_discovery_open_items(project_dir, current_gate="gate1")
        if discovery_issues:
            transition_issues.extend(discovery_issues)

    elif current_gate == "gate2":
        required_review_runs = [
            ("security-review", "보안 검토"),
            ("screen-review", "화면 검토"),
            ("ui-review", "UI 품질 검토"),
            ("development-standard-review", "개발표준 검토"),
        ]
        for skill_name, label in required_review_runs:
            if not has_completed_run(project_dir, gate="gate2", skill=skill_name):
                transition_issues.append(f"필수 검수 Run 미완료: Gate 3 진입 전 {label}({skill_name}) Run이 완료되어야 합니다.")

    elif current_gate == "impl":
        if not has_completed_run(project_dir, gate="impl", skill="implementation-plan"):
            transition_issues.append("Implementation Plan Run 미완료: 구현 진행 전 구현 계획 Run(implementation-plan)이 완료되어야 합니다.")

        wave_records = collect_build_wave_records(project_dir)
        active_waves = [w for w in wave_records if w.get("status") not in ("Verified", "Completed", "Done")]
        for w in active_waves:
            run_file_str = f" ({w['run']})" if w['run'] else ""
            transition_issues.append(f"진행 중인 Build Wave 존재: 완료되지 않은 Build Wave {w['id']} ({w['status']}){run_file_str}가 있습니다.")

    elif current_gate == "gate4":
        tst_results, _source = parse_effective_test_status(project_dir)
        failed_tests = [tid for tid, s in tst_results if s in ("fail", "not_executed", "environment_blocked")]
        if failed_tests and profile != "poc":
            transition_issues.append(f"테스트 미통과: 통과되지 않았거나 미실행된 테스트 {len(failed_tests)}건이 있습니다 (예: {', '.join(failed_tests[:5])}).")

    if transition_issues:
        overall_pass = False
        print(f"  -> 결과: ❌ {len(transition_issues)}건의 위반 사항 발견 (완료 불가)")
        for issue in transition_issues:
            print(f"     - {issue}")
    else:
        print("  -> 결과: ✨ 필수 요구사항 충족 (통과)")
    print()

    print("--------------------------------------------------")
    if overall_pass:
        print("진단 결과: ✨ [전환 준비 완료]")
        print("다음 단계로의 전환이 가능합니다! 아래 명령어를 실행하여 완료 처리를 하십시오:")
        print()
        if next_gate == "completed":
            print(f"  python vulcan.py session --gate {current_gate} --status done --approved --approval-evidence \"<최종 승인 근거>\"")
        else:
            print(f"  python vulcan.py session --gate {current_gate} --status done --approved --approval-evidence \"<승인 근거>\"")
    else:
        print("진단 결과: ❌ [전환 불가]")
        print("다음 단계로의 전환이 차단되었습니다. 위의 이슈들을 해결하고 다시 시도하십시오.")
    print("==================================================")

    if not overall_pass:
        sys.exit(1)


class DatabaseInspector:
    def get_tables(self) -> list:
        raise NotImplementedError

    def get_columns(self, table_name: str) -> list:
        raise NotImplementedError


class SQLiteInspector(DatabaseInspector):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_tables(self) -> list:
        import sqlite3
        if not os.path.exists(self.db_path):
            return []
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[경고] SQLite 테이블 목록 조회 중 오류: {e}")
            return []
        finally:
            conn.close()

    def get_columns(self, table_name: str) -> list:
        import sqlite3
        if not os.path.exists(self.db_path):
            return []
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            safe_table_name = '"' + table_name.replace('"', '""') + '"'
            cursor.execute(f"PRAGMA table_info({safe_table_name});")
            cols = []
            for row in cursor.fetchall():
                cols.append({
                    "name": row[1],
                    "type": row[2].upper()
                })
            return cols
        except Exception as e:
            print(f"[경고] SQLite 테이블 {table_name} 컬럼 조회 중 오류: {e}")
            return []
        finally:
            conn.close()


def find_sqlite_database_file(project_dir: str) -> str:
    common_candidates = [
        "todo.db",
        "app.db",
        "application.db",
        "database.db",
        os.path.join("backend", "todo.db"),
        os.path.join("backend", "app.db"),
        os.path.join("backend", "application.db"),
        os.path.join("backend", "database.db"),
        os.path.join("data", "todo.db"),
        os.path.join("data", "app.db"),
        os.path.join("data", "database.db"),
    ]
    for rel_path in common_candidates:
        candidate = os.path.join(project_dir, rel_path)
        if os.path.exists(candidate):
            return candidate

    matches = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [
            d for d in dirs
            if d not in {".git", ".vulcan", "node_modules", ".venv", "__pycache__", ".pytest_cache"}
            and not d.startswith(".")
        ]
        for filename in files:
            if filename.lower().endswith((".db", ".sqlite", ".sqlite3")):
                matches.append(os.path.join(root, filename))
    return sorted(matches)[0] if matches else os.path.join(project_dir, "todo.db")


def create_database_inspector(project_dir: str, db_path: str = "", database_url: str = "") -> DatabaseInspector:
    db_url = database_url or os.getenv("DATABASE_URL", "")
    resolved_db_path = db_path or ""
    if resolved_db_path:
        if not os.path.isabs(resolved_db_path):
            resolved_db_path = os.path.join(project_dir, resolved_db_path)
        return SQLiteInspector(resolved_db_path)

    if db_url:
        if db_url.startswith("sqlite:///"):
            resolved_db_path = db_url.replace("sqlite:///", "")
            if not os.path.isabs(resolved_db_path):
                resolved_db_path = os.path.join(project_dir, resolved_db_path)
        elif "://" in db_url:
            pass
        else:
            resolved_db_path = db_url
            if not os.path.isabs(resolved_db_path):
                resolved_db_path = os.path.join(project_dir, resolved_db_path)
    if not resolved_db_path:
        resolved_db_path = find_sqlite_database_file(project_dir)
    return SQLiteInspector(resolved_db_path)


def find_api_spec_file(project_dir="."):
    api_dir = os.path.join(project_dir, "docs", "artifacts", "02-design", "api")
    if os.path.exists(api_dir):
        for f in os.listdir(api_dir):
            if f.endswith(".md") and ("api" in f.lower() or "spec" in f.lower()):
                return os.path.join(api_dir, f)
    fallback_path = os.path.join(project_dir, "docs", "02-design", "api-design.md")
    if os.path.exists(fallback_path):
        return fallback_path
    return None


def parse_api_design(api_spec_path: str) -> list:
    if not os.path.exists(api_spec_path):
        return []
    apis = []
    with open(api_spec_path, encoding="utf-8") as f:
        lines = f.readlines()
    in_api_list_table = False
    for idx, line in enumerate(lines):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                if "API-ID" in parts and "Method" in parts and "Path" in parts:
                    in_api_list_table = True
                    continue
                if in_api_list_table:
                    if parts[1].startswith("---") or parts[1] == "":
                        continue
                    api_id = parts[1]
                    if not re.match(r"^API-\d+$", api_id):
                        in_api_list_table = False
                        continue
                    method = parts[3].upper()
                    path = parts[4]
                    apis.append({
                        "api_id": api_id,
                        "method": method,
                        "path": path,
                        "line_num": idx + 1
                    })
    return apis


def find_db_spec_file(project_dir="."):
    data_dir = os.path.join(project_dir, "docs", "artifacts", "02-design", "data")
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".md") and ("db" in f.lower() or "database" in f.lower() or "spec" in f.lower()):
                return os.path.join(data_dir, f)
    fallback_path = os.path.join(project_dir, "docs", "02-design", "db-design.md")
    if os.path.exists(fallback_path):
        return fallback_path
    return None


def parse_db_design(db_spec_path: str) -> dict:
    if not os.path.exists(db_spec_path):
        return {}
    tables = {}
    with open(db_spec_path, encoding="utf-8") as f:
        content = f.read()
    sections = content.split("\n### DB-")
    for sec in sections[1:]:
        lines = sec.splitlines()
        first_line = "DB-" + lines[0]
        db_id_match = re.match(r"^(DB-\d+)", first_line)
        if not db_id_match:
            continue
        db_id = db_id_match.group(1)
        physical_name = ""
        logical_name = ""
        for line in lines:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    if "물리명" in parts[1]:
                        physical_name = parts[2]
                    elif "논리명" in parts[1]:
                        logical_name = parts[2]
        if not physical_name:
            continue
        columns = []
        in_col_table = False
        idx_phys = -1
        idx_type = -1
        idx_pk = -1
        idx_nn = -1
        for line in lines:
            trimmed_line = line.strip()
            if trimmed_line.startswith("#"):
                in_col_table = False
                continue
            if not trimmed_line.startswith("|"):
                if in_col_table and trimmed_line != "":
                    in_col_table = False
                continue

            parts = [p.strip() for p in trimmed_line.split("|")]
            if len(parts) >= 8:
                if "물리명" in parts and "데이터 타입" in parts:
                    in_col_table = True
                    idx_phys = parts.index("물리명")
                    idx_type = parts.index("데이터 타입")
                    idx_pk = parts.index("PK") if "PK" in parts else -1
                    idx_nn = parts.index("NN") if "NN" in parts else -1
                    continue
                if in_col_table:
                    if parts[1].startswith("---") or parts[1] == "":
                        continue
                    if len(parts) < max(idx_phys, idx_type) + 1:
                        in_col_table = False
                        continue
                    col_phys = parts[idx_phys]
                    if col_phys == "해당없음" or col_phys == "":
                        continue
                    col_type = parts[idx_type].upper()
                    is_pk = False
                    if idx_pk != -1 and idx_pk < len(parts):
                        is_pk = parts[idx_pk] in ("Y", "y", "Yes", "yes", "true", "True")
                    is_nn = False
                    if idx_nn != -1 and idx_nn < len(parts):
                        is_nn = parts[idx_nn] in ("Y", "y", "Yes", "yes", "true", "True")
                    columns.append({
                        "name": col_phys,
                        "type": col_type,
                        "pk": is_pk,
                        "nn": is_nn
                    })
        tables[physical_name] = {
            "db_id": db_id,
            "logical_name": logical_name,
            "columns": columns
        }
    return tables


def scan_codebase_for_traces(project_dir="."):
    trace_map = {}
    exclude_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", ".antigravitycli", ".tmp", "dist", "build"}
    exclude_files = {"traceability.md", "task.md", "walkthrough.md", "implementation_plan.md", "vulcan.py"}
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for file in files:
            if file.lower() in exclude_files or file.startswith("vulcan_"):
                continue
            if not file.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go")):
                continue
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, project_dir)
            try:
                with open(filepath, encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                continue
            for idx, line in enumerate(lines):
                vulcan_matches = re.findall(r"@vulcan\.(trace|test_for)\s+([A-Za-z0-9_\-\s]+)", line)
                for tag_type, ids_str in vulcan_matches:
                    ids = [i.strip() for i in re.split(r"[\s,]+", ids_str) if i.strip()]
                    for trace_id in ids:
                        trace_map.setdefault(trace_id, []).append({
                            "file": rel_path,
                            "line_num": idx + 1,
                            "context": line.strip()
                        })
                decorator_matches = re.findall(r"@(trace|test_for)\(([^)]+)\)", line)
                for dec_type, args_str in decorator_matches:
                    ids = [i.strip().replace('"', '').replace("'", "") for i in args_str.split(",") if i.strip()]
                    for trace_id in ids:
                        trace_map.setdefault(trace_id, []).append({
                            "file": rel_path,
                            "line_num": idx + 1,
                            "context": line.strip()
                        })
                id_matches = TRACE_ID_PATTERN.findall(line)
                for trace_id in id_matches:
                    is_comment_or_doc = False
                    trimmed = line.strip()
                    if "#" in line or "//" in line or "/*" in line or "*" in line or trimmed.startswith(('"', "'")):
                        is_comment_or_doc = True
                    if is_comment_or_doc:
                        already_added = any(item["file"] == rel_path and item["line_num"] == idx + 1 for item in trace_map.get(trace_id, []))
                        if not already_added:
                            trace_map.setdefault(trace_id, []).append({
                                "file": rel_path,
                                "line_num": idx + 1,
                                "context": line.strip()
                            })
    return trace_map


def join_route_paths(prefix: str, path: str) -> str:
    prefix = (prefix or "").strip()
    path = (path or "").strip()
    if not prefix:
        joined = path
    elif not path or path == "/":
        joined = prefix
    else:
        joined = prefix.rstrip("/") + "/" + path.lstrip("/")
    if not joined.startswith("/"):
        joined = "/" + joined
    return joined.rstrip("/") or "/"


def scan_codebase_for_routes(project_dir="."):
    routes = []
    exclude_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache", ".venv"}
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for file in files:
            if file == "vulcan.py" or file.startswith("vulcan_"):
                continue
            if not file.endswith(".py"):
                continue
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, project_dir)
            try:
                with open(filepath, encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                continue
            router_prefixes = {}
            include_router_prefixes = {}
            for line in lines:
                router_match = re.search(
                    r"(\w+)\s*=\s*APIRouter\([^)]*prefix\s*=\s*['\"]([^'\"]*)['\"]",
                    line,
                )
                if router_match:
                    router_prefixes[router_match.group(1)] = router_match.group(2)

                include_match = re.search(
                    r"\.include_router\(\s*([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)?)[^)]*prefix\s*=\s*['\"]([^'\"]*)['\"]",
                    line,
                )
                if include_match:
                    router_name = include_match.group(1).split(".")[-1]
                    include_router_prefixes[router_name] = include_match.group(2)

            for router_name, prefix in include_router_prefixes.items():
                existing = router_prefixes.get(router_name, "")
                router_prefixes[router_name] = join_route_paths(prefix, existing) if existing else prefix

            for idx, line in enumerate(lines):
                route_match = re.search(r"@([A-Za-z0-9_]+)\.(get|post|put|delete|patch|options)\(\s*['\"]([^'\"]*)['\"]", line)
                if route_match:
                    router_name = route_match.group(1)
                    method = route_match.group(2).upper()
                    path = join_route_paths(router_prefixes.get(router_name, ""), route_match.group(3))
                    routes.append({
                        "method": method,
                        "path": path,
                        "file": rel_path,
                        "line_num": idx + 1
                    })
    return routes


def normalize_route_path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path).rstrip("/")


def normalize_sql_type(sql_type: str) -> str:
    sql_type = sql_type.upper().strip()
    if sql_type in ("INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT"):
        return "INTEGER"
    if sql_type in ("VARCHAR", "CHAR", "TEXT", "STRING"):
        return "TEXT"
    if sql_type in ("BOOL", "BOOLEAN"):
        return "BOOLEAN"
    if sql_type in ("REAL", "FLOAT", "DOUBLE", "NUMERIC", "DECIMAL"):
        return "REAL"
    return sql_type


def cmd_drift_report(project_dir=".", output_file="contract-drift-report.md", db_path="", database_url=""):
    print("==================================================")
    print(" [drift-report] 설계-코드 불일치 검사 (Drift Analyzer)")
    print("==================================================")
    session = load_session(project_dir)
    print(f" 프로젝트: {session.get('project', '프로젝트')}")
    print()
    has_drift = False
    report_sections = []
    report_sections.append(f"# Contract Drift Report - {session.get('project', '프로젝트')}\n")
    report_sections.append(f"발생 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_sections.append("본 보고서는 설계 산출물(Traceability Matrix, API 정의서, DB 명세서)과 실제 구현 소스코드/테스트/데이터베이스 물리 스키마 간의 불일치(Drift) 현상을 감지한 리포트입니다.\n")
    report_sections.append("---")

    print("[1] Traceability 매핑 및 코드 내 주석 일치 검사")
    trace_matrix_path = find_artifact_file(
        project_dir,
        os.path.join("docs", "artifacts", "02-traceability"),
        r"traceability.*\.md$",
    ) or find_first_existing(project_dir, [
        os.path.join("docs", "TRACEABILITY.md"),
    ])
    trace_matrix_file = os.path.relpath(trace_matrix_path, project_dir) if trace_matrix_path else None
    trace_drift_issues = []
    if trace_matrix_path and os.path.exists(trace_matrix_path):
        traceability = parse_traceability(project_dir)
        code_traces = scan_codebase_for_traces(project_dir)
        for req_id, info in traceability.items():
            if info.get("status") == "삭제됨" or re.search(r'통합', info.get("status", "")):
                continue
            if req_id not in code_traces:
                trace_drift_issues.append({
                    "type": "Gap (구현 누락)",
                    "id": req_id,
                    "detail": f"추적표({trace_matrix_file}:{info.get('__line_num__')})에 정의되어 있으나, 소스코드/테스트 코드 내 주석태그(@vulcan.trace 등)로 탐지되지 않았습니다."
                })
        for trace_id, occurrences in code_traces.items():
            if not re.match(r"^(REQ|NREQ)-\d+", trace_id):
                continue
            if trace_id not in traceability:
                occ_desc = ", ".join(f"{o['file']}:{o['line_num']}" for o in occurrences[:3])
                if len(occurrences) > 3:
                    occ_desc += f" 외 {len(occurrences)-3}곳"
                trace_drift_issues.append({
                    "type": "Orphan (비계약 구현)",
                    "id": trace_id,
                    "detail": f"코드 내 주석태그로 기재되었으나({occ_desc}), 공식 추적표({trace_matrix_file})에 등록되어 있지 않습니다."
                })
    else:
        trace_drift_issues.append({
            "type": "오류",
            "id": "-",
            "detail": "공식 추적표(TRACEABILITY.md)를 찾을 수 없습니다."
        })
    report_sections.append("\n## 1. Traceability Drift (요구사항 추적 불일치)")
    if trace_drift_issues:
        has_drift = True
        report_sections.append("\n| 구분 | 대상 ID | 상세 내용 |")
        report_sections.append("| --- | --- | --- |")
        for issue in trace_drift_issues:
            report_sections.append(f"| {issue['type']} | `{issue['id']}` | {issue['detail']} |")
        print(f"  -> 결과: ❌ {len(trace_drift_issues)}건의 불일치 감지")
    else:
        report_sections.append("\n✨ **일치**: 추적표와 코드 내 어노테이션/주석 정보가 100% 일치합니다.\n")
        print("  -> 결과: ✨ 0건의 불일치 감지")
    print()

    print("[2] API 정의서와 코드 라우트 일치 검사")
    api_spec_path = find_api_spec_file(project_dir)
    api_drift_issues = []
    if api_spec_path and os.path.exists(api_spec_path):
        designed_apis = parse_api_design(api_spec_path)
        actual_routes = scan_codebase_for_routes(project_dir)
        designed_map = {}
        for api in designed_apis:
            norm_path = normalize_route_path(api["path"])
            key = (api["method"], norm_path)
            designed_map[key] = api
        actual_map = {}
        for route in actual_routes:
            norm_path = normalize_route_path(route["path"])
            key = (route["method"], norm_path)
            actual_map.setdefault(key, []).append(route)
        for key, api in designed_map.items():
            if key not in actual_map:
                api_drift_issues.append({
                    "type": "Missing Endpoint (설계 미구현)",
                    "api_id": api["api_id"],
                    "method": api["method"],
                    "path": api["path"],
                    "detail": f"API 정의서({os.path.relpath(api_spec_path, project_dir)}:{api['line_num']})에 존재하지만, 백엔드 코드에서 구현된 라우터를 찾을 수 없습니다."
                })
        for key, routes in actual_map.items():
            if key not in designed_map:
                for r in routes:
                    api_drift_issues.append({
                        "type": "Orphan Endpoint (비설계 구현)",
                        "api_id": "-",
                        "method": r["method"],
                        "path": r["path"],
                        "detail": f"백엔드 코드({r['file']}:{r['line_num']})에 라우터가 구현되어 있으나, API 정의서 설계 대상 목록에 없습니다."
                    })
    else:
        api_drift_issues.append({
            "type": "오류",
            "api_id": "-",
            "method": "-",
            "path": "-",
            "detail": "API 정의서(DOC-API-G2-001) 파일을 찾을 수 없습니다."
        })
    report_sections.append("\n## 2. API Specification Drift (API 명세 불일치)")
    if api_drift_issues:
        has_drift = True
        report_sections.append("\n| 구분 | API-ID | Method | Path | 상세 내용 |")
        report_sections.append("| --- | --- | --- | --- | --- |")
        for issue in api_drift_issues:
            report_sections.append(f"| {issue['type']} | `{issue['api_id']}` | **{issue['method']}** | `{issue['path']}` | {issue['detail']} |")
        print(f"  -> 결과: ❌ {len(api_drift_issues)}건의 불일치 감지")
    else:
        report_sections.append("\n✨ **일치**: API 정의서의 설계 목록과 소스코드에 구현된 API 라우트가 100% 일치합니다.\n")
        print("  -> 결과: ✨ 0건의 불일치 감지")
    print()

    print("[3] DB 명세서와 물리 데이터베이스 스키마 일치 검사")
    db_spec_path = find_db_spec_file(project_dir)
    db_drift_issues = []
    if db_spec_path and os.path.exists(db_spec_path):
        designed_tables = parse_db_design(db_spec_path)
        inspector = create_database_inspector(project_dir, db_path=db_path, database_url=database_url)
        actual_tables = inspector.get_tables()
        for t_name, info in designed_tables.items():
            if t_name not in actual_tables:
                db_drift_issues.append({
                    "type": "Missing Table",
                    "table": t_name,
                    "column": "-",
                    "detail": f"DB 명세서(`{info['db_id']}`)에 설계되어 있으나, 실제 DB 스키마에 테이블이 존재하지 않습니다."
                })
            else:
                actual_cols = {c["name"]: c for c in inspector.get_columns(t_name)}
                designed_cols = {c["name"]: c for c in info["columns"]}
                for c_name, c_info in designed_cols.items():
                    if c_name not in actual_cols:
                        db_drift_issues.append({
                            "type": "Missing Column",
                            "table": t_name,
                            "column": c_name,
                            "detail": f"테이블 `{t_name}`의 설계 컬럼 `{c_name}`이 실제 DB 테이블에 없습니다."
                        })
                    else:
                        act_type = normalize_sql_type(actual_cols[c_name]["type"])
                        des_type = normalize_sql_type(c_info["type"])
                        if act_type != des_type:
                            db_drift_issues.append({
                                "type": "Type Mismatch",
                                "table": t_name,
                                "column": c_name,
                                "detail": f"컬럼 `{c_name}`의 타입 불일치 (설계: `{des_type}` vs 실제: `{act_type}`)"
                            })
                for c_name in actual_cols:
                    if c_name not in designed_cols:
                        db_drift_issues.append({
                            "type": "Orphan Column",
                            "table": t_name,
                            "column": c_name,
                            "detail": f"실제 DB 테이블 `{t_name}`에 컬럼 `{c_name}`이 존재하지만, DB 명세서 설계 컬럼 목록에 누락되었습니다."
                        })
        for act_t in actual_tables:
            if act_t not in designed_tables:
                db_drift_issues.append({
                    "type": "Orphan Table",
                    "table": act_t,
                    "column": "-",
                    "detail": f"실제 DB 스키마에 `{act_t}` 테이블이 존재하지만, DB 명세서 설계 대상 목록에 누락되었습니다."
                })
    else:
        db_drift_issues.append({
            "type": "오류",
            "table": "-",
            "column": "-",
            "detail": "DB 명세서(DOC-DATA-G2-002) 파일을 찾을 수 없습니다."
        })
    report_sections.append("\n## 3. Database Schema Drift (데이터베이스 스키마 불일치)")
    if db_drift_issues:
        has_drift = True
        report_sections.append("\n| 구분 | 대상 테이블 | 대상 컬럼 | 상세 내용 |")
        report_sections.append("| --- | --- | --- | --- |")
        for issue in db_drift_issues:
            report_sections.append(f"| {issue['type']} | `{issue['table']}` | `{issue['column']}` | {issue['detail']} |")
        print(f"  -> 결과: ❌ {len(db_drift_issues)}건의 불일치 감지")
    else:
        report_sections.append("\n✨ **일치**: DB 명세서의 상세 스펙과 실제 물리 DB 파일의 스키마가 100% 일치합니다.\n")
        print("  -> 결과: ✨ 0건의 불일치 감지")
    print()

    report_content = "\n".join(report_sections) + "\n"
    report_path = os.path.join(project_dir, output_file)
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"불일치 분석 보고서 작성 완료: {output_file}")
    except Exception as e:
        print(f"보고서 파일 작성 실패: {e}")
    print("--------------------------------------------------")
    if has_drift:
        print("진단 결과: ❌ [불일치(Drift) 발견]")
        print(f"설계와 구현 간에 불일치가 감지되었습니다. 상세 내역은 '{output_file}'을 참조하여 조치하십시오.")
        sys.exit(1)
    else:
        print("진단 결과: ✨ [정합성 완벽]")
        print("설계 산출물과 실제 소스코드, 데이터베이스가 완벽히 동기화되어 있습니다.")
    print("==================================================")


def require_gate_start_sequence(session, target_gate):
    """Gate 시작이 현재 Gate 바로 다음 단계인지와 이전 Gate 승인 근거를 확인한다."""
    if target_gate not in GATE_ORDER:
        return

    current_gate = session.get("current_gate", "phase0")
    if current_gate == target_gate:
        return

    if current_gate not in GATE_ORDER:
        print(f"오류: session.json의 current_gate가 유효하지 않습니다: {current_gate}")
        print(f"  사용 가능: {', '.join(GATE_ORDER)}")
        sys.exit(1)

    current_idx = GATE_ORDER.index(current_gate)
    target_idx = GATE_ORDER.index(target_gate)
    if target_idx != current_idx + 1:
        print("오류: Gate는 순차적으로만 시작할 수 있습니다.")
        print(f"  현재 Gate: {current_gate}")
        print(f"  요청 Gate: {target_gate}")
        next_gate = GATE_ORDER[current_idx + 1] if current_idx + 1 < len(GATE_ORDER) else "completed"
        print(f"  다음에 시작 가능한 Gate: {next_gate}")
        sys.exit(1)

    previous_gate = current_gate
    previous_status = session.get("gate_status", {}).get(previous_gate)
    previous_approval = session.get("approvals", {}).get(previous_gate, {})
    approval_evidence = previous_approval.get("approval_evidence")
    if previous_status != "done" or not approval_evidence:
        print("오류: 다음 Gate를 시작하려면 현재 Gate 완료와 사용자 승인 근거가 필요합니다.")
        print(f"  현재 Gate: {previous_gate}")
        print(f"  현재 상태: {previous_status or 'missing'}")
        print("  완료 처리 예:")
        print(f"  python vulcan.py session --gate {previous_gate} --status done --approved --approval-evidence \"<승인 근거>\"")
        sys.exit(1)


def require_current_gate_for_command(project_dir, command_name, allowed_gates):
    session = load_session(project_dir)
    current_gate = session.get("current_gate", "phase0")
    if current_gate not in allowed_gates:
        print(f"오류: {command_name} 명령은 {', '.join(allowed_gates)} 단계에서만 실행할 수 있습니다.")
        print(f"  현재 Gate: {current_gate}")
        sys.exit(1)
    return session


# ── backlog ────────────────────────────────────────────────────────────────

BACKLOG_PATH = "docs/backlog/DOC-PM-OPS-001_Backlog_v0.1.md"
LEGACY_BACKLOG_PATH = "docs/backlog/BACKLOG.md"


def get_backlog_path(project_dir="."):
    path = os.path.join(project_dir, BACKLOG_PATH)
    if os.path.exists(path):
        return path
    legacy_path = os.path.join(project_dir, LEGACY_BACKLOG_PATH)
    if os.path.exists(legacy_path):
        return legacy_path
    return path


def _parse_backlog_items(content):
    """BACKLOG.md Active 섹션의 마크다운 테이블에서 BL-NNN 항목을 파싱한다.

    Returns: list of dict{id, title, type, level, priority, status, req, gate, run, source, note}
    """
    items = []
    in_active = False
    for line in content.splitlines():
        if line.startswith("## Active"):
            in_active = True
            continue
        if in_active and line.startswith("## ") and not line.startswith("## Active"):
            break
        if not in_active:
            continue
        m = re.match(r'^\|\s*(BL-\d{3})\s*\|', line)
        if not m:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 8:
            continue
        if len(cols) >= 11:
            items.append({
                "id": cols[0], "title": cols[1], "type": cols[2],
                "level": cols[3], "priority": cols[4], "status": cols[5],
                "req": cols[6], "gate": cols[7], "run": cols[8],
                "source": cols[9], "note": cols[10],
            })
        else:
            items.append({
                "id": cols[0], "title": cols[1], "type": "-",
                "level": cols[2], "priority": cols[3], "status": cols[4],
                "req": cols[5], "gate": "-", "run": "-",
                "source": cols[6], "note": cols[7],
            })
    return items


def compute_backlog_stats(project_dir="."):
    """BACKLOG.md에서 Active/Done/Rejected 건수와 레벨·우선순위별 카운트를 계산한다."""
    path = get_backlog_path(project_dir)
    if not os.path.exists(path):
        return {
            "active": 0, "done": 0, "rejected": 0,
            "by_type": {"idea": 0, "find": 0, "cr": 0, "issue": 0, "debt": 0},
            "by_level": {"trivial": 0, "small": 0, "major": 0},
            "by_priority": {"p0": 0, "p1": 0, "p2": 0, "p3": 0},
        }

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Active 항목 파싱 (레벨·우선순위 포함)
    active_items = _parse_backlog_items(content)

    # Done / Rejected 건수: BL-NNN 행만 카운트 (헤더·빈행 제외)
    def _count_section(section_header):
        count = 0
        in_section = False
        for line in content.splitlines():
            if line.startswith(f"## {section_header}"):
                in_section = True
                continue
            if in_section and line.startswith("## ") and not line.startswith(f"## {section_header}"):
                break
            if in_section and re.match(r'^\|\s*BL-\d{3}\s*\|', line):
                count += 1
        return count

    level_map = {
        "Trivial": "trivial", "Small": "small", "Major": "major",
        "🟢": "trivial", "🟡": "small", "🔴": "major",
    }
    by_level = {"trivial": 0, "small": 0, "major": 0}
    by_priority = {"p0": 0, "p1": 0, "p2": 0, "p3": 0}
    by_type = {"idea": 0, "find": 0, "cr": 0, "issue": 0, "debt": 0}
    for item in active_items:
        typ = item.get("type", "").lower()
        if typ in by_type:
            by_type[typ] += 1
        lv = level_map.get(item["level"])
        if lv:
            by_level[lv] += 1
        pr = item["priority"].lower()
        if pr in by_priority:
            by_priority[pr] += 1

    return {
        "active":       len(active_items),
        "done":         _count_section("Done"),
        "rejected":     _count_section("Rejected"),
        "by_type":      by_type,
        "by_level":     by_level,
        "by_priority":  by_priority,
    }


def _count_backlog_section(content, section_header):
    count = 0
    in_section = False
    for line in content.splitlines():
        if line.startswith(f"## {section_header}"):
            in_section = True
            continue
        if in_section and line.startswith("## ") and not line.startswith(f"## {section_header}"):
            break
        if in_section and re.match(r"^\|\s*BL-\d{3}\s*\|", line):
            count += 1
    return count


def _refresh_backlog_summary(content):
    stats = {
        "Active": len(_parse_backlog_items(content)),
        "Done": _count_backlog_section(content, "Done"),
        "Rejected": _count_backlog_section(content, "Rejected"),
        "Deferred": _count_backlog_section(content, "Deferred"),
    }
    lines = content.splitlines()
    out = []
    in_stats = False
    wrote = False
    for line in lines:
        if line.startswith("## 통계"):
            in_stats = True
            wrote = True
            out.append(line)
            out.append("")
            for key, value in stats.items():
                out.append(f"- **{key}**: {value}건")
            continue
        if in_stats and line.startswith("## "):
            in_stats = False
            out.append(line)
            continue
        if in_stats:
            continue
        out.append(line)

    if not wrote:
        if out and out[-1].strip():
            out.append("")
        out.extend([
            "## 통계",
            "",
            f"- **Active**: {stats['Active']}건",
            f"- **Done**: {stats['Done']}건",
            f"- **Rejected**: {stats['Rejected']}건",
            f"- **Deferred**: {stats['Deferred']}건",
        ])

    return "\n".join(out) + ("\n" if content.endswith("\n") else "")


def _next_backlog_id(content):
    ids = re.findall(r'\bBL-(\d{3})\b', content)
    next_num = max([int(i) for i in ids], default=0) + 1
    return f"BL-{next_num:03d}"


def cmd_backlog_list(project_dir="."):
    path = get_backlog_path(project_dir)
    if not os.path.exists(path):
        print(f"오류: {BACKLOG_PATH} 없음. 프로젝트가 Vulcan-Anvil Ex 구조인지 확인하세요.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    items = _parse_backlog_items(content)
    if not items:
        print("  백로그 Active 항목이 없습니다.")
        return

    # 우선순위 순 정렬: P0 > P1 > P2 > P3 > 기타
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    items.sort(key=lambda x: order.get(x["priority"], 9))

    print(f"\n  백로그 Active {len(items)}건:\n")
    for it in items:
        item_type = "" if it.get("type") in ("", "-") else f"{it['type']}/"
        print(f"  {it['id']} [{it['priority']}/{item_type}{it['level']}] {it['status']:10s} {it['title']}")
        if it["req"] and it["req"] != "-":
            print(f"         ↳ {it['req']}  ({it['source']})")
        if it.get("gate") and it["gate"] != "-":
            print(f"         ↳ gate: {it['gate']}  run: {it.get('run') or '-'}")
    print()


def cmd_backlog_add(
    title,
    level="",
    priority="P2",
    req="",
    source="",
    note="",
    item_type="IDEA",
    gate="phase0",
    run="",
    project_dir=".",
):
    path = get_backlog_path(project_dir)
    if not os.path.exists(path):
        print(f"오류: {BACKLOG_PATH} 없음.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        content = f.read()

    new_id = _next_backlog_id(content)
    new_row = (
        f"| {new_id} | {title} | {item_type or 'IDEA'} | {level or '-'} | {priority} | Proposed | "
        f"{req or '-'} | {gate or '-'} | {run or '-'} | {source or '-'} | {note or '-'} |"
    )

    # Active 테이블의 placeholder 행이 있으면 대체, 아니면 마지막 BL 행 뒤에 삽입
    lines = content.splitlines()
    out = []
    inserted = False
    in_active = False
    for i, line in enumerate(lines):
        if line.startswith("## Active"):
            in_active = True
            out.append(line)
            continue
        if in_active and line.startswith("## ") and not line.startswith("## Active"):
            if not inserted:
                # Active 섹션이 끝나기 전에 새 행 삽입 (빈 줄 앞)
                # 직전 빈 줄들 건너뛰고 테이블 끝 찾기
                j = len(out) - 1
                while j > 0 and out[j].strip() == "":
                    j -= 1
                out.insert(j + 1, new_row)
                inserted = True
            in_active = False
            out.append(line)
            continue
        if in_active and "(아직 없음)" in line:
            out.append(new_row)
            inserted = True
            continue
        out.append(line)

    if not inserted:
        print("오류: BACKLOG.md Active 섹션을 찾지 못했습니다.")
        sys.exit(1)

    updated = _refresh_backlog_summary("\n".join(out) + ("\n" if content.endswith("\n") else ""))
    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"  추가: {new_id} - {title}")
    print(f"  다음 단계: Triage (레벨/우선순위 결정) 후 상태 → Triaged")


def cmd_backlog_done(bl_id, commit_hash="", project_dir="."):
    """BL 항목을 Done으로 이동시킨다. Active에서 제거 후 Done 섹션에 기록."""
    path = get_backlog_path(project_dir)
    if not os.path.exists(path):
        print(f"오류: {BACKLOG_PATH} 없음.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        content = f.read()

    items = _parse_backlog_items(content)
    target = next((i for i in items if i["id"] == bl_id), None)
    if not target:
        print(f"오류: {bl_id}를 Active 섹션에서 찾지 못했습니다.")
        sys.exit(1)

    done_row = (
        f"| {target['id']} | {target['title']} | {date.today().isoformat()} | "
        f"{commit_hash or '-'} | {target.get('type', '-')} | {target['level']} | "
        f"{target['req']} | {target.get('run', '-')} |"
    )

    lines = content.splitlines()
    out = []
    in_done = False
    removed = False
    done_inserted = False
    for line in lines:
        # Active에서 대상 행 제거
        if not removed and re.match(r'^\|\s*' + re.escape(bl_id) + r'\s*\|', line):
            removed = True
            continue
        if line.startswith("## Done"):
            in_done = True
            out.append(line)
            continue
        if in_done and line.startswith("## ") and not line.startswith("## Done"):
            in_done = False
        if in_done and "(아직 없음)" in line and not done_inserted:
            out.append(done_row)
            done_inserted = True
            continue
        if in_done and re.match(r'^\|\s*\|', line) and not done_inserted:
            pass  # skip accidentally
        out.append(line)

    if in_done and not done_inserted:
        pass

    # 만약 placeholder가 없었다면 Done 섹션 마지막 행 다음에 추가
    if not done_inserted:
        new_out = []
        in_done2 = False
        appended = False
        for line in out:
            if line.startswith("## Done"):
                in_done2 = True
                new_out.append(line)
                continue
            if in_done2 and line.startswith("## ") and not line.startswith("## Done") and not appended:
                # 섹션 종료 직전에 삽입
                j = len(new_out) - 1
                while j > 0 and new_out[j].strip() == "":
                    j -= 1
                new_out.insert(j + 1, done_row)
                appended = True
                in_done2 = False
            new_out.append(line)
        out = new_out
        done_inserted = appended

    updated = _refresh_backlog_summary("\n".join(out) + ("\n" if content.endswith("\n") else ""))
    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"  완료: {bl_id} → Done ({commit_hash or 'commit 미지정'})")


def cmd_backlog_reject(bl_id, reason="", project_dir="."):
    path = get_backlog_path(project_dir)
    if not os.path.exists(path):
        print(f"오류: {BACKLOG_PATH} 없음.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        content = f.read()

    items = _parse_backlog_items(content)
    target = next((i for i in items if i["id"] == bl_id), None)
    if not target:
        print(f"오류: {bl_id}를 Active 섹션에서 찾지 못했습니다.")
        sys.exit(1)

    rej_row = f"| {target['id']} | {target['title']} | {date.today().isoformat()} | {reason or '-'} |"

    lines = content.splitlines()
    out = []
    in_rej = False
    removed = False
    rej_inserted = False
    for line in lines:
        if not removed and re.match(r'^\|\s*' + re.escape(bl_id) + r'\s*\|', line):
            removed = True
            continue
        if line.startswith("## Rejected"):
            in_rej = True
            out.append(line)
            continue
        if in_rej and line.startswith("## ") and not line.startswith("## Rejected"):
            in_rej = False
        if in_rej and "(아직 없음)" in line and not rej_inserted:
            out.append(rej_row)
            rej_inserted = True
            continue
        out.append(line)

    if not rej_inserted:
        # fallback: append before next section
        new_out = []
        in_rej2 = False
        appended = False
        for line in out:
            if line.startswith("## Rejected"):
                in_rej2 = True
                new_out.append(line)
                continue
            if in_rej2 and line.startswith("## ") and not line.startswith("## Rejected") and not appended:
                j = len(new_out) - 1
                while j > 0 and new_out[j].strip() == "":
                    j -= 1
                new_out.insert(j + 1, rej_row)
                appended = True
                in_rej2 = False
            new_out.append(line)
        out = new_out

    updated = _refresh_backlog_summary("\n".join(out) + ("\n" if content.endswith("\n") else ""))
    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"  반려: {bl_id} → Rejected ({reason or '사유 미지정'})")


# ── session ────────────────────────────────────────────────────────────────

def cmd_session(gate, status, feature, approved=False, approval_evidence="", project_dir="."):
    session = load_session(project_dir)

    if gate not in GATE_LABELS:
        print(f"오류: 유효하지 않은 gate - {gate}")
        print(f"  사용 가능: {', '.join(GATE_LABELS.keys())}")
        sys.exit(1)

    if feature:
        session["feature"] = feature

    gate_order = ["phase0", "gate1", "gate2", "gate3", "impl", "gate4", "gate5"]
    next_gate = None
    if status == "done" and not approved:
        print("오류: Gate 완료(done)는 사용자 명시 승인 후에만 기록할 수 있습니다.")
        print("  승인 대기 상태로 멈추려면:")
        print(f"  python vulcan.py session --gate {gate} --status awaiting-approval --feature \"{session.get('feature', feature or '')}\"")
        print("  사용자가 다음 Gate 진행을 명시 승인한 뒤에만:")
        print(f"  python vulcan.py session --gate {gate} --status done --approved --approval-evidence \"<승인 근거>\"")
        sys.exit(1)

    if status == "done":
        current_idx = gate_order.index(gate)
        if current_idx + 1 < len(gate_order):
            next_gate = gate_order[current_idx + 1]
        else:
            next_gate = "completed"
        if next_gate != "completed":
            require_gate_start_prerequisites(project_dir, next_gate)

    session.setdefault("gate_status", {})[gate] = status

    if status == "done":
        session["current_gate"] = next_gate

        entry = f"{GATE_LABELS[gate]} - {session.get('feature', '')}"
        if entry not in session.get("completed", []):
            session.setdefault("completed", []).append(entry)
        session.setdefault("approvals", {})[gate] = {
            "approved_at": datetime.now().isoformat(timespec="seconds"),
            "approval_evidence": approval_evidence or "CLI --approved",
        }
        if gate in session.get("approval_requests", {}):
            session["approval_requests"][gate]["approval_status"] = "approved"
            session["approval_requests"][gate]["approval_evidence"] = approval_evidence or "CLI --approved"
    elif status == "awaiting-approval":
        session["current_gate"] = gate
        session.setdefault("approval_requests", {})[gate] = {
            "requested_at": datetime.now().isoformat(timespec="seconds"),
            "next_gate_candidate": gate_order[gate_order.index(gate) + 1] if gate_order.index(gate) + 1 < len(gate_order) else "completed",
            "approval_status": "pending",
        }

    refresh_session_stats(session, project_dir)
    save_session(session, project_dir)
    print(f"  session.json 업데이트: {gate} → {status}")

    feature_label = session.get("feature", "")
    if status == "awaiting-approval":
        commit_msg = f"session: {gate} awaiting approval - {GATE_LABELS[gate]}"
    elif status == "pending":
        commit_msg = f"session: {gate} pending - {GATE_LABELS[gate]}"
    else:
        commit_msg = f"session: {gate} done - {GATE_LABELS[gate]}"
    if feature_label:
        commit_msg += f" ({feature_label})"
    # 구현(impl), Gate 4(QA리뷰), Gate 5(최종승인): 소스코드 포함 커밋
    include_source = status == "done" and gate in ("impl", "gate4", "gate5")
    committed = git_commit(commit_msg, project_dir, include_source=include_source)
    if committed:
        git_push_if_remote(project_dir)


def cmd_gate_start(gate, feature=None, project_dir="."):
    """현재 진행 Gate를 명시적으로 전환한다.

    Gate 시작은 원격 대시보드/다른 세션이 현재 단계를 알 수 있도록
    session.json만 커밋하고 push한다.
    """
    session = load_session(project_dir)

    if gate not in GATE_LABELS:
        print(f"오류: 유효하지 않은 gate - {gate}")
        print(f"  사용 가능: {', '.join(GATE_LABELS.keys())}")
        sys.exit(1)

    if feature:
        session["feature"] = feature

    require_gate_start_sequence(session, gate)
    require_gate_start_prerequisites(project_dir, gate)

    session["current_gate"] = gate
    session.setdefault("gate_status", {})[gate] = "pending"
    refresh_session_stats(session, project_dir)
    save_session(session, project_dir)
    print(f"  Gate 시작: {gate} - {GATE_LABELS[gate]}")

    feature_label = session.get("feature", "")
    commit_msg = f"session: {gate} start - {GATE_LABELS[gate]}"
    if feature_label:
        commit_msg += f" ({feature_label})"
    committed = git_commit(commit_msg, project_dir, paths=["session.json"])
    if committed:
        git_push_if_remote(project_dir)

    if gate == "impl":
        workflow = workflow_policy(project_dir)
        if workflow.get("branch_mode") not in ("none", "single", "disabled") and workflow.get("impl_uses_integration_branch", True):
            integration_branch = workflow.get("integration_branch") or "dev"
            print(f"  다음 단계: python vulcan.py branch-start impl  # 구현 통합 브랜치 `{integration_branch}` 사용")

    if has_open_run_for_gate(project_dir, gate):
        print(f"  Run 초안 생략: {gate}에 진행 중인 Run이 이미 있습니다.")
        return

    profile = load_delivery_profile(project_dir)
    if profile == "poc":
        print("  PoC profile: Gate별 Orchestrator Plan Run 자동 생성을 생략합니다.")
        print("  다음 단계: docs/poc/ 문서를 갱신하고 필요할 때만 compact Run 또는 worker Run을 생성하세요.")
        return
    if profile == "product":
        print("  Product profile: Gate별 Orchestrator Plan Run 자동 생성을 생략합니다.")
        print("  다음 단계: docs/product/ 문서를 갱신하고 구현/검수 위임이 필요할 때만 Run을 생성하세요.")
        return

    goal = f"{GATE_LABELS[gate]} 시작 계획"
    if feature_label:
        goal = f"{feature_label} - {goal}"
    print(f"  Run 초안 자동 생성: {gate} Orchestrator Plan")
    cmd_orchestrator_plan(goal=goal, gate=gate, related_ids="", project_dir=project_dir)


def sync_session(project_dir="."):
    session = load_session(project_dir)
    refresh_session_stats(session, project_dir)
    save_session(session, project_dir)
    return session


def cmd_sync_session(project_dir="."):
    session = sync_session(project_dir)
    impl = session.get("implementation", {})
    reqs = impl.get("requirements", {})
    waves = impl.get("waves", {})
    print("  session.json 동기화 완료")
    print(f"  요구사항 구현률: {reqs.get('implemented', 0)}/{reqs.get('total', 0)}")
    print(f"  Build Wave: {waves.get('completed', 0)}/{waves.get('total', 0)} 완료")
    if waves.get("current"):
        print(f"  현재 Wave: {waves.get('current')}")


def product_related_ids_for_seeds(project_dir, seeds, base_ids=None):
    ids = list(base_ids or [])
    seed_set = {str(seed).strip().upper() for seed in seeds or [] if str(seed).strip()}
    if not seed_set:
        return ids

    product_docs = [
        "docs/product/PRODUCT_BRIEF.md",
        "docs/product/PRODUCT_CONTRACTS.md",
        "docs/product/PRODUCT_TRACEABILITY.md",
        "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
    ]
    product_rows = []
    for rel_path in product_docs:
        path = os.path.join(project_dir, rel_path)
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        for _headers, rows in parse_markdown_tables(content):
            for row in rows:
                row_text = " ".join(str(value) for key, value in row.items() if not key.startswith("__"))
                row_ids = product_trace_find_ids(row_text)
                if row_ids:
                    product_rows.append(row_ids)

    closure = merge_unique(ids, list(seed_set))
    while True:
        before = set(closure)
        for row_ids in product_rows:
            if before.intersection(row_ids):
                closure = merge_unique(closure, row_ids)
        if set(closure) == before:
            break
    ids = merge_unique(ids, closure)
    return ids


def product_trace_find_ids(value):
    product_id_pattern = re.compile(
        r"\b(?:"
        r"SCN-\d{3}|REQ-\d{3}(?:-\d{2})?|API-\d{3}|DATA-\d{3}|UI-\d{3}(?:-\d{2})?|"
        r"REG-\d{3}|EV-[A-Z0-9-]+|ISSUE-[A-Z0-9-]+|FIND-\d{3}|CR-\d{3}"
        r")\b",
        re.IGNORECASE,
    )
    ids = []
    for match in product_id_pattern.finditer(value or ""):
        if match.start() > 0 and value[match.start() - 1] == "~":
            continue
        if match.end() < len(value) and value[match.end()] == "~":
            continue
        item = match.group(0).upper()
        if item not in ids:
            ids.append(item)
    return ids


def classify_product_target_contracts(ids):
    groups = classify_related_ids(ids)
    product_groups = {
        "scenario": [],
        "req": groups.get("req", []),
        "api": groups.get("api", []),
        "data": [],
        "ui": groups.get("ui", []),
        "regression": [],
        "test": groups.get("test", []),
        "other": [],
    }
    for item in ids or []:
        value = str(item).strip().upper()
        if not value:
            continue
        if value.startswith("SCN-"):
            product_groups["scenario"].append(value)
        elif value.startswith("DATA-"):
            product_groups["data"].append(value)
        elif value.startswith("REG-"):
            product_groups["regression"].append(value)
        elif value.startswith(("REQ-", "API-", "UI-", "UT-", "IT-", "PT-", "TST-")):
            continue
        else:
            product_groups["other"].append(value)
    return {key: merge_unique(values) for key, values in product_groups.items()}


def cmd_wave_start(bw_id, title="", related_ids="", trace_seed="", trace_depth=None, project_dir="."):
    if not re.fullmatch(r"BW-\d{3}", bw_id):
        print(f"오류: BW-ID 형식이 아닙니다: {bw_id}")
        print("  예: BW-001")
        sys.exit(1)

    session = sync_session(project_dir)
    current_gate = session.get("current_gate")
    if current_gate != "impl":
        print(f"오류: Build Wave는 impl 단계에서만 시작할 수 있습니다. 현재 Gate: {current_gate}")
        sys.exit(1)
    workflow_branch_guard(project_dir, "impl", "wave-start")

    impl = session.setdefault("implementation", {})
    waves = impl.setdefault("waves", {})
    current = waves.get("current")
    items = waves.setdefault("items", [])
    if current and current != bw_id:
        current_item = next((item for item in items if item.get("id") == current), {})
        if current_item.get("status") not in WAVE_DONE_STATUSES:
            print(f"오류: 이미 active Build Wave가 있습니다: {current}")
            print("  먼저 wave-complete 또는 sync-session으로 현재 Wave를 정리하세요.")
            sys.exit(1)

    existing = next((item for item in items if item.get("id") == bw_id), None)
    profile = load_delivery_profile(project_dir)
    trace_depth = effective_trace_depth(project_dir, trace_depth)
    trace_info = trace_context_run_enrichment(
        os.path.abspath(project_dir),
        trace_seed=trace_seed,
        related_ids=related_ids,
        depth=trace_depth,
        direction="both",
    )
    ids = trace_info.get("related_ids", split_csv(related_ids))
    if profile == "product":
        ids = product_related_ids_for_seeds(project_dir, trace_info.get("seeds", []), ids)
        trace_info["related_ids"] = ids
        trace_info["target_contracts"] = classify_product_target_contracts(ids)
    run_path = find_wave_run_file(project_dir, bw_id)
    if not run_path:
        run_id = next_run_id(project_dir)
        run_title = title or f"Build Wave {bw_id}"
        rel_path = os.path.join(runs_rel_dir(project_dir), f"{run_id}_build-wave-{bw_id}_{slugify(run_title)}_v0.1.md")
        rel_path_posix = rel_path.replace("\\", "/")
        is_scaffold_wave = bw_id == "BW-000"
        wave_skill = "implementation-scaffold" if is_scaffold_wave else "build-wave"
        skill_path = RUN_SKILLS[wave_skill]
        wave_read_first = [
            "AGENTS.md",
            "session.json",
            rel_path_posix,
            skill_path,
        ]
        wave_working_documents = [
            "docs/artifacts/02-design/development-standard/DOC-DEV-G2-001_Development-Standard_v0.1.md",
            "docs/artifacts/03-test/DOC-QA-G3-001_Test-Cases_v0.1.md",
        ]
        wave_contracts = trace_info.get("target_contracts") or classify_related_ids(ids)
        scaffold_reference_contracts = {}
        if is_scaffold_wave:
            scaffold_reference_contracts = {
                "scr": list(wave_contracts.get("scr", [])),
                "ui": list(wave_contracts.get("ui", [])),
            }
            wave_contracts["ui"] = []
            wave_contracts["test"] = [item for item in wave_contracts.get("test", []) if not str(item).startswith("UI-")]
        wave_reference_documents = ["docs/artifacts/01-requirements/DOC-CORE-G1-001_Requirements-Spec_v0.1.md"]
        if wave_contracts.get("func"):
            wave_reference_documents.append("docs/artifacts/02-design/function/DOC-CORE-G2-001_Function-Spec_v0.1.md")
        if wave_contracts.get("pgm") or wave_contracts.get("func"):
            wave_reference_documents.append("docs/artifacts/02-design/program/DOC-CORE-G2-002_Program-Design_v0.1.md")
        if wave_contracts.get("api"):
            wave_reference_documents.append("docs/artifacts/02-design/api/DOC-API-G2-001_API-Spec_v0.1.md")
        if wave_contracts.get("scr") or wave_contracts.get("ui"):
            wave_reference_documents.append("docs/artifacts/02-design/screen/DOC-CORE-G2-003_Screen-Spec_v0.1.md")
        if wave_contracts.get("db"):
            wave_reference_documents.append("docs/artifacts/02-design/data/DOC-DATA-G2-002_Database-Spec_v0.1.md")
        if wave_contracts.get("sec"):
            wave_reference_documents.append("docs/artifacts/02-design/security/DOC-SEC-G2-001_Security-Guide_v0.1.md")
        if trace_info.get("reference_on_demand"):
            wave_reference_documents = merge_unique(trace_info["reference_on_demand"], wave_reference_documents)
        wave_reference_documents = compact_reference_documents_for_profile(profile, wave_reference_documents)
        orchestrator_reference_documents = [
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
            "docs/core/TRACEABILITY_RULES.md",
            "docs/core/AGENT_RUN_PROTOCOL.md",
            "docs/core/RUN_INPUT_CONTRACT.md",
            "docs/core/RUN_OUTPUT_CONTRACT.md",
        ]
        wave_writable = [
            rel_path_posix,
            "docs/artifacts/04-review/evidence/",
            "TBD: 이 Wave의 코드/테스트 수정 경로를 Orchestrator가 구체화",
        ]
        if profile == "product":
            product_contracts = classify_product_target_contracts(ids)
            product_read_first = [
                "AGENTS.md",
                "session.json",
                rel_path_posix,
                ".agents/skills/vulcan-impl-wave/SKILL.md",
            ]
            product_working_documents = [
                "docs/product/PRODUCT_BRIEF.md",
                "docs/product/PRODUCT_ARCHITECTURE.md",
                "docs/product/PRODUCT_CONTRACTS.md",
                "docs/product/PRODUCT_TRACEABILITY.md",
                "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
            ]
            product_reference_documents = [
                "docs/core/DELIVERY_PROFILES.md",
                "docs/core/TECH_STACK_BASELINES.md",
            ]
            product_writable = [
                rel_path_posix,
                "app/",
                "src/",
                "backend/",
                "frontend/",
                "static/",
                "tests/",
                "requirements.txt",
                "pyproject.toml",
                "package.json",
                "package-lock.json",
                "README.md",
                "docs/product/PRODUCT_TRACEABILITY.md",
                "docs/product/evidence/",
            ]
            content = f"""# {run_id} Build Wave {bw_id} - {run_title}

```yaml
run_id: {run_id}
gate: impl
persona: build
adapter: codex-gpt
skill: {wave_skill}
skill_path: .agents/skills/vulcan-impl-wave/SKILL.md
profile: product
bw_id: {bw_id}
run_type: {"ImplementationScaffold" if is_scaffold_wave else "Implementation"}
status: InProgress
created_at: {date.today()}
related_ids: {format_yaml_list(ids)}
{format_trace_context_metadata(trace_info)}
target_contracts:
{format_yaml_mapping_sequences(product_contracts, 2)}
  interface_contract:
    language: "Product profile stack/runtime is defined in PRODUCT_ARCHITECTURE and PRODUCT_CONTRACTS."
    signatures:
      - "Implement only the scenarios in target_contracts.scenario using the API/UI/DATA contracts listed in target_contracts."
    schemas:
      - "Use PRODUCT_CONTRACTS API/data tables as the public request, response, and persistence shape."
    error_contracts:
      - "Use PRODUCT_CONTRACTS accepted error/validation behavior; if missing, report an open issue instead of inventing a new public contract."
runner_role: worker-runner
source_documents:
  read_first:
{format_yaml_sequence(product_read_first, 4)}
  working_documents:
{format_yaml_sequence(product_working_documents, 4)}
  reference_on_demand:
{format_yaml_sequence(product_reference_documents, 4)}
orchestrator_reference:
  - "docs/core/AGENT_RUN_PROTOCOL.md"
  - "docs/core/RUN_INPUT_CONTRACT.md"
  - "docs/core/RUN_OUTPUT_CONTRACT.md"
scope:
  writable:
{format_yaml_sequence(product_writable, 4)}
  readonly:
    - "docs/core/"
    - "docs/templates/"
    - "docs/product/PRODUCT_BRIEF.md"
    - "docs/product/PRODUCT_ARCHITECTURE.md"
    - "docs/product/PRODUCT_CONTRACTS.md"
    - "docs/product/REGRESSION_AND_RELEASE_REPORT.md"
  excluded:
    - "docs/ref-docs/"
    - "**/*.db"
    - "**/__pycache__/"
    - "**/.ruff_cache/"
    - "**/node_modules/"
    - "**/.next/"
worker_execution_policy:
  forbidden_actions:
    - "Gate 전환을 수행하지 않는다."
    - "session.json의 current_gate, gate_status, completed를 직접 변경하지 않는다."
    - "사용자 승인, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 확정하지 않는다."
    - "scope.writable 밖 파일을 수정하지 않는다."
  required_outputs:
    - "수행한 변경과 검증 결과를 Run 결과에 남긴다."
    - "wave-complete, Gate 전환, session 변경, 최종 승인 판단이 필요하면 Orchestrator 결정 필요 항목으로 반환한다."
  completion_rules:
    - "이 Run의 target_contracts.scenario만 완결한다."
    - "빌드 또는 담당 테스트가 깨진 상태를 완료로 보고하지 않는다."
dependency_install_policy:
  worker_cache_required: true
  npm_cache_env: "npm_config_cache"
  playwright_cache_env: "PLAYWRIGHT_BROWSERS_PATH"
  if_install_blocked: "dependency install이 권한, 인증, 네트워크, registry, cache 문제로 막히면 코드 실패로 단정하지 않고 environment_blocked 또는 not_run으로 보고한다."
development_standards_applied:
  - standard_id: "PRODUCT-LOG-001"
    source: "docs/product/PRODUCT_CONTRACTS.md"
    rule: "사용자 입력, 내부 오류, 저장소 경로, stack trace를 화면이나 공개 응답에 노출하지 않는다."
  - standard_id: "PRODUCT-TEST-001"
    source: "docs/product/REGRESSION_AND_RELEASE_REPORT.md"
    rule: "테스트는 어떤 시나리오와 기대 결과를 검증하는지 사람이 읽을 수 있게 남긴다."
development_standard_checklist:
  logging:
    required: true
    targets:
      - "API handler"
      - "Service or state handler"
    rule: "표준 logger 또는 최소 오류 처리 흐름을 사용하고 민감정보를 로그/화면에 남기지 않는다."
  comments:
    required: true
    targets:
      - "public API handler"
      - "core state mutation function"
    rule: "핵심 책임과 관련 scenario/API/DATA ID를 짧은 주석 또는 docstring으로 남긴다."
  tests:
    required: true
    targets:
      - "scenario smoke"
      - "unit or integration test"
    rule: "테스트 이름이나 설명에 입력값, 기대값, 관련 SCN/REG ID를 남긴다."
verification:
  commands:
    - "python -m compileall app backend src"
    - "python -m pytest"
    - "npm test"
    - "npm run build"
    - "python vulcan.py run-check {rel_path_posix}"
    - "python vulcan.py run-preflight {rel_path_posix}"
  evidence:
    required: true
    target_documents:
      - "docs/product/PRODUCT_TRACEABILITY.md"
      - "docs/product/evidence/"
verification_results: []
evidence: []
delegation_records: []
traceability_updates: []
findings: []
change_requests: []
open_issues: []
```

## 1. Wave 목표

{run_title}

## 2. Product 구현 범위

- 기준 시나리오: {format_yaml_list(product_contracts.get("scenario", []))}
- 관련 요구/계약: {format_yaml_list(ids)}
- Product profile은 audit 산출물 대신 `docs/product/` 문서 세트를 기준으로 구현한다.

## 3. 작업자 입력 계약

- 먼저 `source_documents.read_first`를 읽고 `{bw_id}` 범위와 관련 ID를 확인한다.
- `source_documents.working_documents`의 Product Brief, Architecture, Contracts, Traceability, Regression 문서를 구현 기준으로 삼는다.
- `target_contracts.scenario`, `api`, `data`, `ui`, `regression`에 없는 기능은 추가하지 않는다.
- `target_contracts.interface_contract`는 세부 class 설계가 아니라 Product 계약 경계다. public API/data/UI shape가 충돌하면 임의 변경하지 말고 `open_issues`로 보고한다.
- `scope.writable` 안에서만 코드, 테스트, 자기 Run, Product Trace/evidence를 수정한다.
- 전체 QA Pass, 릴리즈 가능 여부, Gate 전환은 Orchestrator가 판단한다.

## 4. Orchestrator 지시

- 실제 구현은 native worker(subagent/thread/native branch agent)가 수행한다.
- Orchestrator는 worker 결과의 diff/scope를 확인하고, 관련 테스트를 재실행한 뒤 `wave-complete {bw_id}` 여부를 판단한다.
- `agent-run`/`run-exec`는 외부 CLI 실행 증적이나 worktree/watchdog이 필요할 때만 선택한다.

## 5. 검증 계획

- worker는 가능한 self-check만 실행하고, 실패/미실행 명령은 이유를 남긴다.
- Orchestrator는 worker가 작성한 테스트와 가능한 build/smoke를 재실행한다.
- Gate 4의 공식 UI/E2E 증적과 릴리즈 판정은 이 Run 완료 조건이 아니다.

## 6. 결과 기록

### 변경 파일

작성 예정

### 검증 결과

작성 예정

### 위임 기록

작성 예정

### 후속 조치

작성 예정
"""
        elif profile == "poc":
            poc_preset = build_poc_run_input_preset("impl", wave_skill, skill_path, rel_path)
            poc_preset["source_documents"]["reference_on_demand"] = compact_reference_documents_for_profile(
                "poc",
                merge_unique(trace_info.get("reference_on_demand", []), wave_reference_documents, poc_preset["source_documents"].get("reference_on_demand", [])),
            )
            poc_preset["scope"]["writable"] = wave_writable
            input_sections = render_run_input_preset(poc_preset, ids, "build", "impl", trace_info=trace_info)
            content = f"""# {run_id} Build Wave {bw_id} - {run_title}

```yaml
run_id: {run_id}
gate: impl
persona: build
adapter: codex-gpt
skill: {wave_skill}
skill_path: {skill_path}
profile: poc
bw_id: {bw_id}
run_type: {"ImplementationScaffold" if is_scaffold_wave else "Implementation"}
status: InProgress
created_at: {date.today()}
related_ids: {format_yaml_list(ids)}
{format_trace_context_metadata(trace_info)}
verification_results: []
evidence: []
delegation_records: []
traceability_updates: []
findings: []
change_requests: []
open_issues: []
```

## 1. Wave 목표

{run_title}

## 2. PoC 경량화 기준

- 이 Run은 PoC profile compact Run이다.
- 참조 문서는 trace-context 직접 연결과 필수 작업 문서 중심으로 제한한다.
- 자세한 audit 절차 설명은 Run 본문에 반복하지 않고, 필요할 때 Core 문서를 확인한다.

{input_sections}
"""
        else:
            content = f"""# {run_id} Build Wave {bw_id} - {run_title}

```yaml
run_id: {run_id}
gate: impl
persona: build
adapter: codex-gpt
skill: {wave_skill}
skill_path: {skill_path}
bw_id: {bw_id}
run_type: {"ImplementationScaffold" if is_scaffold_wave else "Implementation"}
status: InProgress
created_at: {date.today()}
related_ids: {format_yaml_list(ids)}
{format_trace_context_metadata(trace_info)}
target_contracts:
{format_yaml_mapping_sequences(wave_contracts, 2)}
{"scaffold_reference_contracts:\n  note: \"SCR/UI IDs from trace-context are reference-only for skeleton structure. UI evidence and UI Pass are Gate 4 QA targets.\"\n  scr: " + format_yaml_list(scaffold_reference_contracts.get("scr", [])) + "\n  ui: " + format_yaml_list(scaffold_reference_contracts.get("ui", [])) if is_scaffold_wave else ""}
  interface_contract:
    language: "TBD: Program Design 기준 언어/런타임"
    signatures:
      - "TBD: PGM/IF/MTH public signature를 Program Design에서 복사"
    schemas:
      - "TBD: DTO/Entity/State schema를 Program Design에서 복사"
    error_contracts:
      - "TBD: 오류 코드/예외/사용자 메시지 계약을 Program Design/API/Security에서 복사"
{"  contract_skeleton:\n    mode: \"new\"\n    files:\n      - path: \"TBD: skeleton 파일 경로\"\n        create: \"TBD: 생성/확인할 class/interface/method/DTO\"\n    forbidden:\n      - \"업무 로직 완성\"\n      - \"전체 E2E 또는 Gate 4 QA Pass 선언\"\n    smoke_commands:\n      - \"TBD: compile/import/build smoke 명령\"" if is_scaffold_wave else ""}
development_standards_applied:
{format_development_standards_applied(AUDIT_DEVELOPMENT_STANDARDS_APPLIED, 2)}
development_standard_checklist:
{format_development_standard_checklist(AUDIT_DEVELOPMENT_STANDARD_CHECKLIST, 2)}
runner_role: worker-runner
source_documents:
  read_first:
{format_yaml_sequence(wave_read_first, 4)}
  working_documents:
{format_yaml_sequence(wave_working_documents, 4)}
  reference_on_demand:
{format_yaml_sequence(wave_reference_documents, 4)}
orchestrator_reference:
{format_yaml_sequence(orchestrator_reference_documents, 2)}
scope:
  writable:
{format_yaml_sequence(wave_writable, 4)}
  readonly:
    - "docs/core/"
    - "docs/templates/"
    - "docs/seed-docs/reference-standards/"
  excluded:
    - "docs/ref-docs/"
    - "**/*.db"
    - "**/__pycache__/"
    - "**/.ruff_cache/"
worker_execution_policy:
  forbidden_actions:
    - "Gate 전환을 수행하지 않는다."
    - "session.json의 current_gate, gate_status, completed를 직접 변경하지 않는다."
    - "사용자 승인, QA Pass, 릴리즈 승인, merge 가능 여부를 최종 확정하지 않는다."
    - "scope.writable 밖 파일을 수정하지 않는다."
  required_outputs:
    - "수행한 변경과 검증 결과를 Run 결과에 남긴다."
    - "wave-complete, Gate 전환, session 변경, 최종 승인 판단이 필요하면 Orchestrator 결정 필요 항목으로 반환한다."
  completion_rules:
    - "이 Run의 target_contracts만 완결한다."
    - "빌드 또는 담당 테스트가 깨진 상태를 완료로 보고하지 않는다."
    - "범위가 너무 크면 중간 구현하지 말고 Orchestrator 결정 필요 항목으로 반환한다."
dependency_install_policy:
  worker_cache_required: true
  npm_cache_env: "npm_config_cache"
  playwright_cache_env: "PLAYWRIGHT_BROWSERS_PATH"
  if_install_blocked: "npm install/npm ci/npx playwright install이 권한, 인증, 네트워크, registry, cache 문제로 막히면 코드 실패로 단정하지 않고 environment_blocked 또는 not_run으로 보고한다."
  worker_node_playwright_scope: "worker worktree의 npm/build/Playwright는 보조 self-check이며 최종 UI/Playwright 증적은 workflow.integration_branch 기준 QA-000 workspace 결과를 Gate 4 판정 기준으로 사용한다."
wave_verification_boundary:
  scope:
    - "Gate 3 테스트 설계 중 이 Wave의 target_contracts에 매핑된 UT/IT/UI 또는 smoke 기준만 Wave 검증으로 수행한다."
    - "Wave가 전체 사용자 시나리오를 완성하지 않았다면 전체 E2E, 상태별 화면 증적, QA Pass를 Wave 완료 조건으로 요구하지 않는다."
    - "전체 통합 시나리오와 Playwright 화면 증적 판정은 Gate 4 QA에서 수행한다."
  reporting_rule: "완료 보고는 전체 통합 테스트 완료가 아니라 Wave 범위 계약 테스트와 가능한 회귀 검증 완료로 쓴다."
verification_results: []
evidence: []
delegation_records: []
traceability_updates: []
findings: []
change_requests: []
open_issues: []
```

## 1. Wave 작업지시

{run_title}

## 2. 관련 ID

{format_yaml_list(ids)}

## 3. 작업자 입력 계약

- 먼저 `source_documents.read_first`만 읽고 `{bw_id}` 범위와 관련 ID를 확인한다.
- `target_contracts`의 FUNC/PGM/API/DB/SEC/TEST 묶음이 이 Run의 실제 작업 범위다.
- BW-000 scaffold Run에서 `scaffold_reference_contracts`에 SCR/UI가 있으면 화면 구조 참고용이다. UI-001-* Pass, 상태별 캡처, Playwright 증적은 이번 Run의 직접 완료 조건이 아니라 Gate 4 QA 대상이다.
- `development_standards_applied`와 `development_standard_checklist`는 코드/테스트 작성 체크리스트다. 로깅, 주석/JavaDoc, 테스트 설명을 구현 결과와 자기 Run 보고에 반영한다.
- `source_documents.working_documents`는 이번 Wave의 필수 작업 문서다.
- `source_documents.reference_on_demand`는 설계 충돌, 기준 확인, 세부 판단이 필요할 때만 참고한다.
- `orchestrator_reference`는 worker 입력 계약이 아니다. Orchestrator가 worker 결과 통합, 추적성 반영, Run 입출력 정규화, session/Wave 상태 갱신 판단에 사용한다.
- `scope.writable`에 `TBD`가 남아 있으면 코드 수정 전에 Orchestrator에게 수정 허용 경로를 요청한다.
- 작업 단위는 기능/계약 단위로 완결되어야 하며, 목표 10분 내외/최대 15분 기준은 쪼개기 보조 기준이다.
- 시간이 부족하다는 이유로 빌드/테스트가 깨지는 중간 구현을 완료 처리하지 않는다.
- Node/Playwright 설치가 필요하면 worker cache를 사용하고, 설치가 환경 문제로 막히면 `environment_blocked` 또는 `not_run`으로 기록한다.
- worker worktree에서 화면 서버나 Playwright를 실행하지 못해도 그 사실만으로 구현 실패를 확정하지 않는다.
- Wave 검증은 담당 계약 테스트와 현재까지 가능한 회귀 검증까지만 의미한다. 전체 E2E, 상태별 화면 증적, QA Pass는 Gate 4에서 판정한다.
- 최종 UI/Playwright 증적은 workflow.integration_branch 기준 QA-000 workspace에서 수행한다.

## 4. Orchestrator 지시

- 이 Run은 `{bw_id}` 하나만 수행한다.
- 실제 코드/테스트/UI/API 구현은 native worker(subagent/thread/native branch agent)가 수행한다. `agent-run`/`run-exec`는 외부 CLI 실행 증적이 필요할 때 선택한다. Orchestrator는 작업지시, 통합, 검증, 상태 갱신을 담당한다.
- 다른 Build Wave의 코드 수정은 하지 않는다.
- 한 Wave를 여러 runner에게 나누어 동시에 구현시키지 않는다. backend/frontend처럼 작업지시서가 분리되어야 하면 서로 다른 Build Wave Run으로 나눈다.
- 구현 결과는 Orchestrator가 검토하고 통합한다.
- Orchestrator는 worker 테스트케이스와 해당 Wave 범위의 가능한 회귀 검증을 재실행한다. 전체 시나리오 검증이 불가능한 Wave를 전체 통합 테스트 완료로 보고하지 않는다.
- 작업자 runner는 Gate 전환, session 상태 변경, 최종 승인 판단을 하지 않는다.
- `session.json`의 `current_gate`, `gate_status`, `completed`는 직접 변경하지 않는다.
- 완료 시 테스트와 Run 기록을 갱신하고, 추적표 갱신 필요 항목 및 `wave-complete {bw_id}` 실행 필요 여부를 Orchestrator에게 보고한다.
- 사용자가 worker 사용을 명시하지 않았다는 점은 Orchestrator 직접 구현 사유가 아니다. 구현 진행 승인이 있으면 별도 요청이 없어도 native worker 위임을 기본 절차로 둔다.
- 직접 구현 예외는 worker/subagent/thread 실행 불가, worker 결과 통합 중 충돌 해결에 필요한 최소 수정, 긴급한 1~2줄 연결 수정, 사용자의 명시적 직접 구현 승인에 한해 허용한다.
- Orchestrator가 직접 수정한 예외가 있으면 `orchestrator_direct_edit_reason`, `direct_edit_scope.files`, `direct_edit_scope.estimated_loc`, `direct_edit_scope.contract_changed`, 실행 검증, 후속 검수 필요 여부를 남긴다.
- 직접 구현 예외는 2개 이하 파일, 약 30 LOC 이하, public API/PGM/IF/MTH/DTO/schema/DB/security/SCR/UI contract 변경 없음, 기존 테스트 또는 작은 테스트 보정으로 검증 가능한 경우로 제한한다.

## 5. 수정 범위

| 항목 | 내용 |
| --- | --- |
| 수정 허용 | TBD |
| 읽기 전용 | 요구사항, 설계, 테스트케이스, 개발표준 |
| 제외 | 다른 Wave 범위, 승인되지 않은 리팩터링, `docs/ref-docs/` |

## 6. 검증 계획

TBD

## 7. 결과 기록

### 변경 파일

TBD

### 검증 결과

TBD

### 추적표 갱신

TBD

### 후속 조치

TBD
"""
        write_file(project_dir, rel_path, content)
        run_path = os.path.join(project_dir, rel_path)

    rel_run = os.path.relpath(run_path, project_dir)
    if existing:
        existing["status"] = "In Progress"
        existing["run"] = rel_run
        existing["related_ids"] = sorted(set(existing.get("related_ids", []) + ids))
    else:
        items.append({"id": bw_id, "status": "In Progress", "run": rel_run, "related_ids": ids})

    waves["current"] = bw_id
    refresh_session_stats(session, project_dir)
    session["implementation"].setdefault("waves", {})["current"] = bw_id
    session["stats"]["implementation"] = session["implementation"]
    save_session(session, project_dir)
    print(f"  Build Wave 시작: {bw_id}")
    print(f"  Run 문서: {rel_run}")
    if trace_info.get("seeds"):
        print(f"  trace-context 보강: {format_yaml_list(trace_info['seeds'])} → related_ids {len(ids)}개")
    print_run_preflight_notice(run_path, context="wave-start")


def cmd_wave_complete(bw_id, status="Verified", req_ids="", project_dir="."):
    if not re.fullmatch(r"BW-\d{3}", bw_id):
        print(f"오류: BW-ID 형식이 아닙니다: {bw_id}")
        sys.exit(1)
    if status not in WAVE_KNOWN_STATUSES:
        print(f"오류: 지원하지 않는 Wave 상태입니다: {status}")
        print(f"  사용 가능: {', '.join(sorted(WAVE_KNOWN_STATUSES))}")
        sys.exit(1)

    blockers = wave_completion_blockers(project_dir, bw_id, status)
    if blockers:
        print("오류: Wave 완료 전 Run 이슈 정리가 필요합니다.")
        for blocker in blockers:
            print(f"  - {blocker}")
        sys.exit(1)

    session = sync_session(project_dir)
    impl = session.setdefault("implementation", {})
    waves = impl.setdefault("waves", {})
    items = waves.setdefault("items", [])
    item = next((entry for entry in items if entry.get("id") == bw_id), None)
    if not item:
        item = {"id": bw_id, "status": status, "run": "", "related_ids": []}
        items.append(item)
    item["status"] = status

    completed_reqs = split_csv(req_ids)
    if completed_reqs:
        reqs = impl.setdefault("requirements", {})
        current_ids = set(reqs.get("completed_ids", []))
        current_ids.update(completed_reqs)
        reqs["completed_ids"] = sorted(current_ids)
        item["related_ids"] = sorted(set(item.get("related_ids", []) + completed_reqs))

    if waves.get("current") == bw_id and status in WAVE_DONE_STATUSES:
        waves["current"] = ""

    rel_run = update_wave_run_status(project_dir, bw_id, status)
    if rel_run:
        item["run"] = rel_run

    refresh_session_stats(session, project_dir)
    if waves.get("current") and status not in WAVE_DONE_STATUSES:
        session["implementation"]["waves"]["current"] = waves.get("current")
    session["stats"]["implementation"] = session["implementation"]
    save_session(session, project_dir)

    impl = session.get("implementation", {})
    req_stats = impl.get("requirements", {})
    wave_stats = impl.get("waves", {})
    print(f"  Build Wave 갱신: {bw_id} → {status}")
    print(f"  요구사항 구현률: {req_stats.get('implemented', 0)}/{req_stats.get('total', 0)}")
    print(f"  Build Wave: {wave_stats.get('completed', 0)}/{wave_stats.get('total', 0)} 완료")


# ── export ────────────────────────────────────────────────────────────────

def git_log_timeline(project_dir="."):
    try:
        result = subprocess.run(
            ["git", "log", "--grep=^session:", "--date=short",
             "--pretty=format:%H|%ad|%s", "--", "session.json"],
            cwd=project_dir, capture_output=True, text=True, check=True
        )
        timeline = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            commit, date_str, message = parts
            timeline.append({"commit": commit[:7], "date": date_str, "message": message})
        return list(reversed(timeline))
    except subprocess.CalledProcessError:
        return []


def collect_documents(project_dir="."):
    docs = {"requirements": None, "design": [], "test_plan": None, "review": []}

    req = os.path.join(project_dir, "docs", "01-requirements", "REQUIREMENTS.md")
    if os.path.exists(req):
        docs["requirements"] = "docs/01-requirements/REQUIREMENTS.md"

    design_dir = os.path.join(project_dir, "docs", "02-design")
    if os.path.isdir(design_dir):
        docs["design"] = sorted([
            f"docs/02-design/{f}" for f in os.listdir(design_dir) if f.endswith(".md")
        ])

    tp = os.path.join(project_dir, "docs", "03-test-plan", "Test-Plan.md")
    if os.path.exists(tp):
        docs["test_plan"] = "docs/03-test-plan/Test-Plan.md"

    review_dir = os.path.join(project_dir, "docs", "04-review")
    if os.path.isdir(review_dir):
        docs["review"] = sorted([
            f"docs/04-review/{f}" for f in os.listdir(review_dir) if f.endswith(".md")
        ])

    return docs


def cmd_export(output="snapshot.json", project_dir="."):
    from datetime import datetime
    session = load_session(project_dir)
    workflow = workflow_policy(project_dir)

    snapshot = {
        "schema_version": "1.0",
        "framework": "vulcan-anvil",
        "project": session.get("project", ""),
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "current_gate": session.get("current_gate", "phase0"),
        "gate_status": session.get("gate_status", {}),
        "feature": session.get("feature", ""),
        "started": session.get("started", ""),
        "completed": session.get("completed", []),
        "blocked": session.get("blocked", []),
        "branch": {
            "current": git_current_branch(project_dir),
            "state": session.get("branch_state", {}),
            "workflow": workflow,
        },
        "timeline": git_log_timeline(project_dir),
        "documents": collect_documents(project_dir),
        "stats": session.get("stats"),
    }

    out_path = os.path.join(project_dir, output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"  snapshot 생성: {output}")
    print(f"  프로젝트: {snapshot['project']} | Gate: {snapshot['current_gate']}")


# ── release ───────────────────────────────────────────────────────────────

# dashboard/ 복사 시 제외할 디렉토리/파일 이름 목록 (REQ-008-03, SEC-002-03)
_DASHBOARD_EXCLUDES = {"node_modules", ".next", ".env.local"}


def _copy_tree_filtered(src_dir, dst_dir, excludes):
    """excludes에 포함된 이름을 건너뛰며 디렉토리 트리를 복사합니다.

    Args:
        src_dir: 복사 원본 디렉토리 절대 경로.
        dst_dir: 복사 대상 디렉토리 절대 경로.
        excludes: 건너뛸 파일/디렉토리 이름 집합.
    """
    import shutil
    for root, dirs, files in os.walk(src_dir):
        # 제외 디렉토리는 재귀 탐색에서도 제외 (os.walk in-place 수정)
        dirs[:] = [d for d in dirs if d not in excludes]
        rel_root = os.path.relpath(root, src_dir)
        for f in files:
            if f in excludes:
                continue
            src = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f) if rel_root != "." else f
            dst = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def cmd_release(target):
    """Vulcan-Dev에서 Vulcan-Anvil 경로로 배포 대상 파일을 복사합니다.

    배포 대상: vulcan.py, vulcan_core/, templates/, dashboard/, README.md
    배포 제외: docs/, session.json, .claude/, node_modules/, .env.local, .git/

    Args:
        target: 배포 대상 디렉토리 경로 (절대 또는 상대). (REQ-008-01)
    """
    import shutil

    target_abs = os.path.abspath(target)

    # 자기 자신 덮어쓰기 방지 (REQ-008-01)
    if os.path.abspath(VULCAN_DIR) == target_abs:
        print(f"오류: 대상 경로가 현재 Vulcan-Dev 디렉토리와 동일합니다. 자기 자신 덮어쓰기는 허용되지 않습니다.")
        sys.exit(1)

    # 대상 경로 존재 확인
    if not os.path.isdir(target_abs):
        print(f"오류: 대상 경로가 존재하지 않습니다 — {target_abs}")
        sys.exit(1)

    print(f"\nVulcan-Anvil release")
    print(f"  소스: {VULCAN_DIR}")
    print(f"  대상: {target_abs}\n")

    # vulcan.py 복사
    src_vulcan = os.path.join(VULCAN_DIR, "vulcan.py")
    if os.path.isfile(src_vulcan):
        shutil.copy2(src_vulcan, os.path.join(target_abs, "vulcan.py"))
        print(f"  생성/업데이트: vulcan.py")

    src_core = os.path.join(VULCAN_DIR, "vulcan_core")
    if os.path.isdir(src_core):
        dst_core = os.path.join(target_abs, "vulcan_core")
        _copy_tree_filtered(src_core, dst_core, excludes={"__pycache__"})
        print(f"  생성/업데이트: vulcan_core/")

    # templates/ 복사
    src_templates = os.path.join(VULCAN_DIR, "templates")
    if os.path.isdir(src_templates):
        dst_templates = os.path.join(target_abs, "templates")
        _copy_tree_filtered(src_templates, dst_templates, excludes=set())
        print(f"  생성/업데이트: templates/")

    # dashboard/ 복사 (node_modules/, .next/, .env.local 제외)
    src_dashboard = os.path.join(VULCAN_DIR, "dashboard")
    if os.path.isdir(src_dashboard):
        dst_dashboard = os.path.join(target_abs, "dashboard")
        _copy_tree_filtered(src_dashboard, dst_dashboard, excludes=_DASHBOARD_EXCLUDES)
        print(f"  생성/업데이트: dashboard/")

    # README.md 복사
    src_readme = os.path.join(VULCAN_DIR, "README.md")
    if os.path.isfile(src_readme):
        shutil.copy2(src_readme, os.path.join(target_abs, "README.md"))
        print(f"  생성/업데이트: README.md")

    print(f"\n완료! {target_abs} 에 배포되었습니다.")


# ── upgrade ────────────────────────────────────────────────────────────────

# upgrade 시 타겟에서 삭제할 파일 (이전 버전에서 제거된 파일)
DEPRECATED_FILES = [
    ".claude/skills/gate-transition/skill.md",
    "docs/CHANGE_PROCESS.md",
    "commenting-standards.md",
]

FRAMEWORK_FILES = [
    # CLAUDE.md & settings
    ".claude/CLAUDE.md",
    ".claude/settings.json",
    # agents
    ".claude/agents/discovery.md",
    ".claude/agents/requirements.md",
    ".claude/agents/design.md",
    ".claude/agents/screen-design.md",
    ".claude/agents/security-review.md",
    ".claude/agents/screen-review.md",
    ".claude/agents/ui-review.md",
    ".claude/agents/development-review.md",
    ".claude/agents/test-design.md",
    ".claude/agents/build-planning.md",
    ".claude/agents/build-frontend.md",
    ".claude/agents/build-backend.md",
    ".claude/agents/evidence.md",
    ".claude/agents/review.md",
    # rules
    ".claude/rules/core-principles.md",
    ".claude/rules/gate1-requirements.md",
    ".claude/rules/gate2-design.md",
    ".claude/rules/gate3-testplan.md",
    ".claude/rules/gate4-review.md",
    ".claude/rules/implementation.md",
    ".claude/rules/traceability.md",
    # skills
    ".claude/skills/vulcan/skill.md",
    ".claude/skills/security-baseline/skill.md",
    ".claude/skills/debugging-and-error-recovery/skill.md",
    ".claude/skills/context-engineering/skill.md",
    ".claude/skills/git-workflow-and-versioning/skill.md",
    # docs & guides
    "GATE_GUIDE.md",
    "docs/core/GATE_EXECUTION_CHECKLIST.md",
    # backlog (v1.1+): PROCESS.md는 upgrade 시 덮어쓰기, BACKLOG.md는 보존
    "docs/backlog/PROCESS.md",
]


def read_version_from_vulcan(vulcan_py_path):
    try:
        with open(vulcan_py_path, encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'^VULCAN_VERSION\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        return match.group(1) if match else "unknown"
    except OSError:
        return "unknown"


def extract_variables(project_dir="."):
    """CLAUDE.md에서 프로젝트 변수 추출."""
    claude_path = os.path.join(project_dir, ".claude", "CLAUDE.md")
    if not os.path.exists(claude_path):
        print("오류: .claude/CLAUDE.md를 찾을 수 없습니다.")
        sys.exit(1)

    with open(claude_path, encoding="utf-8") as f:
        content = f.read()

    project = re.search(r'^# (.+?)(?:\s+-|\s+Harness)', content, re.MULTILINE)
    generated = re.search(r'생성일: (.+)', content)

    session = load_session(project_dir)

    return {
        "PROJECT_NAME": project.group(1).strip() if project else session.get("project", "Unknown"),
        "GENERATED_DATE": generated.group(1).strip() if generated else str(date.today()),
    }


def cmd_upgrade(project_dir="."):
    import shutil

    session = load_session(project_dir)
    vulcan_src = session.get("vulcan_src") or VULCAN_DIR
    src_templates = os.path.join(vulcan_src, "templates")

    if not os.path.isdir(src_templates):
        print("오류: Vulcan-Anvil 원본 경로를 찾을 수 없습니다.")
        print(f"  templates 디렉터리가 없습니다: {src_templates}")
        sys.exit(1)

    current_ver = session.get("vulcan_version", "unknown")
    src_vulcan = os.path.join(vulcan_src, "vulcan.py")
    new_ver = read_version_from_vulcan(src_vulcan)

    variables = extract_variables(project_dir)
    print(f"\nVulcan-Anvil upgrade")
    print(f"  프로젝트: {variables['PROJECT_NAME']}")
    print(f"  버전: {current_ver} → {new_ver}")
    print(f"  소스: {vulcan_src}\n")

    for rel_path in FRAMEWORK_FILES:
        tpl_path = os.path.join(src_templates, rel_path)
        if not os.path.exists(tpl_path):
            print(f"  건너뜀 (템플릿 없음): {rel_path}")
            continue
        with open(tpl_path, encoding="utf-8") as f:
            content = render(f.read(), variables)
        dst = os.path.join(project_dir, rel_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  업데이트: {rel_path}")

    for rel_path in DEPRECATED_FILES:
        dst = os.path.join(project_dir, rel_path)
        if os.path.exists(dst):
            os.remove(dst)
            parent = os.path.dirname(dst)
            if os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)
            print(f"  삭제 (deprecated): {rel_path}")

    if os.path.exists(src_vulcan):
        shutil.copy2(src_vulcan, os.path.join(project_dir, "vulcan.py"))
        print(f"  업데이트: vulcan.py")

    src_core = os.path.join(vulcan_src, "vulcan_core")
    if os.path.isdir(src_core):
        dst_core = os.path.join(project_dir, "vulcan_core")
        _copy_tree_filtered(src_core, dst_core, excludes={"__pycache__"})
        print(f"  업데이트: vulcan_core/")

    # v1.1+: Backlog 공식 문서가 없으면 생성하고, legacy BACKLOG.md는 보존한다.
    backlog_dst = os.path.join(project_dir, BACKLOG_PATH)
    if not os.path.exists(backlog_dst):
        legacy_backlog = os.path.join(project_dir, LEGACY_BACKLOG_PATH)
        if os.path.exists(legacy_backlog):
            os.makedirs(os.path.dirname(backlog_dst), exist_ok=True)
            shutil.copy2(legacy_backlog, backlog_dst)
            print(f"  마이그레이션: {LEGACY_BACKLOG_PATH} → {BACKLOG_PATH}")
        else:
            tpl = os.path.join(src_templates, "docs/backlog/BACKLOG.md")
            if os.path.exists(tpl):
                with open(tpl, encoding="utf-8") as f:
                    content = render(f.read(), variables)
                os.makedirs(os.path.dirname(backlog_dst), exist_ok=True)
                with open(backlog_dst, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  생성 (Ex 신규): {BACKLOG_PATH}")

    install_project_doc_framework(project_dir, variables, overwrite=True, source_root=vulcan_src)
    profile = load_delivery_profile(project_dir)
    if profile == "poc":
        install_poc_artifacts(project_dir, variables, overwrite=False, source_root=vulcan_src)
    elif profile == "product":
        install_product_artifacts(project_dir, variables, overwrite=False, source_root=vulcan_src)
    else:
        install_project_artifacts(project_dir, variables, overwrite=False, source_root=vulcan_src)
    ensure_gitignore_entry(project_dir, "docs/ref-docs/")
    for db_ignore in ("*.db", "*.sqlite", "*.sqlite3"):
        ensure_gitignore_entry(project_dir, db_ignore)
    create_vulcan_config(project_dir, profile=profile, primary=load_primary_runner(project_dir))
    if migrate_vulcan_config_models(project_dir):
        print(f"  마이그레이션: vulcan.config.json unsupported Codex model → gpt-5.5")
    if migrate_vulcan_config_qa_workspace_policy(project_dir):
        print(f"  마이그레이션: vulcan.config.json Gate 4 QA 기본 workspace → integration branch")

    session["vulcan_version"] = new_ver
    session["vulcan_src"] = vulcan_src
    save_session(session, project_dir)

    print(f"\n완료! v{current_ver} → v{new_ver}")
    print(f"보존된 파일: ENVIRONMENT.md, session.json, docs/")


# ── version ───────────────────────────────────────────────────────────────

def cmd_version(project_dir="."):
    print(f"Vulcan-Anvil Ex v{VULCAN_VERSION}")
    session_path = os.path.join(project_dir, "session.json")
    if os.path.exists(session_path):
        session = load_session(project_dir)
        project_ver = session.get("vulcan_version", "unknown")
        print(f"  프로젝트: {session.get('project', '-')} (설치 버전: {project_ver})")


# ── init ───────────────────────────────────────────────────────────────────

def cmd_run_new(adapter, gate, skill, title, related_ids, persona=None, trace_seed="", trace_depth=None, project_dir="."):
    if skill not in RUN_SKILLS:
        print(f"오류: 알 수 없는 skill입니다: {skill}")
        print("사용 가능 skill:")
        for name in RUN_SKILLS:
            print(f"  - {name}")
        sys.exit(1)

    persona = persona or default_persona_for_run(gate, skill)
    if persona not in RUN_PERSONAS:
        print(f"오류: 알 수 없는 persona입니다: {persona}")
        print("사용 가능 persona:")
        for name in RUN_PERSONAS:
            print(f"  - {name}")
        sys.exit(1)

    lock = acquire_run_generation_lock(project_dir)
    try:
        run_id = next_run_id(project_dir)
        file_title = title
        if skill == "qa-fix-loop" and "qa-fix-loop" not in slugify(title):
            file_title = f"qa-fix-loop-{title}"
        rel_path = os.path.join(runs_rel_dir(project_dir), f"{run_id}_{slugify(file_title)}_v0.1.md")
        profile = load_delivery_profile(project_dir)
        trace_depth = effective_trace_depth(project_dir, trace_depth)
        trace_info = trace_context_run_enrichment(
            os.path.abspath(project_dir),
            trace_seed=trace_seed,
            related_ids=related_ids,
            depth=trace_depth,
            direction="both",
        )
        ids = trace_info.get("related_ids", split_csv(related_ids))
        skill_path = RUN_SKILLS[skill]
        preset = build_run_input_preset(profile, gate, skill, skill_path, rel_path, adapter=adapter)
        if preset:
            source_docs = preset.setdefault("source_documents", {})
            if is_gemini_long_context_mode(project_dir) and profile != "poc":
                long_context_docs = []
                for root_dir in ["docs/core", "docs/artifacts"]:
                    abs_root = os.path.join(project_dir, root_dir)
                    if os.path.isdir(abs_root):
                        for dirpath, _, filenames in os.walk(abs_root):
                            for filename in filenames:
                                if filename.endswith(".md") or filename.endswith(".dbml"):
                                    full_p = os.path.join(dirpath, filename)
                                    rel_p = os.path.relpath(full_p, project_dir).replace("\\", "/")
                                    long_context_docs.append(rel_p)
                source_docs["reference_on_demand"] = merge_unique(long_context_docs, source_docs.get("reference_on_demand", []))
            elif trace_info.get("reference_on_demand"):
                source_docs["reference_on_demand"] = compact_reference_documents_for_profile(
                    profile,
                    merge_unique(trace_info["reference_on_demand"], source_docs.get("reference_on_demand", [])),
                )
            for source_key in ("read_first", "reference_on_demand", "optional"):
                source_docs[source_key] = filter_adapter_specific_docs(source_docs.get(source_key, []), adapter)
        run_type = preset["run_type"] if preset else RUN_TYPES_BY_GATE.get(gate, "Review")
        completion_section_number = "6" if preset else "5"
        first_read_docs = preset["source_documents"]["read_first"] if preset else [
            "AGENTS.md",
            "session.json",
            "docs/core/TRACEABILITY_RULES.md",
            skill_path,
        ]
        first_read_section = "\n".join(f"- `{path}`" for path in first_read_docs)
        input_sections = render_run_input_preset(preset, ids, persona, gate, trace_info=trace_info) if preset else f"""## 3. 입력 범위

| 항목 | 내용 |
| --- | --- |
| 관련 ID | `{format_yaml_list(ids)}` |
| Trace Context | `{format_yaml_list(trace_info.get("seeds", [])) if trace_info.get("seeds") else "없음"}` |
| Persona | `{persona}` |
| 대상 문서 | 실행 전 Run 작성자가 구체 경로를 기입 |
| 대상 코드 | 실행 전 Run 작성자가 구체 경로를 기입 |
| 제외 범위 | `docs/ref-docs/`, 비밀/토큰/개인정보, 관련 없는 리팩터링 |

## 4. 수행 지시

1. 관련 문서와 코드를 확인한다.
2. `{persona}` persona의 책임과 금지사항을 확인한다.
3. skill 절차에 따라 누락, 결함, 변경 필요 여부를 판단한다.
4. 전역 memory, 과거 세션 요약, 다른 샘플 프로젝트 기억은 현재 Run의 근거로 사용하지 않는다.
5. 필요한 경우 문서, 코드, 테스트, 증적을 갱신한다.
6. 검증 명령을 실행하고 결과를 기록한다.
7. `RUN_OUTPUT_CONTRACT.md` 형식에 맞게 이 Run 기록을 갱신한다."""

        content = f"""# {run_id} {title}

```yaml
run_id: {run_id}
gate: {gate}
persona: {persona}
adapter: {adapter}
skill: {skill}
skill_path: {skill_path}
profile: {profile}
run_type: {run_type}
status: Draft
created_at: {date.today()}
related_ids: {format_yaml_list(ids)}
{format_trace_context_metadata(trace_info)}
verification_results: []
evidence: []
delegation_records: []
traceability_updates: []
findings: []
change_requests: []
open_issues: []
```

## 1. Run 목표

{title}

## 2. 에이전트가 먼저 읽을 문서

{first_read_section}

나머지 기준 문서는 `source_documents.reference_on_demand`에 있을 때만 필요 시 참고한다.

{input_sections}

## {completion_section_number}. 완료 보고

### 요약

Draft 상태. 작업 완료 후 `RUN_OUTPUT_CONTRACT.md`에 맞춰 요약한다.

### 변경 파일

Draft 상태. 작업 완료 후 변경 파일을 기록한다.

### 검증 결과

Draft 상태. 작업 완료 후 실제 실행한 검증 명령과 결과를 기록한다.

### 후속 조치

Draft 상태. 작업 완료 후 후속 조치나 다음 Run 제안을 기록한다.
"""
        write_file(project_dir, rel_path, content)
    finally:
        release_run_generation_lock(lock)
    print(f"\nRun 초안 생성 완료: {rel_path}")
    if trace_info.get("seeds"):
        print(f"  trace-context 보강: {format_yaml_list(trace_info['seeds'])} → related_ids {len(ids)}개")
    version_run_document(rel_path, f"run: create {run_id} - {title}", project_dir)
    if skill == "build-wave":
        print_run_preflight_notice(os.path.join(project_dir, rel_path), context="run-new")
    print(f"다음 단계: 에이전트는 Run 파일과 `{skill_path}`를 기준으로 작업합니다.")


def cmd_orchestrator_plan(goal, gate, related_ids, persona=None, adapter="codex-gpt", project_dir="."):
    persona = persona or GATE_DEFAULT_PERSONAS.get(gate, "review")
    if persona not in RUN_PERSONAS:
        print(f"오류: 알 수 없는 persona입니다: {persona}")
        sys.exit(1)

    primary_runner = load_primary_runner(project_dir)
    agent_guide = "GEMINI.md" if primary_runner == "antigravity-cli" else "AGENTS.md"
    persona_delegation = "docs/adapters/gemini/PERSONA_MAPPING_GEMINI.md" if primary_runner == "antigravity-cli" else "docs/adapters/codex-gpt/PERSONA_DELEGATION.md"

    run_id = next_run_id(project_dir)
    title = f"Orchestrator Plan - {goal}"
    rel_path = os.path.join(runs_rel_dir(project_dir), f"{run_id}_{slugify(title)}_v0.1.md")
    ids = split_csv(related_ids)
    skill = "orchestrator-plan"
    skill_path = RUN_SKILLS[skill]

    content = f"""# {run_id} {title}

```yaml
run_id: {run_id}
gate: {gate}
persona: {persona}
skill: {skill}
skill_path: {skill_path}
status: Draft
created_at: {date.today()}
related_ids: {format_yaml_list(ids)}
verification_results: []
evidence: []
delegation_records: []
traceability_updates: []
findings: []
change_requests: []
open_issues: []
```

## 1. Orchestrator 목표

{goal}

## 2. 먼저 읽을 문서

- `{agent_guide}`
- `docs/core/ORCHESTRATOR_PROTOCOL.md`
- `docs/core/AGENT_PERSONAS.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/CHANGE_CONTROL_PROCESS.md`
- `{persona_delegation}`
- `docs/core/RUN_INPUT_CONTRACT.md`
- `docs/core/RUN_OUTPUT_CONTRACT.md`
- 런타임 memory나 과거 샘플 프로젝트 기억은 현재 프로젝트의 근거로 사용하지 않는다.

## 3. 판단 범위

| 항목 | 내용 |
| --- | --- |
| Gate | `{gate}` |
| 우선 persona | `{persona}` |
| 관련 ID | `{format_yaml_list(ids)}` |
| 목표 산출물 | TBD |
| 제외 범위 | TBD |
| 사용자 승인 필요 항목 | TBD |

## 4. 권장 Run 순서

| 순서 | persona | 목적 | 산출물 | 검증 |
| --- | --- | --- | --- | --- |
| 1 | `{persona}` | 현재 목표와 관련 산출물 확인 | 영향 범위와 누락 항목 | 문서 존재 여부 |
| 2 | TBD | 필요한 구현 또는 문서 수정 | 변경 파일 | 테스트/정적검사 |
| 3 | `review` | 산출물, 추적성, 증적 검수 | FIND/CR/ISSUE 판단 | `vulcan.py run-check` |

## 5. Orchestrator 체크리스트

- [ ] 목표와 관련 ID가 연결되어 있다.
- [ ] 위임할 persona와 직접 수행할 일을 구분했다.
- [ ] 서브에이전트 결과를 최종 사실로 확정하기 전에 Orchestrator가 재검증한다.
- [ ] 구현자가 스스로 최종 검수를 끝내지 않도록 `review` 관점의 검수를 둔다.
- [ ] Gate 4 진입 시 별도 handoff가 도움이 되는지 사용자에게 제안한다.
- [ ] 사용자가 handoff를 수락하지 않으면 현재 작업 환경에서 가능한 검증을 계속한다.
- [ ] `FIND`, `CR`, `ISSUE` 분류 기준을 적용한다.
- [ ] 다음 단계로 넘기기 전에 필요한 사용자 승인을 받는다.

## 6. 완료 보고

### 요약

TBD

### 위임 결과

TBD

### 검증 결과

TBD

### 다음 핸드오프

TBD
"""
    write_file(project_dir, rel_path, content)
    print(f"\nOrchestrator 계획 생성 완료: {rel_path}")
    version_run_document(rel_path, f"run: create {run_id} - orchestrator plan", project_dir)
    print("다음 단계: 계획을 검토한 뒤 필요한 persona Run 또는 handoff를 생성합니다.")


def cmd_handoff(target, title, from_run, gate, related_ids, persona="review", adapter="codex-gpt", project_dir="."):
    if target not in HANDOFF_TARGETS:
        print(f"오류: 알 수 없는 handoff 대상입니다: {target}")
        print("사용 가능 대상:")
        for name in HANDOFF_TARGETS:
            print(f"  - {name}")
        sys.exit(1)
    if persona not in RUN_PERSONAS:
        print(f"오류: 알 수 없는 persona입니다: {persona}")
        sys.exit(1)

    run_id = next_run_id(project_dir)
    full_title = f"Handoff to {target} - {title}"
    rel_path = os.path.join(runs_rel_dir(project_dir), f"{run_id}_{slugify(full_title)}_v0.1.md")
    ids = split_csv(related_ids)
    skill = "handoff"
    skill_path = RUN_SKILLS[skill]
    source_run = from_run or "TBD"

    content = f"""# {run_id} {full_title}

```yaml
run_id: {run_id}
gate: {gate}
persona: {persona}
skill: {skill}
skill_path: {skill_path}
status: Draft
created_at: {date.today()}
handoff_to: {target}
from_run: {source_run}
related_ids: {format_yaml_list(ids)}
verification_results: []
evidence: []
delegation_records: []
traceability_updates: []
findings: []
change_requests: []
open_issues: []
```

## 1. Handoff 목표

{title}

## 2. 이전 맥락

| 항목 | 내용 |
| --- | --- |
| 이전 Run | `{source_run}` |
| 대상 환경 | `{target}` |
| 요청 persona | `{persona}` |
| 관련 ID | `{format_yaml_list(ids)}` |

## 3. 대상 환경 지시

- `desktop`: 구현 결과를 브라우저로 열고 화면, 상호작용, 스크린샷 증적을 확인한다.
- `cli`: 테스트, 린트, `vulcan.py run-check`, `vulcan.py check-trace`처럼 재현 가능한 명령을 우선 실행한다.
- `github`: PR diff, 리뷰 코멘트, CI 결과를 기준으로 코드 변경 위험을 검수한다.
- `codex-review`: GitHub 코드 리뷰 결과를 Vulcan 산출물의 `FIND`, `CR`, `ISSUE` 후보로 변환한다.
- `claude`: `CLAUDE.md`와 Claude agent/skill 구조를 참고하되 Core 규약과 추적성 규칙을 우선한다.
- `manual`: 사람이 확인해야 하는 승인, 정책, 일정, 대외 커뮤니케이션 항목을 정리한다.

## 4. 먼저 읽을 문서

- `AGENTS.md`
- `docs/core/ORCHESTRATOR_PROTOCOL.md`
- `docs/core/AGENT_PERSONAS.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/CHANGE_CONTROL_PROCESS.md`
- `docs/core/RUN_OUTPUT_CONTRACT.md`

## 5. 완료 조건

- [ ] 이전 Run의 결론을 그대로 믿지 않고 대상 환경에서 재검증했다.
- [ ] 검증 명령, 화면 캡처, PR 리뷰, 수동 확인 중 하나 이상의 증적을 남겼다.
- [ ] 발견사항을 `FIND`, `CR`, `ISSUE` 중 하나로 분류했다.
- [ ] 필요한 문서 또는 추적표 갱신 대상을 기록했다.
- [ ] Orchestrator에게 다음 의사결정 항목을 반환했다.

## 6. 완료 보고

### 요약

TBD

### 검증 결과

TBD

### 증적

TBD

### Orchestrator 결정 필요 항목

TBD
"""
    write_file(project_dir, rel_path, content)
    print(f"\nHandoff 문서 생성 완료: {rel_path}")
    version_run_document(rel_path, f"run: create {run_id} - handoff {target}", project_dir)
    print("다음 단계: 대상 환경에서 검증한 뒤 이 Run 파일을 갱신합니다.")


def git_status_porcelain(project_dir="."):
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def execution_rel_dir(project_dir="."):
    return os.path.join(runs_rel_dir(project_dir), "_exec")


def agent_activity_rel_path(project_dir, target_id, runner):
    slug = runner_log_slug(runner)
    return os.path.join(execution_rel_dir(project_dir), f"{target_id}_{slug}-activity.json")


def agent_status_rel_path(project_dir, target_id, runner):
    slug = runner_log_slug(runner)
    return os.path.join(execution_rel_dir(project_dir), f"{target_id}_{slug}-status.json")


def write_agent_activity(project_dir, activity):
    events = activity.get("events")
    if isinstance(events, list) and len(events) > 100:
        activity["events"] = events[-100:]
    rel_path = agent_activity_rel_path(project_dir, activity["target_id"], activity["runner"])
    abs_path = os.path.abspath(os.path.join(project_dir, rel_path))
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        json.dump(activity, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return rel_path


def append_agent_event(activity, phase, message, status=None):
    clean_message = truncate_dashboard_message(message or phase or status or "worker activity")
    event = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "phase": phase or activity.get("phase") or status or "running",
        "message": clean_message,
    }
    if status:
        event["status"] = status
    events = activity.setdefault("events", [])
    if not isinstance(events, list):
        events = []
        activity["events"] = events
    if events and events[-1].get("phase") == event["phase"] and events[-1].get("message") == event["message"]:
        events[-1] = event
    else:
        events.append(event)
    if len(events) > 100:
        activity["events"] = events[-100:]


def write_agent_status(project_dir, status):
    rel_path = status.get("status_file") or agent_status_rel_path(project_dir, status["target_id"], status["runner"])
    status["status_file"] = rel_path.replace("\\", "/")
    status["last_update"] = datetime.now().isoformat(timespec="seconds")
    abs_path = os.path.abspath(os.path.join(project_dir, rel_path))
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return rel_path


def load_latest_agent_activity(project_dir, target_id, runner=None):
    exec_dir = os.path.join(project_dir, execution_rel_dir(project_dir))
    if not os.path.isdir(exec_dir):
        return None, ""
    runner_slug = runner_log_slug(normalize_exec_runner(runner)) if runner else ""
    candidates = []
    for name in os.listdir(exec_dir):
        if not name.startswith(f"{target_id}_") or not name.endswith("-activity.json"):
            continue
        if runner_slug and not name.startswith(f"{target_id}_{runner_slug}-"):
            continue
        path = os.path.join(exec_dir, name)
        candidates.append((os.path.getmtime(path), path))
    if not candidates:
        return None, ""
    _, path = sorted(candidates, reverse=True)[0]
    rel_path = os.path.relpath(path, project_dir)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), rel_path
    except (OSError, json.JSONDecodeError):
        return None, rel_path


def runner_resume_info(runner, stdout):
    normalized = normalize_exec_runner(runner)
    if normalized == "codex-cli":
        for line in (stdout or "").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            thread_id = event.get("thread_id") if event.get("type") == "thread.started" else ""
            if thread_id:
                return {
                    "thread_id": thread_id,
                    "resume_supported": True,
                    "resume_hint": f"codex exec resume {thread_id}",
                }
    if normalized == "claude-cli":
        lines = (stdout or "").splitlines()
        if len(lines) <= 1:
            try:
                payload = json.loads(stdout) if (stdout or "").strip() else {}
            except json.JSONDecodeError:
                payload = {}
            session_id = payload.get("session_id") or payload.get("sessionId") or payload.get("conversation_id")
            if session_id:
                return {
                    "session_id": session_id,
                    "resume_supported": True,
                    "resume_hint": f"claude --resume {session_id}",
                }
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            session_id = event.get("session_id") or event.get("sessionId") or event.get("conversation_id")
            if session_id:
                return {
                    "session_id": session_id,
                    "resume_supported": True,
                    "resume_hint": f"claude --resume {session_id}",
                }
        return {
            "resume_supported": True,
            "resume_hint": "claude --continue",
        }
    return {}


def runner_last_message(runner, stdout):
    normalized = normalize_exec_runner(runner)
    if normalized == "claude-cli":
        last_text = ""
        for line in (stdout or "").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "assistant":
                content = ((event.get("message") or {}).get("content") or [])
                text = "".join(part.get("text", "") for part in content if part.get("type") == "text")
                if text:
                    last_text = text
            elif event.get("type") == "result":
                result_text = event.get("result") or event.get("text") or event.get("message")
                if isinstance(result_text, str) and result_text:
                    last_text = result_text
        if last_text:
            return last_text
    try:
        parsed_stdout = json.loads(stdout) if (stdout or "").strip() else {}
        message = (
            parsed_stdout.get("result")
            or parsed_stdout.get("text")
            or parsed_stdout.get("message")
            or stdout
        )
    except json.JSONDecodeError:
        message = stdout
    return message if isinstance(message, str) else json.dumps(message, ensure_ascii=False, indent=2)


def truncate_dashboard_message(value, limit=220):
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def extract_runner_stream_delta(runner, line):
    normalized = normalize_exec_runner(runner)
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return ""
    if normalized == "codex-cli":
        if event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message":
                return item.get("text") or ""
    if normalized == "claude-cli":
        if event.get("type") == "stream_event":
            stream_event = event.get("event") or {}
            if stream_event.get("type") == "content_block_delta":
                delta = stream_event.get("delta") or {}
                if delta.get("type") == "text_delta":
                    return delta.get("text") or ""
    return ""


def codex_item_label(item_type, status):
    labels = {
        "agent_message": ("응답 작성 중", "응답 작성 완료"),
        "reasoning": ("검토 중", "검토 완료"),
        "function_call": ("도구 호출 중", "도구 호출 완료"),
        "tool_call": ("도구 실행 중", "도구 실행 완료"),
        "command_execution": ("명령 실행 중", "명령 실행 완료"),
        "file_change": ("파일 변경 중", "파일 변경 완료"),
        "patch": ("패치 작성 중", "패치 작성 완료"),
    }
    default = (f"{item_type or 'item'} 처리 중", f"{item_type or 'item'} 처리 완료")
    started, completed = labels.get(item_type or "", default)
    return completed if status == "completed" else started


def extract_runner_status_update(runner, line):
    normalized = normalize_exec_runner(runner)
    if normalized != "codex-cli":
        return {}
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return {}

    event_type = event.get("type") or ""
    if event_type == "thread.started":
        return {
            "phase": "session_started",
            "current_task": "Codex 세션 시작",
        }
    if event_type == "turn.started":
        return {
            "phase": "turn_started",
            "current_task": "Codex 작업 시작",
        }
    if event_type == "turn.completed":
        return {
            "phase": "turn_completed",
            "current_task": "Codex 작업 완료",
        }
    if event_type == "turn.failed":
        return {
            "phase": "turn_failed",
            "current_task": "Codex 작업 실패",
        }
    if event_type in ("item.started", "item.completed"):
        item = event.get("item") or {}
        item_type = item.get("type") or item.get("item_type") or ""
        status = "completed" if event_type.endswith(".completed") else "started"
        task = codex_item_label(item_type, status)
        command = item.get("command") or item.get("cmd")
        name = item.get("name") or item.get("tool_name")
        detail = command or name
        if detail and item_type in ("command_execution", "function_call", "tool_call"):
            task = f"{task}: {truncate_dashboard_message(str(detail), 80)}"
        return {
            "phase": f"codex_{item_type or 'item'}_{status}",
            "current_task": task,
        }
    return {}


def extract_runner_log_update(runner, line):
    normalized = normalize_exec_runner(runner)
    if normalized != "antigravity-cli":
        return {}
    text = (line or "").strip()
    if not text:
        return {}

    update = {}
    model_match = re.search(r'Propagating selected model override.*label="([^"]+)"', text)
    if model_match:
        model_label = model_match.group(1)
        update.update({
            "phase": "model_selected",
            "current_task": f"Gemini 모델 확인: {model_label}",
            "current_message": model_label,
            "model_observed": model_label,
        })
        return update

    conversation_match = re.search(r"(?:Created|Streaming) conversation ([0-9a-fA-F-]{20,})", text)
    if conversation_match:
        conversation_id = conversation_match.group(1)
        streaming = "Streaming conversation" in text
        update.update({
            "conversation_id": conversation_id,
            "resume_supported": True,
            "resume_hint": f"agy.exe --conversation {conversation_id}",
            "phase": "session_streaming" if streaming else "session_started",
            "current_task": "Gemini 응답 스트림 수신 중" if streaming else "Gemini conversation 생성",
        })
        return update

    if "streamGenerateContent" in text:
        trace_match = re.search(r"Trace:\s*(0x[0-9a-fA-F]+)", text)
        trace_suffix = f" ({trace_match.group(1)})" if trace_match else ""
        return {
            "phase": "model_stream",
            "current_task": f"Gemini 모델 응답 생성 중{trace_suffix}",
        }
    if "PlannerResponse without ModifiedResponse" in text:
        return {
            "phase": "planner_response",
            "current_task": "Gemini 응답 후보 정리 중",
        }
    if "checkpoint model generated tool calls" in text:
        return {
            "phase": "tool_call_planned",
            "current_task": "Gemini 도구 호출 생성",
        }
    if "Drip stopped" in text:
        drip_match = re.search(r"charIdx=(\d+),\s*length=(\d+)", text)
        if drip_match:
            current, total = drip_match.groups()
            return {
                "phase": "message_stream",
                "current_task": f"Gemini 응답 출력 완료 ({current}/{total}자)",
                "current_message": f"Gemini 응답 출력 완료 ({current}/{total}자)",
            }
        return {
            "phase": "message_stream",
            "current_task": "Gemini 응답 출력 완료",
        }
    if "Stopping conversation stream" in text:
        return {
            "phase": "stream_stopped",
            "current_task": "Gemini 응답 스트림 종료",
        }
    if "Failed to" in text or "ERROR" in text or "Error" in text:
        return {
            "phase": "runner_warning",
            "current_task": truncate_dashboard_message(text, limit=80),
            "current_message": truncate_dashboard_message(text),
        }
    return {}


def collect_runner_log_updates(runner, log_path):
    updates = {}
    if not log_path or not os.path.exists(log_path):
        return updates
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                update = extract_runner_log_update(runner, line)
                if update:
                    updates.update(update)
    except OSError:
        return updates
    return updates


def antigravity_conversation_id_from_log(log_path):
    if not log_path or not os.path.exists(log_path):
        return ""
    conversation_id = ""
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                match = re.search(r"(?:Created|Streaming) conversation ([0-9a-fA-F-]{20,})", line)
                if match:
                    conversation_id = match.group(1)
    except OSError:
        return ""
    return conversation_id


def antigravity_transcript_log_dir(conversation_id):
    if not conversation_id:
        return ""
    return os.path.join(
        os.path.expanduser("~"),
        ".gemini",
        "antigravity-cli",
        "brain",
        conversation_id,
        ".system_generated",
        "logs",
    )


def antigravity_transcript_paths(conversation_id):
    log_dir = antigravity_transcript_log_dir(conversation_id)
    if not log_dir:
        return []
    return [
        os.path.join(log_dir, "transcript_full.jsonl"),
        os.path.join(log_dir, "transcript.jsonl"),
    ]


def antigravity_transcript_path(conversation_id):
    for path in antigravity_transcript_paths(conversation_id):
        if os.path.exists(path):
            return path
    log_dir = antigravity_transcript_log_dir(conversation_id)
    if not log_dir:
        return ""
    return os.path.join(
        log_dir,
        "transcript.jsonl",
    )


def extract_antigravity_event_text(event):
    if not isinstance(event, dict):
        return ""
    source = str(event.get("source") or "")
    event_type = str(event.get("type") or "")
    if source != "MODEL":
        return ""
    if event_type not in {"PLANNER_RESPONSE", "FINAL_RESPONSE", "MODEL_RESPONSE", "TEXT", "CODE_ACTION"}:
        return ""
    for key in ("content", "text", "message"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def antigravity_transcript_probe(log_path):
    conversation_id = antigravity_conversation_id_from_log(log_path)
    transcript_paths = antigravity_transcript_paths(conversation_id)
    transcript = next((path for path in transcript_paths if os.path.exists(path)), "")
    probe = {
        "conversation_id": conversation_id,
        "transcript_path": transcript,
        "transcript_paths": [path for path in transcript_paths if os.path.exists(path)],
        "transcript_message": "",
        "has_transcript_response": False,
        "has_transcript_model_event": False,
    }
    if not probe["transcript_path"]:
        return probe
    last_message = ""
    has_model_event = False
    try:
        with open(transcript, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("source") == "MODEL":
                    has_model_event = True
                text = extract_antigravity_event_text(event)
                if text:
                    last_message = text
    except OSError:
        return probe
    probe["transcript_message"] = last_message
    probe["has_transcript_response"] = bool(last_message)
    probe["has_transcript_model_event"] = has_model_event
    return probe


def project_display_path(project_dir, path):
    if not path:
        return ""
    project_abs = os.path.abspath(project_dir)
    path_abs = os.path.abspath(path)
    try:
        if os.path.commonpath([project_abs, path_abs]) == project_abs:
            return os.path.relpath(path_abs, project_abs).replace("\\", "/")
    except ValueError:
        pass
    return path_abs


def runner_log_identity_fields(updates):
    return {
        key: value
        for key, value in (updates or {}).items()
        if key not in ("status", "phase", "current_task")
    }


def create_execution_worktree(project_dir, run_id, runner, branch_name=None, worktree_dir=None):
    project_abs = os.path.abspath(project_dir)
    target = os.path.abspath(worktree_dir) if worktree_dir else default_execution_worktree_path(project_abs, run_id, runner)
    branch = branch_name or default_execution_branch(run_id, runner)

    if os.path.exists(target):
        print(f"오류: 실행 worktree 경로가 이미 존재합니다: {target}")
        sys.exit(1)
    os.makedirs(os.path.dirname(target), exist_ok=True)

    try:
        subprocess.run(
            ["git", "worktree", "add", "-b", branch, target, "HEAD"],
            cwd=project_abs,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or str(e)).strip()
        print(f"오류: 실행 worktree 생성 실패 - {detail}")
        sys.exit(1)

    return target, branch


QA_STAGE_PATTERN = re.compile(r"\bQA-(000|001|002|003)\b", re.IGNORECASE)


def qa_stage_from_run(run_content, run_meta=None):
    run_meta = run_meta or {}
    candidates = [
        str(run_meta.get("qa_stage") or ""),
        str(run_meta.get("stage") or ""),
        str(run_meta.get("title") or ""),
        run_content[:5000] if run_content else "",
    ]
    for candidate in candidates:
        match = QA_STAGE_PATTERN.search(candidate)
        if match:
            return f"QA-{match.group(1)}".upper()
    return ""


def is_gate4_qa_execution_run(run_meta, run_content=""):
    if run_meta.get("gate") == "gate4" and run_meta.get("skill") == "qa-execution":
        return True
    return bool(
        re.search(r"(?m)^\s*gate\s*:\s*['\"]?gate4['\"]?\s*$", run_content or "", re.IGNORECASE)
        and re.search(r"(?m)^\s*skill\s*:\s*['\"]?qa-execution['\"]?\s*$", run_content or "", re.IGNORECASE)
    )


def default_qa_worktree_path(project_dir):
    return os.path.abspath(os.path.join(project_dir, ".vulcan", "worktrees", "QA-GATE4"))


def qa_workspace_state(session):
    qa_execution = session.get("qa_execution")
    if not isinstance(qa_execution, dict):
        return {}
    workspace = qa_execution.get("gate4_workspace") or qa_execution.get("gate4_worktree")
    return workspace if isinstance(workspace, dict) else {}


def save_qa_workspace_state(project_dir, *, stage, run_id, worktree_path, branch="", status="active"):
    session = load_session(project_dir)
    qa_execution = session.setdefault("qa_execution", {})
    if not isinstance(qa_execution, dict):
        qa_execution = {}
        session["qa_execution"] = qa_execution

    existing = qa_workspace_state(session)
    now = datetime.now().isoformat(timespec="seconds")
    base_commit = git_text(["rev-parse", "HEAD"], worktree_path) or git_text(["rev-parse", "HEAD"], project_dir)
    workspace_abs = os.path.abspath(worktree_path)
    mode = "integration-workspace" if os.path.normcase(workspace_abs) == os.path.normcase(os.path.abspath(project_dir)) else "qa-worktree"
    qa_execution["gate4_workspace"] = {
        "path": workspace_abs,
        "mode": mode,
        "branch": branch or existing.get("branch") or git_current_branch(worktree_path),
        "base_commit": existing.get("base_commit") or base_commit,
        "created_by_run": existing.get("created_by_run") or run_id,
        "created_at": existing.get("created_at") or now,
        "last_stage": stage,
        "last_run": run_id,
        "updated_at": now,
        "status": status,
    }
    refresh_session_stats(session, project_dir)
    save_session(session, project_dir)


def resolve_gate4_qa_workspace(project_dir, *, run_id, run_meta, run_content, create_worktree, worktree_dir):
    if not is_gate4_qa_execution_run(run_meta, run_content):
        return "", "", ""

    stage = qa_stage_from_run(run_content, run_meta)
    if not stage:
        return "", "", ""
    if stage == "QA-000":
        return stage, "", ""

    session = load_session(project_dir)
    state = qa_workspace_state(session)
    qa_path = state.get("path") or ""
    qa_status = state.get("status") or ""
    if not qa_path or not os.path.isdir(qa_path):
        print(f"오류: {stage}는 QA-000에서 만든 QA workspace를 재사용해야 합니다.")
        print("  먼저 QA-000 qa-execution Run을 실행해 qa_execution.gate4_workspace.path를 기록하세요.")
        sys.exit(1)
    if qa_status in ("blocked", "failed", "missing", "environment_blocked"):
        print(f"오류: QA-000 workspace 상태가 {qa_status}입니다. 후속 QA Run을 진행할 수 없습니다.")
        print(f"  QA workspace: {qa_path}")
        for line in qa_workspace_blocked_followup_lines(stage, qa_status, qa_path)[1:]:
            print(f"  {line}")
        sys.exit(1)
    if worktree_dir and os.path.abspath(worktree_dir) != os.path.abspath(qa_path):
        print(f"오류: {stage}는 QA-000 workspace를 재사용해야 합니다.")
        print(f"  QA-000 workspace: {qa_path}")
        print(f"  요청 worktree-dir: {os.path.abspath(worktree_dir)}")
        sys.exit(1)
    return stage, os.path.abspath(qa_path), state.get("branch") or ""


def sync_run_file_to_execution_workspace(run_abs, exec_run_abs, exec_dir, run_rel_path):
    if os.path.exists(exec_run_abs):
        changed = subprocess.run(
            ["git", "status", "--porcelain", "--", run_rel_path],
            cwd=exec_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        has_local_change = bool((changed.stdout or "").strip()) if changed.returncode == 0 else True
        if not has_local_change and file_sha256(run_abs) != file_sha256(exec_run_abs):
            shutil.copy2(run_abs, exec_run_abs)
            print(f"  QA workspace Run 문서 갱신: {run_rel_path}")
        elif has_local_change and file_sha256(run_abs) != file_sha256(exec_run_abs):
            print(f"  경고: QA workspace의 Run 문서에 로컬 변경이 있어 덮어쓰지 않았습니다: {run_rel_path}")
        return

    os.makedirs(os.path.dirname(exec_run_abs), exist_ok=True)
    shutil.copy2(run_abs, exec_run_abs)
    print(f"  QA workspace Run 문서 동기화: {run_rel_path}")


def coerce_process_output(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def command_output_or_empty(cmd, cwd, timeout=10):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return (result.stdout or "") + (result.stderr or "")
    except (OSError, subprocess.TimeoutExpired):
        return ""


def file_hash_or_empty(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return ""


def load_status_probe(path):
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def git_progress_fingerprint(cwd):
    status_text = command_output_or_empty(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain", "-uall"],
        cwd,
        timeout=10,
    )
    diff_text = command_output_or_empty(
        ["git", "-c", "core.quotePath=false", "diff", "--no-ext-diff", "--binary"],
        cwd,
        timeout=20,
    )
    cached_text = command_output_or_empty(
        ["git", "-c", "core.quotePath=false", "diff", "--cached", "--no-ext-diff", "--binary"],
        cwd,
        timeout=20,
    )
    combined = "\n".join([status_text, diff_text, cached_text])
    return {
        "hash": hashlib.sha256(combined.encode("utf-8", errors="replace")).hexdigest(),
        "changed_file_count": len(parse_git_status_files(status_text)),
    }


def capture_worker_progress_snapshot(cwd, project_dir, status_rel, stdout_len, stderr_len, log_path=None):
    status_abs = os.path.abspath(os.path.join(project_dir, status_rel)) if status_rel else ""
    status_data = load_status_probe(status_abs)
    status_is_heartbeat = bool(status_data.get("heartbeat"))
    status_is_watchdog_probe = bool(status_data.get("watchdog_probe"))
    status_signal = ""
    if status_data and status_is_watchdog_probe:
        status_signal = str(status_data.get("observed_status_signal") or "")
    elif status_data and not status_is_heartbeat:
        status_signal = "|".join([
            str(status_data.get("status") or ""),
            str(status_data.get("phase") or ""),
            str(status_data.get("current_task") or status_data.get("current_message") or ""),
        ])
    git_probe = git_progress_fingerprint(cwd)
    log_size = 0
    if log_path:
        try:
            log_size = os.path.getsize(log_path)
        except OSError:
            log_size = 0
    return {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "status_hash": file_hash_or_empty(status_abs) if status_data and not status_is_heartbeat and not status_is_watchdog_probe else "",
        "status_signal": status_signal,
        "status_phase": str(status_data.get("phase") or ""),
        "status_task": str(status_data.get("current_task") or status_data.get("current_message") or ""),
        "status_is_heartbeat": status_is_heartbeat,
        "status_is_watchdog_probe": status_is_watchdog_probe,
        "git_hash": git_probe["hash"],
        "changed_file_count": git_probe["changed_file_count"],
        "stdout_len": stdout_len,
        "stderr_len": stderr_len,
        "log_size": log_size,
    }


def build_timeout_policy_payload(
    soft_timeout_seconds,
    hard_timeout_seconds=None,
    extension_seconds=0,
    max_extensions=0,
    progress_probe_seconds=0,
    no_progress_timeout_seconds=0,
    min_runtime_seconds=0,
    started_at="",
    watchdog_state=None,
):
    watchdog_enabled = int(progress_probe_seconds or 0) > 0 and int(no_progress_timeout_seconds or 0) > 0
    return {
        "soft_timeout_seconds": int(soft_timeout_seconds or 0),
        "hard_timeout_seconds": int(hard_timeout_seconds or soft_timeout_seconds or 0),
        "extension_seconds": int(extension_seconds or 0),
        "max_extensions": int(max_extensions or 0),
        "extensions_used": 0,
        "extension_events": [],
        "watchdog_enabled": watchdog_enabled,
        "progress_probe_seconds": int(progress_probe_seconds or 0),
        "no_progress_timeout_seconds": int(no_progress_timeout_seconds or 0),
        "min_runtime_seconds": int(min_runtime_seconds or 0),
        "watchdog_state": watchdog_state if watchdog_state is not None else ("running" if watchdog_enabled else ""),
        "last_probe_at": "",
        "last_progress_at": started_at,
        "last_progress_age_seconds": 0,
        "last_progress_reasons": [],
        "quiet_probe_count": 0,
        "timeout_reason": "",
    }


def worker_progress_reasons(before, after):
    reasons = []
    if not before:
        return reasons
    if after.get("status_signal") and after.get("status_signal") != before.get("status_signal"):
        reasons.append("worker status changed")
    if after.get("git_hash") and after.get("git_hash") != before.get("git_hash"):
        reasons.append("worktree diff changed")
    if int(after.get("changed_file_count") or 0) > int(before.get("changed_file_count") or 0):
        reasons.append("changed file count increased")
    log_grew = (
        int(after.get("stdout_len") or 0) > int(before.get("stdout_len") or 0)
        or int(after.get("stderr_len") or 0) > int(before.get("stderr_len") or 0)
        or int(after.get("log_size") or 0) > int(before.get("log_size") or 0)
    )
    active_phase = re.search(
        r"edit|test|build|writing|running|실행|수정|작성|검증|테스트|빌드",
        str(after.get("status_phase") or "") + " " + str(after.get("status_task") or ""),
        re.IGNORECASE,
    )
    if log_grew and (active_phase or reasons):
        reasons.append("runner output/log advanced")
    return reasons


def terminate_process_tree(process, force=True):
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        try:
            cmd = ["taskkill", "/PID", str(process.pid), "/T"]
            if force:
                cmd.append("/F")
            subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
            )
            return
        except OSError:
            pass
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL if force else signal.SIGTERM)
            return
        except OSError:
            pass
    try:
        process.kill() if force else process.terminate()
    except OSError:
        pass


def run_command_with_status_heartbeat(
    cmd,
    cwd,
    timeout_seconds,
    project_dir,
    status_payload,
    current_task,
    heartbeat_seconds=30,
    hard_timeout_seconds=None,
    extension_seconds=0,
    max_extensions=0,
    progress_grace_seconds=300,
    progress_probe_seconds=0,
    no_progress_timeout_seconds=0,
    min_runtime_seconds=120,
    on_stdout_line=None,
    tail_file_path=None,
    on_tail_line=None,
    env=None,
):
    stop_event = threading.Event()
    popen_kwargs = {}
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        popen_kwargs["start_new_session"] = True
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        **popen_kwargs,
    )
    soft_timeout_seconds = max(1, int(timeout_seconds or 1))
    hard_timeout_seconds = int(hard_timeout_seconds or soft_timeout_seconds)
    if hard_timeout_seconds < soft_timeout_seconds:
        hard_timeout_seconds = soft_timeout_seconds
    extension_seconds = max(0, int(extension_seconds or 0))
    max_extensions = max(0, int(max_extensions or 0))
    progress_grace_seconds = max(1, int(progress_grace_seconds or 1))
    progress_probe_seconds = max(0, int(progress_probe_seconds or 0))
    no_progress_timeout_seconds = max(0, int(no_progress_timeout_seconds or 0))
    min_runtime_seconds = max(0, int(min_runtime_seconds or 0))
    watchdog_enabled = progress_probe_seconds > 0 and no_progress_timeout_seconds > 0
    timeout_policy = build_timeout_policy_payload(
        soft_timeout_seconds,
        hard_timeout_seconds=hard_timeout_seconds,
        extension_seconds=extension_seconds,
        max_extensions=max_extensions,
        progress_probe_seconds=progress_probe_seconds,
        no_progress_timeout_seconds=no_progress_timeout_seconds,
        min_runtime_seconds=min_runtime_seconds,
        started_at=datetime.now().isoformat(timespec="seconds"),
    )
    pid_payload = dict(status_payload)
    pid_payload.update({
        "status": "running",
        "phase": pid_payload.get("phase") or "process_started",
        "current_task": current_task,
        "pid": process.pid,
        "soft_timeout_seconds": soft_timeout_seconds,
        "hard_timeout_seconds": hard_timeout_seconds,
        "extension_seconds": extension_seconds,
        "max_extensions": max_extensions,
        "watchdog_enabled": watchdog_enabled,
        "progress_probe_seconds": progress_probe_seconds,
        "no_progress_timeout_seconds": no_progress_timeout_seconds,
        "min_runtime_seconds": min_runtime_seconds,
        "timeout_policy": timeout_policy,
    })
    write_agent_status(project_dir, pid_payload)

    def heartbeat():
        while not stop_event.wait(heartbeat_seconds):
            if process.poll() is not None:
                break

            status_rel = status_payload.get("status_file", "")
            status_abs = os.path.abspath(os.path.join(project_dir, status_rel)) if status_rel else ""
            if status_abs and os.path.exists(status_abs):
                age_seconds = time.time() - os.path.getmtime(status_abs)
                if age_seconds < max(5, heartbeat_seconds - 3):
                    continue

            payload = dict(status_payload)
            payload.update({
                "status": "running",
                "phase": payload.get("phase") or "runner_waiting",
                "current_task": current_task,
                "heartbeat": True,
                "pid": process.pid,
                "timeout_policy": timeout_policy,
            })
            write_agent_status(project_dir, payload)

    stdout_chunks = []
    stderr_chunks = []

    def read_stream(stream, chunks, callback=None):
        if stream is None:
            return
        for line in stream:
            chunks.append(line)
            if callback:
                try:
                    callback(line)
                except Exception:
                    pass

    def tail_file():
        if not tail_file_path or not on_tail_line:
            return
        position = 0
        while not stop_event.wait(1):
            try:
                if not os.path.exists(tail_file_path):
                    continue
                size = os.path.getsize(tail_file_path)
                if size < position:
                    position = 0
                with open(tail_file_path, encoding="utf-8", errors="replace") as f:
                    f.seek(position)
                    lines = f.readlines()
                    position = f.tell()
                for line in lines:
                    on_tail_line(line)
            except Exception:
                continue

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.stdout, stdout_chunks, on_stdout_line),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.stderr, stderr_chunks, None),
        daemon=True,
    )
    tail_thread = threading.Thread(target=tail_file, daemon=True)
    heartbeat_thread.start()
    stdout_thread.start()
    stderr_thread.start()
    tail_thread.start()
    timed_out = False
    timeout_reason = ""
    extension_events = []
    extensions_used = 0
    watchdog_events = []
    watchdog_state = "running"
    quiet_probe_count = 0
    last_probe_at = ""
    last_progress_at = datetime.now().isoformat(timespec="seconds")
    last_progress_reasons = []
    started_monotonic = time.monotonic()
    soft_deadline = started_monotonic + soft_timeout_seconds
    hard_deadline = started_monotonic + hard_timeout_seconds
    next_probe = started_monotonic + (progress_probe_seconds or soft_timeout_seconds)
    last_progress_monotonic = started_monotonic
    status_rel = status_payload.get("status_file", "")
    last_snapshot = capture_worker_progress_snapshot(
        cwd,
        project_dir,
        status_rel,
        stdout_len=0,
        stderr_len=0,
        log_path=tail_file_path,
    )
    try:
        while True:
            if watchdog_enabled:
                now_monotonic = time.monotonic()
                remaining = min(next_probe, hard_deadline) - now_monotonic
                if remaining > 0:
                    try:
                        process.wait(timeout=min(remaining, 5))
                    except subprocess.TimeoutExpired:
                        pass
                    if process.poll() is not None:
                        watchdog_state = "completed"
                        break
                    continue

                now_monotonic = time.monotonic()
                if now_monotonic >= hard_deadline:
                    timed_out = True
                    timeout_reason = "hard_timeout"
                    watchdog_state = "timeout_hard"
                    break

                current_snapshot = capture_worker_progress_snapshot(
                    cwd,
                    project_dir,
                    status_rel,
                    stdout_len=sum(len(chunk) for chunk in stdout_chunks),
                    stderr_len=sum(len(chunk) for chunk in stderr_chunks),
                    log_path=tail_file_path,
                )
                reasons = worker_progress_reasons(last_snapshot, current_snapshot)
                last_probe_at = current_snapshot["captured_at"]
                runtime_seconds = int(now_monotonic - started_monotonic)
                no_progress_age = int(now_monotonic - last_progress_monotonic)

                if reasons:
                    watchdog_state = "active"
                    quiet_probe_count = 0
                    last_progress_monotonic = now_monotonic
                    last_progress_at = current_snapshot["captured_at"]
                    last_progress_reasons = reasons
                    last_snapshot = current_snapshot
                else:
                    quiet_probe_count += 1
                    watchdog_state = "quiet"

                event = {
                    "probe_at": current_snapshot["captured_at"],
                    "state": watchdog_state,
                    "reasons": reasons,
                    "quiet_probe_count": quiet_probe_count,
                    "last_progress_age_seconds": int(now_monotonic - last_progress_monotonic),
                    "changed_file_count": current_snapshot.get("changed_file_count", 0),
                }
                watchdog_events.append(event)
                if len(watchdog_events) > 20:
                    watchdog_events = watchdog_events[-20:]

                status_abs = os.path.abspath(os.path.join(project_dir, status_rel)) if status_rel else ""
                status_age = None
                if status_abs and os.path.exists(status_abs):
                    try:
                        status_age = time.time() - os.path.getmtime(status_abs)
                    except OSError:
                        status_age = None
                stall_candidate = (
                    runtime_seconds >= min_runtime_seconds
                    and now_monotonic - last_progress_monotonic >= no_progress_timeout_seconds
                )
                timeout_policy.update({
                    "extensions_used": extensions_used,
                    "extension_events": extension_events,
                    "watchdog_state": watchdog_state,
                    "last_probe_at": last_probe_at,
                    "last_progress_at": last_progress_at,
                    "last_progress_age_seconds": int(now_monotonic - last_progress_monotonic),
                    "last_progress_reasons": last_progress_reasons,
                    "quiet_probe_count": quiet_probe_count,
                    "timeout_reason": timeout_reason,
                })
                write_watchdog_status = True
                if write_watchdog_status:
                    if watchdog_state == "active":
                        watchdog_task = "watchdog active; progress detected"
                    elif watchdog_state == "quiet":
                        watchdog_task = f"worker quiet for {no_progress_age}s"
                    else:
                        watchdog_task = f"watchdog {watchdog_state}"
                    payload = dict(status_payload)
                    payload.update({
                        "status": "running",
                        "phase": f"watchdog_{watchdog_state}",
                        "current_task": watchdog_task,
                        "watchdog_probe": True,
                        "observed_status_signal": current_snapshot.get("status_signal") or last_snapshot.get("status_signal") or "",
                        "pid": process.pid,
                        "watchdog": {
                            "enabled": True,
                            "state": watchdog_state,
                            "last_probe_at": last_probe_at,
                            "last_progress_at": last_progress_at,
                            "last_progress_age_seconds": int(now_monotonic - last_progress_monotonic),
                            "last_progress_reasons": last_progress_reasons,
                            "quiet_probe_count": quiet_probe_count,
                            "progress_probe_seconds": progress_probe_seconds,
                            "no_progress_timeout_seconds": no_progress_timeout_seconds,
                            "min_runtime_seconds": min_runtime_seconds,
                        },
                        "hard_timeout_seconds": hard_timeout_seconds,
                        "timeout_policy": dict(timeout_policy),
                    })
                    write_agent_status(project_dir, payload)
                last_snapshot = current_snapshot

                if stall_candidate:
                    timed_out = True
                    timeout_reason = "no_progress_timeout"
                    watchdog_state = "stalled"
                    break

                next_probe = now_monotonic + progress_probe_seconds
                continue

            remaining = min(soft_deadline, hard_deadline) - time.monotonic()
            if remaining > 0:
                try:
                    process.wait(timeout=min(remaining, 5))
                except subprocess.TimeoutExpired:
                    pass
                if process.poll() is not None:
                    break
                continue

            now_monotonic = time.monotonic()
            if now_monotonic >= hard_deadline:
                timed_out = True
                timeout_reason = "hard_timeout"
                break

            current_snapshot = capture_worker_progress_snapshot(
                cwd,
                project_dir,
                status_rel,
                stdout_len=sum(len(chunk) for chunk in stdout_chunks),
                stderr_len=sum(len(chunk) for chunk in stderr_chunks),
                log_path=tail_file_path,
            )
            reasons = worker_progress_reasons(last_snapshot, current_snapshot)
            within_grace = (
                datetime.fromisoformat(current_snapshot["captured_at"]) - datetime.fromisoformat(last_snapshot["captured_at"])
            ).total_seconds() <= max(progress_grace_seconds, soft_timeout_seconds + 5)
            if reasons and within_grace and extensions_used < max_extensions and extension_seconds > 0:
                extensions_used += 1
                old_deadline = datetime.now().isoformat(timespec="seconds")
                soft_deadline = min(now_monotonic + extension_seconds, hard_deadline)
                event = {
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "extension": extensions_used,
                    "added_seconds": int(max(0, soft_deadline - now_monotonic)),
                    "reasons": reasons,
                    "old_deadline_at": old_deadline,
                    "new_deadline_at": (
                        datetime.now() + timedelta(seconds=max(0, soft_deadline - now_monotonic))
                    ).isoformat(timespec="seconds"),
                }
                extension_events.append(event)
                payload = dict(status_payload)
                payload.update({
                    "status": "running",
                    "phase": "timeout_extended",
                    "current_task": f"soft timeout extended ({extensions_used}/{max_extensions})",
                    "timeout_extended": True,
                    "extension_count": extensions_used,
                    "extension_reasons": reasons,
                    "deadline_at": event["new_deadline_at"],
                    "hard_timeout_seconds": hard_timeout_seconds,
                    "pid": process.pid,
                })
                write_agent_status(project_dir, payload)
                last_snapshot = current_snapshot
                continue

            timed_out = True
            timeout_reason = "soft_timeout_no_progress" if not reasons else "extensions_exhausted"
            break

        if process.poll() is not None:
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            exit_code = process.returncode
        else:
            terminate_process_tree(process, force=True)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            exit_code = 124
            elapsed_seconds = int(time.monotonic() - started_monotonic)
            stderr_chunks.append(f"\nTIMEOUT after {elapsed_seconds} seconds ({timeout_reason or 'timeout'})")
    except subprocess.TimeoutExpired:
        timed_out = True
        timeout_reason = "wait_timeout"
        terminate_process_tree(process, force=True)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        exit_code = 124
        stderr_chunks.append(f"\nTIMEOUT after {timeout_seconds} seconds")
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=1)
        tail_thread.join(timeout=1)

    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    timeout_meta = {
        "soft_timeout_seconds": soft_timeout_seconds,
        "hard_timeout_seconds": hard_timeout_seconds,
        "extension_seconds": extension_seconds,
        "max_extensions": max_extensions,
        "extensions_used": extensions_used,
        "extension_events": extension_events,
        "watchdog_enabled": watchdog_enabled,
        "progress_probe_seconds": progress_probe_seconds,
        "no_progress_timeout_seconds": no_progress_timeout_seconds,
        "min_runtime_seconds": min_runtime_seconds,
        "watchdog_state": watchdog_state,
        "last_probe_at": last_probe_at,
        "last_progress_at": last_progress_at,
        "last_progress_age_seconds": int(time.monotonic() - last_progress_monotonic),
        "last_progress_reasons": last_progress_reasons,
        "quiet_probe_count": quiet_probe_count,
        "watchdog_events": watchdog_events,
        "timeout_reason": timeout_reason,
        "pid": process.pid,
    }
    return exit_code, stdout or "", stderr or "", timed_out, timeout_meta


def worker_dependency_cache_env(project_dir, base_env=None):
    env = dict(base_env or os.environ)
    cache_root = os.path.abspath(os.path.join(project_dir, ".vulcan", "cache"))
    npm_cache = os.path.join(cache_root, "npm")
    playwright_cache = os.path.join(cache_root, "ms-playwright")
    os.makedirs(npm_cache, exist_ok=True)
    os.makedirs(playwright_cache, exist_ok=True)
    env.setdefault("npm_config_cache", npm_cache)
    env.setdefault("NPM_CONFIG_CACHE", npm_cache)
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", playwright_cache)
    env.setdefault("npm_config_update_notifier", "false")
    env.setdefault("NPM_CONFIG_UPDATE_NOTIFIER", "false")
    return env, {
        "npm_config_cache": npm_cache,
        "PLAYWRIGHT_BROWSERS_PATH": playwright_cache,
    }


def activity_status_payload(activity):
    status = {}
    for key in (
        "target_type",
        "target_id",
        "review_id",
        "run_id",
        "runner",
        "requested_runner",
        "started_at",
        "deadline_at",
        "exec_dir",
        "worktree_path",
        "branch",
        "status_file",
        "resume",
        "resume_started_at",
    ):
        if key in activity:
            status[key] = activity[key]
    return status


def make_runner_resume_capture(project_dir, activity, current_task):
    lock = threading.Lock()
    message_chunks = []
    last_message_status_at = 0.0

    def capture(line):
        nonlocal last_message_status_at
        info = runner_resume_info(activity.get("runner", ""), line)
        delta = extract_runner_stream_delta(activity.get("runner", ""), line)
        status_update = extract_runner_status_update(activity.get("runner", ""), line)
        log_update = extract_runner_log_update(activity.get("runner", ""), line)
        with lock:
            should_update = False
            status_phase = ""
            status_task = current_task
            if info.get("thread_id") and activity.get("thread_id") != info.get("thread_id"):
                activity.update(info)
                should_update = True
                status_phase = "session_started"
            if info.get("session_id") and activity.get("session_id") != info.get("session_id"):
                activity.update(info)
                should_update = True
                status_phase = "session_started"
            if delta:
                if delta != "".join(message_chunks):
                    message_chunks.append(delta)
                now = time.time()
                if now - last_message_status_at >= 30:
                    activity["current_message"] = truncate_dashboard_message("".join(message_chunks))
                    should_update = True
                    status_phase = status_phase or "message_stream"
                    last_message_status_at = now
            if status_update:
                activity.update(status_update)
                should_update = True
                status_phase = status_update.get("phase") or status_phase or "runner_status"
                status_task = status_update.get("current_task") or status_task
            if log_update:
                activity.update(log_update)
                should_update = True
                status_phase = log_update.get("phase") or status_phase or "runner_log"
                status_task = log_update.get("current_task") or status_task
            if not should_update:
                return
            event_message = status_task if (status_update or log_update) else (activity.get("current_message") or status_task or status_phase)
            append_agent_event(activity, status_phase or "running", event_message, status="running")
            write_agent_activity(project_dir, activity)
            status = activity_status_payload(activity)
            status.update({
                "status": "running",
                "phase": status_phase or "running",
                "current_task": status_task,
            })
            if "current_message" in activity:
                status["current_message"] = activity["current_message"]
            status.update(info)
            status.update(status_update)
            status.update(log_update)
            write_agent_status(project_dir, status)

    return capture


def parse_git_status_files(status_text):
    files = []
    for line in (status_text or "").splitlines():
        if not line.strip():
            continue

        # Accept both `git status --porcelain` (`XY path`) and
        # `git diff --name-status` (`M<TAB>path`) shaped inputs. Older summary
        # files showed paths like `ocs/...` and `ackend/...` when tab-separated
        # name-status lines were sliced as fixed-width porcelain lines.
        if "\t" in line:
            parts = line.split("\t")
            value = parts[-1] if len(parts) > 1 else line.strip()
        else:
            match = re.match(r"^(.{2})\s+(.*)$", line)
            value = match.group(2) if match else line.strip()

        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        files.append(value.strip().strip('"'))
    return files


def git_status_porcelain_all(project_dir="."):
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain", "-uall"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.rstrip()
    except subprocess.CalledProcessError:
        return ""


def parse_git_status_entries(status_text):
    entries = []
    for line in (status_text or "").splitlines():
        if not line.strip():
            continue
        status = line[:2]
        value = line[3:] if len(line) > 3 else line.strip()
        old_path = ""
        path = value.strip()
        if " -> " in value:
            old_path, path = [part.strip() for part in value.split(" -> ", 1)]
        path = decode_git_quoted_path(path)
        old_path = decode_git_quoted_path(old_path)
        entries.append({
            "status": status.strip() or status,
            "path": path,
            "old_path": old_path,
            "raw": line,
            "untracked": status == "??",
        })
    return entries


def decode_git_quoted_path(path):
    path = (path or "").strip()
    if len(path) < 2 or not (path.startswith('"') and path.endswith('"')):
        return path

    body = path[1:-1]
    raw = bytearray()
    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\":
            raw.extend(ch.encode("utf-8"))
            i += 1
            continue

        if i + 1 >= len(body):
            raw.extend(b"\\")
            i += 1
            continue

        nxt = body[i + 1]
        if nxt in "01234567":
            digits = nxt
            j = i + 2
            while j < len(body) and len(digits) < 3 and body[j] in "01234567":
                digits += body[j]
                j += 1
            raw.append(int(digits, 8))
            i = j
            continue

        escape_map = {
            "a": 7,
            "b": 8,
            "t": 9,
            "n": 10,
            "v": 11,
            "f": 12,
            "r": 13,
            '"': ord('"'),
            "\\": ord("\\"),
        }
        raw.append(escape_map.get(nxt, ord(nxt)))
        i += 2

    return raw.decode("utf-8", errors="replace")


def filter_ignorable_status_entries(entries):
    ignorable_prefixes = [
        ".vulcan/",
        "docs/runs/_exec/",
    ]
    kept = []
    for entry in entries:
        paths = [normalize_repo_path(entry.get("path", ""))]
        if entry.get("old_path"):
            paths.append(normalize_repo_path(entry.get("old_path", "")))
        if paths and all(any(path.startswith(prefix) for prefix in ignorable_prefixes) for path in paths):
            continue
        kept.append(entry)
    return kept


def has_blocking_dirty_status(project_dir="."):
    entries = parse_git_status_entries(git_status_porcelain_all(project_dir))
    return bool(filter_ignorable_status_entries(entries))


def blocking_dirty_entries(project_dir="."):
    entries = parse_git_status_entries(git_status_porcelain_all(project_dir))
    return filter_ignorable_status_entries(entries)


def print_blocking_dirty_summary(project_dir=".", max_entries=12):
    entries = blocking_dirty_entries(project_dir)
    if not entries:
        return
    print("  커밋/정리 대상 파일:")
    for entry in entries[:max_entries]:
        status = entry.get("status") or "?"
        path = entry.get("path") or "-"
        if entry.get("old_path"):
            path = f"{entry.get('old_path')} -> {path}"
        print(f"    - {status} {path}")
    if len(entries) > max_entries:
        print(f"    - ... 외 {len(entries) - max_entries}건")


def normalize_repo_path(path):
    normalized = path.replace("\\", "/").strip().strip('"').strip("'")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def extract_nested_yaml_list(content, parent_key, child_key):
    lines = content.splitlines()
    in_parent = False
    in_child = False
    items = []
    for line in lines:
        if not in_parent:
            if re.match(rf"^{re.escape(parent_key)}\s*:\s*$", line):
                in_parent = True
            continue
        if re.match(r"^\S", line):
            break
        if not in_child:
            if re.match(rf"^\s{{2}}{re.escape(child_key)}\s*:\s*$", line):
                in_child = True
            continue
        if re.match(r"^\s{0,2}\S", line):
            break
        match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if match:
            items.append(normalize_repo_path(match.group(1)))
    return items


def scope_pattern_matches(path, pattern):
    path = normalize_repo_path(path)
    pattern = normalize_repo_path(pattern)
    if not pattern:
        return False
    if pattern.endswith("/"):
        return path.startswith(pattern)
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    if any(ch in pattern for ch in "*?[]"):
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch("/" + path, pattern)
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def path_matches_any_scope(path, patterns):
    return any(scope_pattern_matches(path, pattern) for pattern in patterns or [])


def classify_config_hotfix_candidate(path, worktree_path=""):
    path = normalize_repo_path(path)
    name = os.path.basename(path)
    lower_path = path.lower()
    lower_name = name.lower()

    if not path or lower_path.startswith("docs/") or lower_path.startswith(".vulcan/"):
        return None

    exact_names = {
        "playwright.config.js",
        "playwright.config.cjs",
        "playwright.config.mjs",
        "playwright.config.ts",
        "vite.config.js",
        "vite.config.cjs",
        "vite.config.mjs",
        "vite.config.ts",
        "vitest.config.js",
        "vitest.config.cjs",
        "vitest.config.mjs",
        "vitest.config.ts",
        "pytest.ini",
        "tox.ini",
        "mypy.ini",
    }
    if lower_name in exact_names:
        return {
            "classification": "config_hotfix_candidate",
            "reason": "테스트/빌드 실행 설정 파일입니다. 기능 계약 변경 없이 검증 실행을 가능하게 하는 보정인지 확인하세요.",
            "contract_change_allowed": False,
            "dependency_change_review_required": False,
        }

    if re.fullmatch(r"tsconfig(?:\.[\w-]+)?\.json", lower_name):
        return {
            "classification": "config_hotfix_candidate",
            "reason": "TypeScript compile/test 설정 파일입니다. include/path/moduleResolution 보정인지 확인하세요.",
            "contract_change_allowed": False,
            "dependency_change_review_required": False,
        }

    if lower_name.startswith("eslint.config.") or lower_name.startswith(".eslintrc"):
        return {
            "classification": "config_hotfix_candidate",
            "reason": "Lint 실행 설정 파일입니다. 규칙 완화가 아니라 실행 환경 보정인지 확인하세요.",
            "contract_change_allowed": False,
            "dependency_change_review_required": False,
        }

    if lower_name == "pyproject.toml":
        return {
            "classification": "config_hotfix_candidate",
            "reason": "Python tool/test 설정 파일일 수 있습니다. build-system/dependency 변경이 아닌 test/lint 설정 보정인지 확인하세요.",
            "contract_change_allowed": False,
            "dependency_change_review_required": True,
        }

    if lower_name == "package.json":
        return {
            "classification": "config_hotfix_candidate_requires_dependency_review",
            "reason": "npm script 또는 test/build tooling 보정일 수 있습니다. dependencies/devDependencies 변경이면 Config Hotfix로 자동 수용하지 말고 review/CR 여부를 판단하세요.",
            "contract_change_allowed": False,
            "dependency_change_review_required": True,
        }

    if lower_name in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock"}:
        return {
            "classification": "dependency_lock_review_candidate",
            "reason": "Lockfile 변경은 의존성 변경을 동반할 수 있습니다. Config Hotfix로 수용하려면 package 변경 원인과 보안/버전 영향을 확인하세요.",
            "contract_change_allowed": False,
            "dependency_change_review_required": True,
        }

    return None


def run_integration_report_rel_path(project_dir, run_id):
    return os.path.join(execution_rel_dir(project_dir), f"{run_id}_integrate-report.json")


def load_latest_run_exec_summary(project_dir, run_id, runner=None):
    exec_dir = os.path.join(project_dir, execution_rel_dir(project_dir))
    if not os.path.isdir(exec_dir):
        return None, ""
    runner_slug = runner_log_slug(normalize_exec_runner(runner)) if runner else ""
    candidates = []
    for name in os.listdir(exec_dir):
        if not name.startswith(f"{run_id}_") or not name.endswith("-summary.json"):
            continue
        if runner_slug and not name.startswith(f"{run_id}_{runner_slug}-"):
            continue
        path = os.path.join(exec_dir, name)
        candidates.append((os.path.getmtime(path), path))
    if not candidates:
        return None, ""
    _, path = sorted(candidates, reverse=True)[0]
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), os.path.relpath(path, project_dir)
    except (OSError, json.JSONDecodeError):
        return None, os.path.relpath(path, project_dir)


def review_config_get(review_config, key, default=None):
    new_key = f"independent_{key}"
    if new_key in review_config:
        return review_config.get(new_key)
    return default


def create_review_worktree(project_dir, review_id, worktree_dir=None):
    project_abs = os.path.abspath(project_dir)
    if worktree_dir:
        target = os.path.abspath(worktree_dir)
    else:
        parent = os.path.dirname(project_abs)
        target = os.path.join(parent, f"{os.path.basename(project_abs)}-review-{review_id.lower()}")

    if os.path.exists(target):
        print(f"오류: 독립 검수 worktree 경로가 이미 존재합니다: {target}")
        sys.exit(1)

    try:
        subprocess.run(
            ["git", "worktree", "add", "--detach", target, "HEAD"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or str(e)).strip()
        print(f"오류: 독립 검수 worktree 생성 실패 - {detail}")
        sys.exit(1)

    return target


def cmd_review_request(title, gate, related_ids, from_run="", runner=None, create_worktree=None, worktree_dir="", project_dir="."):
    config = load_vulcan_config(project_dir)
    review_config = config.get("review", {}) if isinstance(config.get("review"), dict) else {}
    runner = runner or review_config_get(review_config, "runner", "codex-cli")
    if runner not in INDEPENDENT_REVIEW_RUNNERS:
        print(f"오류: 알 수 없는 독립 검수 runner입니다: {runner}")
        print("사용 가능 runner:")
        for name in INDEPENDENT_REVIEW_RUNNERS:
            print(f"  - {name}")
        sys.exit(1)

    if create_worktree is None:
        create_worktree = bool(review_config_get(review_config, "worktree", True))

    ids = split_csv(related_ids)
    review_id = next_review_id(project_dir)
    review_slug = slugify(f"review {gate} {title}")
    review_rel_dir = reviews_rel_dir(project_dir)
    request_rel_path = os.path.join(review_rel_dir, f"{review_id}_{review_slug}_request.md")
    result_rel_path = os.path.join(review_rel_dir, f"{review_id}_{review_slug}_result.md")
    run_id = next_run_id(project_dir)
    run_rel_path = os.path.join(runs_rel_dir(project_dir), f"{run_id}_independent-review-{review_slug}_v0.1.md")
    source_run = from_run or "TBD"
    dirty_status = git_status_porcelain(project_dir)
    worktree_path = "TBD"

    if create_worktree:
        worktree_path = create_review_worktree(project_dir, review_id, worktree_dir or None)

    gate_focus = {
        "gate2": [
            "Gate 2만 보지 말고 Phase 0 -> Gate 1 -> Gate 2 순서로 상류 정합성을 먼저 확인한다.",
            "Phase 0의 목표, 제약, 가정, 질문, DEC/RISK/ASM이 Gate 1 요구사항/범위에 반영되었는지 확인한다.",
            "Gate 1의 REQ/NREQ/AC, 포함/제외 범위, DEC/ISSUE가 Gate 2 설계 전제와 모순되지 않는지 확인한다.",
            "Gate 2 설계가 승인된 Gate 1 범위를 임의로 축소하거나 확장하지 않았는지 확인한다.",
            "Gate 2 설계 순서(G2-01~G2-10)가 지켜졌는지 확인한다.",
            "REQ/AC가 FUNC, SCR, PGM, API, DB, SEC, DEV 기준으로 빠짐없이 전개되었는지 확인한다.",
            "SW Architecture가 Draft에서 Baseline 후보로 충분히 보강되었는지 확인한다.",
            "UIREF/ui-baseline이 있으면 UI Implementation Contract와 상태별 UI 증적 기준이 있는지 확인한다.",
            "Gate 3 테스트 설계로 넘길 검증 후보와 미해결 질문이 분리되었는지 확인한다.",
        ],
        "gate4": [
            "테스트 결과가 개발표준과 테스트케이스의 필수 명령을 모두 실행했는지 확인한다.",
            "각 검증 결과에 cwd, 명령, exit code, 성공 기준, 로그/증적 경로가 있는지 확인한다.",
            "UI 증적이 상태/시나리오별 UI-ID와 1:1로 연결되었는지 확인한다.",
            "기준 UIREF와 구현 screenshot 차이가 Pass/FIND/CR로 판정되었는지 확인한다.",
            "미실행 검증이나 기대 화면과 다른 캡처가 Pass로 기록되지 않았는지 확인한다.",
        ],
    }.get(gate, [
        "현재 Gate 산출물, Run 결과, 추적표의 일관성을 확인한다.",
        "완료 선언 전에 사용자 승인 대기와 미해결 항목이 분리되었는지 확인한다.",
        "발견사항을 PASS, FIND, CR, ISSUE 중 하나로 분류한다.",
    ])

    upstream_review_content = ""
    upstream_result_content = ""
    if gate == "gate2":
        upstream_review_content = """
## 4.1 Gate 2 상류 정합성 필수 검토

Gate 2 독립 검수는 Gate 2 산출물만 보는 검수가 아니다.
반드시 다음 순서로 앞단부터 확인한 뒤 설계 산출물을 판정한다.

| 순서 | 확인 범위 | 확인 기준 |
| --- | --- | --- |
| 1 | Phase 0 | 프로젝트 목표, 사용자, 제약, 가정, 질문, 리스크, 의사결정이 기록되어 있는가 |
| 2 | Phase 0 -> Gate 1 | Phase 0의 목표/제약/가정/질문이 Gate 1 요구사항, 범위, DEC/ISSUE로 내려왔는가 |
| 3 | Gate 1 | REQ/NREQ/AC, 포함/제외 범위, DEC/ISSUE가 명확한가 |
| 4 | Gate 1 -> Gate 2 | REQ/NREQ/AC가 FUNC, SCR, PGM, API, DB, SEC, DEV 설계로 누락 없이 전개됐는가 |
| 5 | Scope Drift | Gate 2가 승인된 Gate 1 범위를 임의 확장/축소하지 않았는가 |
| 6 | Open Decisions | 미해결 DEC/ISSUE/RISK/ASM이 닫혔거나 Gate 3 입력/Orchestrator 판단 항목으로 분리됐는가 |
| 7 | Design Internal Consistency | 아키텍처, 화면, 기능, API, 프로그램, DB, 보안, 개발표준이 서로 모순되지 않는가 |

상류 정합성에서 누락이나 모순이 있으면 Gate 2 문서 내부가 잘 작성되어 있어도 `PASS`로 판정하지 않는다.
승인된 범위 안에서 보완 가능한 결함은 `FIND`, 요구사항/범위/기준선 변경이 필요하면 `CR`, 사용자 판단이 필요하면 `ISSUE`로 남긴다.
"""
        upstream_result_content = """
## 2.1 Gate 2 상류 정합성 판정

| 판정 항목 | 결과 | 근거 | FIND/CR/ISSUE 후보 |
| --- | --- | --- | --- |
| Phase0 -> Gate1 | TBD |  |  |
| Gate1 -> Gate2 | TBD |  |  |
| Scope Drift | TBD |  |  |
| Open Decisions | TBD |  |  |
| Design Internal Consistency | TBD |  |  |
"""

    request_content = f"""# {review_id} Independent Review Request - {title}

```yaml
review_id: {review_id}
review_type: independent
status: Requested
runner: {runner}
gate: {gate}
upstream_review_required: {"true" if gate == "gate2" else "false"}
source_run: {source_run}
request_file: {request_rel_path}
result_file: {result_rel_path}
worktree_path: {worktree_path}
independent_session_required: true
readonly_review: true
related_ids: {format_yaml_list(ids)}
created_at: {date.today()}
```

## 1. 리뷰 목적

{title}

독립 검수는 작성 세션과 분리된 검수다. 리뷰어는 산출물을 직접 수정하지 않고, 결과 파일에 `PASS`, `FIND`, `CR`, `ISSUE` 후보를 남긴다.

## 2. 먼저 읽을 문서

- `AGENTS.md`
- `session.json`
- `vulcan.config.json`
- `docs/core/INDEPENDENT_REVIEW_PROCESS.md`
- `docs/core/TRACEABILITY_RULES.md`
- `docs/core/AGENT_RUN_PROTOCOL.md`
- `docs/core/RUN_INPUT_CONTRACT.md`
- `docs/core/RUN_OUTPUT_CONTRACT.md`
- `docs/adapters/codex-gpt/skills/independent-review.md`

## 3. 리뷰 대상

| 항목 | 내용 |
| --- | --- |
| Gate | `{gate}` |
| 원본 Run | `{source_run}` |
| 관련 ID | `{format_yaml_list(ids)}` |
| 결과 파일 | `{result_rel_path}` |

## 4. 중점 검토 항목

{chr(10).join(f"- {item}" for item in gate_focus)}
{upstream_review_content}

## 5. 범위

### Readonly

- `docs/artifacts/`
- `docs/runs/`
- `docs/core/`
- `docs/adapters/`
- `session.json`
- `vulcan.config.json`

### Writable

- `{result_rel_path}`

## 6. 판정 규칙

| 판정 | 기준 |
| --- | --- |
| PASS | Gate 산출물과 증적이 다음 Gate 진행에 충분하다 |
| FIND | 승인된 범위 안의 결함이며 Gate 안에서 수정 가능하다 |
| CR | 요구사항, 설계, 보안, 데이터, 릴리즈 범위 변경이 필요하다 |
| ISSUE | 결론을 내리려면 추가 질문 또는 사용자 판단이 필요하다 |

## 7. 주의

- 리뷰어는 작성자의 의도를 추측하지 않는다.
- 리뷰어는 Gate 전환, session 상태 변경, 최종 승인 판단을 하지 않는다.
- 대화상 사용자 승인 없이 `User Approved`로 기록하지 않는다.
- 실행하지 않은 테스트나 확인하지 않은 화면을 Pass로 판정하지 않는다.
- 산출물을 수정해야 한다면 직접 수정하지 말고 결과 파일에 `FIND` 또는 `CR`로 남긴다.
"""

    result_content = f"""# {review_id} Independent Review Result - {title}

```yaml
review_id: {review_id}
review_type: independent
status: Draft
runner: {runner}
gate: {gate}
source_run: {source_run}
reviewed_by: TBD
environment: independent-session
result_verdict: Pending
related_ids: {format_yaml_list(ids)}
verification_results: []
evidence: []
delegation_records: []
findings: []
change_requests: []
issues: []
orchestrator_decision_needed: []
```

## 1. 요약

TBD

## 2. 실행/확인 증적

| 항목 | 결과 | 근거 |
| --- | --- | --- |
| 문서 검토 | TBD |  |
| 추적성 검토 | TBD |  |
| 검증 명령 확인 | TBD |  |
| UI/증적 확인 | TBD |  |
{upstream_result_content}

## 3. Findings

| ID | 심각도 | 관련 ID | 내용 | 권고 처리 |
| --- | --- | --- | --- | --- |
| FIND- | Blocker/Major/Minor |  |  |  |

## 4. CR 후보

| ID | 관련 ID | 변경 필요 범위 | 사유 |
| --- | --- | --- | --- |
| CR- |  |  |  |

## 5. ISSUE 후보

| ID | 질문/위험 | 필요한 결정 |
| --- | --- | --- |
| ISSUE- |  |  |

## 6. Orchestrator 결정 필요 항목

TBD
"""

    run_content = f"""# {run_id} Independent Review - {title}

```yaml
run_id: {run_id}
gate: {gate}
persona: review
skill: independent-review
skill_path: docs/adapters/codex-gpt/skills/independent-review.md
status: Draft
created_at: {date.today()}
review_id: {review_id}
review_type: independent
runner: {runner}
from_run: {source_run}
request_file: {request_rel_path}
result_file: {result_rel_path}
worktree_path: {worktree_path}
related_ids: {format_yaml_list(ids)}
verification_results: []
evidence: []
delegation_records: []
traceability_updates: []
findings: []
change_requests: []
open_issues: []
```

## 1. 목적

{title}

## 2. 독립 검수 요청

- 요청 파일: `{request_rel_path}`
- 결과 파일: `{result_rel_path}`
- 독립 세션/worktree: `{worktree_path}`

## 3. Orchestrator 처리 원칙

- 독립 검수 결과를 최종 사실로 바로 확정하지 않는다.
- 결과 파일의 `FIND`, `CR`, `ISSUE` 후보를 본선 산출물과 대조한다.
- 반영이 필요하면 별도 Run 또는 QA Fix Loop로 처리한다.
- 독립 검수 runner는 Gate 전환, session 상태 변경, 최종 승인 판단을 하지 않는다.
- 리뷰 worktree는 결과 수집 후 사용자가 확인한 뒤 정리한다.

## 4. 완료 보고

TBD
"""

    write_file(project_dir, request_rel_path, request_content)
    write_file(project_dir, result_rel_path, result_content)
    write_file(project_dir, run_rel_path, run_content)

    if create_worktree and worktree_path != "TBD":
        for rel_path in (request_rel_path, result_rel_path, run_rel_path):
            src = os.path.join(project_dir, rel_path)
            dst = os.path.join(worktree_path, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, encoding="utf-8") as f:
                content = f.read()
            with open(dst, "w", encoding="utf-8") as f:
                f.write(content)

    print(f"\n독립 검수 요청 생성 완료: {request_rel_path}")
    print(f"독립 검수 결과 초안 생성 완료: {result_rel_path}")
    print(f"독립 검수 Run 생성 완료: {run_rel_path}")
    if create_worktree:
        print(f"독립 검수 worktree 생성 완료: {worktree_path}")
    if dirty_status and create_worktree:
        print("\n주의: 본 작업공간에 커밋되지 않은 변경이 있습니다.")
        print("  worktree는 HEAD 기준으로 생성되므로 미커밋 변경은 포함되지 않을 수 있습니다.")
    print("\n다음 단계: 새 Codex/Claude 세션에서 request 파일을 열고 result 파일을 작성합니다.")


def cmd_review_run(
    review_id,
    runner=None,
    model=None,
    reasoning_effort=None,
    timeout_seconds=None,
    sandbox=None,
    dry_run=False,
    project_dir=".",
):
    config = load_vulcan_config(project_dir)
    review_config = config.get("review", {}) if isinstance(config.get("review"), dict) else {}
    project_abs = os.path.abspath(project_dir)
    request_rel_path = find_review_file(project_abs, review_id, "_request.md")
    result_rel_path = find_review_file(project_abs, review_id, "_result.md")
    run_rel_path = find_independent_review_run_file(project_abs, review_id)
    if not request_rel_path or not result_rel_path:
        print(f"오류: {review_id}에 해당하는 독립 검수 request/result 파일을 찾을 수 없습니다.")
        sys.exit(1)

    request_abs = os.path.abspath(os.path.join(project_abs, request_rel_path))
    result_abs = os.path.abspath(os.path.join(project_abs, result_rel_path))
    run_abs = os.path.abspath(os.path.join(project_abs, run_rel_path)) if run_rel_path else ""
    with open(request_abs, encoding="utf-8") as f:
        request_content = f.read()
    request_meta = parse_simple_yaml_block(request_content)
    requested_runner = request_meta.get("runner", "")
    runner = runner or requested_runner or review_config_get(review_config, "runner", "") or runtime_role_runner(config, "review")
    runner_normalized = normalize_exec_runner(runner)
    if runner_normalized not in INDEPENDENT_REVIEW_EXEC_RUNNERS:
        print(f"오류: review-run에서 아직 지원하지 않는 runner입니다: {runner}")
        print("현재 지원 runner: codex-cli, claude-cli, antigravity-cli")
        sys.exit(1)

    worktree_path = request_meta.get("worktree_path", "TBD")
    exec_dir = os.path.abspath(worktree_path) if worktree_path and worktree_path != "TBD" and os.path.isdir(worktree_path) else project_abs
    exec_result_abs = os.path.abspath(os.path.join(exec_dir, result_rel_path))
    exec_request_abs = os.path.abspath(os.path.join(exec_dir, request_rel_path))
    if not os.path.exists(exec_request_abs):
        exec_request_abs = request_abs
    if not os.path.exists(exec_result_abs):
        exec_result_abs = result_abs

    runner_config = runtime_runner_config(config, runner_normalized)
    model_resolution = {
        "model_source": runner_model_source(runner_normalized),
        "effort_source": "runner-config",
        "policy_role": "",
    }
    if runner_normalized == "codex-cli":
        cli_model = model
        cli_effort = reasoning_effort
        review_model = review_config_get(review_config, "model", "")
        review_effort = review_config_get(review_config, "reasoning_effort", "")
        if cli_model or cli_effort:
            model, reasoning_effort, model_resolution = resolve_codex_model_effort(
                config,
                "review",
                explicit_model=cli_model,
                explicit_effort=cli_effort,
                runner_config=runner_config,
            )
        elif review_model or review_effort:
            model = review_model or runner_config.get("model") or "gpt-5.5"
            reasoning_effort = (
                review_effort
                or runner_config.get("reasoning_effort")
                or runner_config.get("effort")
                or "high"
            )
            model_resolution = {
                "model_source": "review-config" if review_model else "runner-config",
                "effort_source": "review-config" if review_effort else "runner-config",
                "policy_role": "review",
            }
        else:
            model, reasoning_effort, model_resolution = resolve_codex_model_effort(
                config,
                "review",
                runner_config=runner_config,
            )
    elif runner_normalized == "claude-cli":
        model = model or review_config_get(review_config, "claude_model", "") or runner_config.get("model") or "claude-opus-4-7"
        reasoning_effort = (
            reasoning_effort
            or review_config_get(review_config, "claude_effort", "")
            or runner_config.get("effort")
            or runner_config.get("reasoning_effort")
            or "high"
        )
    else:
        model = model or runner_config.get("model") or "gemini-3.5-flash"
        reasoning_effort = (
            reasoning_effort
            or runner_config.get("effort")
            or runner_config.get("reasoning_effort")
            or "high"
        )
    sandbox = sandbox or review_config_get(review_config, "sandbox", "") or runner_config.get("sandbox") or "workspace-write"
    if sandbox == "read-only":
        print("오류: 독립 검수 실행은 result 파일을 작성해야 하므로 --sandbox read-only를 사용할 수 없습니다.")
        print("  result 파일까지 runner가 직접 작성하려면 --sandbox workspace-write를 사용하세요.")
        print("  읽기 전용 관찰만 필요하면 runner를 직접 실행하고 last-message를 수동 검토하세요.")
        sys.exit(1)
    timeout_seconds = int(timeout_seconds or review_config_get(review_config, "exec_timeout_seconds", 1800))

    review_rel_dir = reviews_rel_dir(project_dir)
    log_slug = runner_log_slug(runner_normalized)
    log_ext = runner_log_ext(runner_normalized)
    log_rel_path = os.path.join(review_rel_dir, f"{review_id}_{log_slug}-exec.{log_ext}")
    stderr_rel_path = os.path.join(review_rel_dir, f"{review_id}_{log_slug}-exec.stderr.txt")
    last_message_rel_path = os.path.join(review_rel_dir, f"{review_id}_{log_slug}-last-message.md")
    status_rel_path = agent_status_rel_path(project_abs, review_id, runner_normalized)
    log_abs = os.path.abspath(os.path.join(project_abs, log_rel_path))
    stderr_abs = os.path.abspath(os.path.join(project_abs, stderr_rel_path))
    last_message_abs = os.path.abspath(os.path.join(project_abs, last_message_rel_path))
    status_abs = os.path.abspath(os.path.join(project_abs, status_rel_path))
    os.makedirs(os.path.dirname(log_abs), exist_ok=True)

    prompt = f"""You are executing an independent review for Vulcan-Anvil Ex right now.

This is not a preparation request. Do not answer that you will review later.
You must read the request file, perform the review in this run, and update the result file before exiting.
If you cannot update the result file, write a failed/blocked result and explain why.

Working directory:
{exec_dir}

Read this independent review request:
{request_rel_path}

Write your review result only to:
{result_rel_path}

Update this worker status file at start and whenever the phase changes:
{status_abs}

Rules:
- Treat this as a new independent review session.
- Do not modify project artifacts, source code, requirements, design documents, test results, or traceability documents.
- You may read files and run safe verification commands if needed.
- You must update the result file with status, reviewed_by, result_verdict, reviewed documents, findings, CR candidates, ISSUE candidates, and evidence.
- Use PASS, FIND, CR, or ISSUE as the result verdict.
- Do not rely on wall-clock timers. Update the status file when you start, after loading context, while reviewing, while writing the result, and when completed/blocked/failed.
- Keep status.current_task to one short dashboard line, 80 characters or fewer.
- Status JSON shape: {{"target_id":"{review_id}","target_type":"review","runner":"{runner_normalized}","status":"running","phase":"context_loaded","current_task":"Gate2 review context loaded","last_update":"<ISO time>"}}.
- Do not perform Gate transitions, edit session state, or make final approval/merge/release decisions.
- Do not mark user approval unless the request/result contains explicit user approval evidence.
- In your final response, summarize what you wrote to the result file and mention the result verdict.
"""

    if runner_normalized == "codex-cli":
        runner_exe = shutil.which("codex")
        if not runner_exe:
            print("오류: codex CLI를 찾을 수 없습니다. `codex --version`이 실행되는지 확인하세요.")
            sys.exit(1)
        cmd = [
            runner_exe,
            "-a",
            "never",
            "exec",
            "--cd",
            exec_dir,
            "--add-dir",
            project_abs,
            "-m",
            model,
            "-c",
            f"model_reasoning_effort={format_yaml_scalar(reasoning_effort)}",
            "--sandbox",
            sandbox,
            "--json",
            "--output-last-message",
            last_message_abs,
            prompt,
        ]
    elif runner_normalized == "claude-cli":
        runner_exe = shutil.which("claude")
        if not runner_exe:
            print("오류: Claude CLI를 찾을 수 없습니다. `claude --version`이 실행되는지 확인하세요.")
            sys.exit(1)
        cmd = [
            runner_exe,
            "-p",
            prompt,
            "--add-dir",
            project_abs,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--effort",
            reasoning_effort,
            "--dangerously-skip-permissions",
        ]
        if model:
            cmd.extend(["--model", model])
    else:
        runner_exe = antigravity_executable()
        if not runner_exe:
            print("오류: Antigravity headless CLI(agy.exe)를 찾을 수 없습니다. `agy.exe --help`가 실행되는지 확인하세요.")
            sys.exit(1)
        prompt = f"""Antigravity/Gemini runner settings:
- Requested model: {model}
- Requested reasoning effort: {reasoning_effort}
- Model source: inherit current Antigravity CLI configuration

{prompt}
"""
        cmd = [
            runner_exe,
            "--add-dir",
            exec_dir,
            "--add-dir",
            project_abs,
            "--log-file",
            log_abs,
            "--print-timeout",
            f"{timeout_seconds}s",
        ]
        if sandbox == "read-only":
            cmd.append("--sandbox")
        else:
            cmd.append("--dangerously-skip-permissions")
        cmd.extend(["--print", prompt])

    printable_cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd)
    if dry_run:
        print("Independent review run dry-run")
        print(f"  review_id: {review_id}")
        print(f"  runner: {runner_normalized}")
        print(f"  model: {model or '(runner default)'}")
        print(f"  reasoning_effort: {reasoning_effort}")
        print(f"  model_source: {model_resolution.get('model_source')}")
        print(f"  effort_source: {model_resolution.get('effort_source')}")
        if model_resolution.get("policy_role"):
            print(f"  model_policy_role: {model_resolution.get('policy_role')}")
        if model_resolution.get("model_fallback_reason"):
            print(f"  model_fallback_reason: {model_resolution.get('model_fallback_reason')}")
        if runner_normalized == "antigravity-cli":
            print("  model_source: agy-config-inherited")
            print("  note: Antigravity CLI의 현재 모델/effort 설정을 상속합니다.")
        print(f"  exec_dir: {exec_dir}")
        print(f"  command: {printable_cmd}")
        return

    before_hash = file_sha256(exec_result_abs)
    started_dt = datetime.now()
    deadline_dt = started_dt + timedelta(seconds=timeout_seconds)
    started_at = started_dt.isoformat(timespec="seconds")
    deadline_at = deadline_dt.isoformat(timespec="seconds")
    initial_timeout_policy = build_timeout_policy_payload(timeout_seconds, started_at=started_at)
    activity = {
        "target_type": "review",
        "target_id": review_id,
        "review_id": review_id,
        "status": "running",
        "runner": runner_normalized,
        "requested_runner": requested_runner or runner_normalized,
        "model": model or "(runner default)",
        "reasoning_effort": reasoning_effort,
        "model_source": model_resolution.get("model_source") or runner_model_source(runner_normalized),
        "effort_source": model_resolution.get("effort_source") or "",
        "model_policy_role": model_resolution.get("policy_role") or "",
        "model_fallback_reason": model_resolution.get("model_fallback_reason") or "",
        "sandbox": sandbox,
        "exec_dir": exec_dir,
        "started_at": started_at,
        "deadline_at": deadline_at,
        "timeout_seconds": timeout_seconds,
        "timed_out": False,
        "log": log_rel_path.replace("\\", "/"),
        "stderr_log": stderr_rel_path.replace("\\", "/"),
        "last_message": last_message_rel_path.replace("\\", "/"),
        "result_file": result_rel_path.replace("\\", "/"),
        "status_file": status_rel_path.replace("\\", "/"),
    }
    append_agent_event(activity, "started", f"{review_id} 독립 검수 시작", status="running")
    activity_rel_path = write_agent_activity(project_abs, activity)
    write_agent_status(project_abs, {
        "target_type": "review",
        "target_id": review_id,
        "review_id": review_id,
        "runner": runner_normalized,
        "requested_runner": requested_runner or runner_normalized,
        "status": "running",
        "phase": "started",
        "current_task": f"{review_id} 독립 검수 시작",
        "started_at": started_at,
        "deadline_at": deadline_at,
        "exec_dir": exec_dir,
        "status_file": status_rel_path,
    })
    exit_code, stdout, stderr, timed_out, timeout_meta = run_command_with_status_heartbeat(
        cmd=cmd,
        cwd=exec_dir,
        timeout_seconds=timeout_seconds,
        project_dir=project_abs,
        status_payload={
            "target_type": "review",
            "target_id": review_id,
            "review_id": review_id,
            "runner": runner_normalized,
            "requested_runner": requested_runner or runner_normalized,
            "started_at": started_at,
            "deadline_at": deadline_at,
            "exec_dir": exec_dir,
            "status_file": status_rel_path,
        },
        current_task=f"{review_id} {runner_normalized} 응답 대기 중",
        on_stdout_line=make_runner_resume_capture(
            project_abs,
            activity,
            f"{review_id} {runner_normalized} 세션 연결됨",
        ),
        tail_file_path=log_abs if runner_normalized == "antigravity-cli" else None,
        on_tail_line=make_runner_resume_capture(
            project_abs,
            activity,
            f"{review_id} {runner_normalized} 로그 수신 중",
        ) if runner_normalized == "antigravity-cli" else None,
    )
    completed_dt = datetime.now()
    completed_at = completed_dt.isoformat(timespec="seconds")
    duration_seconds = int((completed_dt - started_dt).total_seconds())

    if runner_normalized == "antigravity-cli":
        if stdout.strip():
            with open(log_abs, "a", encoding="utf-8") as f:
                f.write("\n\n--- stdout ---\n")
                f.write(stdout)
    else:
        with open(log_abs, "w", encoding="utf-8") as f:
            f.write(stdout)
    with open(stderr_abs, "w", encoding="utf-8") as f:
        f.write(stderr)
    agy_probe = antigravity_transcript_probe(log_abs) if runner_normalized == "antigravity-cli" else {}
    if runner_normalized in ("claude-cli", "antigravity-cli"):
        last_message_text = runner_last_message(runner_normalized, stdout)
        if runner_normalized == "antigravity-cli" and not (last_message_text or "").strip():
            last_message_text = agy_probe.get("transcript_message") or ""
        with open(last_message_abs, "w", encoding="utf-8") as f:
            f.write(last_message_text)

    after_hash = file_sha256(exec_result_abs)
    result_changed = bool(before_hash and after_hash and before_hash != after_hash)
    empty_output = (
        runner_normalized == "antigravity-cli"
        and runner_empty_output(stdout, stderr)
        and not agy_probe.get("has_transcript_response")
    )
    if timed_out:
        run_status = "timeout"
    elif exit_code != 0:
        run_status = "failed"
    elif empty_output and not result_changed:
        run_status = "failed_empty_output"
    elif not result_changed:
        run_status = "completed_no_result_change"
    else:
        run_status = "completed"
    activity.update({
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "timed_out": timed_out,
        "status": run_status,
        "exit_code": exit_code,
        "empty_output": empty_output,
        "result_file_changed": result_changed,
    })
    activity.update(collect_runner_log_updates(runner_normalized, log_abs))
    activity.update(runner_resume_info(runner_normalized, stdout))
    if runner_normalized == "antigravity-cli" and agy_probe:
        if agy_probe.get("conversation_id"):
            activity.update({
                "conversation_id": agy_probe["conversation_id"],
                "resume_supported": True,
                "resume_hint": f"agy.exe --conversation {agy_probe['conversation_id']}",
            })
        if agy_probe.get("transcript_path"):
            activity["transcript"] = project_display_path(project_abs, agy_probe["transcript_path"])
            activity["transcript_response_detected"] = bool(agy_probe.get("has_transcript_response"))
    append_agent_event(
        activity,
        "completed" if run_status == "completed" else run_status,
        f"{review_id} 검수 결과 작성 완료" if result_changed else f"{review_id} 결과 파일 미갱신",
        status=run_status,
    )
    write_agent_activity(project_abs, activity)
    write_agent_status(project_abs, {
        "target_type": "review",
        "target_id": review_id,
        "review_id": review_id,
        "runner": runner_normalized,
        "requested_runner": requested_runner or runner_normalized,
        "status": run_status,
        "phase": "completed" if run_status == "completed" else run_status,
        "current_task": (
            f"{review_id} 검수 결과 작성 완료"
            if result_changed
            else f"{review_id} 결과 파일 미갱신"
        ),
        "started_at": started_at,
        "deadline_at": deadline_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "exec_dir": exec_dir,
        "status_file": status_rel_path,
        "result_file_changed": result_changed,
        "exit_code": exit_code,
        **runner_log_identity_fields(collect_runner_log_updates(runner_normalized, log_abs)),
        **runner_resume_info(runner_normalized, stdout),
    })
    if os.path.normcase(exec_result_abs) != os.path.normcase(result_abs) and os.path.exists(exec_result_abs):
        os.makedirs(os.path.dirname(result_abs), exist_ok=True)
        shutil.copy2(exec_result_abs, result_abs)

    if run_abs and os.path.exists(run_abs):
        execution_note = f"""

## 5. 독립 검수 실행 기록

```yaml
executed_at: {started_at}
deadline_at: {deadline_at}
completed_at: {completed_at}
duration_seconds: {duration_seconds}
timeout_seconds: {timeout_seconds}
hard_timeout_seconds: {timeout_meta.get("hard_timeout_seconds")}
extension_seconds: {timeout_meta.get("extension_seconds")}
max_extensions: {timeout_meta.get("max_extensions")}
extensions_used: {timeout_meta.get("extensions_used")}
timeout_reason: {timeout_meta.get("timeout_reason") or ""}
timed_out: {str(timed_out).lower()}
empty_output: {str(empty_output).lower()}
status: {run_status}
runner: {runner_normalized}
model: {model or "(runner default)"}
reasoning_effort: {reasoning_effort}
model_source: {model_resolution.get("model_source") or runner_model_source(runner_normalized)}
effort_source: {model_resolution.get("effort_source") or ""}
model_policy_role: {model_resolution.get("policy_role") or ""}
model_fallback_reason: {model_resolution.get("model_fallback_reason") or ""}
sandbox: {sandbox}
exec_dir: {exec_dir}
exit_code: {exit_code}
json_log: {log_rel_path}
stderr_log: {stderr_rel_path}
last_message: {last_message_rel_path}
activity: {activity_rel_path}
result_file_changed: {str(result_changed).lower()}
transcript: {project_display_path(project_abs, agy_probe.get("transcript_path") or "") if runner_normalized == "antigravity-cli" else ""}
transcript_response_detected: {str(bool(agy_probe.get("has_transcript_response"))).lower() if runner_normalized == "antigravity-cli" else "false"}
```
"""
        with open(run_abs, "a", encoding="utf-8") as f:
            f.write(execution_note)

    print("\n독립 검수 실행 완료")
    print(f"  review_id: {review_id}")
    print(f"  runner: {runner_normalized}")
    print(f"  model: {model or '(runner default)'}")
    print(f"  reasoning_effort: {reasoning_effort}")
    print(f"  status: {run_status}")
    print(f"  duration_seconds: {duration_seconds}")
    print(f"  exit_code: {exit_code}")
    print(f"  empty_output: {str(empty_output).lower()}")
    print(f"  result_changed: {str(result_changed).lower()}")
    print(f"  json_log: {log_rel_path}")
    print(f"  last_message: {last_message_rel_path}")
    print(f"  activity: {activity_rel_path}")
    if exit_code != 0:
        print(f"오류: {runner_normalized} 실행이 비정상 종료되었습니다. stderr 로그를 확인하세요: {stderr_rel_path}")
        sys.exit(exit_code)
    if empty_output and not result_changed:
        print(f"오류: {runner_normalized} 실행이 exit code 0으로 종료됐지만 stdout/stderr와 result 변경이 모두 없습니다.")
        print(f"  wrapper 또는 인증/세션 문제일 수 있습니다. 로그를 확인하세요: {log_rel_path}, {stderr_rel_path}")
        sys.exit(1)
    if not result_changed:
        print("경고: result 파일 변경이 감지되지 않았습니다. 독립 검수 결과를 확인하세요.")


def infer_execution_role(run_content, metadata):
    persona = (metadata.get("persona") or "").lower()
    skill = (metadata.get("skill") or "").lower()
    title_hint = f"{metadata.get('run_id') or ''} {metadata.get('title') or ''} {metadata.get('bw_id') or ''}".lower()
    text = run_content.lower()
    header_text = run_content[:2000].lower()

    if skill == "qa-execution" or "qa-execution" in text:
        return "qa-execution"
    if skill == "qa-fix-loop" or "qa-fix-loop" in text:
        return "qa-fix-loop"

    if skill in ("build-wave", "implementation-scaffold") or persona in ("build", "frontend", "backend", "ui", "screen"):
        if persona == "backend" or "backend" in title_hint or "백엔드" in title_hint:
            return "build-backend"
        if persona in ("ui", "screen", "frontend") or "frontend" in title_hint or "프론트" in title_hint:
            return "build-frontend"
        target_contracts_block = re.search(r"(?is)target_contracts:\s*(.+?)(?:\n[a-zA-Z_][\w-]*:|\Z)", run_content)
        target_contracts_text = (target_contracts_block.group(1) if target_contracts_block else "").lower()
        has_api_or_data_contract = bool(re.search(r"(?m)^\s*(api|data|db)\s*:", target_contracts_text))
        has_ui_contract = bool(re.search(r"(?m)^\s*ui\s*:", target_contracts_text))
        has_backend_scope = any(marker in text for marker in ["backend/", "app/", "src/", "api"])
        has_frontend_scope = any(marker in text for marker in ["frontend/", "static/", "ui-"])
        if has_ui_contract and has_api_or_data_contract and has_backend_scope and has_frontend_scope:
            return "build"
        header_frontend = min([idx for idx in [header_text.find("frontend"), header_text.find("front-end"), header_text.find("프론트")] if idx >= 0] or [999999])
        header_backend = min([idx for idx in [header_text.find("backend"), header_text.find("back-end"), header_text.find("백엔드")] if idx >= 0] or [999999])
        if header_backend < header_frontend:
            return "build-backend"
        if header_frontend < header_backend:
            return "build-frontend"
        if "frontend" in text or "front-end" in text or "프론트" in run_content or persona in ("ui", "screen", "frontend"):
            return "build-frontend"
        if "backend" in text or "back-end" in text or "백엔드" in run_content or persona == "backend":
            return "build-backend"
        return "build"

    if "independent-review" in skill or skill.endswith("-review") or "review" in persona:
        return "review"
    if "evidence" in persona or "evidence" in skill:
        return "evidence"
    if "frontend" in text or "front-end" in text or "프론트" in run_content or persona in ("ui", "screen", "frontend") or "frontend" in title_hint:
        return "build-frontend"
    if "backend" in text or "back-end" in text or "백엔드" in run_content or "backend" in title_hint:
        return "build-backend"
    if "review" in text or "검수" in run_content:
        return "review"
    return "build"


def _execute_verification_commands(run_content):
    commands = extract_nested_yaml_list(run_content, "verification", "commands")
    if commands:
        return commands

    matches = re.findall(r"(?im)^\s*command\s*:\s*(.+?)\s*$", run_content)
    return [match.strip().strip('"').strip("'") for match in matches if match.strip()]


def _print_execute_items(label, items, max_items=8):
    print(f"  {label}: {len(items)}")
    for item in items[:max_items]:
        print(f"    - {item}")
    if len(items) > max_items:
        print(f"    - ... 외 {len(items) - max_items}건")


def _execute_status_label(blockers, warnings, pass_label="pass", warn_label="warn", block_label="block"):
    if blockers:
        return block_label
    if warnings:
        return warn_label
    return pass_label


def _execute_plan(run_id, runner="native", project_dir="."):
    project_abs = os.path.abspath(project_dir)
    config = load_vulcan_config(project_abs)
    run_path = find_run_file(project_abs, run_id)
    if not run_path:
        print(f"오류: {run_id}에 해당하는 Run 문서를 찾을 수 없습니다.")
        print(f"  검색 위치: {runs_rel_dir(project_abs)}")
        sys.exit(1)

    run_abs = os.path.abspath(run_path)
    run_rel_path = os.path.relpath(run_abs, project_abs)
    current_abs = os.path.abspath(".")
    run_command_path = run_rel_path if current_abs == project_abs else run_abs
    with open(run_abs, encoding="utf-8") as f:
        run_content = f.read()
    run_meta = parse_simple_yaml_block(run_content)
    workflow_branch_guard(project_abs, run_meta.get("gate") or "", "execute", strict=False)

    run_check_issues, run_check_warnings = check_run_file(run_abs)
    preflight_blockers, preflight_warnings = run_preflight_file(run_abs)
    role = infer_execution_role(run_content, run_meta)

    selected_runner = runner or "native"
    runner_normalized = normalize_exec_runner(selected_runner)
    is_external_cli = runner_normalized in [normalize_exec_runner(name) for name in EXEC_RUNNERS]
    if selected_runner in {"native", "subagent", "thread", "native-branch", "agy-branch-agent"}:
        runner_mode = "native-delegation"
        runner_detail = selected_runner
    elif is_external_cli:
        runner_mode = "external-cli"
        runner_detail = runner_normalized
    else:
        runner_mode = "custom-native"
        runner_detail = selected_runner

    sidecar_rel_path = normalize_repo_path(os.path.join(".vulcan", "delegations", f"{run_id}.json"))
    writable_scope = extract_nested_yaml_list(run_content, "scope", "writable")
    readonly_scope = extract_nested_yaml_list(run_content, "scope", "readonly")
    verification_commands = _execute_verification_commands(run_content)

    runner_config = runtime_runner_config(config, runner_detail) if runner_mode == "external-cli" else {}
    model = runner_config.get("model") or "-"
    effort = runner_config.get("effort") or runner_config.get("reasoning_effort") or "-"
    sandbox = runner_config.get("sandbox") or "-"

    sidecar_candidate = {
        "path": sidecar_rel_path,
        "run_id": run_id,
        "mode": runner_detail,
        "status": "delegated",
        "task": run_meta.get("title") or run_meta.get("skill") or "",
        "changed_files": [],
        "self_check": [],
        "orchestrator_verification": [],
        "note": "candidate only; create/update when native delegation actually starts",
    }

    planned_flow = [
        f'python vulcan.py run-preflight "{run_command_path}"',
        f"record delegation sidecar candidate: {sidecar_rel_path}",
    ]
    if runner_mode == "external-cli":
        planned_flow.extend([
            f"from project_dir, execute external runner: python vulcan.py run-exec --run-id {run_id} --runner {runner_detail}",
            f"from project_dir, inspect worker diff: python vulcan.py run-integrate --run-id {run_id} --runner {runner_detail} --dry-run",
        ])
    else:
        planned_flow.extend([
            f"delegate to {runner_detail} and require delegation_records or sidecar update",
            "collect changed_files/self_check from worker result",
        ])
    planned_flow.extend([
        "Orchestrator reruns the Run-specific verification commands",
        f'python vulcan.py run-check "{run_command_path}"',
        "update delegation status to verified/needs_review/blocked after Orchestrator verification",
    ])

    return {
        "run_id": run_id,
        "project_dir": project_abs,
        "run_file": normalize_repo_path(run_rel_path),
        "gate": run_meta.get("gate") or "",
        "profile": run_meta.get("profile") or load_delivery_profile(project_abs),
        "skill": run_meta.get("skill") or "",
        "inferred_role": role,
        "runner_mode": runner_mode,
        "selected_runner": runner_detail,
        "runner": {
            "model": model if runner_mode == "external-cli" else "",
            "reasoning_effort": effort if runner_mode == "external-cli" else "",
            "sandbox": sandbox if runner_mode == "external-cli" else "",
        },
        "delegation_sidecar": sidecar_candidate,
        "run_check": {
            "status": _execute_status_label(run_check_issues, run_check_warnings, block_label="fail"),
            "issues": run_check_issues,
            "warnings": run_check_warnings,
        },
        "preflight": {
            "status": _execute_status_label(preflight_blockers, preflight_warnings),
            "blockers": preflight_blockers,
            "warnings": preflight_warnings,
        },
        "scope": {
            "writable": writable_scope,
            "readonly": readonly_scope,
        },
        "verification": {
            "commands": verification_commands,
        },
        "planned_flow": planned_flow,
        "exit_code": 1 if run_check_issues or preflight_blockers else 0,
    }


def cmd_execute(run_id, runner="native", dry_run=False, project_dir=".", emit_json=False):
    plan = _execute_plan(run_id, runner=runner, project_dir=project_dir)

    if emit_json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        if not dry_run:
            print("오류: execute MVP는 현재 --dry-run만 지원합니다.", file=sys.stderr)
            sys.exit(1)
        if plan["exit_code"]:
            sys.exit(plan["exit_code"])
        return

    print("Vulcan execute dry-run")
    print(f"  run_id: {plan['run_id']}")
    print(f"  project_dir: {plan['project_dir']}")
    print(f"  run_file: {plan['run_file']}")
    print(f"  gate: {plan.get('gate') or '-'}")
    print(f"  profile: {plan.get('profile') or '-'}")
    print(f"  skill: {plan.get('skill') or '-'}")
    print(f"  inferred_role: {plan.get('inferred_role') or '-'}")
    print(f"  runner_mode: {plan['runner_mode']}")
    print(f"  selected_runner: {plan['selected_runner']}")
    if plan["runner_mode"] == "external-cli":
        print(f"  runner_model: {plan['runner']['model'] or '-'}")
        print(f"  runner_effort: {plan['runner']['reasoning_effort'] or '-'}")
        print(f"  runner_sandbox: {plan['runner']['sandbox'] or '-'}")
    print(f"  delegation_sidecar: {plan['delegation_sidecar']['path']}")
    print(f"  run_check: {plan['run_check']['status']}")
    print(f"  preflight: {plan['preflight']['status']}")

    _print_execute_items("scope.writable", plan["scope"]["writable"])
    _print_execute_items("scope.readonly", plan["scope"]["readonly"], max_items=5)
    _print_execute_items("verification.commands", plan["verification"]["commands"])

    if plan["run_check"]["warnings"]:
        print("\nRun-check warnings:")
        for warning in plan["run_check"]["warnings"]:
            print(f"  - {warning}")
    if plan["run_check"]["issues"]:
        print("\nRun-check blockers:")
        for issue in plan["run_check"]["issues"]:
            print(f"  - {issue}")
    if plan["preflight"]["warnings"]:
        print("\nPreflight warnings:")
        for warning in plan["preflight"]["warnings"]:
            print(f"  - {warning}")
    if plan["preflight"]["blockers"]:
        print("\nPreflight blockers:")
        for blocker in plan["preflight"]["blockers"]:
            print(f"  - {blocker}")

    print("\nPlanned flow:")
    for index, item in enumerate(plan["planned_flow"], start=1):
        print(f"  {index}. {item}")

    if not dry_run:
        print("\n오류: execute MVP는 현재 --dry-run만 지원합니다.")
        print("  실제 실행은 native 위임을 수동 수행하거나 run-exec/agent-run 원자 명령을 사용하세요.")
        sys.exit(1)

    if plan["exit_code"]:
        sys.exit(plan["exit_code"])


def cmd_run_exec(
    run_id,
    runner=None,
    model=None,
    reasoning_effort=None,
    timeout_seconds=None,
    sandbox=None,
    create_worktree=None,
    worktree_dir="",
    branch_name="",
    allow_dirty=False,
    dry_run=False,
    project_dir=".",
):
    project_abs = os.path.abspath(project_dir)
    config = load_vulcan_config(project_abs)
    execution_config = config.get("execution", {}) if isinstance(config.get("execution"), dict) else {}

    run_path = find_run_file(project_abs, run_id)
    if not run_path:
        print(f"오류: {run_id}에 해당하는 Run 문서를 찾을 수 없습니다.")
        print(f"  검색 위치: {runs_rel_dir(project_abs)}")
        sys.exit(1)

    run_abs = os.path.abspath(run_path)
    run_rel_path = os.path.relpath(run_abs, project_abs)
    with open(run_abs, encoding="utf-8") as f:
        run_content = f.read()
    run_meta = parse_simple_yaml_block(run_content)
    workflow_branch_guard(project_abs, run_meta.get("gate") or "", "run-exec", strict=not dry_run)

    run_preflight_or_exit(run_abs, context="run-exec")

    role = infer_execution_role(run_content, run_meta)
    runner = runner or runtime_role_runner(config, role)
    runner_normalized = normalize_exec_runner(runner)
    if runner_normalized not in [normalize_exec_runner(name) for name in EXEC_RUNNERS]:
        print(f"오류: run-exec에서 아직 지원하지 않는 runner입니다: {runner}")
        print("현재 지원 runner: codex-cli, claude-cli, antigravity-cli")
        sys.exit(1)

    runner_config = runtime_runner_config(config, runner_normalized)
    model_resolution = {
        "model_source": runner_model_source(runner_normalized),
        "effort_source": "runner-config",
        "policy_role": "",
    }
    if runner_normalized == "codex-cli":
        model, reasoning_effort, model_resolution = resolve_codex_model_effort(
            config,
            role,
            explicit_model=model,
            explicit_effort=reasoning_effort,
            runner_config=runner_config,
        )
    elif runner_normalized == "claude-cli":
        model = model or runner_config.get("model") or "claude-opus-4-7"
        reasoning_effort = (
            reasoning_effort
            or runner_config.get("effort")
            or runner_config.get("reasoning_effort")
            or "high"
        )
    else:
        model = model or runner_config.get("model") or "gemini-3.5-flash"
        reasoning_effort = (
            reasoning_effort
            or runner_config.get("effort")
            or runner_config.get("reasoning_effort")
            or "high"
        )
    sandbox = sandbox or runner_config.get("sandbox") or "workspace-write"
    timeout_seconds = int(timeout_seconds or execution_config.get("default_timeout_seconds", 2400))
    hard_timeout_seconds = int(execution_config.get("hard_timeout_seconds") or max(timeout_seconds, 5400))
    extension_seconds = int(execution_config.get("extension_seconds") or 0)
    max_extensions = int(execution_config.get("max_extensions") or 0)
    progress_grace_seconds = int(execution_config.get("progress_grace_seconds") or 300)
    progress_probe_seconds = int(execution_config.get("progress_probe_seconds") or 0)
    no_progress_timeout_seconds = int(execution_config.get("no_progress_timeout_seconds") or 0)
    min_runtime_seconds = int(execution_config.get("min_runtime_seconds") or 120)

    explicit_worktree_arg = create_worktree is not None
    if create_worktree is None:
        create_worktree = bool(execution_config.get("default_worktree", True))

    qa_stage_hint = qa_stage_from_run(run_content, run_meta) if is_gate4_qa_execution_run(run_meta, run_content) else ""
    if qa_stage_hint and not explicit_worktree_arg and not bool(workflow_policy(project_abs).get("qa_worktree_enabled", False)):
        create_worktree = False

    qa_stage, qa_reuse_worktree_path, qa_reuse_branch = resolve_gate4_qa_workspace(
        project_abs,
        run_id=run_id,
        run_meta=run_meta,
        run_content=run_content,
        create_worktree=create_worktree,
        worktree_dir=worktree_dir,
    )

    dirty_status = git_status_porcelain(project_abs)
    blocking_dirty = has_blocking_dirty_status(project_abs)
    if create_worktree and not qa_reuse_worktree_path and blocking_dirty and not allow_dirty and not dry_run:
        print("오류: 현재 worktree에 미커밋 변경이 있어 실행 worktree를 만들 수 없습니다.")
        print("  run-exec worktree는 HEAD 기준으로 생성되므로 미커밋 변경이 누락될 수 있습니다.")
        print("  먼저 커밋하거나, 위험을 이해했다면 --allow-dirty를 사용하세요.")
        sys.exit(1)

    exec_dir = project_abs
    worktree_path = ""
    execution_branch = ""
    if create_worktree:
        if qa_reuse_worktree_path:
            worktree_path = qa_reuse_worktree_path
            execution_branch = qa_reuse_branch
        elif qa_stage == "QA-000":
            worktree_path = worktree_dir or default_qa_worktree_path(project_abs)
            execution_branch = branch_name or default_execution_branch(run_id, runner_normalized)
        else:
            worktree_path = worktree_dir or default_execution_worktree_path(project_abs, run_id, runner_normalized)
            execution_branch = branch_name or default_execution_branch(run_id, runner_normalized)
        exec_dir = os.path.abspath(worktree_path)

    exec_run_abs = os.path.abspath(os.path.join(exec_dir, run_rel_path))

    exec_rel_dir = execution_rel_dir(project_abs)
    log_slug = runner_log_slug(runner_normalized)
    log_ext = runner_log_ext(runner_normalized)
    log_rel_path = os.path.join(exec_rel_dir, f"{run_id}_{log_slug}-exec.{log_ext}")
    stderr_rel_path = os.path.join(exec_rel_dir, f"{run_id}_{log_slug}-exec.stderr.txt")
    last_message_rel_path = os.path.join(exec_rel_dir, f"{run_id}_{log_slug}-last-message.md")
    summary_rel_path = os.path.join(exec_rel_dir, f"{run_id}_{log_slug}-summary.json")
    status_rel_path = agent_status_rel_path(project_abs, run_id, runner_normalized)
    log_abs = os.path.abspath(os.path.join(project_abs, log_rel_path))
    stderr_abs = os.path.abspath(os.path.join(project_abs, stderr_rel_path))
    last_message_abs = os.path.abspath(os.path.join(project_abs, last_message_rel_path))
    summary_abs = os.path.abspath(os.path.join(project_abs, summary_rel_path))
    status_abs = os.path.abspath(os.path.join(project_abs, status_rel_path))
    worker_env, dependency_cache = worker_dependency_cache_env(project_abs)

    prompt = f"""You are executing a worker Run for Vulcan-Anvil Ex right now.

This is not a preparation request. Do not answer that you will work later.
You must read the Run document, perform the requested work in this run, and update the Run document before exiting.
If you cannot update the Run document, write blocked/failed details in the Run document and final response.

Working directory:
{exec_dir}

Read and execute this Run document:
{run_rel_path}

Update this worker status file at start and whenever the phase changes:
{status_abs}

Rules:
- You are a worker runner, not the Orchestrator.
- Use the Run document, source_documents, completion_criteria, verification, and scope as your contract.
- Modify only files allowed by the Run document's writable scope.
- Do not perform Gate transitions.
- Do not edit session current_gate, gate_status, completed gate state, or final approval state.
- Do not make merge, release, or final acceptance decisions.
- Do not mark user approval unless explicit user approval evidence already exists.
- If frontend dependencies or Playwright are needed, use the provided worker cache paths.
- Worker worktree npm/build/Playwright execution is a best-effort self-check, not the final UI or QA verdict.
- If npm install/npm ci/npx playwright install fails because of permission, registry, auth, network, or cache access, do not hide it and do not call the implementation failed by itself. Record verification as not_run or environment_blocked with the failing command, cwd, exit code, log path, and the exact Orchestrator rerun command.
- If npm run dev/build or Playwright cannot run in the worker worktree, report it as environment_blocked/not_run when appropriate. Final UI/Playwright evidence is produced from the configured integration branch workspace or the QA-000 QA workspace during Gate 4.
- Record your work in the Run document: changed_files, verification_results, evidence, traceability_updates, open_issues, and orchestrator_decision_needed.
- Do not rely on wall-clock timers. Update the status file when you start, after loading context, while editing, while testing, while writing the result, and when completed/blocked/failed.
- Keep status.current_task to one short dashboard line, 80 characters or fewer.
- Status JSON shape: {{"target_id":"{run_id}","target_type":"run","runner":"{runner_normalized}","status":"running","phase":"editing","current_task":"Backend tests running","last_update":"<ISO time>"}}.
- In your final response, summarize changed files, verification commands/results, and any Orchestrator decision needed.
{f"- Gate 4 QA stage: {qa_stage}. Use the current working directory as the single QA workspace for this stage." if qa_stage else ""}
{f"- QA workspace continuity is required: QA-001, QA-002, and QA-003 must use the QA-000 workspace path recorded by the Orchestrator. The default QA workspace is the current integration branch working directory. Do not create or switch to a different QA workspace." if qa_stage else ""}

Worker dependency cache:
- npm_config_cache={dependency_cache["npm_config_cache"]}
- PLAYWRIGHT_BROWSERS_PATH={dependency_cache["PLAYWRIGHT_BROWSERS_PATH"]}
"""

    if runner_normalized == "codex-cli":
        runner_exe = shutil.which("codex")
        if not runner_exe:
            print("오류: codex CLI를 찾을 수 없습니다. `codex --version`이 실행되는지 확인하세요.")
            sys.exit(1)
        cmd = [
            runner_exe,
            "-a",
            "never",
            "exec",
            "--cd",
            exec_dir,
            "--add-dir",
            project_abs,
            "-m",
            model,
            "-c",
            f"model_reasoning_effort={format_yaml_scalar(reasoning_effort)}",
            "--sandbox",
            sandbox,
            "--json",
            "--output-last-message",
            last_message_abs,
            prompt,
        ]
    elif runner_normalized == "claude-cli":
        runner_exe = shutil.which("claude")
        if not runner_exe:
            print("오류: Claude CLI를 찾을 수 없습니다. `claude --version`이 실행되는지 확인하세요.")
            sys.exit(1)
        cmd = [
            runner_exe,
            "-p",
            prompt,
            "--add-dir",
            project_abs,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--effort",
            reasoning_effort,
            "--dangerously-skip-permissions",
        ]
        if model:
            cmd.extend(["--model", model])
    else:
        runner_exe = antigravity_executable()
        if not runner_exe:
            print("오류: Antigravity headless CLI(agy.exe)를 찾을 수 없습니다. `agy.exe --help`가 실행되는지 확인하세요.")
            sys.exit(1)
        prompt = f"""Antigravity/Gemini runner settings:
- Requested model: {model}
- Requested reasoning effort: {reasoning_effort}
- Model source: inherit current Antigravity CLI configuration

{prompt}
"""
        cmd = [
            runner_exe,
            "--add-dir",
            exec_dir,
            "--add-dir",
            project_abs,
            "--log-file",
            log_abs,
            "--print-timeout",
            f"{timeout_seconds}s",
        ]
        if sandbox == "read-only":
            cmd.append("--sandbox")
        else:
            cmd.append("--dangerously-skip-permissions")
        cmd.extend(["--print", prompt])

    printable_cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd)
    if dry_run:
        print("Run execution dry-run")
        print(f"  run_id: {run_id}")
        print(f"  run_file: {run_rel_path}")
        print(f"  inferred_role: {role}")
        print(f"  runner: {runner_normalized}")
        print(f"  model: {model or '(runner default)'}")
        print(f"  reasoning_effort: {reasoning_effort}")
        print(f"  model_source: {model_resolution.get('model_source')}")
        print(f"  effort_source: {model_resolution.get('effort_source')}")
        if model_resolution.get("policy_role"):
            print(f"  model_policy_role: {model_resolution.get('policy_role')}")
        if model_resolution.get("model_fallback_reason"):
            print(f"  model_fallback_reason: {model_resolution.get('model_fallback_reason')}")
        if runner_normalized == "antigravity-cli":
            print("  model_source: agy-config-inherited")
            print("  note: Antigravity CLI의 현재 모델/effort 설정을 상속합니다.")
        print(f"  sandbox: {sandbox}")
        print(f"  timeout_seconds: {timeout_seconds}")
        print(f"  hard_timeout_seconds: {hard_timeout_seconds}")
        print(f"  extension_seconds: {extension_seconds}")
        print(f"  max_extensions: {max_extensions}")
        print(f"  progress_probe_seconds: {progress_probe_seconds}")
        print(f"  no_progress_timeout_seconds: {no_progress_timeout_seconds}")
        print(f"  min_runtime_seconds: {min_runtime_seconds}")
        print(f"  npm_config_cache: {dependency_cache['npm_config_cache']}")
        print(f"  PLAYWRIGHT_BROWSERS_PATH: {dependency_cache['PLAYWRIGHT_BROWSERS_PATH']}")
        print(f"  worktree: {str(create_worktree).lower()}")
        if qa_stage and not create_worktree:
            print(f"  qa_stage: {qa_stage}")
            print("  qa_workspace_mode: integration-workspace")
            print(f"  qa_workspace_path: {qa_reuse_worktree_path or exec_dir}")
        if create_worktree:
            print(f"  worktree_path: {worktree_path}")
            print(f"  branch: {execution_branch}")
            if qa_stage:
                print(f"  qa_stage: {qa_stage}")
                print(f"  qa_workspace_mode: {'reuse' if qa_reuse_worktree_path else 'create'}")
            if not qa_reuse_worktree_path and blocking_dirty and not allow_dirty:
                print("  warning: current worktree is dirty; non-dry-run would require commit or --allow-dirty")
        print(f"  command: {printable_cmd}")
        return

    if create_worktree and not qa_reuse_worktree_path:
        worktree_path, execution_branch = create_execution_worktree(
            project_abs,
            run_id,
            runner_normalized,
            branch_name=execution_branch,
            worktree_dir=worktree_path,
        )
        exec_dir = worktree_path
        exec_run_abs = os.path.abspath(os.path.join(exec_dir, run_rel_path))
        if qa_stage == "QA-000":
            save_qa_workspace_state(
                project_abs,
                stage=qa_stage,
                run_id=run_id,
                worktree_path=worktree_path,
                branch=execution_branch,
                status="preparing",
            )
            print(f"  QA workspace prepared: {worktree_path}")
    elif qa_reuse_worktree_path:
        exec_dir = qa_reuse_worktree_path
        exec_run_abs = os.path.abspath(os.path.join(exec_dir, run_rel_path))
        sync_run_file_to_execution_workspace(run_abs, exec_run_abs, exec_dir, run_rel_path)
        save_qa_workspace_state(
            project_abs,
            stage=qa_stage,
            run_id=run_id,
            worktree_path=qa_reuse_worktree_path,
            branch=execution_branch,
            status="active",
        )
        print(f"  QA workspace reused: {qa_reuse_worktree_path}")

    if not os.path.exists(exec_run_abs):
        print(f"오류: 실행 위치에서 Run 문서를 찾을 수 없습니다: {exec_run_abs}")
        sys.exit(1)

    os.makedirs(os.path.dirname(log_abs), exist_ok=True)

    before_hash = file_sha256(exec_run_abs)
    started_dt = datetime.now()
    deadline_dt = started_dt + timedelta(seconds=timeout_seconds)
    started_at = started_dt.isoformat(timespec="seconds")
    deadline_at = deadline_dt.isoformat(timespec="seconds")
    initial_timeout_policy = build_timeout_policy_payload(
        timeout_seconds,
        hard_timeout_seconds=hard_timeout_seconds,
        extension_seconds=extension_seconds,
        max_extensions=max_extensions,
        progress_probe_seconds=progress_probe_seconds,
        no_progress_timeout_seconds=no_progress_timeout_seconds,
        min_runtime_seconds=min_runtime_seconds,
        started_at=started_at,
    )
    activity = {
        "target_type": "run",
        "target_id": run_id,
        "run_id": run_id,
        "run_file": run_rel_path.replace("\\", "/"),
        "inferred_role": role,
        "status": "running",
        "runner": runner_normalized,
        "model": model or "(runner default)",
        "reasoning_effort": reasoning_effort,
        "model_source": model_resolution.get("model_source") or runner_model_source(runner_normalized),
        "effort_source": model_resolution.get("effort_source") or "",
        "model_policy_role": model_resolution.get("policy_role") or "",
        "model_fallback_reason": model_resolution.get("model_fallback_reason") or "",
        "sandbox": sandbox,
        "exec_dir": exec_dir,
        "worktree_path": worktree_path or None,
        "branch": execution_branch or None,
        "started_at": started_at,
        "deadline_at": deadline_at,
        "timeout_seconds": timeout_seconds,
        "hard_timeout_seconds": hard_timeout_seconds,
        "extension_seconds": extension_seconds,
        "max_extensions": max_extensions,
        "progress_probe_seconds": progress_probe_seconds,
        "no_progress_timeout_seconds": no_progress_timeout_seconds,
        "min_runtime_seconds": min_runtime_seconds,
        "timeout_policy": initial_timeout_policy,
        "timed_out": False,
        "log": log_rel_path.replace("\\", "/"),
        "stderr_log": stderr_rel_path.replace("\\", "/"),
        "last_message": last_message_rel_path.replace("\\", "/"),
        "summary": summary_rel_path.replace("\\", "/"),
        "status_file": status_rel_path.replace("\\", "/"),
        "dependency_cache": dependency_cache,
    }
    append_agent_event(activity, "started", f"{run_id} worker 실행 시작", status="running")
    activity_rel_path = write_agent_activity(project_abs, activity)
    write_agent_status(project_abs, {
        "target_type": "run",
        "target_id": run_id,
        "run_id": run_id,
        "runner": runner_normalized,
        "status": "running",
        "phase": "started",
        "current_task": f"{run_id} worker 실행 시작",
        "started_at": started_at,
        "deadline_at": deadline_at,
        "hard_timeout_seconds": hard_timeout_seconds,
        "extension_seconds": extension_seconds,
        "max_extensions": max_extensions,
        "progress_probe_seconds": progress_probe_seconds,
        "no_progress_timeout_seconds": no_progress_timeout_seconds,
        "min_runtime_seconds": min_runtime_seconds,
        "timeout_policy": initial_timeout_policy,
        "exec_dir": exec_dir,
        "worktree_path": worktree_path or None,
        "branch": execution_branch or None,
        "status_file": status_rel_path,
        "dependency_cache": dependency_cache,
    })
    exit_code, stdout, stderr, timed_out, timeout_meta = run_command_with_status_heartbeat(
        cmd=cmd,
        cwd=exec_dir,
        timeout_seconds=timeout_seconds,
        hard_timeout_seconds=hard_timeout_seconds,
        extension_seconds=extension_seconds,
        max_extensions=max_extensions,
        progress_grace_seconds=progress_grace_seconds,
        progress_probe_seconds=progress_probe_seconds,
        no_progress_timeout_seconds=no_progress_timeout_seconds,
        min_runtime_seconds=min_runtime_seconds,
        project_dir=project_abs,
        status_payload={
            "target_type": "run",
            "target_id": run_id,
            "run_id": run_id,
            "runner": runner_normalized,
            "deadline_at": deadline_at,
            "started_at": started_at,
            "exec_dir": exec_dir,
            "worktree_path": worktree_path or None,
            "branch": execution_branch or None,
            "status_file": status_rel_path,
            "dependency_cache": dependency_cache,
        },
        current_task=f"{run_id} {runner_normalized} 응답 대기 중",
        on_stdout_line=make_runner_resume_capture(
            project_abs,
            activity,
            f"{run_id} {runner_normalized} 세션 연결됨",
        ),
        tail_file_path=log_abs if runner_normalized == "antigravity-cli" else None,
        on_tail_line=make_runner_resume_capture(
            project_abs,
            activity,
            f"{run_id} {runner_normalized} 로그 수신 중",
        ) if runner_normalized == "antigravity-cli" else None,
        env=worker_env,
    )
    completed_dt = datetime.now()
    completed_at = completed_dt.isoformat(timespec="seconds")
    duration_seconds = int((completed_dt - started_dt).total_seconds())

    changed_status = git_status_porcelain(exec_dir)
    changed_files = parse_git_status_files(changed_status)
    after_hash = file_sha256(exec_run_abs)
    run_file_changed = bool(before_hash and after_hash and before_hash != after_hash)

    agy_probe = antigravity_transcript_probe(log_abs) if runner_normalized == "antigravity-cli" else {}
    empty_output = (
        runner_normalized == "antigravity-cli"
        and runner_empty_output(stdout, stderr)
        and not agy_probe.get("has_transcript_response")
    )
    if timed_out:
        run_status = "timeout"
    elif exit_code != 0:
        run_status = "failed"
    elif empty_output and not run_file_changed:
        run_status = "failed_empty_output"
    elif not run_file_changed:
        run_status = "completed_no_result_change"
    else:
        run_status = "completed"
    activity.update({
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "timed_out": timed_out,
        "status": run_status,
        "exit_code": exit_code,
        "empty_output": empty_output,
        "run_file_changed": run_file_changed,
        "changed_files": changed_files,
        "timeout_policy": timeout_meta,
    })
    activity.update(collect_runner_log_updates(runner_normalized, log_abs))
    activity.update(runner_resume_info(runner_normalized, stdout))
    if runner_normalized == "antigravity-cli" and agy_probe:
        if agy_probe.get("conversation_id"):
            activity.update({
                "conversation_id": agy_probe["conversation_id"],
                "resume_supported": True,
                "resume_hint": f"agy.exe --conversation {agy_probe['conversation_id']}",
            })
        if agy_probe.get("transcript_path"):
            activity["transcript"] = project_display_path(project_abs, agy_probe["transcript_path"])
            activity["transcript_response_detected"] = bool(agy_probe.get("has_transcript_response"))
    append_agent_event(
        activity,
        "completed" if run_status == "completed" else run_status,
        f"{run_id} worker 결과 작성 완료" if run_file_changed or changed_files else f"{run_id} 변경 없음",
        status=run_status,
    )
    write_agent_activity(project_abs, activity)
    write_agent_status(project_abs, {
        "target_type": "run",
        "target_id": run_id,
        "run_id": run_id,
        "runner": runner_normalized,
        "status": run_status,
        "phase": "completed" if run_status == "completed" else run_status,
        "current_task": (
            f"{run_id} worker 결과 작성 완료"
            if run_file_changed or changed_files
            else f"{run_id} 변경 없음"
        ),
        "started_at": started_at,
        "deadline_at": deadline_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "exec_dir": exec_dir,
        "worktree_path": worktree_path or None,
        "branch": execution_branch or None,
        "status_file": status_rel_path,
        "run_file_changed": run_file_changed,
        "changed_files": changed_files,
        "exit_code": exit_code,
        "timeout_policy": timeout_meta,
        **runner_log_identity_fields(collect_runner_log_updates(runner_normalized, log_abs)),
        **runner_resume_info(runner_normalized, stdout),
    })

    if runner_normalized == "antigravity-cli":
        if stdout.strip():
            with open(log_abs, "a", encoding="utf-8") as f:
                f.write("\n\n--- stdout ---\n")
                f.write(stdout)
    else:
        with open(log_abs, "w", encoding="utf-8") as f:
            f.write(stdout)
    with open(stderr_abs, "w", encoding="utf-8") as f:
        f.write(stderr)
    if runner_normalized in ("claude-cli", "antigravity-cli"):
        last_message_text = runner_last_message(runner_normalized, stdout)
        if runner_normalized == "antigravity-cli" and not (last_message_text or "").strip():
            last_message_text = agy_probe.get("transcript_message") or ""
        with open(last_message_abs, "w", encoding="utf-8") as f:
            f.write(last_message_text)

    if qa_stage:
        if qa_stage == "QA-000":
            qa_status = "ready" if run_status in ("completed", "completed_no_result_change") else "blocked"
        else:
            qa_status = "active" if run_status in ("completed", "completed_no_result_change") else "blocked"
        save_qa_workspace_state(
            project_abs,
            stage=qa_stage,
            run_id=run_id,
            worktree_path=worktree_path or exec_dir,
            branch=execution_branch or git_current_branch(exec_dir),
            status=qa_status,
        )

    if os.path.normcase(exec_run_abs) != os.path.normcase(run_abs) and os.path.exists(exec_run_abs):
        shutil.copy2(exec_run_abs, run_abs)

    summary = {
        "run_id": run_id,
        "run_file": run_rel_path.replace("\\", "/"),
        "executed_at": started_at,
        "deadline_at": deadline_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "timeout_seconds": timeout_seconds,
        "timed_out": timed_out,
        "timeout_policy": timeout_meta,
        "status": run_status,
        "runner": runner_normalized,
        "model": model or "(runner default)",
        "reasoning_effort": reasoning_effort,
        "model_source": model_resolution.get("model_source") or runner_model_source(runner_normalized),
        "effort_source": model_resolution.get("effort_source") or "",
        "model_policy_role": model_resolution.get("policy_role") or "",
        "model_fallback_reason": model_resolution.get("model_fallback_reason") or "",
        "sandbox": sandbox,
        "exec_dir": exec_dir,
        "worktree_path": worktree_path or None,
        "branch": execution_branch or None,
        "exit_code": exit_code,
        "empty_output": empty_output,
        "json_log": log_rel_path.replace("\\", "/"),
        "stderr_log": stderr_rel_path.replace("\\", "/"),
        "last_message": last_message_rel_path.replace("\\", "/"),
        "activity": activity_rel_path.replace("\\", "/"),
        "status_file": status_rel_path.replace("\\", "/"),
        "dependency_cache": dependency_cache,
        "run_file_changed": run_file_changed,
        "changed_files": changed_files,
    }
    if runner_normalized == "antigravity-cli" and agy_probe:
        summary["transcript"] = project_display_path(project_abs, agy_probe.get("transcript_path") or "")
        summary["transcript_response_detected"] = bool(agy_probe.get("has_transcript_response"))
    with open(summary_abs, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    execution_note = f"""

## Run Execution Record

```yaml
executed_at: {started_at}
deadline_at: {deadline_at}
completed_at: {completed_at}
duration_seconds: {duration_seconds}
timeout_seconds: {timeout_seconds}
hard_timeout_seconds: {timeout_meta.get("hard_timeout_seconds")}
extension_seconds: {timeout_meta.get("extension_seconds")}
max_extensions: {timeout_meta.get("max_extensions")}
extensions_used: {timeout_meta.get("extensions_used")}
timeout_reason: {timeout_meta.get("timeout_reason") or ""}
timed_out: {str(timed_out).lower()}
empty_output: {str(empty_output).lower()}
status: {run_status}
runner: {runner_normalized}
model: {model or "(runner default)"}
reasoning_effort: {reasoning_effort}
model_source: {model_resolution.get("model_source") or runner_model_source(runner_normalized)}
effort_source: {model_resolution.get("effort_source") or ""}
model_policy_role: {model_resolution.get("policy_role") or ""}
model_fallback_reason: {model_resolution.get("model_fallback_reason") or ""}
sandbox: {sandbox}
exec_dir: {exec_dir}
worktree_path: {worktree_path or ""}
branch: {execution_branch or ""}
exit_code: {exit_code}
json_log: {log_rel_path}
stderr_log: {stderr_rel_path}
last_message: {last_message_rel_path}
summary: {summary_rel_path}
activity: {activity_rel_path}
npm_config_cache: {dependency_cache["npm_config_cache"]}
PLAYWRIGHT_BROWSERS_PATH: {dependency_cache["PLAYWRIGHT_BROWSERS_PATH"]}
run_file_changed: {str(run_file_changed).lower()}
transcript: {project_display_path(project_abs, agy_probe.get("transcript_path") or "") if runner_normalized == "antigravity-cli" else ""}
transcript_response_detected: {str(bool(agy_probe.get("has_transcript_response"))).lower() if runner_normalized == "antigravity-cli" else "false"}
changed_files:
{format_yaml_sequence(changed_files, indent=2)}
```
"""
    with open(run_abs, "a", encoding="utf-8") as f:
        f.write(execution_note)

    print("\nRun 실행 완료")
    print(f"  run_id: {run_id}")
    print(f"  runner: {runner_normalized}")
    print(f"  model: {model or '(runner default)'}")
    print(f"  reasoning_effort: {reasoning_effort}")
    print(f"  status: {run_status}")
    print(f"  duration_seconds: {duration_seconds}")
    print(f"  exit_code: {exit_code}")
    print(f"  empty_output: {str(empty_output).lower()}")
    print(f"  run_file_changed: {str(run_file_changed).lower()}")
    print(f"  changed_files: {len(changed_files)}")
    print(f"  summary: {summary_rel_path}")
    print(f"  activity: {activity_rel_path}")
    if worktree_path:
        print(f"  worktree: {worktree_path}")
        print(f"  branch: {execution_branch}")
    if exit_code != 0:
        print(f"오류: {runner_normalized} 실행이 비정상 종료되었습니다. stderr 로그를 확인하세요: {stderr_rel_path}")
        sys.exit(exit_code)
    if empty_output and not run_file_changed:
        print(f"오류: {runner_normalized} 실행이 exit code 0으로 종료됐지만 stdout/stderr와 Run 변경이 모두 없습니다.")
        print(f"  wrapper 또는 인증/세션 문제일 수 있습니다. 로그를 확인하세요: {log_rel_path}, {stderr_rel_path}")
        sys.exit(1)
    if not run_file_changed:
        print("경고: Run 문서 변경이 감지되지 않았습니다. runner 출력과 summary를 확인하세요.")


def cmd_run_integrate(
    run_id,
    runner=None,
    worktree_dir="",
    apply=False,
    allow_dirty=False,
    dry_run=False,
    project_dir=".",
):
    require_current_gate_for_command(project_dir, "run-integrate", ("impl", "gate4"))

    project_abs = os.path.abspath(project_dir)
    run_path = find_run_file(project_abs, run_id)
    if not run_path:
        print(f"오류: {run_id}에 해당하는 Run 문서를 찾을 수 없습니다.")
        print(f"  검색 위치: {runs_rel_dir(project_abs)}")
        sys.exit(1)

    run_abs = os.path.abspath(run_path)
    run_rel_path = os.path.relpath(run_abs, project_abs).replace("\\", "/")
    with open(run_abs, encoding="utf-8") as f:
        run_content = f.read()

    summary, summary_rel = load_latest_run_exec_summary(project_abs, run_id, runner=runner)
    summary_worktree = ""
    summary_branch = ""
    summary_runner = normalize_exec_runner(runner) if runner else ""
    if summary:
        summary_worktree = summary.get("worktree_path") or ""
        summary_branch = summary.get("branch") or ""
        summary_runner = normalize_exec_runner(summary.get("runner") or summary_runner)

    worktree_path = os.path.abspath(worktree_dir or summary_worktree or "")
    if not worktree_path or not os.path.isdir(worktree_path):
        print("오류: 통합할 worker worktree를 찾을 수 없습니다.")
        print("  --worktree-dir를 지정하거나, run-exec summary에 worktree_path가 있어야 합니다.")
        if summary_rel:
            print(f"  summary: {summary_rel}")
        sys.exit(1)

    writable_scope = extract_nested_yaml_list(run_content, "scope", "writable")
    excluded_scope = extract_nested_yaml_list(run_content, "scope", "excluded")
    if not writable_scope:
        print("오류: Run 입력 계약에서 scope.writable을 찾을 수 없습니다.")
        print(f"  run_file: {run_rel_path}")
        sys.exit(1)

    status_text = git_status_porcelain_all(worktree_path)
    entries = parse_git_status_entries(status_text)
    allowed = []
    violations = []
    config_hotfix_candidates = []
    for entry in entries:
        paths_to_check = [entry["path"]]
        if entry.get("old_path"):
            paths_to_check.append(entry["old_path"])
        excluded = any(path_matches_any_scope(path, excluded_scope) for path in paths_to_check)
        writable = all(path_matches_any_scope(path, writable_scope) for path in paths_to_check)
        classified = dict(entry)
        classified["path"] = normalize_repo_path(classified["path"])
        classified["old_path"] = normalize_repo_path(classified.get("old_path", ""))
        if excluded or not writable:
            classified["reason"] = "excluded_scope" if excluded else "outside_writable_scope"
            hotfix = classify_config_hotfix_candidate(classified["path"], worktree_path=worktree_path)
            if hotfix:
                classified["config_hotfix_candidate"] = hotfix
                config_hotfix_candidates.append(classified)
            violations.append(classified)
        else:
            allowed.append(classified)

    report_runner = summary_runner or (normalize_exec_runner(runner) if runner else "")
    report = {
        "run_id": run_id,
        "run_file": run_rel_path,
        "runner": report_runner,
        "summary": (summary_rel or "").replace("\\", "/"),
        "worktree_path": worktree_path,
        "branch": summary_branch,
        "status": "blocked_scope_violation" if violations else "ready_to_apply",
        "apply_requested": bool(apply),
        "dry_run": bool(dry_run),
        "writable_scope": writable_scope,
        "excluded_scope": excluded_scope,
        "allowed_files": allowed,
        "violations": violations,
        "config_hotfix_candidates": config_hotfix_candidates,
        "orchestrator_next_actions": [
            "위반 파일이 있으면 worker 재작업 Run 또는 FIND로 돌려보낸다.",
            "Config Hotfix 후보가 있으면 자동 승인/자동 되돌림 없이 Accept Config Hotfix, qa-fix-loop, CR, Reject 중 하나를 Orchestrator가 선택한다.",
            "허용 파일만 반영한 뒤 별도 Review/QA worker로 검수한다.",
            "추적표, session, wave-complete, check-trace는 Orchestrator 통합 단계에서 별도 처리한다.",
        ],
    }

    print("Run integration analysis")
    print(f"  run_id: {run_id}")
    print(f"  run_file: {run_rel_path}")
    print(f"  worktree: {worktree_path}")
    if summary_rel:
        print(f"  summary: {summary_rel}")
    if summary_branch:
        print(f"  branch: {summary_branch}")
    print(f"  changed_files: {len(entries)}")
    print(f"  allowed_files: {len(allowed)}")
    print(f"  violations: {len(violations)}")
    if violations:
        print("  status: blocked_scope_violation")
        for item in violations[:20]:
            print(f"    - {item['status']} {item['path']} ({item['reason']})")
        if config_hotfix_candidates:
            print("  config_hotfix_candidates:")
            for item in config_hotfix_candidates[:20]:
                candidate = item.get("config_hotfix_candidate") or {}
                print(f"    - {item['path']} [{candidate.get('classification', 'config_hotfix_candidate')}]")
                print(f"      reason: {candidate.get('reason', '')}")
                print(f"      required_decision: accept_config_hotfix | create_qa_fix_loop | escalate_to_CR | reject_or_revert")
            print("  decision_rule: do not revert automatically; do not apply silently; Orchestrator must decide.")
    else:
        print("  status: ready_to_apply")

    report_rel = run_integration_report_rel_path(project_abs, run_id)
    report_abs = os.path.join(project_abs, report_rel)
    main_dirty_before_apply = has_blocking_dirty_status(project_abs)

    if dry_run:
        print("  dry_run: true")
        print(f"  report_target: {report_rel}")
        return

    os.makedirs(os.path.dirname(report_abs), exist_ok=True)
    with open(report_abs, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  report: {report_rel}")

    if not apply:
        print("  apply: false")
        print("  다음 단계: 위반이 없으면 --apply로 허용 diff만 반영할 수 있습니다.")
        return

    if violations:
        print("오류: scope 위반 파일이 있어 적용하지 않았습니다.")
        print("  worker 재작업 또는 Run scope 조정 후 다시 실행하세요.")
        sys.exit(1)

    if main_dirty_before_apply and not allow_dirty:
        print("오류: 현재 main worktree에 미커밋 변경이 있어 적용하지 않았습니다.")
        print("  먼저 커밋하거나, 위험을 이해했다면 --allow-dirty를 사용하세요.")
        sys.exit(1)

    allowed_paths = [item["path"] for item in allowed]
    tracked_paths = []
    for item in allowed:
        if item.get("untracked"):
            continue
        if item.get("old_path"):
            tracked_paths.append(item["old_path"])
        tracked_paths.append(item["path"])
    tracked_paths = merge_unique(tracked_paths)
    untracked_paths = [item["path"] for item in allowed if item.get("untracked")]

    if tracked_paths:
        diff_result = subprocess.run(
            ["git", "diff", "--binary", "HEAD", "--"] + tracked_paths,
            cwd=worktree_path,
            check=True,
            capture_output=True,
        )
        if diff_result.stdout:
            apply_result = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", "-"],
                cwd=project_abs,
                input=diff_result.stdout,
                capture_output=True,
            )
            if apply_result.returncode != 0:
                detail = coerce_process_output(apply_result.stderr).strip()
                print(f"오류: 허용 diff 적용 실패 - {detail}")
                sys.exit(1)

    for rel_path in untracked_paths:
        src = os.path.join(worktree_path, rel_path)
        dst = os.path.join(project_abs, rel_path)
        if os.path.isdir(src):
            copy_tree(src, dst)
        elif os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    print("  apply: true")
    print(f"  applied_files: {len(allowed_paths)}")
    print("  다음 단계: Review/QA worker 검수와 Orchestrator 상태 갱신을 별도 Run으로 진행하세요.")


def cmd_agent_run(
    mode,
    target_id="",
    review_id="",
    run_id="",
    runner=None,
    model=None,
    reasoning_effort=None,
    timeout_seconds=None,
    sandbox=None,
    create_worktree=None,
    worktree_dir="",
    branch_name="",
    allow_dirty=False,
    dry_run=False,
    project_dir=".",
):
    if mode == "review":
        resolved_review_id = review_id or target_id
        if not resolved_review_id:
            print("오류: agent-run --mode review에는 --target-id RV-NNN 또는 --review-id RV-NNN이 필요합니다.")
            sys.exit(1)
        return cmd_review_run(
            review_id=resolved_review_id,
            runner=runner,
            model=model,
            reasoning_effort=reasoning_effort,
            timeout_seconds=timeout_seconds,
            sandbox=sandbox,
            dry_run=dry_run,
            project_dir=project_dir,
        )

    if mode == "work":
        resolved_run_id = run_id or target_id
        if not resolved_run_id:
            print("오류: agent-run --mode work에는 --target-id RUN-NNN 또는 --run-id RUN-NNN이 필요합니다.")
            sys.exit(1)
        return cmd_run_exec(
            run_id=resolved_run_id,
            runner=runner,
            model=model,
            reasoning_effort=reasoning_effort,
            timeout_seconds=timeout_seconds,
            sandbox=sandbox,
            create_worktree=create_worktree,
            worktree_dir=worktree_dir,
            branch_name=branch_name,
            allow_dirty=allow_dirty,
            dry_run=dry_run,
            project_dir=project_dir,
        )

    print(f"오류: 지원하지 않는 agent-run mode입니다: {mode}")
    print("현재 지원 mode: review, work")
    sys.exit(1)


def cmd_agent_resume(
    target_id,
    runner=None,
    prompt="",
    timeout_seconds=None,
    dry_run=False,
    project_dir=".",
):
    project_abs = os.path.abspath(project_dir)
    activity, activity_rel_path = load_latest_agent_activity(project_abs, target_id, runner=runner)
    if not activity:
        print(f"오류: {target_id}의 이전 agent activity를 찾을 수 없습니다.")
        print(f"  검색 위치: {execution_rel_dir(project_abs)}")
        if runner:
            print(f"  runner: {runner}")
        sys.exit(1)

    runner_normalized = normalize_exec_runner(activity.get("runner") or runner)
    if runner_normalized not in ("codex-cli", "claude-cli"):
        print(f"오류: resume은 현재 codex-cli와 claude-cli만 지원합니다: {runner_normalized}")
        sys.exit(1)

    config = load_vulcan_config(project_abs)
    execution_config = config.get("execution", {}) if isinstance(config.get("execution"), dict) else {}
    review_config = config.get("review", {}) if isinstance(config.get("review"), dict) else {}
    timeout_seconds = int(
        timeout_seconds
        or activity.get("timeout_seconds")
        or execution_config.get("default_timeout_seconds")
        or review_config_get(review_config, "exec_timeout_seconds", 1800)
    )

    target_type = activity.get("target_type") or ("review" if target_id.startswith("RV-") else "run")
    exec_dir = activity.get("exec_dir") or project_abs
    if not os.path.isdir(exec_dir):
        exec_dir = project_abs
    status_rel_path = activity.get("status_file") or agent_status_rel_path(project_abs, target_id, runner_normalized)
    status_abs = os.path.abspath(os.path.join(project_abs, status_rel_path))
    log_slug = runner_log_slug(runner_normalized)
    log_ext = runner_log_ext(runner_normalized)
    exec_rel_dir = execution_rel_dir(project_abs)
    resume_log_rel_path = os.path.join(exec_rel_dir, f"{target_id}_{log_slug}-resume.{log_ext}")
    resume_stderr_rel_path = os.path.join(exec_rel_dir, f"{target_id}_{log_slug}-resume.stderr.txt")
    resume_last_rel_path = os.path.join(exec_rel_dir, f"{target_id}_{log_slug}-resume-last-message.md")
    resume_log_abs = os.path.abspath(os.path.join(project_abs, resume_log_rel_path))
    resume_stderr_abs = os.path.abspath(os.path.join(project_abs, resume_stderr_rel_path))
    resume_last_abs = os.path.abspath(os.path.join(project_abs, resume_last_rel_path))
    os.makedirs(os.path.dirname(resume_log_abs), exist_ok=True)

    resume_prompt = prompt or f"""Resume the previous Vulcan-Anvil Ex {target_type} worker session for {target_id}.

This is not a preparation request. Continue the original task now.
Update the configured Run or review result file before exiting, or record blocked/failed details if you cannot.
Update this worker status file at start and whenever the phase changes:
{status_abs}
Keep status.current_task to one short dashboard line, 80 characters or fewer.
Do not perform Gate transitions, edit session gate state, or make final approval/merge/release decisions.
"""

    if runner_normalized == "codex-cli":
        thread_id = activity.get("thread_id") or ""
        if not thread_id:
            print(f"오류: {target_id} activity에 Codex thread_id가 없어 resume할 수 없습니다.")
            print(f"  activity: {activity_rel_path}")
            sys.exit(1)
        runner_exe = shutil.which("codex")
        if not runner_exe:
            print("오류: codex CLI를 찾을 수 없습니다. `codex --version`이 실행되는지 확인하세요.")
            sys.exit(1)
        cmd = [
            runner_exe,
            "-a",
            "never",
            "exec",
            "resume",
            thread_id,
            resume_prompt,
        ]
    else:
        runner_exe = shutil.which("claude")
        if not runner_exe:
            print("오류: Claude CLI를 찾을 수 없습니다. `claude --version`이 실행되는지 확인하세요.")
            sys.exit(1)
        session_id = activity.get("session_id") or ""
        cmd = [runner_exe]
        if session_id:
            cmd.extend(["--resume", session_id])
        else:
            cmd.append("--continue")
        cmd.extend([
            "-p",
            resume_prompt,
            "--add-dir",
            project_abs,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--dangerously-skip-permissions",
        ])

    printable_cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd)
    if dry_run:
        print("Agent resume dry-run")
        print(f"  target_id: {target_id}")
        print(f"  target_type: {target_type}")
        print(f"  runner: {runner_normalized}")
        print(f"  exec_dir: {exec_dir}")
        print(f"  activity: {activity_rel_path}")
        print(f"  status_file: {status_rel_path}")
        print(f"  command: {printable_cmd}")
        return

    started_dt = datetime.now()
    deadline_dt = started_dt + timedelta(seconds=timeout_seconds)
    started_at = started_dt.isoformat(timespec="seconds")
    deadline_at = deadline_dt.isoformat(timespec="seconds")
    activity.update({
        "status": "running",
        "resume": True,
        "resume_started_at": started_at,
        "deadline_at": deadline_at,
        "timeout_seconds": timeout_seconds,
        "exec_dir": exec_dir,
        "status_file": status_rel_path.replace("\\", "/"),
        "resume_log": resume_log_rel_path.replace("\\", "/"),
        "resume_stderr_log": resume_stderr_rel_path.replace("\\", "/"),
        "resume_last_message": resume_last_rel_path.replace("\\", "/"),
    })
    write_agent_activity(project_abs, activity)
    write_agent_status(project_abs, {
        "target_type": target_type,
        "target_id": target_id,
        "runner": runner_normalized,
        "status": "running",
        "phase": "resume",
        "current_task": f"{target_id} resume 실행 중",
        "started_at": activity.get("started_at") or started_at,
        "resume_started_at": started_at,
        "deadline_at": deadline_at,
        "exec_dir": exec_dir,
        "status_file": status_rel_path,
        "resume": True,
    })

    exit_code, stdout, stderr, timed_out, timeout_meta = run_command_with_status_heartbeat(
        cmd=cmd,
        cwd=exec_dir,
        timeout_seconds=timeout_seconds,
        project_dir=project_abs,
        status_payload={
            "target_type": target_type,
            "target_id": target_id,
            "runner": runner_normalized,
            "started_at": activity.get("started_at") or started_at,
            "resume_started_at": started_at,
            "deadline_at": deadline_at,
            "exec_dir": exec_dir,
            "status_file": status_rel_path,
            "resume": True,
        },
        current_task=f"{target_id} {runner_normalized} resume 응답 대기 중",
        on_stdout_line=make_runner_resume_capture(
            project_abs,
            activity,
            f"{target_id} {runner_normalized} resume 세션 연결됨",
        ),
    )

    completed_dt = datetime.now()
    completed_at = completed_dt.isoformat(timespec="seconds")
    duration_seconds = int((completed_dt - started_dt).total_seconds())
    with open(resume_log_abs, "w", encoding="utf-8") as f:
        f.write(stdout)
    with open(resume_stderr_abs, "w", encoding="utf-8") as f:
        f.write(stderr)
    with open(resume_last_abs, "w", encoding="utf-8") as f:
        if runner_normalized == "claude-cli":
            f.write(runner_last_message(runner_normalized, stdout))
        else:
            f.write(stdout)

    run_status = "timeout" if timed_out else ("failed" if exit_code != 0 else "completed")
    activity.update({
        "status": run_status,
        "resume_completed_at": completed_at,
        "resume_duration_seconds": duration_seconds,
        "timed_out": timed_out,
        "exit_code": exit_code,
    })
    activity.update(runner_resume_info(runner_normalized, stdout))
    write_agent_activity(project_abs, activity)
    write_agent_status(project_abs, {
        "target_type": target_type,
        "target_id": target_id,
        "runner": runner_normalized,
        "status": run_status,
        "phase": "resume_completed" if run_status == "completed" else run_status,
        "current_task": f"{target_id} resume 완료" if run_status == "completed" else f"{target_id} resume 실패",
        "started_at": activity.get("started_at") or started_at,
        "resume_started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "exec_dir": exec_dir,
        "status_file": status_rel_path,
        "resume": True,
        "exit_code": exit_code,
        **runner_resume_info(runner_normalized, stdout),
    })

    print("\nAgent resume 완료")
    print(f"  target_id: {target_id}")
    print(f"  runner: {runner_normalized}")
    print(f"  status: {run_status}")
    print(f"  duration_seconds: {duration_seconds}")
    print(f"  exit_code: {exit_code}")
    print(f"  activity: {activity_rel_path}")
    print(f"  status_file: {status_rel_path}")
    print(f"  resume_log: {resume_log_rel_path}")
    if exit_code != 0:
        print(f"오류: {runner_normalized} resume 실행이 비정상 종료되었습니다. stderr 로그를 확인하세요: {resume_stderr_rel_path}")
        sys.exit(exit_code)


def run_body_without_yaml(content):
    return re.sub(r"```yaml.*?```", "", content, flags=re.IGNORECASE | re.DOTALL)


def yaml_field_has_nonempty_items(content, key):
    inline_match = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*\[(.*?)\]\s*$", content)
    if inline_match:
        raw = inline_match.group(1).strip()
        return bool(raw)

    block_match = re.search(
        rf"(?ms)^\s*{re.escape(key)}\s*:\s*\n((?:[ \t]+.*(?:\n|$)|\s*\n)*)",
        content,
    )
    if not block_match:
        return False

    block_text = block_match.group(1)
    for item_match in re.finditer(r"(?m)^\s*-\s*(.*?)\s*$", block_text):
        item = item_match.group(1).strip().strip('"').strip("'")
        if item and item not in {"[]", "{}", "null", "~"} and not item.startswith("#"):
            return True

    return bool(re.search(r"(?m)^\s{2,}[\w_-]+\s*:\s*(?!\[\]\s*$|null\s*$|~\s*$).+", block_text))


def delegation_record_shape_warnings(content, prefix="delegation_records"):
    if "delegation_records" not in content:
        return []
    match = re.search(
        r"(?ms)^\s*delegation_records\s*:\s*\n((?:[ \t]+.*(?:\n|$)|\s*\n)*)",
        content,
    )
    if not match:
        return []
    block_text = match.group(1)
    warnings = []
    for field in (
        "mode",
        "delegate",
        "started_at",
        "completed_at",
        "duration_seconds",
        "heartbeat_count",
        "status_probe_count",
        "first_file_change_at",
        "last_file_change_at",
        "worker_final_response_at",
        "final_response_lag_seconds",
    ):
        values = re.findall(rf"(?im)^\s*{field}\s*:\s*(.*?)\s*$", block_text)
        if len(values) > 1:
            warnings.append(f"{prefix}.{field}가 중복 기록되어 있습니다. 같은 field는 한 번만 남기세요.")
        if any((value or "").strip().lower() in {"null", "~"} for value in values):
            warnings.append(f"{prefix}.{field}가 null로 기록되어 있습니다. 알 수 없으면 필드를 생략하거나 notes에 근거를 남기세요.")
    return warnings


def delegation_record_verification_warnings(content, prefix="delegation_records"):
    if "delegation_records" not in content:
        return []
    match = re.search(
        r"(?ms)^\s*delegation_records\s*:\s*\n((?:[ \t]+.*(?:\n|$)|\s*\n)*)",
        content,
    )
    if not match:
        return []

    block_text = match.group(1)
    status_values = [
        value.strip().strip('"').strip("'").lower()
        for value in re.findall(r"(?im)^\s*status\s*:\s*(.*?)\s*$", block_text)
    ]
    if not status_values:
        return []

    worker_complete_statuses = {"completed", "worker_completed", "completed_no_result_change"}
    final_statuses = {"verified", "needs_review", "blocked", "failed", "environment_blocked"}
    has_worker_completed_only = any(status in worker_complete_statuses for status in status_values)
    has_final_status = any(status in final_statuses for status in status_values)
    has_orchestrator_verification = bool(
        re.search(r"(?im)^\s*orchestrator_verification\s*:\s*(?!\[\]\s*$).+", block_text)
        or re.search(r"(?ims)^\s*orchestrator_verification\s*:\s*\n\s*-\s+", block_text)
    )

    if has_worker_completed_only and not has_final_status and not has_orchestrator_verification:
        return [
            f"{prefix}가 worker 완료 상태만 기록하고 Orchestrator 재검증 기록이 없습니다. "
            "worker_completed/completed는 검증 완료가 아니므로 orchestrator_verification을 남기거나 status를 verified/needs_review/blocked로 정리하세요."
        ]
    return []


def impl_code_result_claim(body):
    if re.search(r"구현\s*완료|implementation-complete|직접\s*구현\s*완료", body, re.IGNORECASE):
        return True

    changed_match = re.search(
        r"(?ims)(?:^#{2,4}\s*(?:\d+\.\s*)?(?:변경\s*파일|changed\s*files)|^changed_files\s*:)(.*?)(?=^#{1,4}\s|\Z)",
        body,
    )
    if changed_match and re.search(
        r"backend/|frontend/|src/main|src/test|app/|pages/|components/|package\.json|build\.gradle|pom\.xml",
        changed_match.group(1),
        re.IGNORECASE,
    ):
        return True

    verification_match = re.search(
        r"(?ims)(?:^#{2,4}\s*(?:\d+\.\s*)?(?:검증\s*결과|verification\s*results)|^verification_results\s*:)(.*?)(?=^#{1,4}\s|\Z)",
        body,
    )
    if verification_match:
        verification_text = verification_match.group(1)
        has_code_command = re.search(
            r"npm\s+run|gradlew|pytest|py_compile|browser smoke|Playwright|mvn\s+test",
            verification_text,
            re.IGNORECASE,
        )
        has_result = re.search(
            r"통과|passed|pass\b|exit[_ -]?code\s*[:=]\s*0|성공",
            verification_text,
            re.IGNORECASE,
        )
        if has_code_command and has_result:
            return True

    return False


def trace_final_state_claim(body):
    return any(
        (
            re.search(r"추적표|traceability", line, re.IGNORECASE)
            and re.search(r"\bImplemented\b|\bVerified\b|상태를\s*Pass|Pass\s*반영|확정|최종\s*반영", line, re.IGNORECASE)
            and not re.search(r"필요|후보|하지 않았다|needs?|candidate|권장|should", line, re.IGNORECASE)
        )
        or re.search(r"Pass\s*반영|상태를\s*Pass", line, re.IGNORECASE)
        for line in body.splitlines()
    )


def infer_bw_id(metadata, path="", content=""):
    bw_id = str(metadata.get("bw_id", "")).strip()
    if bw_id:
        return bw_id
    candidates = " ".join([
        os.path.basename(path or ""),
        str(metadata.get("run_id", "")),
        content[:4000],
    ])
    match = re.search(r"\b(BW-\d{3})\b", candidates, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def direct_edit_reason_present(content):
    return bool(
        re.search(
            r"(?im)^\s*(?:[-*]\s*)?(?:orchestrator_direct_edit_reason|direct\s*(?:edit|implementation)\s*reason)\s*:",
            content,
        )
        or re.search(
            r"(?im)^\s*(?:[-*]\s*)?직접\s*(?:구현|수정)\s*사유\s*[:：]",
            content,
        )
    )


def direct_edit_scope_block(content):
    match = re.search(r"(?ms)^direct_edit_scope\s*:\s*(.*?)(?=^\S|\Z)", content)
    return match.group(1).strip() if match else ""


def direct_edit_scope_file_count(scope_text):
    if not scope_text:
        return 0
    files_match = re.search(r"(?ms)files\s*:\s*(.*?)(?=^\s{0,2}\w[\w_-]*\s*:|\Z)", scope_text)
    target = files_match.group(1) if files_match else scope_text
    return len(re.findall(r"(?m)^\s*-\s+", target))


def direct_edit_scope_estimated_loc(scope_text):
    if not scope_text:
        return None
    match = re.search(r"estimated_loc\s*:\s*[\"']?(\d+)", scope_text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def direct_edit_scope_contract_changed(scope_text):
    if not scope_text:
        return None
    match = re.search(r"contract_changed\s*:\s*[\"']?(true|false|yes|no)", scope_text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() in {"true", "yes"}


def effective_run_contract_profile(project_profile, metadata=None, input_contract=None):
    metadata = metadata or {}
    input_contract = input_contract or {}
    return normalize_delivery_profile(
        metadata.get("profile")
        or input_contract.get("profile")
        or project_profile
    )


def qa_execution_source_mutation_blockers(content):
    blockers = []
    writable_block = _extract_yaml_block_text(content, "writable")
    if re.search(r"(^|\n)\s*-\s*[\"']?(backend|frontend|src|app|packages|server|client)(/|\\|\s*$)", writable_block, re.IGNORECASE):
        blockers.append("qa-execution Run writable scope에는 소스코드 경로를 포함하지 않습니다. QA worker는 증적과 결과 문서만 작성합니다.")
    if re.search(r"\bsession\.json\b", writable_block):
        blockers.append("qa-execution Run writable scope에 session.json을 포함할 수 없습니다.")

    negative_re = re.compile(
        r"하지\s*않|금지|않고|분리|후보|필요하면|qa-fix-loop|CR\s*후보|worker_can_modify_source\s*:\s*false|modify_source\s*:\s*false|do\s+not|does\s+not|must\s+not|without\s+modifying|not\s+modify",
        re.IGNORECASE,
    )
    positive_re = re.compile(
        r"(?:새\s*(?:API|메소드|method)|소스(?:코드)?|코드|source|backend|frontend|src|app).*(?:수정하|고치|패치하|추가하|생성하|구현하|변경하|\b(?:fix|modify|patch|add|create|implement|update)\b)"
        r"|(?:수정하|고치|패치하|추가하|생성하|구현하|변경하|\b(?:fix|modify|patch|add|create|implement|update)\b).*(?:새\s*(?:API|메소드|method)|소스(?:코드)?|코드|source|backend|frontend|src|app)",
        re.IGNORECASE,
    )
    for line in content.splitlines():
        if re.match(r"^\s*(summary|update|note|result|log_path|document|status)\s*:", line, re.IGNORECASE):
            continue
        if negative_re.search(line):
            continue
        if positive_re.search(line):
            blockers.append("qa-execution Run이 소스 수정 지시처럼 보입니다. 실패는 FIND/CR/ISSUE 후보로 보고하고 수정은 승인된 qa-fix-loop로 분리하세요.")
            break
    return blockers


def check_run_file(path):
    issues = []
    warnings = []
    project_dir = project_dir_for_run_file(path) or "."
    profile = load_delivery_profile(project_dir)
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(f"오류: Run 파일을 읽을 수 없습니다: {e}")
        sys.exit(1)

    for key in RUN_REQUIRED_KEYS:
        if not re.search(rf"^\s*{re.escape(key)}\s*:", content, re.MULTILINE):
            issues.append(f"필수 필드 누락: {key}")

    if not re.search(r"\b(REQ|NREQ|AC|FUNC|SCR|UIREF|UICON|PGM|DB|IF|SEC|UT|IT|PT|UI|FIND|CR|ISSUE|RUN)-\d+\b", content):
        issues.append("관련 추적 ID가 없습니다.")

    top_metadata = parse_simple_yaml_block(content)
    input_contract = parse_run_input_contract_yaml(content)
    run_contract_profile = effective_run_contract_profile(profile, top_metadata, input_contract)
    if input_contract:
        compare_fields = ["profile", "adapter", "run_type", "gate", "persona", "skill"]
        for field in compare_fields:
            top_value = str(top_metadata.get(field, "")).strip()
            input_value = str(input_contract.get(field, "")).strip()
            if top_value and input_value and top_value != input_value:
                message = f"Run 상단 metadata와 3. Run 입력 계약의 {field} 값이 다릅니다: top={top_value}, input={input_value}"
                if run_contract_profile == "poc":
                    warnings.append(message)
                else:
                    issues.append(message)

    status = ""
    status_match = re.search(r"^\s*status\s*:\s*(.+)$", content, re.MULTILINE)
    if status_match:
        status = status_match.group(1).strip()
        if status not in {"Draft", "Requested", "InProgress", "Completed", "Verified", "Blocked", "Failed", "CompletedWithIssues", "AwaitingApproval"}:
            issues.append(f"허용되지 않은 status 값: {status}")

    skill = ""
    skill_match = re.search(r"^\s*skill\s*:\s*(.+)$", content, re.MULTILINE)
    if skill_match:
        skill = skill_match.group(1).strip()
        if skill not in RUN_SKILLS:
            issues.append(f"알 수 없는 skill 값: {skill}")

    gate = ""
    gate_match = re.search(r"^\s*gate\s*:\s*(.+)$", content, re.MULTILINE)
    if gate_match:
        gate = gate_match.group(1).strip()

    run_type = ""
    run_type_match = re.search(r"^\s*run_type\s*:\s*(.+)$", content, re.MULTILINE)
    if run_type_match:
        run_type = run_type_match.group(1).strip()

    persona_match = re.search(r"^\s*persona\s*:\s*(.+)$", content, re.MULTILINE)
    if persona_match:
        persona = persona_match.group(1).strip()
        if persona not in RUN_PERSONAS:
            issues.append(f"알 수 없는 persona 값: {persona}")

    if skill == "qa-execution":
        issues.extend(qa_execution_source_mutation_blockers(content))

    if re.search(r"result\s*:\s*passed", content, re.IGNORECASE) and not re.search(r"command\s*:", content):
        issues.append("passed 결과가 있지만 검증 command가 없습니다.")

    if re.search(r"status\s*:\s*Completed", content) and re.search(r"verification_results\s*:\s*\[\]", content):
        warnings.append("Completed 상태이지만 verification_results가 비어 있습니다.")

    if re.search(r"status\s*:\s*Completed", content) and re.search(r"traceability_updates\s*:\s*\[\]", content):
        warnings.append("Completed 상태이지만 traceability_updates가 비어 있습니다.")

    has_open_issues = yaml_field_has_nonempty_items(content, "open_issues")
    if status == "Verified" and has_open_issues:
        issues.append("Verified 상태이지만 open_issues가 남아 있습니다. 미해결 항목을 닫거나 status를 CompletedWithIssues/Blocked로 낮추세요.")
    elif status == "Completed" and has_open_issues:
        warnings.append("Completed 상태이지만 open_issues가 남아 있습니다. 후속 이슈가 완료 조건에 영향을 주면 CompletedWithIssues를 사용하세요.")

    if status in {"Completed", "Verified", "CompletedWithIssues"}:
        body_without_yaml = run_body_without_yaml(content)
        if re.search(r"(?im)(^|\|)\s*(TBD|확정필요|작성필요)\s*(\||$)", body_without_yaml):
            if profile == "poc":
                if poc_tbd_decision_context_present(content):
                    warnings.append("PoC Completed Run 본문에 TBD/확정필요/작성필요가 남아 있습니다. 사유와 후속 판단 시점 기준으로 확인하세요.")
                else:
                    warnings.append("PoC Completed Run 본문에 TBD/확정필요/작성필요가 있으나 사유 또는 후속 판단 시점이 부족합니다.")
            else:
                issues.append("Completed 상태이지만 본문에 TBD/확정필요/작성필요 placeholder가 남아 있습니다.")

        is_impl_run = (
            gate == "impl"
            or run_type.lower().startswith("implementation")
            or run_type.lower() == "qafix"
            or skill == "qa-fix-loop"
        )
        has_impl_code_result = impl_code_result_claim(body_without_yaml)
        has_trace_final_claim = trace_final_state_claim(body_without_yaml)
        if is_impl_run and skill in {"implementation-plan", "orchestrator-plan"} and has_impl_code_result:
            issues.append("구현 계획/Orchestrator Plan Run이 실제 구현 완료 보고서처럼 쓰였습니다. 구현 결과는 Build Wave Run 또는 worker Run으로 분리하세요.")

        bw_id = infer_bw_id(top_metadata, path, content)
        if bw_id == "BW-000" and has_trace_final_claim:
            issues.append("BW-000 scaffold Run이 요구사항/테스트 상태를 Implemented/Verified/Pass로 확정하는 표현을 포함합니다. BW-000은 skeleton/build smoke만 보고하고 기능 구현 상태 확정은 이후 Wave 또는 Orchestrator 재검증으로 분리하세요.")

        worker_skills = {"build-wave", "implementation-scaffold", "qa-execution", "qa-fix-loop"}
        is_worker_result_run = skill in worker_skills and status in {"Completed", "Verified", "CompletedWithIssues"}
        has_delegation_records = yaml_field_has_nonempty_items(content, "delegation_records")
        has_run_execution_record = bool(re.search(r"(?im)^#{2,4}\s*Run Execution Record\b", content))
        has_native_delegation_hint = bool(re.search(r"agy-branch-agent|Workspace:\s*branch|native branch agent", content, re.IGNORECASE))
        if is_worker_result_run and has_native_delegation_hint and not has_delegation_records:
            issues.append("native/Agy worker 사용 흔적이 있지만 delegation_records가 비어 있습니다. 위임 대상, 범위, 변경 파일, 결과 요약, Orchestrator 재검증을 기록하세요.")
        elif is_worker_result_run and not has_delegation_records and not has_run_execution_record and not direct_edit_reason_present(content):
            warnings.append("완료된 worker Run이지만 delegation_records 또는 Run Execution Record가 없습니다. native 위임/외부 runner/직접 수정 중 어떤 실행 경로였는지 추적 기록을 남기세요.")
        elif is_worker_result_run and has_delegation_records:
            warnings.extend(delegation_record_shape_warnings(content))
            warnings.extend(delegation_record_verification_warnings(content))
            missing_timing = [
                field for field in ("started_at", "completed_at", "duration_seconds")
                if not re.search(rf"(?im)^\s*{field}\s*:", content)
            ]
            if missing_timing:
                warnings.append(f"delegation_records에 병목 분석용 시간 필드가 부족합니다: {', '.join(missing_timing)}.")
            if not re.search(r"(?im)^\s*(heartbeat_count|status_probe_count)\s*:", content):
                warnings.append("delegation_records에 heartbeat_count 또는 status_probe_count가 없습니다. 장시간 worker 병목 분석을 위해 기록을 권장합니다.")

        has_direct_reason = direct_edit_reason_present(content)
        if is_impl_run and has_impl_code_result and has_direct_reason:
            scope_text = direct_edit_scope_block(content)
            if not scope_text:
                warnings.append("Orchestrator 직접 구현 예외가 있지만 direct_edit_scope가 없습니다. files, estimated_loc, contract_changed, verification, followup_review_required를 남기세요.")
            else:
                file_count = direct_edit_scope_file_count(scope_text)
                estimated_loc = direct_edit_scope_estimated_loc(scope_text)
                contract_changed = direct_edit_scope_contract_changed(scope_text)
                if file_count > ORCHESTRATOR_DIRECT_EDIT_LIMITS["max_files"]:
                    issues.append(f"Orchestrator 직접 구현 예외 파일 수가 기준을 초과합니다: {file_count}>{ORCHESTRATOR_DIRECT_EDIT_LIMITS['max_files']}. Build Wave/worker Run으로 분리하세요.")
                if estimated_loc is None:
                    warnings.append("direct_edit_scope.estimated_loc가 없습니다. 직접 구현 예외의 변경량을 기록하세요.")
                elif estimated_loc > ORCHESTRATOR_DIRECT_EDIT_LIMITS["max_loc"]:
                    issues.append(f"Orchestrator 직접 구현 예외 변경량이 기준을 초과합니다: {estimated_loc}>{ORCHESTRATOR_DIRECT_EDIT_LIMITS['max_loc']} LOC. Build Wave/worker Run으로 분리하세요.")
                if contract_changed is None:
                    warnings.append("direct_edit_scope.contract_changed가 없습니다. public API/PGM/DTO/DB/security/SCR/UI 계약 변경 여부를 명시하세요.")
                elif contract_changed:
                    issues.append("Orchestrator 직접 구현 예외에서 contract_changed=true는 허용하지 않습니다. Build Wave/worker Run 또는 CR로 분리하세요.")
                if not re.search(r"followup_review_required\s*:", scope_text, re.IGNORECASE):
                    warnings.append("direct_edit_scope.followup_review_required가 없습니다. 직접 구현 후 후속 worker/review 필요 여부를 기록하세요.")

        is_audit_run = bool(re.search(r"^\s*profile\s*:\s*audit\s*$", content, re.MULTILINE))
        if is_audit_run:
            if not re.search(r"gate_exit_summary\s*:", content):
                issues.append("Audit Run 완료 상태이지만 gate_exit_summary가 없습니다.")
            if not re.search(r"approval_request\s*:", content):
                issues.append("Audit Run 완료 상태이지만 다음 Gate 승인 질문(approval_request)이 없습니다.")

        is_scaffold_run = skill == "implementation-scaffold" or run_type.lower() == "implementationscaffold"
        if not is_scaffold_run:
            has_ui_reference = bool(re.search(r"\bUI-\d{3}\b", content))
            has_state_level_ui = bool(re.search(r"\bUI-\d{3}-\d{2}\b", content))
            has_ui_evidence_context = bool(re.search(
                r"UI Evidence|화면\s*증적|actual_path|capture_tool|screenshot|캡처",
                content,
                re.IGNORECASE,
            ))
            if has_ui_reference and has_ui_evidence_context and not has_state_level_ui:
                issues.append("UI 증적이 포함된 완료 Run이지만 상태/시나리오 단위 UI-ID(UI-001-01)가 없습니다.")
            has_ui_pass_evidence = (
                has_ui_reference
                and has_ui_evidence_context
                and re.search(r"result\s*:\s*(passed|Pass)|\|\s*Pass\s*\|", content, re.IGNORECASE)
            )
            has_playwright_evidence = bool(re.search(
                r"capture_tool\s*:\s*Playwright|npx\s+playwright\s+test|playwright\s+test|Playwright.+exit code",
                content,
                re.IGNORECASE,
            ))
            if has_ui_pass_evidence and not has_playwright_evidence:
                issues.append("UI Pass 증적이 있지만 Playwright 실행 결과 또는 capture_tool: Playwright 기록이 없습니다.")
            has_official_playwright_runner = bool(re.search(
                r"@playwright/test|npx\s+(?:--yes\s+)?playwright\s+test|(?:^|\s)playwright\s+test|playwright\.config\.(?:ts|js|mjs|cjs)|playwright-report|test-results",
                content,
                re.IGNORECASE | re.MULTILINE,
            ))
            has_custom_playwright_script = bool(re.search(
                r"run-e2e\.(?:js|mjs|ts)|require\(['\"]playwright['\"]\)|from\s+['\"]playwright['\"]|page\.screenshot\s*\(",
                content,
                re.IGNORECASE,
            ))
            looks_like_official_gate4_ui_pass = bool(re.search(
                r"\b(gate4|qa-execution|QA-002|DOC-QA-G4|Audit Profile|Product Profile|Solution Profile|profile\s*:\s*(audit|product|solution))\b",
                content,
                re.IGNORECASE,
            ))
            if has_ui_pass_evidence and looks_like_official_gate4_ui_pass and not has_official_playwright_runner:
                issues.append("Gate 4 공식 UI Pass는 @playwright/test 러너 실행 결과가 필요합니다. 커스텀 Playwright script는 PoC smoke/demo 또는 보조 증적으로만 기록하세요.")
            if has_ui_pass_evidence and has_custom_playwright_script and not has_official_playwright_runner:
                issues.append("커스텀 Playwright script 기반 UI Pass가 공식 러너 증적 없이 기록되었습니다. audit/product에서는 `npx playwright test`와 report/trace/screenshot 증적을 연결하세요.")

    # JSON Schema 기반 구조화 출력(Run metadata & Output) 정합성 검증
    yaml_meta = parse_simple_yaml_block(content)
    if yaml_meta:
        # 1. 필수 문자열/필드 정밀 타입 검사
        string_fields = ["run_id", "gate", "persona", "skill", "status"]
        for sf in string_fields:
            val = yaml_meta.get(sf)
            if val is not None and not isinstance(val, str):
                issues.append(f"JSON Schema 위반: '{sf}' 필드는 문자열 타입이어야 합니다. (현재: {type(val).__name__})")

        # 2. 리스트(Array) 타입 검사
        array_fields = ["related_ids", "verification_results", "evidence", "delegation_records", "traceability_updates", "findings", "change_requests", "open_issues"]
        for af in array_fields:
            val = yaml_meta.get(af)
            if isinstance(val, str) and val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                val = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()] if inner else []
            if val is not None and not isinstance(val, list):
                issues.append(f"JSON Schema 위반: '{af}' 필드는 배열(List) 타입이어야 합니다. (현재: {type(val).__name__})")

        # 3. status가 Completed/Verified일 때, 구조화된 list item 스키마 검증
        if status in {"Completed", "Verified"}:
            v_results = yaml_meta.get("verification_results")
            if isinstance(v_results, str) and v_results.startswith("[") and v_results.endswith("]"):
                inner = v_results[1:-1].strip()
                v_results = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()] if inner else []
            if isinstance(v_results, list):
                for idx, item in enumerate(v_results):
                    if isinstance(item, str) and item.startswith("{") and item.endswith("}"):
                        try:
                            import json
                            item = json.loads(item.replace("'", '"'))
                        except Exception:
                            pass
                    if isinstance(item, dict):
                        for k, t in [("command", str), ("exit_code", int), ("result", str)]:
                            if k in item and not isinstance(item[k], t):
                                issues.append(f"JSON Schema 위반: verification_results[{idx}].{k} 필드는 {t.__name__} 타입이어야 합니다.")
                    elif not isinstance(item, str):
                        issues.append(f"JSON Schema 위반: verification_results[{idx}] 항목은 Object 또는 String 타입이어야 합니다.")

    return issues, warnings


def cmd_run_check(run_file):
    issues, warnings = check_run_file(run_file)
    if warnings:
        print("경고:")
        for warning in warnings:
            print(f"  - {warning}")

    if issues:
        print("Run 검증 실패:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    print("Run 검증 통과")


def _extract_yaml_list_inline(content, key):
    match = re.search(rf"^\s*{re.escape(key)}\s*:\s*\[(.*?)\]", content, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    raw = match.group(1)
    return [item.strip().strip('"').strip("'") for item in raw.split(",") if item.strip()]


def _extract_yaml_block_text(content, key):
    lines = content.splitlines()
    capture = []
    in_block = False
    base_indent = 0
    for line in lines:
        if not in_block:
            match = re.match(rf"^(\s*){re.escape(key)}\s*:\s*(.*)$", line)
            if match:
                in_block = True
                base_indent = len(match.group(1))
                trailing = match.group(2).strip()
                if trailing:
                    capture.append(trailing)
            continue

        if line.strip() == "":
            capture.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= base_indent and not line.lstrip().startswith("-"):
            break
        capture.append(line)
    return "\n".join(capture).strip()


def project_dir_for_run_file(path):
    current = os.path.abspath(path)
    if os.path.isfile(current):
        current = os.path.dirname(current)

    while True:
        if os.path.exists(os.path.join(current, "session.json")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return ""
        current = parent


def is_placeholder_path(value):
    text = str(value or "").strip()
    return bool(text and text.startswith("<") and text.endswith(">"))


def qa_workspace_blocked_followup_lines(stage, qa_status, qa_path):
    return [
        f"{stage}는 QA-000 workspace 상태가 {qa_status}이면 실행할 수 없습니다: {qa_path}",
        "다음 조치: QA-000 Run의 doctor JSON과 evidence 로그를 확인하고 제품 결함과 환경 차단을 분리하세요.",
        "환경 문제이면 ISSUE/environment_blocked로 정리하고 QA-001/QA-002를 보류하세요.",
        "제품 수정이 필요하면 사용자 또는 Orchestrator 결정 후 qa-fix-loop를 생성하세요.",
    ]


def qa_workspace_preflight_blockers(run_file, stage):
    if stage not in {"QA-001", "QA-002", "QA-003"}:
        return []

    blockers = []
    project_dir = project_dir_for_run_file(run_file)
    if not project_dir:
        return [f"{stage} Run preflight에서 session.json 위치를 찾을 수 없습니다."]

    session_path = os.path.join(project_dir, "session.json")
    try:
        with open(session_path, encoding="utf-8") as f:
            session = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [f"{stage} Run preflight에서 session.json을 읽을 수 없습니다: {e}"]

    state = qa_workspace_state(session)
    qa_path = str(state.get("path") or "").strip()
    qa_status = str(state.get("status") or "").strip().lower()
    if not qa_path:
        blockers.append(
            f"{stage}는 QA-000이 기록한 qa_execution.gate4_workspace.path 없이는 실행할 수 없습니다."
        )
        return blockers

    if qa_status in {"blocked", "failed", "missing", "environment_blocked"}:
        blockers.extend(qa_workspace_blocked_followup_lines(stage, qa_status, qa_path))

    qa_abs_path = qa_path if os.path.isabs(qa_path) else os.path.join(project_dir, qa_path)
    if not is_placeholder_path(qa_path) and not os.path.isdir(os.path.abspath(qa_abs_path)):
        blockers.append(f"{stage} QA workspace 경로가 존재하지 않습니다: {qa_path}")

    return blockers


def run_preflight_file(path):
    blockers = []
    warnings = []
    project_dir = project_dir_for_run_file(path) or "."
    profile = load_delivery_profile(project_dir)
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return [f"Run 파일을 읽을 수 없습니다: {e}"], []

    metadata = parse_simple_yaml_block(content)
    skill = metadata.get("skill", "")
    gate = metadata.get("gate", "")
    run_id = metadata.get("run_id", os.path.basename(path))
    status = metadata.get("status", "")
    lower_content = content.lower()
    body_without_yaml = re.sub(r"```yaml.*?```", "", content, flags=re.IGNORECASE | re.DOTALL)

    input_contract = parse_run_input_contract_yaml(content)
    run_contract_profile = effective_run_contract_profile(profile, metadata, input_contract)
    if input_contract:
        for field in ("profile", "adapter", "run_type", "gate", "persona", "skill"):
            top_value = str(metadata.get(field, "")).strip()
            input_value = str(input_contract.get(field, "")).strip()
            if top_value and input_value and top_value != input_value:
                message = f"Run 상단 metadata와 3. Run 입력 계약의 {field} 값이 다릅니다: top={top_value}, input={input_value}"
                if run_contract_profile == "poc":
                    warnings.append(message)
                else:
                    blockers.append(message)

    is_impl = (
        gate == "impl"
        or metadata.get("run_type", "").lower() in {"implementation", "qafix"}
        or skill == "qa-fix-loop"
    )
    has_code_result_claim = impl_code_result_claim(body_without_yaml)
    has_trace_final_claim = trace_final_state_claim(body_without_yaml)

    if is_impl and skill == "orchestrator-plan" and has_code_result_claim:
        warnings.append("orchestrator-plan Run이 구현 결과/검증 결과를 포함합니다. 계획 Run과 실행 결과 Run을 분리하세요.")

    if is_impl and skill == "implementation-plan" and has_code_result_claim:
        warnings.append("implementation-plan Run이 구현 완료 보고서처럼 쓰였습니다. 구현 결과는 Build Wave Run 또는 통합 보고로 분리하세요.")

    if skill == "implementation-plan" and has_trace_final_claim:
        warnings.append("implementation-plan Run이 추적표 Implemented/Verified/Pass 확정처럼 보이는 내용을 포함합니다.")

    invalid_direct_reason = any(
        re.search(r"orchestrator_direct_edit_reason|direct\s*(edit|implementation)\s*reason|직접\s*(구현|수정)\s*사유", line, re.IGNORECASE)
        and re.search(r"worker\s*사용.*명시하지|worker.*명시.*않|subagent.*지시.*없|별도\s+subagent\s+실행\s+지시는\s+없|worker.*요청.*없", line, re.IGNORECASE)
        and not re.search(r"아니다|아니며|not\s+a\s+reason|not\s+an\s+acceptable\s+reason", line, re.IGNORECASE)
        for line in content.splitlines()
    )
    if invalid_direct_reason:
        blockers.append("Orchestrator 직접 구현 사유로 'worker/subagent를 명시하지 않았다'는 취지의 문구를 사용할 수 없습니다.")

    if is_impl and has_code_result_claim and direct_edit_reason_present(content):
        scope_text = direct_edit_scope_block(content)
        if not scope_text:
            warnings.append("Orchestrator 직접 구현 예외가 있지만 direct_edit_scope가 없습니다. files, estimated_loc, contract_changed, verification, followup_review_required를 남기세요.")
        else:
            file_count = direct_edit_scope_file_count(scope_text)
            estimated_loc = direct_edit_scope_estimated_loc(scope_text)
            contract_changed = direct_edit_scope_contract_changed(scope_text)
            if file_count > ORCHESTRATOR_DIRECT_EDIT_LIMITS["max_files"]:
                blockers.append(f"Orchestrator 직접 구현 예외 파일 수가 기준을 초과합니다: {file_count}>{ORCHESTRATOR_DIRECT_EDIT_LIMITS['max_files']}. Build Wave/worker Run으로 분리하세요.")
            if estimated_loc is not None and estimated_loc > ORCHESTRATOR_DIRECT_EDIT_LIMITS["max_loc"]:
                blockers.append(f"Orchestrator 직접 구현 예외 변경량이 기준을 초과합니다: {estimated_loc}>{ORCHESTRATOR_DIRECT_EDIT_LIMITS['max_loc']} LOC. Build Wave/worker Run으로 분리하세요.")
            if contract_changed:
                blockers.append("Orchestrator 직접 구현 예외에서 contract_changed=true는 허용하지 않습니다. Build Wave/worker Run 또는 CR로 분리하세요.")

    if skill in ("build-wave", "implementation-scaffold"):
        if not metadata.get("bw_id"):
            blockers.append("worker Run에는 bw_id가 필요합니다.")
        if "target_contracts:" not in content:
            blockers.append("worker Run에는 target_contracts가 필요합니다.")
        if "interface_contract:" not in content and "contract_skeleton:" not in content:
            warnings.append("구현 worker Run인데 interface_contract 또는 contract_skeleton이 없습니다.")
        if skill == "implementation-scaffold" and "contract_skeleton:" not in content:
            blockers.append("implementation-scaffold Run에는 contract_skeleton이 필요합니다.")
        target_contracts_block = _extract_yaml_block_text(content, "target_contracts")
        if re.search(r"\bTBD\b|TBD:", target_contracts_block):
            blockers.append("worker Run의 target_contracts에 TBD가 남아 있습니다. 실행 전 public signature/schema/skeleton을 구체화하세요.")
        if "worker_execution_policy:" not in content:
            warnings.append("worker Run에 worker_execution_policy가 없습니다.")
        if "development_standards_applied:" not in content:
            warnings.append("구현 worker Run에 development_standards_applied가 없습니다. 로깅/주석/테스트 설명 기준을 작업지시서에 직접 바인딩하세요.")
        if "development_standard_checklist:" not in content:
            warnings.append("구현 worker Run에 development_standard_checklist가 없습니다. logger, JavaDoc/docstring, 테스트 설명 체크리스트를 추가하세요.")
        else:
            checklist_block = _extract_yaml_block_text(content, "development_standard_checklist")
            if not re.search(r"logging|logger|로그", checklist_block, re.IGNORECASE):
                warnings.append("development_standard_checklist에 로깅/logger 기준이 없습니다.")
            if not re.search(r"comments?|javadoc|docstring|주석", checklist_block, re.IGNORECASE):
                warnings.append("development_standard_checklist에 주석/JavaDoc/docstring 기준이 없습니다.")
            if not re.search(r"displayname|given|when|then|입력값|기대값|출력값|테스트", checklist_block, re.IGNORECASE):
                warnings.append("development_standard_checklist에 테스트 설명 기준이 없습니다.")
        source_documents_block = _extract_yaml_block_text(content, "source_documents")
        if re.search(
            r"Traceability-Matrix|AGENT_RUN_PROTOCOL|RUN_INPUT_CONTRACT|RUN_OUTPUT_CONTRACT|TRACEABILITY_RULES",
            source_documents_block,
            re.IGNORECASE,
        ):
            warnings.append("worker Run source_documents에 Orchestrator 운영 문서가 포함되어 있습니다. 추적표/Run 입출력/절차 문서는 orchestrator_reference로 분리하세요.")

        related_ids = _extract_yaml_list_inline(content, "related_ids")
        req_ids = _extract_yaml_list_inline(content, "req")
        all_ids_text = " ".join(related_ids + req_ids)
        has_parent_req = bool(re.search(r"\bREQ-\d{3}\b", all_ids_text))
        has_detail_req = bool(re.search(r"\bREQ-\d{3}-\d{2}\b", all_ids_text))
        if has_parent_req and not has_detail_req and profile not in ("poc", "product"):
            warnings.append("target_contracts/related_ids가 parent REQ 중심입니다. 상세 REQ-NNN-NN 단위 매핑을 추가하세요.")

        ui_ids = set(re.findall(r"\bUI-\d{3}-\d{2}\b", content))
        scr_block = _extract_yaml_block_text(content, "scr")
        scr_empty = bool(re.search(r"^\[\s*\]\s*$", scr_block or ""))
        if ui_ids and (not scr_block or scr_empty):
            warnings.append("UI 구현/테스트 ID가 있지만 target_contracts.scr가 비어 있습니다. 관련 SCR-ID를 연결하세요.")

        writable_block = _extract_yaml_block_text(content, "writable")
        if re.search(r"\bTBD\b|TBD:", writable_block):
            blockers.append("worker Run writable scope에 TBD가 남아 있습니다. 실행 전 수정 허용 경로를 구체화하세요.")
        if re.search(r"\bsession\.json\b", writable_block):
            blockers.append("worker Run writable scope에 session.json을 포함할 수 없습니다.")
        if re.search(r"docs/artifacts/02-traceability|Traceability-Matrix", writable_block, re.IGNORECASE):
            warnings.append("worker Run writable scope에 추적표가 포함되어 있습니다. worker는 갱신 필요 항목만 보고하는 편이 안전합니다.")
        if re.search(r"docs/artifacts/03-test|Test-Cases", writable_block, re.IGNORECASE):
            warnings.append("worker Run writable scope에 Gate3 테스트케이스 문서가 포함되어 있습니다. 테스트 코드/자기 Run 문서 중심으로 좁히세요.")

        commands_block = _extract_yaml_block_text(content, "commands")
        if re.search(r"check-trace|sync-session|wave-complete|gate-start|python\s+vulcan\.py\s+session", commands_block, re.IGNORECASE):
            warnings.append("worker Run에 Orchestrator 전용 명령이 포함되어 있을 수 있습니다. worker self-check와 Orchestrator 재실행 명령을 분리하세요.")

        if "verification:" not in content and "verification_results:" not in content:
            warnings.append("검증 명령 또는 결과가 없습니다. worker self-check와 Orchestrator 재실행 명령을 명시하세요.")

        bw_id = infer_bw_id(metadata, path, content)
        if bw_id == "BW-000" and status in {"Completed", "Verified", "CompletedWithIssues"} and has_trace_final_claim:
            blockers.append("BW-000 scaffold Run은 요구사항/테스트 상태를 Implemented/Verified/Pass로 확정할 수 없습니다. skeleton/build smoke 결과와 기능 구현 상태를 분리하세요.")
        elif status in {"Completed", "Verified", "CompletedWithIssues"} and has_trace_final_claim:
            warnings.append("Build Wave 결과가 추적표 Implemented/Verified/Pass 확정처럼 보입니다. worker 결과와 Orchestrator 재검증 반영을 구분하세요.")

        has_delegation_records = yaml_field_has_nonempty_items(content, "delegation_records")
        has_run_execution_record = bool(re.search(r"(?im)^#{2,4}\s*Run Execution Record\b", content))
        has_native_delegation_hint = bool(re.search(r"agy-branch-agent|Workspace:\s*branch|native branch agent", content, re.IGNORECASE))
        if status in {"Completed", "Verified", "CompletedWithIssues"} and has_native_delegation_hint and not has_delegation_records:
            blockers.append("native/Agy worker 사용 흔적이 있지만 delegation_records가 비어 있습니다. 위임 대상, 범위, 변경 파일, 결과 요약, Orchestrator 재검증을 기록하세요.")
        elif status in {"Completed", "Verified", "CompletedWithIssues"} and not has_delegation_records and not has_run_execution_record and not direct_edit_reason_present(content):
            warnings.append("완료된 worker Run이지만 delegation_records 또는 Run Execution Record가 없습니다. native 위임/외부 runner/직접 수정 중 실행 경로를 기록하세요.")
        elif status in {"Completed", "Verified", "CompletedWithIssues"} and has_delegation_records:
            warnings.extend(delegation_record_shape_warnings(content))
            warnings.extend(delegation_record_verification_warnings(content))

    if skill == "qa-execution":
        qa_stage = qa_stage_from_run(content, metadata)
        if "qa_execution_policy:" not in content:
            warnings.append("qa-execution Run에는 qa_execution_policy가 있는 편이 안전합니다.")
        if "qa_failure_report_contract:" not in content:
            warnings.append("qa-execution Run에는 실패/차단 시 worker가 남길 qa_failure_report_contract가 필요합니다.")
        if not re.search(r"\bQA-00[0-3]\b", content):
            warnings.append("qa-execution Run은 QA-000 환경 준비, QA-001 명령 검증, QA-002 UI/E2E 증적, QA-003 결과 정리 중 현재 단계가 드러나야 합니다.")
        if re.search(r"\bQA-000\b", content) and not re.search(r"qa_workspace|qa_workspace_path", content, re.IGNORECASE):
            warnings.append("QA-000 Run은 후속 QA Run이 재사용할 qa_workspace_path를 기록해야 합니다.")
        if re.search(r"\bQA-000\b", content) and not re.search(r"doctor\s+--json|qa000_doctor_evidence|QA-000-doctor\.json", content, re.IGNORECASE):
            warnings.append("QA-000 Run은 `python vulcan.py doctor --json` 결과를 QA-000-doctor.json 환경 증적으로 남기는 것이 좋습니다.")
        if re.search(r"\bQA-00[1-3]\b", content) and not re.search(r"qa_workspace|qa_workspace_path", content, re.IGNORECASE):
            warnings.append("QA-001~QA-003 Run은 QA-000이 기록한 같은 qa_workspace_path를 입력으로 받아야 합니다.")
        blockers.extend(qa_workspace_preflight_blockers(path, qa_stage))
        blockers.extend(qa_execution_source_mutation_blockers(content))
        if status in {"Completed", "Verified", "CompletedWithIssues", "Failed", "Blocked"}:
            has_delegation_records = yaml_field_has_nonempty_items(content, "delegation_records")
            has_run_execution_record = bool(re.search(r"(?im)^#{2,4}\s*Run Execution Record\b", content))
            has_native_delegation_hint = bool(re.search(r"agy-branch-agent|Workspace:\s*branch|native branch agent", content, re.IGNORECASE))
            if has_native_delegation_hint and not has_delegation_records:
                blockers.append("native/Agy QA worker 사용 흔적이 있지만 delegation_records가 비어 있습니다. QA 위임 대상, 범위, 증적 파일, 결과 요약, Orchestrator 재검증을 기록하세요.")
            elif not has_delegation_records and not has_run_execution_record and not direct_edit_reason_present(content):
                warnings.append("완료된 QA worker Run이지만 delegation_records 또는 Run Execution Record가 없습니다. QA 실행 경로를 추적할 수 있게 기록하세요.")
            elif has_delegation_records:
                warnings.extend(delegation_record_shape_warnings(content, prefix="QA delegation_records"))
                warnings.extend(delegation_record_verification_warnings(content, prefix="QA delegation_records"))
                missing_timing = [
                    field for field in ("started_at", "completed_at", "duration_seconds")
                    if not re.search(rf"(?im)^\s*{field}\s*:", content)
                ]
                if missing_timing:
                    warnings.append(f"QA delegation_records에 병목 분석용 시간 필드가 부족합니다: {', '.join(missing_timing)}.")
                if not re.search(r"(?im)^\s*(heartbeat_count|status_probe_count)\s*:", content):
                    warnings.append("QA delegation_records에 heartbeat_count 또는 status_probe_count가 없습니다. 장시간 QA worker 병목 분석을 위해 기록을 권장합니다.")
            has_failure_like_result = re.search(
                r"\b(Fail|Failed|failed|Not Run|not_run|environment_blocked)\b",
                body_without_yaml,
            )
            if has_failure_like_result and "failure_reports" not in content:
                warnings.append("qa-execution 결과에 실패/차단이 있지만 failure_reports가 없습니다. 명령, cwd, exit code, 로그, 재현 명령, 영향 ID를 구조화하세요.")

    if skill == "qa-fix-loop":
        if not re.search(r"\bFIND-\d{3}(?:-\d{2})?\b", content):
            warnings.append("qa-fix-loop Run에는 수정 대상 FIND-ID가 명시되어야 합니다.")
        if "target_contracts:" not in content:
            blockers.append("qa-fix-loop Run에는 수정할 설계/코드 계약 target_contracts가 필요합니다.")
        if "worker_execution_policy:" not in content:
            warnings.append("qa-fix-loop Run에는 worker_execution_policy가 필요합니다.")
        writable_block = _extract_yaml_block_text(content, "writable")
        if re.search(r"\bsession\.json\b", writable_block):
            blockers.append("qa-fix-loop Run writable scope에 session.json을 포함할 수 없습니다.")
        if re.search(r"docs/artifacts/02-traceability|Traceability-Matrix", writable_block, re.IGNORECASE):
            warnings.append("qa-fix-loop worker는 추적표를 직접 확정하지 않고 갱신 필요 항목을 보고하는 편이 안전합니다.")
        if re.search(r"docs/artifacts/03-test|Test-Cases", writable_block, re.IGNORECASE):
            warnings.append("qa-fix-loop worker는 Gate3 테스트 설계 문서를 직접 수정하지 않고 테스트 코드와 자기 Run 결과 중심으로 수정하세요.")
        commands_block = _extract_yaml_block_text(content, "commands")
        if re.search(r"check-trace|sync-session|wave-complete|gate-start|python\s+vulcan\.py\s+session", commands_block, re.IGNORECASE):
            warnings.append("qa-fix-loop Run에 Orchestrator 전용 명령이 포함되어 있을 수 있습니다. worker self-check와 Orchestrator 재실행 명령을 분리하세요.")
        if re.search(r"새\s*(요구사항|API|화면|DB)|new\s+(requirement|api|screen|table)", body_without_yaml, re.IGNORECASE):
            warnings.append("qa-fix-loop가 새 계약 생성처럼 보입니다. 승인된 설계 범위를 넘으면 CR 후보로 멈추세요.")
        if status in {"Completed", "Verified"} and not re.search(r"check-contract|pytest|npm\s+run|gradlew|mvn\s+test|run-check", body_without_yaml, re.IGNORECASE):
            warnings.append("qa-fix-loop 완료 상태이지만 재검증 명령 기록이 약합니다. 관련 check-contract/test/run-check 결과를 남기세요.")

    return blockers, warnings


def cmd_run_preflight(run_file):
    blockers, warnings = run_preflight_file(run_file)
    if warnings:
        print("Preflight 경고:")
        for warning in warnings:
            print(f"  - {warning}")

    if blockers:
        print("Preflight 차단:")
        for blocker in blockers:
            print(f"  - {blocker}")
        sys.exit(1)

    if not warnings:
        print("Run preflight 통과")
    else:
        print("Run preflight 통과 (경고 있음)")


def print_run_preflight_notice(run_file, context="run"):
    blockers, warnings = run_preflight_file(run_file)
    if not blockers and not warnings:
        print(f"  {context} preflight: 통과")
        return

    print(f"  {context} preflight: worker 실행 전 보정 필요")
    if warnings:
        print("  경고:")
        for warning in warnings:
            print(f"    - {warning}")
    if blockers:
        print("  차단:")
        for blocker in blockers:
            print(f"    - {blocker}")


def run_preflight_or_exit(run_file, context="run-exec"):
    blockers, warnings = run_preflight_file(run_file)
    if warnings:
        print(f"{context} preflight 경고:")
        for warning in warnings:
            print(f"  - {warning}")
    if blockers:
        print(f"{context} preflight 차단:")
        for blocker in blockers:
            print(f"  - {blocker}")
        print("오류: worker 실행 전 Run 작업지시서를 먼저 보정하세요.")
        sys.exit(1)


def create_session_json(target_dir, project_name, profile=DEFAULT_DELIVERY_PROFILE):
    profile = normalize_delivery_profile(profile)
    session = {
        "project": project_name,
        "vulcan_src": VULCAN_DIR,
        "vulcan_version": VULCAN_VERSION,
        "profile": profile,
        "current_gate": "phase0",
        "gate_status": {
            "phase0": "pending",
            "gate1": "pending",
            "gate2": "pending",
            "gate3": "pending",
            "impl":  "pending",
            "gate4": "pending",
            "gate5": "pending"
        },
        "feature": "",
        "started": str(date.today()),
        "completed": [],
        "pending": [],
        "blocked": []
    }
    write_file(target_dir, "session.json", json.dumps(session, ensure_ascii=False, indent=2))


def deep_merge_dict(base, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge_dict(base[key], value)
        else:
            base[key] = value
    return base


def codex_model_policy(config):
    runtime = config.get("runtime", {}) if isinstance(config.get("runtime"), dict) else {}
    policy_root = runtime.get("model_policy", {}) if isinstance(runtime.get("model_policy"), dict) else {}
    codex_policy = policy_root.get("codex-cli", {}) if isinstance(policy_root.get("codex-cli"), dict) else {}
    policy = json.loads(json.dumps(CODEX_MODEL_POLICY_DEFAULTS))
    deep_merge_dict(policy, codex_policy)
    return policy


def resolve_codex_model_effort(config, role, explicit_model=None, explicit_effort=None, runner_config=None):
    runner_config = runner_config or {}
    policy = codex_model_policy(config)
    policy_enabled = bool(policy.get("enabled", True))
    roles = policy.get("roles", {}) if isinstance(policy.get("roles"), dict) else {}
    fallback = policy.get("fallback", {}) if isinstance(policy.get("fallback"), dict) else {}
    role_config = roles.get(role, {}) if policy_enabled and isinstance(roles.get(role), dict) else {}

    model_source = "cli-argument" if explicit_model else ""
    effort_source = "cli-argument" if explicit_effort else ""
    model = explicit_model or role_config.get("model")
    reasoning_effort = explicit_effort or role_config.get("effort") or role_config.get("reasoning_effort")
    if model and not model_source:
        model_source = f"codex-model-policy:{role}"
    if reasoning_effort and not effort_source:
        effort_source = f"codex-model-policy:{role}"

    if not model:
        model = runner_config.get("model") or fallback.get("model") or "gpt-5.5"
        model_source = "runner-config" if runner_config.get("model") else "codex-model-policy:fallback"
    if not reasoning_effort:
        reasoning_effort = (
            runner_config.get("reasoning_effort")
            or runner_config.get("effort")
            or fallback.get("effort")
            or fallback.get("reasoning_effort")
            or "high"
        )
        effort_source = (
            "runner-config"
            if runner_config.get("reasoning_effort") or runner_config.get("effort")
            else "codex-model-policy:fallback"
        )
    model_fallback_reason = ""
    fallback_target = CODEX_MODEL_FALLBACKS.get(model)
    if fallback_target:
        original_model = model
        model = fallback_target.get("model") or model
        model_fallback_reason = fallback_target.get("reason") or f"{original_model} -> {model}"
        model_source = f"{model_source}|compat-fallback:{original_model}"
    return model, reasoning_effort, {
        "model_source": model_source,
        "effort_source": effort_source,
        "policy_role": role if role_config else "fallback",
        "model_fallback_reason": model_fallback_reason,
    }


def default_vulcan_config(available_runners=None, profile=DEFAULT_DELIVERY_PROFILE, primary=None):
    has_runner = bool(available_runners) if available_runners is not None else True
    normalized_profile = normalize_delivery_profile(profile)
    config = {
        "version": VULCAN_VERSION,
        "delivery_profile": normalized_profile,
        "profile_rules": delivery_profile_rules(normalized_profile),
        "runtime": {
            "primary": primary,
            "gemini_long_context_mode": True,
            "available_runners": available_runners or [],
            "model_policy": {
                "codex-cli": CODEX_MODEL_POLICY_DEFAULTS
            }
        },
        "workflow": {
            "branch_mode": "audit",
            "main_branch": "main",
            "integration_branch": "dev",
            "impl_uses_integration_branch": True,
            "qa_worktree_enabled": False,
            "qa_stage_mode": "staged",
            "release_merge_to": "main",
            "enforce_branch_guard": True
        },
        "review": {
            "independent_enabled": has_runner,
            "independent_sandbox": "workspace-write",
            "independent_exec_timeout_seconds": 1800,
            "independent_triggers": INDEPENDENT_REVIEW_DEFAULT_GATES,
            "independent_worktree": True,
            "independent_readonly": True
        },
        "execution": {
            "independent_enabled": has_runner,
            "default_worktree": True,
            "default_timeout_seconds": 2400,
            "hard_timeout_seconds": 5400,
            "extension_seconds": 600,
            "max_extensions": 3,
            "progress_grace_seconds": 300,
            "progress_probe_seconds": 300,
            "no_progress_timeout_seconds": 900,
            "min_runtime_seconds": 120
        }
    }
    return config


def create_vulcan_config(target_dir, profile=DEFAULT_DELIVERY_PROFILE, primary=None):
    rel_path = "vulcan.config.json"
    path = os.path.join(target_dir, rel_path)
    if os.path.exists(path):
        return
    available_runners = detect_runtime_runners()
    write_file(target_dir, rel_path, json.dumps(default_vulcan_config(available_runners, profile=profile, primary=primary), ensure_ascii=False, indent=2))


def replace_unsupported_codex_models(value):
    if isinstance(value, dict):
        return {k: replace_unsupported_codex_models(v) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_unsupported_codex_models(v) for v in value]
    if value in CODEX_MODEL_FALLBACKS:
        return CODEX_MODEL_FALLBACKS[value].get("model") or value
    return value


def migrate_vulcan_config_models(project_dir="."):
    path = os.path.join(project_dir, "vulcan.config.json")
    if not os.path.exists(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    migrated = replace_unsupported_codex_models(config)
    if migrated == config:
        return False
    with open(path, "w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return True


def migrate_vulcan_config_qa_workspace_policy(project_dir="."):
    path = os.path.join(project_dir, "vulcan.config.json")
    if not os.path.exists(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    workflow = config.setdefault("workflow", {})
    if not isinstance(workflow, dict):
        return False
    if workflow.get("qa_worktree_enabled") is False:
        return False
    workflow["qa_worktree_enabled"] = False
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return True


def load_vulcan_config(project_dir="."):
    path = os.path.join(project_dir, "vulcan.config.json")
    config = default_vulcan_config()
    if not os.path.exists(path):
        return replace_unsupported_codex_models(config)
    try:
        with open(path, encoding="utf-8") as f:
            user_config = json.load(f)
    except (OSError, json.JSONDecodeError):
        return replace_unsupported_codex_models(config)
    if isinstance(user_config, dict):
        deep_merge_dict(config, user_config)
    return replace_unsupported_codex_models(config)


def workflow_policy(project_dir="."):
    config = load_vulcan_config(project_dir)
    workflow = config.get("workflow", {}) if isinstance(config.get("workflow"), dict) else {}
    defaults = default_vulcan_config().get("workflow", {})
    merged = dict(defaults)
    merged.update(workflow)
    return merged


def git_text(args, project_dir="."):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_current_branch(project_dir="."):
    branch = git_text(["rev-parse", "--abbrev-ref", "HEAD"], project_dir)
    return branch or "unknown"


def git_branch_exists(branch, project_dir="."):
    if not branch:
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", branch],
        cwd=project_dir,
        capture_output=True,
    )
    return result.returncode == 0


def git_checkout_branch(branch, create=False, project_dir="."):
    args = ["checkout", "-b", branch] if create else ["checkout", branch]
    result = subprocess.run(
        ["git"] + args,
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        print(f"오류: git checkout 실패 - {detail or branch}")
        sys.exit(1)


def workflow_branch_guard(project_dir, gate, command_name, strict=None):
    workflow = workflow_policy(project_dir)
    if workflow.get("branch_mode") in ("none", "single", "disabled"):
        return True
    if not workflow.get("impl_uses_integration_branch", True):
        return True
    if gate not in ("impl", "gate4"):
        return True

    integration_branch = workflow.get("integration_branch") or "dev"
    current_branch = git_current_branch(project_dir)
    if current_branch == integration_branch:
        return True

    strict = workflow.get("enforce_branch_guard", True) if strict is None else strict
    message = (
        f"{command_name}는 audit workflow에서 `{integration_branch}` 통합 브랜치에서 실행해야 합니다. "
        f"현재 브랜치: `{current_branch}`"
    )
    if strict:
        print(f"오류: {message}")
        print(f"  먼저 실행: python vulcan.py branch-start impl")
        sys.exit(1)
    print(f"  경고: {message}")
    return False


def cmd_branch_status(project_dir="."):
    project_abs = os.path.abspath(project_dir)
    workflow = workflow_policy(project_abs)
    session_path = os.path.join(project_abs, "session.json")
    session = {}
    if os.path.exists(session_path):
        try:
            session = load_session(project_abs)
        except SystemExit:
            session = {}
    current_branch = git_current_branch(project_abs)
    main_branch = workflow.get("main_branch") or "main"
    integration_branch = workflow.get("integration_branch") or "dev"
    branch_state = session.get("branch_state", {}) if isinstance(session.get("branch_state"), dict) else {}

    print("Vulcan workflow branch status")
    print(f"  mode: {workflow.get('branch_mode')}")
    print(f"  current_gate: {session.get('current_gate') or '-'}")
    print(f"  current_branch: {current_branch}")
    print(f"  main_branch: {main_branch}")
    print(f"  integration_branch: {integration_branch}")
    print(f"  impl_uses_integration_branch: {workflow.get('impl_uses_integration_branch')}")
    print(f"  qa_worktree_enabled: {workflow.get('qa_worktree_enabled')}")
    print(f"  qa_stage_mode: {workflow.get('qa_stage_mode')}")
    print(f"  session_branch_role: {branch_state.get('current_role', '') or '-'}")
    qa_state = qa_workspace_state(session)
    if qa_state:
        print(f"  qa_workspace_path: {qa_state.get('path') or '-'}")
        print(f"  qa_workspace_mode: {qa_state.get('mode') or '-'}")
        print(f"  qa_workspace_status: {qa_state.get('status') or '-'}")
        print(f"  qa_workspace_last_stage: {qa_state.get('last_stage') or '-'}")
    print(f"  integration_exists: {git_branch_exists(integration_branch, project_abs)}")
    print(f"  dirty_blocking: {has_blocking_dirty_status(project_abs)}")


def cmd_profile_status(project_dir="."):
    project_abs = os.path.abspath(project_dir)
    session = {}
    session_path = os.path.join(project_abs, "session.json")
    if os.path.exists(session_path):
        try:
            session = load_session(project_abs)
        except SystemExit:
            session = {}
    config = load_vulcan_config(project_abs)
    profile = load_delivery_profile(project_abs)
    config_profile = normalize_delivery_profile(config.get("delivery_profile") or profile)
    config_rules = config.get("profile_rules", {}) if isinstance(config.get("profile_rules"), dict) else {}
    default_rules = delivery_profile_rules(profile)
    merged_rules = dict(default_rules)
    merged_rules.update(config_rules)

    print("Vulcan delivery profile status")
    print(f"  project: {session.get('project') or os.path.basename(project_abs)}")
    print(f"  session_profile: {normalize_delivery_profile(session.get('profile') or session.get('delivery_profile') or profile)}")
    print(f"  config_profile: {config_profile}")
    print(f"  effective_profile: {profile}")
    if config_profile != profile:
        print("  warning: session profile and config delivery_profile differ; session wins for Run preset selection")
    print("  supported_profiles: " + ", ".join(SUPPORTED_DELIVERY_PROFILES))
    if DELIVERY_PROFILE_ALIASES:
        aliases = ", ".join(f"{alias}->{target}" for alias, target in DELIVERY_PROFILE_ALIASES.items())
        print(f"  aliases: {aliases}")
    print("  profile_rules:")
    for key in (
        "gate_approval",
        "required_artifacts",
        "traceability_level",
        "program_contract_level",
        "security_standard_level",
        "data_standard_level",
        "qa_evidence_level",
        "independent_review_level",
        "run_preflight_strictness",
        "release_control",
    ):
        print(f"    {key}: {merged_rules.get(key) or '-'}")
    if profile != "audit":
        print("  note: non-audit profiles are recorded as overlay policy first; most checks still share audit-safe defaults until profile-specific strictness is implemented.")


def _project_rel_exists(project_dir, rel_path):
    return os.path.exists(os.path.join(os.path.abspath(project_dir), rel_path))


def _profile_gap_rule_status(project_dir, rule):
    ok_any = rule.get("ok_any") or []
    ok_all = rule.get("ok_all") or []
    partial_any = rule.get("partial_any") or []
    partial_all = rule.get("partial_all") or []

    matched = []
    if ok_any:
        matched = [path for path in ok_any if _project_rel_exists(project_dir, path)]
        if matched:
            return "ok", matched
    if ok_all:
        all_matched = [path for path in ok_all if _project_rel_exists(project_dir, path)]
        if len(all_matched) == len(ok_all):
            return "ok", all_matched
        if all_matched:
            matched.extend(all_matched)
    if partial_any:
        partial_matched = [path for path in partial_any if _project_rel_exists(project_dir, path)]
        if partial_matched:
            return "partial", partial_matched
    if partial_all:
        partial_all_matched = [path for path in partial_all if _project_rel_exists(project_dir, path)]
        if len(partial_all_matched) == len(partial_all):
            return "partial", partial_all_matched
        if partial_all_matched:
            matched.extend(partial_all_matched)
    if matched:
        return "partial", matched
    return "missing", []


def collect_profile_gap(project_dir=".", target_profile="product"):
    project_abs = os.path.abspath(project_dir)
    current_profile = load_delivery_profile(project_abs)
    session = load_session(project_abs)
    current_gate = session.get("current_gate", "phase0") if isinstance(session, dict) else "phase0"
    target = normalize_delivery_profile(target_profile)
    content_issues = []
    content_warnings = []
    if target == "poc":
        items = [{
            "id": "poc_target",
            "title": "PoC target",
            "status": "review",
            "matched": [],
            "recommendation": "PoC는 승격 대상이라기보다 경량 실험 profile입니다. 필요하면 새 PoC 목적과 성공 기준을 정리하세요.",
        }]
    else:
        rules = PROFILE_GAP_RULES.get(target)
        if not rules:
            rules = []
        items = []
        for rule in rules:
            status, matched = _profile_gap_rule_status(project_abs, rule)
            items.append({
                "id": rule.get("id") or "",
                "title": rule.get("title") or "",
                "status": status,
                "matched": matched,
                "recommendation": rule.get("recommendation") or "",
            })

    if target == "product":
        content_issues, content_warnings = collect_product_profile_findings(project_abs, gate=current_gate)
    elif target == "audit":
        content_issues, content_warnings = collect_artifact_completion_findings(project_abs)

    summary = {"ok": 0, "partial": 0, "missing": 0, "review": 0}
    for item in items:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    summary["content_issues"] = len(content_issues)
    summary["content_warnings"] = len(content_warnings)
    return {
        "project": os.path.basename(project_abs),
        "current_profile": current_profile,
        "target_profile": target,
        "current_gate": current_gate,
        "items": items,
        "summary": summary,
        "content_issues": content_issues,
        "content_warnings": content_warnings,
        "note": "profile-gap is read-only; it does not change session.json or vulcan.config.json.",
    }


def cmd_profile_gap(target_profile="product", emit_json=False, project_dir="."):
    gap = collect_profile_gap(project_dir=project_dir, target_profile=target_profile)
    if emit_json:
        print(json.dumps(gap, ensure_ascii=False, indent=2))
        return

    print("==================================================")
    print(" [profile-gap] Delivery Profile gap check")
    print("==================================================")
    print(f" project: {gap['project']}")
    print(f" current_profile: {gap['current_profile']}")
    print(f" target_profile: {gap['target_profile']}")
    print(f" current_gate: {gap['current_gate']}")
    print(" read_only: true")
    print()
    print(" summary")
    for key in ("ok", "partial", "missing", "review", "content_issues", "content_warnings"):
        print(f"  {key}: {gap['summary'].get(key, 0)}")
    print()
    print(" items")
    for item in gap["items"]:
        matched = ", ".join(item.get("matched") or []) or "-"
        print(f"  - [{item['status']}] {item['id']} - {item['title']}")
        print(f"    matched: {matched}")
        print(f"    recommendation: {item.get('recommendation') or '-'}")
    print()
    if gap.get("content_issues"):
        print(" content issues")
        for issue in gap["content_issues"][:20]:
            print(f"  - {issue}")
        if len(gap["content_issues"]) > 20:
            print(f"  ... 외 {len(gap['content_issues']) - 20}건")
        print()
    if gap.get("content_warnings"):
        print(" content warnings")
        for warning in gap["content_warnings"][:20]:
            print(f"  - {warning}")
        if len(gap["content_warnings"]) > 20:
            print(f"  ... 외 {len(gap['content_warnings']) - 20}건")
        print()
    if gap["summary"].get("missing", 0) or gap["summary"].get("partial", 0):
        print(" next:")
        print("  부족 항목은 profile 변경 차단 조건이 아니라 backlog 또는 다음 Gate 작업 후보입니다.")
        print("  profile 값을 바꾸려면 사용자 승인 후 session/config 갱신을 별도 수행하세요.")
    elif gap["summary"].get("content_issues", 0) or gap["summary"].get("content_warnings", 0):
        print(" next:")
        print("  목표 profile 문서 세트는 있지만 현재 Gate 판단에 필요한 내용 보완이 남아 있습니다.")
        print("  status --check로 전환 차단 여부를 확인하세요.")
    else:
        print(" next:")
        print("  목표 profile로 운영 강도를 바꿀 수 있는 기본 근거가 있습니다. 최종 변경은 사용자 승인 후 수행하세요.")


def collect_status_summary(project_dir="."):
    project_abs = os.path.abspath(project_dir)
    session = {}
    session_path = os.path.join(project_abs, "session.json")
    if os.path.exists(session_path):
        try:
            session = load_session(project_abs)
        except SystemExit:
            session = {}

    workflow = workflow_policy(project_abs)
    profile = load_delivery_profile(project_abs) if session else DEFAULT_DELIVERY_PROFILE
    current_gate = session.get("current_gate") or "-"
    gate_status = session.get("gate_status", {}) if isinstance(session.get("gate_status"), dict) else {}
    implementation = session.get("implementation", {}) if isinstance(session.get("implementation"), dict) else {}
    if profile in ("poc", "product", "solution"):
        try:
            profile_stats = compute_stats(project_abs)
            computed_implementation = profile_stats.get("implementation")
            if isinstance(computed_implementation, dict):
                implementation = computed_implementation
        except Exception:
            pass
    branch_state = session.get("branch_state", {}) if isinstance(session.get("branch_state"), dict) else {}
    current_branch = git_current_branch(project_abs)
    integration_branch = workflow.get("integration_branch") or "dev"
    main_branch = workflow.get("main_branch") or "main"
    qa_state = qa_workspace_state(session)
    qa_workspace_followup = []
    qa_status = str(qa_state.get("status") or "").strip().lower()
    qa_path = str(qa_state.get("path") or "").strip()
    if qa_status in {"blocked", "failed", "missing", "environment_blocked"} and qa_path:
        qa_workspace_followup = qa_workspace_blocked_followup_lines("후속 QA", qa_status, qa_path)

    open_statuses = {"draft", "inprogress", "in progress", "running"}
    active_runs = []
    for record in collect_run_gate_records(project_abs):
        if current_gate != "-" and record["gate"] != current_gate:
            continue
        if record["status"].strip().lower() in open_statuses:
            active_runs.append(record)

    wave_records = collect_build_wave_records(project_abs)
    active_waves = [
        wave for wave in wave_records
        if wave.get("status") not in ("Verified", "Completed", "Done")
    ]

    next_actions = []
    if not session:
        next_actions.extend([
            "python vulcan.py init <target-dir> <project-name>",
            "python vulcan.py version",
        ])
    else:
        if current_gate == "completed":
            next_actions.append("프로젝트 완료: 추가 Gate 전환 없음")
        else:
            next_actions.append("python vulcan.py status --check")
    if current_gate == "impl":
        if current_branch != integration_branch:
            next_actions.insert(0, "python vulcan.py branch-start impl")
        elif active_waves:
            next_actions.insert(0, "python vulcan.py wave-complete <BW-ID> --status Verified")
        else:
            next_actions.insert(0, "python vulcan.py wave-start <BW-ID> --trace-seed <ID>")
    elif current_gate in ("gate4", "gate5"):
        next_actions.insert(0, "python vulcan.py prepare-transition")
    elif current_gate in GATE_ORDER:
        next_actions.insert(0, f"python vulcan.py session --gate {current_gate} --status done --approved --approval-evidence \"<승인 근거>\"")

    dashboard_comments = collect_dashboard_comments(project_abs)
    model_fallbacks = collect_model_fallbacks(project_abs)
    profile_gap = None
    if session and profile in ("poc", "product", "audit"):
        gap_target = "product" if profile == "poc" else profile
        try:
            profile_gap = collect_profile_gap(project_abs, target_profile=gap_target)
        except Exception as exc:
            profile_gap = {
                "target_profile": gap_target,
                "summary": {"ok": 0, "partial": 0, "missing": 0, "review": 0, "content_issues": 0, "content_warnings": 0},
                "read_error": str(exc),
            }
        gap_summary = profile_gap.get("summary", {}) if isinstance(profile_gap, dict) else {}
        if current_gate in GATE_ORDER and (
            gap_summary.get("content_issues", 0) > 0 or gap_summary.get("missing", 0) > 0
        ):
            preferred_actions = [
                "python vulcan.py status --check",
                f"python vulcan.py profile-gap --to {gap_target}",
            ]
            next_actions = preferred_actions + [
                action for action in next_actions
                if action not in preferred_actions and not action.startswith("python vulcan.py session --gate")
            ]
    if qa_workspace_followup:
        preferred_actions = [
            "QA-000 doctor JSON/evidence 확인",
            "환경 문제는 ISSUE/environment_blocked로 보류",
            "제품 수정 필요 시 qa-fix-loop 생성",
        ]
        next_actions = preferred_actions + [
            action for action in next_actions
            if action not in preferred_actions
        ]

    return {
        "project": session.get("project") or os.path.basename(project_abs),
        "profile": profile,
        "current_gate": current_gate,
        "gate_status": gate_status.get(current_gate, "-") if current_gate != "-" else "-",
        "current_branch": current_branch,
        "main_branch": main_branch,
        "integration_branch": integration_branch,
        "branch_mode": workflow.get("branch_mode"),
        "impl_uses_integration_branch": workflow.get("impl_uses_integration_branch"),
        "session_branch_role": branch_state.get("current_role", "") or "-",
        "qa_workspace": qa_state,
        "qa_workspace_followup": qa_workspace_followup,
        "dirty_blocking": has_blocking_dirty_status(project_abs),
        "integration_exists": git_branch_exists(integration_branch, project_abs),
        "implementation": implementation,
        "active_runs": active_runs,
        "active_waves": active_waves,
        "profile_gap": profile_gap,
        "dashboard_comments": dashboard_comments,
        "model_fallbacks": model_fallbacks,
        "next_actions": next_actions[:3],
    }


def collect_model_fallbacks(project_dir="."):
    exec_dir = os.path.join(os.path.abspath(project_dir), "docs", "runs", "_exec")
    if not os.path.isdir(exec_dir):
        return []

    candidates = []
    try:
        for name in os.listdir(exec_dir):
            if not name.endswith((".json", ".jsonl")):
                continue
            path = os.path.join(exec_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    if name.endswith(".jsonl"):
                        rows = [
                            json.loads(line)
                            for line in f
                            if line.strip().startswith("{")
                        ]
                        payload = rows[-1] if rows else {}
                    else:
                        payload = json.load(f)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            reason = str(payload.get("model_fallback_reason") or "").strip()
            if not reason:
                continue
            target_id = (
                payload.get("target_id")
                or payload.get("run_id")
                or payload.get("review_id")
                or "-"
            )
            candidates.append({
                "target_id": target_id,
                "runner": payload.get("runner") or "-",
                "model": payload.get("model") or "-",
                "reasoning_effort": payload.get("reasoning_effort") or "",
                "model_source": payload.get("model_source") or "",
                "model_fallback_reason": reason,
                "status": payload.get("status") or "",
                "path": os.path.relpath(path, os.path.abspath(project_dir)).replace("\\", "/"),
                "mtime": os.path.getmtime(path),
            })
    except Exception:
        return []

    seen = set()
    deduped = []
    for item in sorted(candidates, key=lambda value: value.get("mtime") or 0, reverse=True):
        key = (item.get("target_id"), item.get("runner"), item.get("model_fallback_reason"))
        if key in seen:
            continue
        seen.add(key)
        item.pop("mtime", None)
        deduped.append(item)
        if len(deduped) >= 5:
            break
    return deduped


def collect_dashboard_comments(project_dir="."):
    comments_path = os.path.join(os.path.abspath(project_dir), ".vulcan", "comments", "comments.jsonl")
    summary = {
        "path": ".vulcan/comments/comments.jsonl",
        "total": 0,
        "open": 0,
        "closed": 0,
        "items": [],
    }
    if not os.path.exists(comments_path):
        return summary

    try:
        with open(comments_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                status = str(item.get("status") or "open").strip().lower()
                if status in ("resolved", "converted", "stale"):
                    status = "closed"
                if status not in ("open", "closed"):
                    status = "open"
                summary["total"] += 1
                summary[status] += 1
                if status == "open":
                    anchor = item.get("anchor") if isinstance(item.get("anchor"), dict) else {}
                    summary["items"].append({
                        "comment_id": item.get("comment_id") or "",
                        "document": item.get("document") or "",
                        "category": item.get("category") or "note",
                        "line": anchor.get("start_line") or "",
                        "body": truncate_dashboard_message(item.get("body") or "", limit=90),
                    })
    except Exception:
        summary["read_error"] = True
    return summary


def _doctor_add(checks, category, name, status, detail="", recommendation=""):
    checks.append({
        "category": category,
        "name": name,
        "status": status,
        "detail": detail,
        "recommendation": recommendation,
    })


def _doctor_command_version(command, args=None, cwd="."):
    exe = shutil.which(command)
    if not exe:
        return None, f"{command} not found"
    try:
        result = subprocess.run(
            [exe] + list(args or ["--version"]),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return "", str(e)
    text = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0:
        return "", text or f"exit code {result.returncode}"
    return text.splitlines()[0] if text else "", ""


def _doctor_json_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _doctor_package_json_paths(project_dir):
    candidates = [
        "package.json",
        "frontend/package.json",
        "client/package.json",
        "web/package.json",
        "app/package.json",
        "dashboard/package.json",
    ]
    paths = []
    for rel_path in candidates:
        abs_path = os.path.join(project_dir, rel_path)
        if os.path.exists(abs_path):
            paths.append(abs_path)
    return paths


def _doctor_package_has_dependency(package_data, dependency):
    if not isinstance(package_data, dict):
        return False
    for key in ("dependencies", "devDependencies", "optionalDependencies"):
        values = package_data.get(key)
        if isinstance(values, dict) and dependency in values:
            return True
    return False


def _doctor_dir_nonempty(path):
    try:
        return os.path.isdir(path) and bool(os.listdir(path))
    except OSError:
        return False


def _doctor_local_port_open(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=0.4):
            return True
    except OSError:
        return False


def collect_doctor_checks(project_dir="."):
    project_abs = os.path.abspath(project_dir)
    checks = []

    _doctor_add(checks, "project", "project_dir", "pass" if os.path.isdir(project_abs) else "fail", project_abs)

    session_path = os.path.join(project_abs, "session.json")
    session = _doctor_json_file(session_path)
    if session is None:
        _doctor_add(checks, "project", "session.json", "warn", "not found or invalid", "init된 Ex 프로젝트라면 session.json을 확인하세요.")
    else:
        _doctor_add(
            checks,
            "project",
            "session.json",
            "pass",
            f"project={session.get('project') or '-'}, current_gate={session.get('current_gate') or '-'}",
        )

    config_path = os.path.join(project_abs, "vulcan.config.json")
    config = _doctor_json_file(config_path)
    if config is None:
        _doctor_add(checks, "project", "vulcan.config.json", "warn", "not found or invalid", "profile/default runner 설정이 없으면 기본값으로 동작합니다.")
    else:
        profile = load_delivery_profile(project_abs)
        runtime_config = config.get("runtime") if isinstance(config.get("runtime"), dict) else {}
        primary = runtime_config.get("primary") or runtime_config.get("primary_runner") or "-"
        _doctor_add(checks, "project", "vulcan.config.json", "pass", f"profile={profile}, primary_runner={primary}")

    python_detail = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ({sys.executable})"
    _doctor_add(checks, "tool", "python", "pass", python_detail)

    git_version, git_error = _doctor_command_version("git", ["--version"], cwd=project_abs)
    if git_version is None:
        _doctor_add(checks, "tool", "git", "fail", git_error, "Git 설치 또는 PATH를 확인하세요.")
    elif git_version == "":
        _doctor_add(checks, "tool", "git", "warn", git_error)
    else:
        git_inside_worktree = git_text(["rev-parse", "--is-inside-work-tree"], project_abs) == "true"
        branch = git_current_branch(project_abs)
        dirty = bool(git_status_porcelain(project_abs))
        remote = has_git_remote(project_abs)
        _doctor_add(
            checks,
            "tool",
            "git",
            "pass" if git_inside_worktree else "warn",
            f"{git_version}; git_repo={git_inside_worktree}; branch={branch}; dirty={dirty}; origin={remote}",
            "init된 Ex 프로젝트라면 git 저장소가 있어야 합니다." if not git_inside_worktree else "",
        )

    node_version, node_error = _doctor_command_version("node", ["--version"], cwd=project_abs)
    if node_version is None:
        _doctor_add(checks, "tool", "node", "warn", node_error, "Frontend/Dashboard/Playwright 작업 전 Node.js를 설치하세요.")
    elif node_version == "":
        _doctor_add(checks, "tool", "node", "warn", node_error)
    else:
        _doctor_add(checks, "tool", "node", "pass", node_version)

    npm_version, npm_error = _doctor_command_version("npm", ["--version"], cwd=project_abs)
    if npm_version is None:
        _doctor_add(checks, "tool", "npm", "warn", npm_error, "Frontend 의존성 설치와 Playwright 실행 전 npm을 확인하세요.")
    elif npm_version == "":
        _doctor_add(checks, "tool", "npm", "warn", npm_error)
    else:
        _doctor_add(checks, "tool", "npm", "pass", npm_version)

    package_paths = _doctor_package_json_paths(project_abs)
    if package_paths:
        rel_packages = [normalize_repo_path(os.path.relpath(path, project_abs)) for path in package_paths]
        _doctor_add(checks, "frontend", "package.json", "pass", ", ".join(rel_packages))
    else:
        _doctor_add(checks, "frontend", "package.json", "info", "not found", "Frontend 없는 프로젝트라면 무시해도 됩니다.")

    playwright_packages = []
    package_with_node_modules = []
    for package_path in package_paths:
        package_data = _doctor_json_file(package_path)
        rel_package = normalize_repo_path(os.path.relpath(package_path, project_abs))
        package_dir = os.path.dirname(package_path)
        if _doctor_package_has_dependency(package_data, "@playwright/test") or _doctor_package_has_dependency(package_data, "playwright"):
            playwright_packages.append(rel_package)
        if os.path.isdir(os.path.join(package_dir, "node_modules")):
            package_with_node_modules.append(rel_package)

    if package_paths and not package_with_node_modules:
        _doctor_add(checks, "frontend", "node_modules", "warn", "package.json exists but node_modules not found", "lockfile 기준 npm ci/npm install 가능 여부를 QA-000에서 확인하세요.")
    elif package_with_node_modules:
        _doctor_add(checks, "frontend", "node_modules", "pass", ", ".join(package_with_node_modules))

    if playwright_packages:
        _doctor_add(checks, "playwright", "package", "pass", ", ".join(playwright_packages))
    elif package_paths:
        _doctor_add(checks, "playwright", "package", "warn", "@playwright/test not found in detected package.json", "Audit/Product UI Pass에는 @playwright/test와 npx playwright test 증적이 필요합니다.")
    else:
        _doctor_add(checks, "playwright", "package", "info", "package.json not found")

    cache_candidates = []
    env_cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env_cache:
        cache_candidates.append(env_cache)
    cache_candidates.extend([
        os.path.join(project_abs, ".vulcan", "cache", "ms-playwright"),
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright"),
        os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright"),
    ])
    existing_caches = [path for path in cache_candidates if _doctor_dir_nonempty(path)]
    if existing_caches:
        _doctor_add(checks, "playwright", "browser_cache", "pass", "; ".join(existing_caches[:3]))
    elif playwright_packages:
        _doctor_add(checks, "playwright", "browser_cache", "warn", "not found", "npx playwright install 또는 프로젝트 지정 cache를 준비하세요.")
    else:
        _doctor_add(checks, "playwright", "browser_cache", "info", "not checked")

    npm_cache = os.environ.get("npm_config_cache") or os.environ.get("NPM_CONFIG_CACHE") or os.path.join(project_abs, ".vulcan", "cache", "npm")
    _doctor_add(
        checks,
        "cache",
        "npm_cache",
        "pass" if os.path.isdir(npm_cache) else "info",
        npm_cache,
        "worker npm 설치가 막히면 npm_config_cache를 이 경로로 고정할 수 있습니다.",
    )

    runners = detect_runtime_runners()
    if runners:
        runner_details = []
        for runner in runners:
            model = runner.get("model") or "-"
            effort = runner.get("effort") or runner.get("reasoning_effort") or "-"
            runner_details.append(f"{runner.get('name')}({model}/{effort})")
        _doctor_add(checks, "runner", "available_runners", "pass", ", ".join(runner_details))
    else:
        _doctor_add(checks, "runner", "available_runners", "warn", "none detected", "codex/claude/agy CLI가 필요하면 설치와 로그인을 확인하세요.")

    dashboard_dir = os.path.join(project_abs, "dashboard")
    if os.path.exists(os.path.join(dashboard_dir, "package.json")):
        dashboard_status = "running" if _doctor_local_port_open("127.0.0.1", 3001) else "not running"
        _doctor_add(checks, "dashboard", "dashboard", "pass", f"package found; port 3001 {dashboard_status}")
    else:
        _doctor_add(checks, "dashboard", "dashboard", "info", "dashboard/package.json not found in this project", "보통 dashboard는 Ex 루트에서 실행합니다.")

    return checks


def cmd_doctor(project_dir=".", emit_json=False):
    project_abs = os.path.abspath(project_dir)
    checks = collect_doctor_checks(project_abs)
    counts = {"pass": 0, "warn": 0, "fail": 0, "info": 0}
    for check in checks:
        status = check.get("status") or "info"
        counts[status] = counts.get(status, 0) + 1

    if emit_json:
        print(json.dumps({
            "project_dir": project_abs,
            "summary": counts,
            "checks": checks,
        }, ensure_ascii=False, indent=2))
    else:
        print("==================================================")
        print(" [doctor] Vulcan local environment check")
        print("==================================================")
        print(f" project_dir: {project_abs}")
        for check in checks:
            status = (check.get("status") or "info").upper()
            line = f" [{status}] {check.get('category')}.{check.get('name')}: {check.get('detail') or '-'}"
            print(line)
            if check.get("recommendation") and check.get("status") in {"warn", "fail"}:
                print(f"        -> {check.get('recommendation')}")
        print("--------------------------------------------------")
        print(f" summary: pass {counts.get('pass', 0)}, warn {counts.get('warn', 0)}, fail {counts.get('fail', 0)}, info {counts.get('info', 0)}")
        print("==================================================")

    if counts.get("fail", 0):
        sys.exit(1)


def capture_prepare_transition_summary(project_dir="."):
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = 0
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            cmd_prepare_transition(project_dir)
        except SystemExit as exc:
            try:
                exit_code = int(exc.code)
            except (TypeError, ValueError):
                exit_code = 1
    return {
        "command": "python vulcan.py prepare-transition",
        "status": "pass" if exit_code == 0 else "fail",
        "exit_code": exit_code,
        "stdout_lines": stdout.getvalue().splitlines(),
        "stderr_lines": stderr.getvalue().splitlines(),
    }


def capture_trace_detail_summary(project_dir="."):
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = 0
    issues = []
    warnings = []
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            issues, warnings = check_trace(project_dir, exit_on_error=False)
        except SystemExit as exc:
            try:
                exit_code = int(exc.code)
            except (TypeError, ValueError):
                exit_code = 1
    if issues and exit_code == 0:
        exit_code = 1
    return {
        "command": "python vulcan.py check-trace",
        "status": "pass" if exit_code == 0 else "fail",
        "exit_code": exit_code,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "stdout_lines": stdout.getvalue().splitlines(),
        "stderr_lines": stderr.getvalue().splitlines(),
    }


def cmd_status(project_dir=".", check=False, trace_detail=False, emit_json=False):
    summary = collect_status_summary(project_dir)

    if emit_json:
        exit_code = 0
        if check:
            transition_check = capture_prepare_transition_summary(project_dir)
            summary["transition_check"] = transition_check
            if transition_check["exit_code"]:
                exit_code = transition_check["exit_code"]
        if trace_detail:
            trace_check = capture_trace_detail_summary(project_dir)
            summary["trace_detail"] = trace_check
            if trace_check["exit_code"] and exit_code == 0:
                exit_code = trace_check["exit_code"]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if exit_code:
            sys.exit(exit_code)
        return

    print("==================================================")
    print(" [status] Vulcan Orchestrator status")
    print("==================================================")
    print(f" project: {summary['project']}")
    print(f" profile: {summary['profile']}")
    print(f" current_gate: {summary['current_gate']}")
    print(f" gate_status: {summary['gate_status']}")
    print()
    print(" branch")
    print(f"  current_branch: {summary['current_branch']}")
    print(f"  main_branch: {summary['main_branch']}")
    print(f"  integration_branch: {summary['integration_branch']}")
    print(f"  integration_exists: {summary['integration_exists']}")
    print(f"  dirty_blocking: {summary['dirty_blocking']}")
    print(f"  session_branch_role: {summary['session_branch_role']}")
    qa_state = summary.get("qa_workspace") or {}
    if qa_state:
        print(" qa_workspace")
        print(f"  path: {qa_state.get('path') or '-'}")
        print(f"  mode: {qa_state.get('mode') or '-'}")
        print(f"  status: {qa_state.get('status') or '-'}")
        print(f"  last_stage: {qa_state.get('last_stage') or '-'}")
        followup = summary.get("qa_workspace_followup") or []
        if followup:
            print("  followup")
            for item in followup:
                print(f"   - {item}")
    print()

    implementation = summary.get("implementation") or {}
    if implementation:
        impl_counts = implementation_display_counts(implementation)
        print(" implementation")
        print(f"  implemented: {impl_counts['implemented']} / {impl_counts['total']}")
        print(f"  percent: {impl_counts['percent']}")
        print(f"  waves: {impl_counts['waves_completed']} / {impl_counts['waves_total']}")
        if impl_counts["waves_current"]:
            print(f"  current_wave: {impl_counts['waves_current']}")
        print()

    active_runs = summary.get("active_runs") or []
    print(f" active_runs: {len(active_runs)}")
    for run in active_runs[:5]:
        print(f"  - {run['path']} ({run['status']})")
    if len(active_runs) > 5:
        print(f"  ... 외 {len(active_runs) - 5}건")

    active_waves = summary.get("active_waves") or []
    print(f" active_waves: {len(active_waves)}")
    for wave in active_waves[:5]:
        run_suffix = f" / {wave.get('run')}" if wave.get("run") else ""
        print(f"  - {wave.get('id')} ({wave.get('status')}){run_suffix}")
    if len(active_waves) > 5:
        print(f"  ... 외 {len(active_waves) - 5}건")
    print()

    model_fallbacks = summary.get("model_fallbacks") or []
    if model_fallbacks:
        print(" model_fallbacks")
        for item in model_fallbacks[:5]:
            effort = f" / {item.get('reasoning_effort')}" if item.get("reasoning_effort") else ""
            source = f" ({item.get('model_source')})" if item.get("model_source") else ""
            print(
                f"  - {item.get('target_id')} {item.get('runner')}: "
                f"{item.get('model')}{effort}{source}"
            )
            print(f"    reason: {item.get('model_fallback_reason')}")
        print()

    profile_gap = summary.get("profile_gap") or {}
    if profile_gap:
        gap_summary = profile_gap.get("summary") or {}
        print(" profile_gap")
        print(f"  target_profile: {profile_gap.get('target_profile') or '-'}")
        print(
            "  docs: "
            f"ok {gap_summary.get('ok', 0)}, "
            f"partial {gap_summary.get('partial', 0)}, "
            f"missing {gap_summary.get('missing', 0)}"
        )
        print(
            "  content: "
            f"issues {gap_summary.get('content_issues', 0)}, "
            f"warnings {gap_summary.get('content_warnings', 0)}"
        )
        if profile_gap.get("read_error"):
            print(f"  read_error: {profile_gap.get('read_error')}")
        print()

    comments = summary.get("dashboard_comments") or {}
    if comments.get("total"):
        print(" dashboard_comments")
        print(f"  path: {comments.get('path')}")
        print(
            f"  open: {comments.get('open', 0)} / total: {comments.get('total', 0)} "
            f"(closed {comments.get('closed', 0)})"
        )
        for item in (comments.get("items") or [])[:5]:
            line = f":L{item.get('line')}" if item.get("line") else ""
            print(f"  - {item.get('comment_id') or '-'} [{item.get('category')}] {item.get('document')}{line} - {item.get('body')}")
        if comments.get("open", 0) > 5:
            print(f"  ... 외 {comments.get('open', 0) - 5}건")
        print()

    print(" next_actions")
    for action in summary.get("next_actions") or []:
        print(f"  - {action}")
    print("==================================================")

    if trace_detail:
        print()
        print("[status --trace-detail] check-trace 상세 진단")
        issues, _warnings = check_trace(project_dir, exit_on_error=False)
        if issues:
            sys.exit(1)

    if check:
        print()
        print("[status --check] prepare-transition 상세 진단")
        cmd_prepare_transition(project_dir)


def _git_log_records(project_dir="."):
    try:
        result = subprocess.run(
            ["git", "log", "--reverse", "--date=iso-strict-local", "--format=%h%x09%cI%x09%s"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError:
        return []
    records = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        commit, iso_value, subject = parts
        try:
            ts = datetime.fromisoformat(iso_value)
        except ValueError:
            ts = None
        records.append({"commit": commit, "time": iso_value, "datetime": ts, "subject": subject})
    return records


def _count_text_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _is_binary_evidence(rel_path):
    return os.path.splitext(rel_path.lower())[1] in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".pdf", ".mp4", ".webm"}


def _classify_metric_file(rel_path):
    rel = normalize_repo_path(rel_path)
    if rel.startswith("docs/runs/"):
        return "runs"
    if rel.startswith("docs/poc/evidence/") or rel.startswith("docs/artifacts/04-review/evidence/"):
        return "evidence"
    if rel.startswith(("docs/poc/", "docs/artifacts/", "docs/backlog/", "docs/reference/")) or rel == "README.md":
        return "docs"
    if rel in {"session.json", "vulcan.config.json"}:
        return "metadata"
    if rel.startswith(("app/", "backend/", "frontend/", "static/", "tests/", "src/")) or rel in {"requirements.txt", "package.json", "package-lock.json", "pyproject.toml"}:
        return "code"
    return "other"


def _changed_files_since_root(project_dir="."):
    try:
        root_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        root = root_result.stdout.splitlines()[0].strip()
        diff_result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "diff", "--name-only", f"{root}..HEAD"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        files = [line.strip() for line in diff_result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, IndexError):
        files = []
    status_files = [entry.get("path") for entry in parse_git_status_entries(git_status_porcelain_all(project_dir))]
    return sorted(set([f for f in files + status_files if f]))


def _first_yaml_scalar(content, key):
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", content)
    if not match:
        return ""
    value = match.group(1).strip()
    if value.lower() in {"null", "~"}:
        return ""
    return value.strip('"').strip("'")


def _first_yaml_int(content, key):
    value = _first_yaml_scalar(content, key)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _collect_delegation_lifecycle(rel_path, content):
    if "delegation_records" not in content:
        return []
    has_lifecycle = any(
        re.search(rf"(?im)^\s*{field}\s*:", content)
        for field in (
            "started_at",
            "completed_at",
            "duration_seconds",
            "first_file_change_at",
            "last_file_change_at",
            "worker_final_response_at",
            "final_response_lag_seconds",
        )
    )
    if not has_lifecycle:
        return []
    return [{
        "run": rel_path,
        "mode": _first_yaml_scalar(content, "mode"),
        "delegate": _first_yaml_scalar(content, "delegate"),
        "started_at": _first_yaml_scalar(content, "started_at"),
        "completed_at": _first_yaml_scalar(content, "completed_at"),
        "duration_seconds": _first_yaml_int(content, "duration_seconds"),
        "first_file_change_at": _first_yaml_scalar(content, "first_file_change_at"),
        "last_file_change_at": _first_yaml_scalar(content, "last_file_change_at"),
        "worker_final_response_at": _first_yaml_scalar(content, "worker_final_response_at"),
        "final_response_lag_seconds": _first_yaml_int(content, "final_response_lag_seconds"),
        "heartbeat_count": _first_yaml_int(content, "heartbeat_count"),
        "status_probe_count": _first_yaml_int(content, "status_probe_count"),
    }]


def collect_project_metrics(project_dir="."):
    project_abs = os.path.abspath(project_dir)
    summary = collect_status_summary(project_abs)
    log_records = _git_log_records(project_abs)
    started_at = log_records[0]["time"] if log_records else ""
    ended_at = log_records[-1]["time"] if log_records else ""
    elapsed_seconds = None
    if log_records and log_records[0].get("datetime") and log_records[-1].get("datetime"):
        elapsed_seconds = int((log_records[-1]["datetime"] - log_records[0]["datetime"]).total_seconds())

    gate_done_commits = []
    for record in log_records:
        match = re.search(r"session:\s+([a-z0-9]+)\s+done\b", record["subject"], re.IGNORECASE)
        if match:
            gate_done_commits.append({
                "gate": match.group(1),
                "commit": record["commit"],
                "time": record["time"],
                "subject": record["subject"],
            })

    file_groups = {}
    for rel_path in _changed_files_since_root(project_abs):
        group = _classify_metric_file(rel_path)
        abs_path = os.path.join(project_abs, rel_path)
        info = file_groups.setdefault(group, {"files": 0, "lines": 0, "binary_files": 0, "paths": []})
        info["files"] += 1
        info["paths"].append(rel_path)
        if _is_binary_evidence(rel_path):
            info["binary_files"] += 1
        elif os.path.isfile(abs_path):
            info["lines"] += _count_text_lines(abs_path)

    run_files = []
    delegation_records = 0
    delegation_lifecycle = []
    runs_dir = os.path.join(project_abs, runs_rel_dir(project_abs))
    if os.path.isdir(runs_dir):
        for name in sorted(os.listdir(runs_dir)):
            if not name.lower().endswith(".md"):
                continue
            rel = normalize_repo_path(os.path.join(runs_rel_dir(project_abs), name))
            content = read_project_text(project_abs, rel)
            run_files.append(rel)
            delegation_records += len(re.findall(r"(?im)^\s*-\s*(?:mode|runner|delegate|persona)\s*:", content))
            delegation_lifecycle.extend(_collect_delegation_lifecycle(rel, content))

    return {
        "project": summary["project"],
        "profile": summary["profile"],
        "current_gate": summary["current_gate"],
        "current_branch": summary["current_branch"],
        "dirty_blocking": summary["dirty_blocking"],
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_seconds": elapsed_seconds,
        "commits": len(log_records),
        "gate_done_commits": gate_done_commits,
        "file_groups": file_groups,
        "runs": {
            "files": len(run_files),
            "paths": run_files,
            "delegation_record_like_entries": delegation_records,
            "delegation_lifecycle": delegation_lifecycle,
        },
        "implementation": summary.get("implementation") or {},
    }


def format_duration(seconds):
    if seconds is None:
        return "-"
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def cmd_metrics(project_dir=".", emit_json=False):
    metrics = collect_project_metrics(project_dir)
    if emit_json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return

    print("==================================================")
    print(" [metrics] Vulcan project metrics")
    print("==================================================")
    print(f" project: {metrics['project']}")
    print(f" profile: {metrics['profile']}")
    print(f" current_gate: {metrics['current_gate']}")
    print(f" current_branch: {metrics['current_branch']}")
    print(f" dirty_blocking: {metrics['dirty_blocking']}")
    print(f" elapsed: {format_duration(metrics['elapsed_seconds'])}")
    print(f" commits: {metrics['commits']}")
    print()
    print(" gate_done_commits")
    for item in metrics["gate_done_commits"]:
        print(f"  - {item['gate']}: {item['time']} ({item['commit']})")
    if not metrics["gate_done_commits"]:
        print("  - none")
    print()
    print(" file_groups")
    for group, info in sorted(metrics["file_groups"].items()):
        print(f"  - {group}: files={info['files']}, lines={info['lines']}, binary={info['binary_files']}")
    print()
    print(" runs")
    print(f"  files: {metrics['runs']['files']}")
    print(f"  delegation_record_like_entries: {metrics['runs']['delegation_record_like_entries']}")
    lifecycle = metrics["runs"].get("delegation_lifecycle") or []
    if lifecycle:
        print("  delegation_lifecycle")
        for item in lifecycle:
            label = item.get("delegate") or item.get("mode") or item.get("run")
            duration = format_duration(item.get("duration_seconds"))
            lag = format_duration(item.get("final_response_lag_seconds"))
            print(f"    - {label}: duration={duration}, final_response_lag={lag}, run={item.get('run')}")
    print("==================================================")


def cmd_branch_start(stage="impl", project_dir="."):
    project_abs = os.path.abspath(project_dir)
    workflow = workflow_policy(project_abs)
    if workflow.get("branch_mode") in ("none", "single", "disabled"):
        print("오류: workflow.branch_mode가 단일 브랜치 모드입니다.")
        sys.exit(1)
    if stage != "impl":
        print(f"오류: 현재 지원하는 branch-start stage는 impl뿐입니다: {stage}")
        sys.exit(1)

    session = load_session(project_abs)
    current_gate = session.get("current_gate")
    if current_gate not in ("impl", "gate4", "gate5"):
        print(f"오류: impl 통합 브랜치는 impl 진입 후 시작합니다. 현재 Gate: {current_gate}")
        print("  먼저 이전 Gate 승인 후 python vulcan.py gate-start impl 을 실행하세요.")
        sys.exit(1)

    if has_blocking_dirty_status(project_abs):
        print("오류: 브랜치 전환 전 미커밋 변경이 있습니다.")
        print("  먼저 변경사항을 커밋하거나 정리한 뒤 다시 실행하세요.")
        sys.exit(1)

    main_branch = workflow.get("main_branch") or "main"
    integration_branch = workflow.get("integration_branch") or "dev"
    current_branch = git_current_branch(project_abs)

    if current_branch == integration_branch:
        print(f"  이미 통합 브랜치입니다: {integration_branch}")
    elif git_branch_exists(integration_branch, project_abs):
        git_checkout_branch(integration_branch, create=False, project_dir=project_abs)
        print(f"  브랜치 전환: {integration_branch}")
    else:
        if current_branch != main_branch:
            print(f"오류: `{integration_branch}` 브랜치를 처음 만들 때는 `{main_branch}`에서 시작해야 합니다.")
            print(f"  현재 브랜치: {current_branch}")
            sys.exit(1)
        git_checkout_branch(integration_branch, create=True, project_dir=project_abs)
        print(f"  브랜치 생성 및 전환: {integration_branch}")

    session["branch_state"] = {
        "main_branch": main_branch,
        "integration_branch": integration_branch,
        "current_role": "integration",
        "current_branch": integration_branch,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "stage": stage,
    }
    refresh_session_stats(session, project_abs)
    save_session(session, project_abs)
    committed = git_commit(
        f"session: branch start {stage} - {integration_branch}",
        project_abs,
        paths=["session.json"],
    )
    if committed:
        git_push_if_remote(project_abs)


def release_pr_body(project_dir, base_branch, head_branch, title):
    session = load_session(project_dir)
    project_name = session.get("project") or session.get("name") or os.path.basename(project_dir)
    profile = load_delivery_profile(project_dir)
    if profile == "poc":
        release_doc = "docs/poc/POC_TEST_REPORT.md"
        evidence_documents = [
            "docs/poc/POC_REQUIREMENTS.md",
            "docs/poc/POC_SYSTEM_DESIGN.md",
            "docs/poc/POC_TEST_REPORT.md",
        ]
        verification_checklist = [
            "`python vulcan.py status --check`",
            "PoC evidence logs and smoke result reviewed",
            "Open ISSUE/Backlog/promotion candidates reviewed",
            "PoC continue/pivot/stop decision reviewed",
            "Independent review completed or explicitly waived",
        ]
    elif profile == "product":
        release_doc = "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md"
        evidence_documents = [
            release_doc,
            "docs/product/PRODUCT_BRIEF.md",
            "docs/product/PRODUCT_CONTRACTS.md",
            "docs/product/PRODUCT_TRACEABILITY.md",
            "docs/product/REGRESSION_AND_RELEASE_REPORT.md",
            "docs/backlog/DOC-PM-OPS-001_Backlog_v0.1.md",
        ]
        verification_checklist = [
            "`python vulcan.py status --check`",
            "Product regression result and release scope reviewed",
            "Product traceability and backlog/deferred items reviewed",
            "Gate 4 UI/API evidence reviewed",
            "Release approval document reviewed",
            "Independent PR review completed or explicitly waived",
        ]
    else:
        release_doc = "docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md"
        evidence_documents = [
            release_doc,
            "docs/artifacts/04-review/DOC-QA-G4-001_QA-Finding_v0.1.md",
            "docs/artifacts/04-review/DOC-QA-G4-002_Test-Result_v0.1.md",
            "docs/artifacts/02-traceability/DOC-CORE-G4-001_Traceability-Matrix_v0.1.md",
        ]
        verification_checklist = [
            "`python vulcan.py check-trace`",
            "`python vulcan.py check-contract` if Program Design contracts are in scope",
            "Gate 4 QA command logs and evidence reviewed",
            "Open FIND/CR/ISSUE/Backlog items reviewed",
            "Release approval document reviewed",
            "Independent PR review completed or explicitly waived",
        ]

    diff_stat = git_text(["diff", "--stat", f"{base_branch}...{head_branch}"], project_dir)
    commit_log = git_text(["log", "--oneline", "--decorate", f"{base_branch}..{head_branch}"], project_dir)
    if not diff_stat:
        diff_stat = "(no local diff stat available)"
    if not commit_log:
        commit_log = "(no local commits found between base/head)"

    doc_lines = []
    for rel_path in evidence_documents:
        marker = "OK" if os.path.exists(os.path.join(project_dir, rel_path)) else "MISSING"
        doc_lines.append(f"- [{marker}] `{rel_path}`")
    checklist_lines = "\n".join(f"- [ ] {item}" for item in verification_checklist)

    return f"""# {title}

## Release Candidate

- Project: `{project_name}`
- Profile: `{profile}`
- Base: `{base_branch}`
- Head: `{head_branch}`
- Source of truth: `{release_doc}`
- Merge policy: manual only after Gate 5 approval

## Gate 5 Evidence Documents

{chr(10).join(doc_lines)}

## Verification Checklist

{checklist_lines}

## Diff Stat

```text
{diff_stat}
```

## Commits

```text
{commit_log}
```

## Notes

This PR is a Gate 5 release candidate from the integration branch to the release baseline.
It must not be auto-merged by runner output alone. Merge requires explicit user approval or the project's Gate 5 release approval process.
"""


def release_pr_body_path(project_dir):
    body_dir = os.path.join(project_dir, ".vulcan", "release")
    os.makedirs(body_dir, exist_ok=True)
    return os.path.join(body_dir, "release-pr-body.md")


def gh_available():
    return bool(shutil.which("gh"))


def gh_open_release_pr(project_dir, base_branch, head_branch, title, body_path, dry_run=False):
    list_cmd = [
        "gh", "pr", "list",
        "--base", base_branch,
        "--head", head_branch,
        "--state", "open",
        "--json", "number,url",
        "--limit", "10",
    ]
    create_cmd = [
        "gh", "pr", "create",
        "--base", base_branch,
        "--head", head_branch,
        "--title", title,
        "--body-file", body_path,
    ]

    if dry_run:
        print("Dry-run: GitHub PR command")
        print("  " + " ".join(create_cmd))
        return

    list_result = subprocess.run(
        list_cmd,
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if list_result.returncode == 0:
        try:
            existing = json.loads(list_result.stdout or "[]")
        except json.JSONDecodeError:
            existing = []
        if existing:
            pr = existing[0]
            number = str(pr.get("number") or "")
            edit_cmd = ["gh", "pr", "edit", number, "--title", title, "--body-file", body_path]
            edit_result = subprocess.run(
                edit_cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if edit_result.returncode != 0:
                detail = (edit_result.stderr or edit_result.stdout or "").strip()
                print(f"오류: 기존 PR 갱신 실패 - {detail}")
                sys.exit(edit_result.returncode)
            print(f"Release PR 갱신: {pr.get('url') or ('#' + number)}")
            return

    create_result = subprocess.run(
        create_cmd,
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if create_result.returncode != 0:
        detail = (create_result.stderr or create_result.stdout or "").strip()
        print(f"오류: Release PR 생성 실패 - {detail}")
        sys.exit(create_result.returncode)
    print(f"Release PR 생성: {(create_result.stdout or '').strip()}")


def cmd_release_pr(base="", head="", title="", dry_run=False, no_push=False, project_dir="."):
    project_abs = os.path.abspath(project_dir)
    workflow = workflow_policy(project_abs)
    if workflow.get("branch_mode") in ("none", "single", "disabled") or not workflow.get("impl_uses_integration_branch", True):
        print("Release PR 생략: workflow가 통합 브랜치 기반이 아닙니다.")
        return

    session = load_session(project_abs)
    current_gate = session.get("current_gate")
    gate_status = session.get("gate_status", {}) if isinstance(session.get("gate_status"), dict) else {}
    if current_gate != "gate5" and gate_status.get("gate5") != "done":
        print(f"오류: release-pr은 Gate 5에서 실행합니다. 현재 Gate: {current_gate or '-'}")
        print("  먼저 Gate 4 완료 후 python vulcan.py gate-start gate5 를 실행하세요.")
        sys.exit(1)

    base_branch = base or workflow.get("release_merge_to") or workflow.get("main_branch") or "main"
    head_branch = head or workflow.get("integration_branch") or "dev"
    current_branch = git_current_branch(project_abs)
    if current_branch != head_branch:
        print(f"오류: release-pr은 통합 브랜치 `{head_branch}`에서 실행합니다. 현재 브랜치: `{current_branch}`")
        sys.exit(1)
    if not git_branch_exists(base_branch, project_abs):
        print(f"오류: release-pr base 브랜치를 찾을 수 없습니다: `{base_branch}`")
        print("  workflow.release_merge_to 또는 --base 값을 확인하세요.")
        sys.exit(1)
    if not git_branch_exists(head_branch, project_abs):
        print(f"오류: release-pr head 브랜치를 찾을 수 없습니다: `{head_branch}`")
        print("  workflow.integration_branch 또는 --head 값을 확인하세요.")
        sys.exit(1)

    release_doc = os.path.join(project_abs, "docs", "artifacts", "07-release", "DOC-PM-G5-001_Release-Approval_v0.1.md")
    if not os.path.exists(release_doc):
        print("오류: Gate 5 릴리즈 승인서가 없습니다.")
        print("  필요 문서: docs/artifacts/07-release/DOC-PM-G5-001_Release-Approval_v0.1.md")
        sys.exit(1)

    if has_blocking_dirty_status(project_abs):
        print("오류: release-pr 생성 전 미커밋 변경이 있습니다.")
        print("  Gate 5 승인서, QA 결과, backlog/session 변경을 먼저 커밋한 뒤 다시 실행하세요.")
        print_blocking_dirty_summary(project_abs)
        if dry_run:
            print("  note: dry-run도 PR body 생성 기준을 고정하기 위해 clean worktree를 요구합니다.")
        sys.exit(1)

    pr_title = title or f"Gate 5 release: {session.get('project') or os.path.basename(project_abs)}"
    body = release_pr_body(project_abs, base_branch, head_branch, pr_title)
    body_path = release_pr_body_path(project_abs)
    with open(body_path, "w", encoding="utf-8") as f:
        f.write(body)

    print("Vulcan release PR")
    print(f"  base: {base_branch}")
    print(f"  head: {head_branch}")
    print(f"  title: {pr_title}")
    print(f"  body: {body_path}")

    if dry_run:
        print("\n--- PR body preview ---")
        print(body)
        if gh_available():
            gh_open_release_pr(project_abs, base_branch, head_branch, pr_title, body_path, dry_run=True)
        else:
            print("Dry-run: gh CLI 없음. 아래 명령을 사용할 수 있습니다.")
            print(f"  gh pr create --base {base_branch} --head {head_branch} --title \"{pr_title}\" --body-file \"{body_path}\"")
        return

    if not gh_available() or not has_git_remote(project_abs):
        print("Release PR 자동 생성 생략: gh CLI 또는 git remote origin이 없습니다.")
        print("아래 명령으로 수동 생성할 수 있습니다.")
        print(f"  gh pr create --base {base_branch} --head {head_branch} --title \"{pr_title}\" --body-file \"{body_path}\"")
        return

    if not no_push:
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", head_branch],
            cwd=project_abs,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if push_result.returncode != 0:
            detail = (push_result.stderr or push_result.stdout or "").strip()
            print(f"오류: release-pr 전 통합 브랜치 push 실패 - {detail}")
            sys.exit(push_result.returncode)
        print(f"  푸시 완료: origin {head_branch}")

    gh_open_release_pr(project_abs, base_branch, head_branch, pr_title, body_path, dry_run=False)


def init(target_dir, project_name, agent_name, remote_url=None, require_remote=False, profile=None, primary=None):
    import shutil
    import sys
    profile_was_explicit = profile is not None
    if not profile_was_explicit and sys.stdin.isatty():
        profile_options = [
            ("audit", "감리/공식 제출 수준 문서와 강한 추적성"),
            ("product", "실사용/릴리즈 가능한 제품 기준"),
            ("poc", "가설 검증과 빠른 실험 중심"),
        ]
        print("프로젝트 Delivery Profile을 선택해 주세요:")
        for idx, (profile_key, desc) in enumerate(profile_options, 1):
            default_mark = " (기본값)" if profile_key == DEFAULT_DELIVERY_PROFILE else ""
            print(f"  {idx}) {profile_key}{default_mark} - {desc}")
        try:
            ans = input(f"선택 (1-{len(profile_options)}, 기본값: 1): ").strip()
            if ans:
                sel = int(ans)
                if 1 <= sel <= len(profile_options):
                    profile = profile_options[sel - 1][0]
        except (ValueError, IndexError, KeyboardInterrupt, EOFError):
            profile = DEFAULT_DELIVERY_PROFILE
    profile = normalize_delivery_profile(profile)
    print(f"\nVulcan-Anvil 초기화")
    print(f"  프로젝트: {project_name}")
    print(f"  대상 폴더: {target_dir}")
    print(f"  Delivery Profile: {profile}")

    if not primary:
        available_runners = detect_runtime_runners()
        if available_runners and sys.stdin.isatty():
            print("프로젝트에서 사용할 주 러너(Primary Runner)를 선택해 주세요:")
            for idx, r in enumerate(available_runners, 1):
                name = r.get("name", "unknown")
                display_name = "Agy / Antigravity CLI (antigravity-cli)" if name == "antigravity-cli" else name
                model = r.get("model", "")
                model_str = f" ({model})" if model else ""
                print(f"  {idx}) {display_name}{model_str}")
            print(f"  {len(available_runners) + 1}) 선택하지 않음 (기본값 설정)")
            try:
                ans = input(f"선택 (1-{len(available_runners) + 1}, 기본값: 1): ").strip()
                if ans:
                    sel = int(ans)
                    if 1 <= sel <= len(available_runners):
                        primary = available_runners[sel - 1].get("name")
                        print(f"  선택된 주 러너: {primary}\n")
            except (ValueError, IndexError, KeyboardInterrupt, EOFError):
                pass
    else:
        print(f"  지정된 주 러너: {primary}\n")

    if require_remote and not remote_url:
        print("오류: --require-remote가 지정되었지만 --remote가 없습니다.")
        print("  예: python vulcan.py init <dir> <name> --remote <git-url> --require-remote")
        sys.exit(1)

    if os.path.exists(target_dir):
        files = os.listdir(target_dir)
        if files:
            print(f"경고: {target_dir} 폴더가 비어있지 않습니다.")
            answer = input("계속 진행할까요? (y/N): ").strip().lower()
            if answer != "y":
                print("취소됨.")
                sys.exit(0)
    else:
        os.makedirs(target_dir)

    variables = {
        "PROJECT_NAME": project_name,
        "GENERATED_DATE": str(date.today()),
    }

    # .claude/ 디렉토리 전체 복사 후 변수 치환
    src_claude = os.path.join(TEMPLATES_DIR, ".claude")
    dst_claude = os.path.join(target_dir, ".claude")
    copy_tree(src_claude, dst_claude)
    print(f"  생성: .claude/ (agents 13, skills 5, rules 7)")

    # .claude/ 내 모든 .md 파일에 변수 치환 적용
    for root, dirs, files in os.walk(dst_claude):
        for f in files:
            if f.endswith(".md"):
                fpath = os.path.join(root, f)
                with open(fpath, encoding="utf-8") as fp:
                    content = render(fp.read(), variables)
                with open(fpath, "w", encoding="utf-8") as fp:
                    fp.write(content)

    # ENVIRONMENT.md
    content = render(read_template("ENVIRONMENT.md"), variables)
    write_file(target_dir, "ENVIRONMENT.md", content)

    # GATE_GUIDE.md
    copy_file(target_dir, "GATE_GUIDE.md")

    # README.md
    content = render(read_template("PROJECT_README.md"), variables)
    write_file(target_dir, "README.md", content)

    # docs/backlog/
    content = render(read_template("docs/backlog/BACKLOG.md"), variables)
    write_file(target_dir, BACKLOG_PATH, content)
    copy_file(target_dir, "docs/backlog/PROCESS.md", "docs/backlog/PROCESS.md")

    # audit and agent coding document framework
    install_project_doc_framework(target_dir, variables, overwrite=True)
    if profile == "poc":
        install_poc_artifacts(target_dir, variables, overwrite=False)
    elif profile == "product":
        install_product_artifacts(target_dir, variables, overwrite=False)
    else:
        install_project_artifacts(target_dir, variables, overwrite=False)

    # session.json
    create_session_json(target_dir, project_name, profile)
    create_vulcan_config(target_dir, profile=profile, primary=primary)

    # vulcan.py 자신을 프로젝트에 복사
    shutil.copy2(__file__, os.path.join(target_dir, "vulcan.py"))
    print(f"  생성: vulcan.py")

    src_core = os.path.join(VULCAN_DIR, "vulcan_core")
    if os.path.isdir(src_core):
        _copy_tree_filtered(src_core, os.path.join(target_dir, "vulcan_core"), excludes={"__pycache__"})
        print(f"  생성: vulcan_core/")

    # .gitignore
    gitignore = "node_modules/\n.env\n.env.local\n__pycache__/\n*.pyc\n.pytest_cache/\n*.db\n*.sqlite\n*.sqlite3\nplaywright-report/\ntest-results/\ndashboard/.next/\ndashboard/node_modules/\ndocs/ref-docs/\n.vulcan/release/\n"
    write_file(target_dir, ".gitignore", gitignore)

    # git init + 초기 커밋
    # 참고: dashboard/는 Vulcan-Anvil 루트에 단일 설치하여 재사용합니다 (REQ-007-01)
    try:
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=target_dir, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        except subprocess.CalledProcessError:
            subprocess.run(["git", "init"], cwd=target_dir, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
            subprocess.run(["git", "branch", "-M", "main"], cwd=target_dir, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        subprocess.run(["git", "add", "-A"], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"init: {project_name} 프로젝트 초기화"],
            cwd=target_dir, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        print(f"  생성: git 저장소 초기화 + 초기 커밋")
        print(f"  생성: git 기본 브랜치 main")

        if remote_url:
            try:
                subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=target_dir, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
                print(f"  생성: git remote origin")
                subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=target_dir, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
                print(f"  푸시 완료: origin HEAD")
            except subprocess.CalledProcessError as e:
                detail = (e.stderr or e.stdout or str(e)).strip()
                message = f"git remote 등록 또는 push 실패 - {detail}"
                if require_remote:
                    print(f"  오류: {message}")
                    sys.exit(1)
                print(f"  경고: {message}")
                print("  안내: 로컬 초기 커밋은 완료되었습니다. 원격 저장소를 만든 뒤 직접 push할 수 있습니다.")
        else:
            print("  안내: remote가 설정되지 않았습니다. Gate 시작/완료 push를 사용하려면 remote를 설정하세요.")
    except Exception as e:
        if require_remote:
            print(f"  오류: git 초기화 또는 remote push 실패 - {e}")
            sys.exit(1)
        print(f"  경고: git 초기화 실패 - {e}")

    print(f"\n완료! {project_name} 프로젝트가 초기화되었습니다.")
    print(f"\n다음 단계:")
    print(f"  1. cd {target_dir}")
    if primary == "antigravity-cli":
        print(f"  2. Antigravity 런타임 실행 (agy.exe)")
    elif primary == "claude-cli":
        print(f"  2. Claude Code 런타임 실행 (claude)")
    else:
        print(f"  2. Codex 또는 Claude 런타임 실행")
    print(f"  3. Orchestrator에게 '무엇을 만들지' 설명하고 Phase 0부터 시작")
    if not remote_url:
        print(f"  4. 협업/GitHub 대시보드를 쓰려면 git remote를 설정하세요.")
    print(f"\n대시보드 실행:")
    print(f"  cd <Vulcan-Anvil 경로>/dashboard && npm run dev")
    print(f"  브라우저: http://localhost:3001")
    print(f"\nGate 완료 시:")
    print(f"  python vulcan.py check-trace")
    print(f"  python vulcan.py session --gate gate1 --status done --feature '기능명'")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Vulcan-Anvil Ex - 5-Gate AI 협업 개발 프레임워크",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
명령어:
  init         새 프로젝트 초기화 (Vulcan-Anvil 디렉토리에서 실행)
  status       현재 Gate/Profile/Branch/Run 상태 요약
  doctor       로컬 실행 환경 건강검진
  metrics      git/Run/증적 기반 프로젝트 진행 통계 요약
  check-trace  현재 Gate 정합성 검사 (프로젝트 디렉토리에서 실행)
  prepare-transition Gate 전환에 필요한 Run 완료 여부, 추적성 정합성 등을 한 번에 검사
  check-contract Program Design 구현 계약과 코드 구조 대조
  trace-context 추적성 그래프에서 ID 주변 Run 입력 후보 출력
  gate-start   현재 진행 Gate 전환 (프로젝트 디렉토리에서 실행)
  session      Gate 상태 업데이트 + git commit (프로젝트 디렉토리에서 실행)
  sync-session session.json 대시보드 상태 캐시 동기화
  profile-status Delivery Profile과 profile_rules 확인
  profile-gap  목표 Delivery Profile 기준 부족 항목 진단
  release-pr   Gate 5 통합 브랜치 -> 기준 브랜치 PR 생성/갱신
  wave-start   Build Wave 시작 및 작업지시 Run 생성
  wave-complete Build Wave 완료/상태 갱신
  execute      Run 실행 전 preflight/위임/검증 계획 dry-run
  export       snapshot.json 생성 (프로젝트 디렉토리에서 실행)
  upgrade      프레임워크 파일 최신화 (프로젝트 디렉토리에서 실행)
  version      현재 프레임워크 버전 확인

예시:
  python vulcan.py init ../my-app "MyApp"
  python vulcan.py init ../my-app "MyApp" --remote https://github.com/me/my-app.git
  python vulcan.py init ../my-app "MyApp" --remote https://github.com/me/my-app.git --require-remote
  python vulcan.py status
  python vulcan.py status --check
  python vulcan.py doctor
  python vulcan.py metrics
  python vulcan.py check-trace
  python vulcan.py check-contract --report docs/artifacts/04-review/evidence/contract/contract-conformance.json
  python vulcan.py trace-context --id REQ-001-01 --depth 2 --emit yaml
  python vulcan.py gate-start gate1 --feature "로그인 기능"
  python vulcan.py session --gate gate1 --status awaiting-approval --feature "로그인 기능"
  python vulcan.py session --gate gate1 --status done --approved --approval-evidence "사용자 승인"
  python vulcan.py sync-session
  python vulcan.py profile-status
  python vulcan.py profile-gap --to product
  python vulcan.py branch-status
  python vulcan.py branch-start impl
  python vulcan.py release-pr --dry-run
  python vulcan.py wave-start BW-001 --title "인증 기반 구현" --related-ids REQ-001-01,PGM-001
  python vulcan.py wave-complete BW-001 --status Verified --req REQ-001-01,REQ-002-01
  python vulcan.py execute --run-id RUN-012 --runner native --dry-run
  python vulcan.py export
  python vulcan.py upgrade
        """
    )
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init", help="새 프로젝트 초기화")
    p_init.add_argument("target_dir", help="초기화할 프로젝트 폴더 경로")
    p_init.add_argument("project_name", help="프로젝트 이름")
    p_init.add_argument("--agent-name", default="VULCAN", help="메인 에이전트 이름 (기본값: VULCAN)")
    p_init.add_argument("--remote", default="", help="초기화 후 origin으로 등록할 Git remote URL")
    p_init.add_argument("--require-remote", action="store_true", help="remote 등록/초기 push 실패 시 init 실패 처리")
    p_init.add_argument("--profile", default=None, choices=list(SUPPORTED_DELIVERY_PROFILES) + list(DELIVERY_PROFILE_ALIASES.keys()), help="Delivery Profile (생략 시 대화형 터미널에서 선택, 비대화형 기본값: audit; solution은 product alias)")
    p_init.add_argument("--primary", default=None, help="주 런타임 러너 (예: codex-cli, claude-cli, antigravity-cli, agy)")

    p_status = subparsers.add_parser("status", help="현재 Gate/Profile/Branch/Run 상태 요약")
    p_status.add_argument("--check", action="store_true", help="status 뒤에 prepare-transition 진단을 이어서 실행")
    p_status.add_argument("--trace-detail", action="store_true", help="status 뒤에 check-trace 상세 진단을 이어서 실행")
    p_status.add_argument("--json", action="store_true", help="상태 요약을 JSON으로 출력")

    p_doctor = subparsers.add_parser("doctor", help="로컬 실행 환경 건강검진")
    p_doctor.add_argument("--project-dir", default=".", help="점검할 프로젝트 루트 경로")
    p_doctor.add_argument("--json", action="store_true", help="환경 점검 결과를 JSON으로 출력")

    p_metrics = subparsers.add_parser("metrics", help="git/Run/증적 기반 프로젝트 진행 통계 요약")
    p_metrics.add_argument("--json", action="store_true", help="통계 요약을 JSON으로 출력")

    subparsers.add_parser("check-trace", help="현재 Gate 정합성 검사")
    subparsers.add_parser("prepare-transition", help="Gate 전환에 필요한 Run 완료 여부, 추적성 정합성 등을 한 번에 검사하고 결과를 요약")
    subparsers.add_parser("profile-status", help="Delivery Profile과 profile_rules 확인")
    p_profile_gap = subparsers.add_parser("profile-gap", help="목표 Delivery Profile 기준 부족 항목 진단")
    p_profile_gap.add_argument("--to", default="product", choices=list(SUPPORTED_DELIVERY_PROFILES) + list(DELIVERY_PROFILE_ALIASES.keys()), help="목표 Delivery Profile")
    p_profile_gap.add_argument("--json", action="store_true", help="JSON으로 출력")

    p_check_contract = subparsers.add_parser("check-contract", help="Program Design 구현 계약과 코드 구조 대조")
    p_check_contract.add_argument("--program-design", default="", help="프로그램 설계서 경로")
    p_check_contract.add_argument("--project-dir", default=".", help="검증할 프로젝트 루트 경로")
    p_check_contract.add_argument("--report", default="", help="검증 결과 JSON 저장 경로")
    p_check_contract.add_argument("--emit-contract", default="", help="Program Design 표에서 추출한 계약 JSON 저장 경로")

    p_drift_report = subparsers.add_parser("drift-report", help="설계 산출물과 실제 코드/DB 스키마 간의 불일치(Drift) 보고서 생성")
    p_drift_report.add_argument("--project-dir", default=".", help="검증할 프로젝트 루트 경로")
    p_drift_report.add_argument("--output", default="contract-drift-report.md", help="분석 결과를 작성할 마크다운 보고서 경로")
    p_drift_report.add_argument("--db-path", default="", help="비교할 SQLite DB 파일 경로")
    p_drift_report.add_argument("--database-url", default="", help="비교할 DB URL 또는 SQLite 파일 경로")

    p_check_architecture = subparsers.add_parser("check-architecture", help="SW 아키텍처 성숙도 검사")
    p_check_architecture.add_argument("--level", default="baseline", choices=["draft", "baseline"], help="검사 수준")

    p_trace_context = subparsers.add_parser("trace-context", help="추적성 그래프에서 ID 주변 Run 입력 후보 출력")
    p_trace_context.add_argument("--id", required=True, help="시작 ID (예: REQ-001-01)")
    p_trace_context.add_argument("--depth", type=int, default=2, help="탐색 깊이")
    p_trace_context.add_argument("--direction", default="downstream", choices=["upstream", "downstream", "both"], help="탐색 방향")
    p_trace_context.add_argument("--edge-types", default="", help="허용 edge type 콤마 구분")
    p_trace_context.add_argument("--emit", default="yaml", choices=["yaml", "json"], help="출력 형식")
    p_trace_context.add_argument("--include-excluded", action="store_true", help="Deferred/Rejected 상태도 포함")

    p_gate_start = subparsers.add_parser("gate-start", help="현재 진행 Gate 전환")
    p_gate_start.add_argument("gate", choices=list(GATE_LABELS.keys()), help="시작할 Gate 이름")
    p_gate_start.add_argument("--feature", default="", help="작업 기능명")

    p_session = subparsers.add_parser("session", help="Gate 상태 업데이트 + git commit")
    p_session.add_argument("--gate", required=True, choices=list(GATE_LABELS.keys()), help="Gate 이름")
    p_session.add_argument("--status", required=True, choices=["done", "pending", "awaiting-approval"], help="상태")
    p_session.add_argument("--feature", default="", help="작업 기능명")
    p_session.add_argument("--approved", action="store_true", help="사용자 명시 승인 후 Gate 완료/다음 Gate 전환 허용")
    p_session.add_argument("--approval-evidence", default="", help="사용자 승인 근거 또는 대화 메모")

    subparsers.add_parser("sync-session", help="session.json 대시보드 상태 캐시 동기화")

    subparsers.add_parser("branch-status", help="workflow 브랜치 정책과 현재 브랜치 상태 확인")

    p_branch_start = subparsers.add_parser("branch-start", help="workflow 단계별 통합 브랜치 시작")
    p_branch_start.add_argument("stage", choices=["impl"], help="시작할 브랜치 단계")

    p_release_pr = subparsers.add_parser("release-pr", help="Gate 5 통합 브랜치 -> 기준 브랜치 PR 생성/갱신")
    p_release_pr.add_argument("--base", default="", help="PR base branch (기본: workflow.release_merge_to 또는 main)")
    p_release_pr.add_argument("--head", default="", help="PR head branch (기본: workflow.integration_branch)")
    p_release_pr.add_argument("--title", default="", help="PR 제목")
    p_release_pr.add_argument("--no-push", action="store_true", help="PR 생성 전 통합 브랜치 push를 생략")
    p_release_pr.add_argument("--dry-run", action="store_true", help="PR을 만들지 않고 body와 명령만 출력")

    p_wave_start = subparsers.add_parser("wave-start", help="Build Wave 시작 및 작업지시 Run 생성")
    p_wave_start.add_argument("bw_id", help="Build Wave ID (예: BW-001)")
    p_wave_start.add_argument("--title", default="", help="Wave 제목")
    p_wave_start.add_argument("--related-ids", default="", help="관련 ID 콤마 구분")
    p_wave_start.add_argument("--trace-seed", default="", help="trace-context로 Run 입력 계약을 보강할 시작 ID 콤마 구분")
    p_wave_start.add_argument("--trace-depth", type=int, default=None, help="trace-context 탐색 깊이 (기본: audit 2, poc 1)")

    p_wave_complete = subparsers.add_parser("wave-complete", help="Build Wave 완료/상태 갱신")
    p_wave_complete.add_argument("bw_id", help="Build Wave ID (예: BW-001)")
    p_wave_complete.add_argument("--status", default="Verified", choices=sorted(WAVE_KNOWN_STATUSES), help="Wave 상태")
    p_wave_complete.add_argument("--req", default="", help="구현 완료 처리할 REQ-ID 콤마 구분")

    p_run_new = subparsers.add_parser("run-new", help="Codex/GPT Run 초안 생성")
    p_run_new.add_argument("--adapter", default="codex-gpt", help="Adapter 이름")
    p_run_new.add_argument("--gate", default="gate1", choices=list(GATE_LABELS.keys()), help="Gate 이름")
    p_run_new.add_argument("--persona", default="", choices=[""] + sorted(RUN_PERSONAS.keys()), help="Run persona")
    p_run_new.add_argument("--skill", required=True, choices=sorted(RUN_SKILLS.keys()), help="Run skill")
    p_run_new.add_argument("--title", required=True, help="Run 제목")
    p_run_new.add_argument("--related-ids", default="", help="관련 ID 콤마 구분")
    p_run_new.add_argument("--trace-seed", default="", help="trace-context로 Run 입력 계약을 보강할 시작 ID 콤마 구분")
    p_run_new.add_argument("--trace-depth", type=int, default=None, help="trace-context 탐색 깊이 (기본: audit 2, poc 1)")

    p_run_check = subparsers.add_parser("run-check", help="Run 결과 문서 검사")
    p_run_check.add_argument("run_file", help="검사할 Run 문서 경로")

    p_run_preflight = subparsers.add_parser("run-preflight", help="worker 실행 전 Build Wave Run 작업지시서 사전 검사")
    p_run_preflight.add_argument("run_file", help="사전 검사할 Run 문서 경로")

    p_execute = subparsers.add_parser("execute", help="Run 실행 전 preflight/위임/검증 계획 dry-run")
    p_execute.add_argument("--run-id", required=True, help="실행 계획을 확인할 Run ID (예: RUN-010)")
    p_execute.add_argument("--runner", default="native", help="native, subagent, thread, agy-branch-agent 또는 codex-cli/claude-cli/antigravity-cli")
    p_execute.add_argument("--project-dir", default=".", help="대상 프로젝트 루트 경로")
    p_execute.add_argument("--dry-run", action="store_true", help="실제 worker 호출 없이 실행 계획만 출력")
    p_execute.add_argument("--json", action="store_true", help="실행 계획 dry-run을 JSON으로 출력")

    p_backlog = subparsers.add_parser("backlog", help="백로그 관리 (list/add/done/reject)")
    p_orchestrator_plan = subparsers.add_parser("orchestrator-plan", help="Orchestrator 실행 계획 Run 생성")
    p_orchestrator_plan.add_argument("--goal", required=True, help="Orchestrator가 수립할 목표")
    p_orchestrator_plan.add_argument("--adapter", default="codex-gpt", help="Adapter 이름")
    p_orchestrator_plan.add_argument("--gate", default="gate1", choices=list(GATE_LABELS.keys()), help="Gate 이름")
    p_orchestrator_plan.add_argument("--persona", default="", choices=[""] + sorted(RUN_PERSONAS.keys()), help="우선 적용 persona")
    p_orchestrator_plan.add_argument("--related-ids", default="", help="관련 ID 콤마 구분")

    p_handoff = subparsers.add_parser("handoff", help="다른 환경/에이전트로 넘길 검수 Run 생성")
    p_handoff.add_argument("--to", required=True, choices=sorted(HANDOFF_TARGETS), help="handoff 대상")
    p_handoff.add_argument("--title", required=True, help="handoff 목표")
    p_handoff.add_argument("--from-run", default="", help="이전 Run ID 또는 파일명")
    p_handoff.add_argument("--adapter", default="codex-gpt", help="Adapter 이름")
    p_handoff.add_argument("--gate", default="gate4", choices=list(GATE_LABELS.keys()), help="Gate 이름")
    p_handoff.add_argument("--persona", default="review", choices=sorted(RUN_PERSONAS.keys()), help="handoff persona")
    p_handoff.add_argument("--related-ids", default="", help="관련 ID 콤마 구분")

    p_review_request = subparsers.add_parser("review-request", help="독립 세션/워크트리 기반 검수 요청 생성")
    p_review_request.add_argument("--title", required=True, help="독립 검수 목표")
    p_review_request.add_argument("--gate", required=True, choices=list(GATE_LABELS.keys()), help="검수 대상 Gate")
    p_review_request.add_argument("--related-ids", default="", help="관련 ID 콤마 구분")
    p_review_request.add_argument("--from-run", default="", help="검수 대상 Run ID 또는 파일명")
    p_review_request.add_argument("--runner", choices=INDEPENDENT_REVIEW_RUNNERS, help="독립 검수 실행 런타임")
    p_review_request.add_argument("--worktree", dest="worktree", action="store_true", help="격리 worktree 생성")
    p_review_request.add_argument("--no-worktree", dest="worktree", action="store_false", help="worktree를 생성하지 않음")
    p_review_request.set_defaults(worktree=None)
    p_review_request.add_argument("--worktree-dir", default="", help="worktree 생성 경로")

    p_review_run = subparsers.add_parser("review-run", help="독립 검수 요청을 CLI runner로 실행")
    p_review_run.add_argument("--review-id", required=True, help="실행할 리뷰 ID (예: RV-001)")
    p_review_run.add_argument("--runner", choices=INDEPENDENT_REVIEW_RUNNERS, help="독립 검수 실행 런타임")
    p_review_run.add_argument("--model", default="", help="runner 모델")
    p_review_run.add_argument("--reasoning-effort", default="", choices=["", "low", "medium", "high", "xhigh"], help="추론 강도")
    p_review_run.add_argument("--timeout-seconds", type=int, default=0, help="runner timeout seconds")
    p_review_run.add_argument("--sandbox", default="", choices=["", "read-only", "workspace-write", "danger-full-access"], help="codex-cli sandbox")
    p_review_run.add_argument("--dry-run", action="store_true", help="실행하지 않고 명령만 출력")

    p_run_exec = subparsers.add_parser("run-exec", help="Run 문서를 CLI 작업자 runner로 실행")
    p_run_exec.add_argument("--run-id", required=True, help="실행할 Run ID (예: RUN-010)")
    p_run_exec.add_argument("--runner", choices=EXEC_RUNNERS, help="작업자 실행 런타임")
    p_run_exec.add_argument("--model", default="", help="runner 모델")
    p_run_exec.add_argument("--reasoning-effort", default="", choices=["", "low", "medium", "high", "xhigh"], help="추론 강도")
    p_run_exec.add_argument("--timeout-seconds", type=int, default=0, help="runner timeout seconds")
    p_run_exec.add_argument("--sandbox", default="", choices=["", "read-only", "workspace-write", "danger-full-access"], help="codex-cli sandbox")
    p_run_exec.add_argument("--worktree", dest="worktree", action="store_true", help="브랜치 worktree에서 실행")
    p_run_exec.add_argument("--no-worktree", dest="worktree", action="store_false", help="현재 worktree에서 실행")
    p_run_exec.set_defaults(worktree=None)
    p_run_exec.add_argument("--worktree-dir", default="", help="worktree 생성 경로")
    p_run_exec.add_argument("--branch", default="", help="worktree 생성 시 사용할 branch 이름")
    p_run_exec.add_argument("--allow-dirty", action="store_true", help="미커밋 변경이 있어도 HEAD 기준 worktree 생성을 허용")
    p_run_exec.add_argument("--dry-run", action="store_true", help="실행하지 않고 명령만 출력")

    p_run_integrate = subparsers.add_parser("run-integrate", help="worker worktree diff를 Run scope 기준으로 수집/검사/반영")
    p_run_integrate.add_argument("--run-id", required=True, help="통합할 worker Run ID (예: RUN-010)")
    p_run_integrate.add_argument("--runner", choices=EXEC_RUNNERS, help="summary 선택에 사용할 runner")
    p_run_integrate.add_argument("--worktree-dir", default="", help="통합할 worker worktree 경로")
    p_run_integrate.add_argument("--apply", action="store_true", help="scope 허용 diff를 현재 worktree에 반영")
    p_run_integrate.add_argument("--allow-dirty", action="store_true", help="현재 worktree가 dirty여도 적용 허용")
    p_run_integrate.add_argument("--dry-run", action="store_true", help="보고서/파일 변경 없이 분석만 출력")

    p_agent_run = subparsers.add_parser("agent-run", help="별도 세션 runner 실행 통합 명령")
    p_agent_run.add_argument("--mode", required=True, choices=["review", "work"], help="실행 유형: review=검수/교차검증, work=작업 실행")
    p_agent_run.add_argument("--target-id", default="", help="실행 대상 ID (review: RV-NNN, work: RUN-NNN)")
    p_agent_run.add_argument("--review-id", default="", help="review mode 대상 리뷰 ID")
    p_agent_run.add_argument("--run-id", default="", help="work mode 대상 Run ID")
    p_agent_run.add_argument("--runner", choices=EXEC_RUNNERS, help="작업자 실행 런타임")
    p_agent_run.add_argument("--model", default="", help="runner 모델")
    p_agent_run.add_argument("--reasoning-effort", default="", choices=["", "low", "medium", "high", "xhigh"], help="추론 강도")
    p_agent_run.add_argument("--timeout-seconds", type=int, default=0, help="runner timeout seconds")
    p_agent_run.add_argument("--sandbox", default="", choices=["", "read-only", "workspace-write", "danger-full-access"], help="codex-cli sandbox")
    p_agent_run.add_argument("--worktree", dest="worktree", action="store_true", help="work mode에서 브랜치 worktree 실행")
    p_agent_run.add_argument("--no-worktree", dest="worktree", action="store_false", help="work mode에서 현재 worktree 실행")
    p_agent_run.set_defaults(worktree=None)
    p_agent_run.add_argument("--worktree-dir", default="", help="work mode worktree 생성 경로")
    p_agent_run.add_argument("--branch", default="", help="work mode worktree 생성 시 사용할 branch 이름")
    p_agent_run.add_argument("--allow-dirty", action="store_true", help="work mode에서 미커밋 변경이 있어도 HEAD 기준 worktree 생성을 허용")
    p_agent_run.add_argument("--dry-run", action="store_true", help="실행하지 않고 명령만 출력")

    p_agent_resume = subparsers.add_parser("agent-resume", help="이전 CLI runner 세션을 이어 실행하고 대시보드 상태를 갱신")
    p_agent_resume.add_argument("--target-id", required=True, help="resume 대상 ID (RV-NNN 또는 RUN-NNN)")
    p_agent_resume.add_argument("--runner", choices=["codex-cli", "codex", "claude-cli", "claude"], help="이전 실행 runner")
    p_agent_resume.add_argument("--prompt", default="", help="resume 세션에 보낼 추가 지시")
    p_agent_resume.add_argument("--timeout-seconds", type=int, default=0, help="resume timeout seconds")
    p_agent_resume.add_argument("--dry-run", action="store_true", help="실행하지 않고 명령만 출력")

    backlog_sub = p_backlog.add_subparsers(dest="backlog_cmd")
    backlog_sub.add_parser("list", help="백로그 Active 항목 나열")
    bl_add = backlog_sub.add_parser("add", help="새 백로그 항목 추가")
    bl_add.add_argument("--title", required=True)
    bl_add.add_argument("--level", default="", help="🟢/🟡/🔴 (선택, 나중에 Triage)")
    bl_add.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    bl_add.add_argument("--req", default="")
    bl_add.add_argument("--source", default="")
    bl_add.add_argument("--note", default="")
    bl_add.add_argument("--type", dest="item_type", default="IDEA", choices=["IDEA", "FIND", "CR", "ISSUE", "DEBT"])
    bl_add.add_argument("--backlog-gate", dest="backlog_gate", default="phase0", help="다시 진행할 Gate 후보")
    bl_add.add_argument("--run", default="", help="관련 Run ID 또는 파일")
    bl_done = backlog_sub.add_parser("done", help="백로그 항목 완료 처리")
    bl_done.add_argument("--id", dest="bl_id", required=True)
    bl_done.add_argument("--commit", dest="commit_hash", default="")
    bl_rej = backlog_sub.add_parser("reject", help="백로그 항목 반려")
    bl_rej.add_argument("--id", dest="bl_id", required=True)
    bl_rej.add_argument("--reason", default="")

    p_export = subparsers.add_parser("export", help="snapshot.json 생성")
    p_export.add_argument("--output", default="snapshot.json", help="출력 파일명")

    subparsers.add_parser("upgrade", help="프레임워크 파일 최신화")
    subparsers.add_parser("version", help="현재 프레임워크 버전 확인")

    p_release = subparsers.add_parser("release", help="Vulcan-Anvil로 코드 배포")
    p_release.add_argument("--target", required=True, help="배포 대상 경로 (예: ../Vulcan-Anvil)")

    args = parser.parse_args()

    if args.command == "init":
        init(
            target_dir=os.path.abspath(args.target_dir),
            project_name=args.project_name,
            agent_name=args.agent_name,
            remote_url=args.remote or None,
            require_remote=args.require_remote,
            profile=args.profile,
            primary=args.primary,
        )
    elif args.command == "status":
        cmd_status(check=args.check, trace_detail=args.trace_detail, emit_json=args.json)
    elif args.command == "doctor":
        cmd_doctor(project_dir=args.project_dir, emit_json=args.json)
    elif args.command == "metrics":
        cmd_metrics(emit_json=args.json)
    elif args.command == "check-trace":
        issues, _ = check_trace()
        if issues:
            sys.exit(1)
    elif args.command == "prepare-transition":
        cmd_prepare_transition()
    elif args.command == "profile-status":
        cmd_profile_status()
    elif args.command == "profile-gap":
        cmd_profile_gap(target_profile=args.to, emit_json=args.json)
    elif args.command == "check-contract":
        sys.exit(cmd_check_contract(
            program_design=args.program_design,
            report=args.report,
            emit_contract=args.emit_contract,
            project_dir=args.project_dir,
        ))
    elif args.command == "drift-report":
        cmd_drift_report(
            project_dir=args.project_dir,
            output_file=args.output,
            db_path=args.db_path,
            database_url=args.database_url,
        )
    elif args.command == "check-architecture":
        cmd_check_architecture(level=args.level)
    elif args.command == "trace-context":
        cmd_trace_context(
            seed_id=args.id,
            depth=args.depth,
            direction=args.direction,
            emit=args.emit,
            edge_types=args.edge_types,
            include_excluded=args.include_excluded,
        )
    elif args.command == "gate-start":
        cmd_gate_start(gate=args.gate, feature=args.feature)
    elif args.command == "session":
        cmd_session(
            gate=args.gate,
            status=args.status,
            feature=args.feature,
            approved=args.approved,
            approval_evidence=args.approval_evidence,
        )
    elif args.command == "sync-session":
        cmd_sync_session()
    elif args.command == "branch-status":
        cmd_branch_status()
    elif args.command == "branch-start":
        cmd_branch_start(stage=args.stage)
    elif args.command == "release-pr":
        cmd_release_pr(
            base=args.base,
            head=args.head,
            title=args.title,
            dry_run=args.dry_run,
            no_push=args.no_push,
        )
    elif args.command == "wave-start":
        cmd_wave_start(
            bw_id=args.bw_id,
            title=args.title,
            related_ids=args.related_ids,
            trace_seed=args.trace_seed,
            trace_depth=args.trace_depth,
        )
    elif args.command == "wave-complete":
        cmd_wave_complete(bw_id=args.bw_id, status=args.status, req_ids=args.req)
    elif args.command == "run-new":
        cmd_run_new(
            adapter=args.adapter,
            gate=args.gate,
            skill=args.skill,
            title=args.title,
            related_ids=args.related_ids,
            persona=args.persona or None,
            trace_seed=args.trace_seed,
            trace_depth=args.trace_depth,
        )
    elif args.command == "run-check":
        cmd_run_check(args.run_file)
    elif args.command == "run-preflight":
        cmd_run_preflight(args.run_file)
    elif args.command == "execute":
        cmd_execute(
            run_id=args.run_id,
            runner=args.runner,
            dry_run=args.dry_run,
            project_dir=args.project_dir,
            emit_json=args.json,
        )
    elif args.command == "orchestrator-plan":
        cmd_orchestrator_plan(
            goal=args.goal,
            gate=args.gate,
            related_ids=args.related_ids,
            persona=args.persona or None,
            adapter=args.adapter,
        )
    elif args.command == "handoff":
        cmd_handoff(
            target=args.to,
            title=args.title,
            from_run=args.from_run,
            gate=args.gate,
            related_ids=args.related_ids,
            persona=args.persona,
            adapter=args.adapter,
        )
    elif args.command == "review-request":
        cmd_review_request(
            title=args.title,
            gate=args.gate,
            related_ids=args.related_ids,
            from_run=args.from_run,
            runner=args.runner,
            create_worktree=args.worktree,
            worktree_dir=args.worktree_dir,
        )
    elif args.command == "review-run":
        cmd_review_run(
            review_id=args.review_id,
            runner=args.runner,
            model=args.model or None,
            reasoning_effort=args.reasoning_effort or None,
            timeout_seconds=args.timeout_seconds or None,
            sandbox=args.sandbox or None,
            dry_run=args.dry_run,
        )
    elif args.command == "run-exec":
        cmd_run_exec(
            run_id=args.run_id,
            runner=args.runner,
            model=args.model or None,
            reasoning_effort=args.reasoning_effort or None,
            timeout_seconds=args.timeout_seconds or None,
            sandbox=args.sandbox or None,
            create_worktree=args.worktree,
            worktree_dir=args.worktree_dir,
            branch_name=args.branch,
            allow_dirty=args.allow_dirty,
            dry_run=args.dry_run,
        )
    elif args.command == "run-integrate":
        cmd_run_integrate(
            run_id=args.run_id,
            runner=args.runner,
            worktree_dir=args.worktree_dir,
            apply=args.apply,
            allow_dirty=args.allow_dirty,
            dry_run=args.dry_run,
        )
    elif args.command == "agent-run":
        cmd_agent_run(
            mode=args.mode,
            target_id=args.target_id,
            review_id=args.review_id,
            run_id=args.run_id,
            runner=args.runner,
            model=args.model or None,
            reasoning_effort=args.reasoning_effort or None,
            timeout_seconds=args.timeout_seconds or None,
            sandbox=args.sandbox or None,
            create_worktree=args.worktree,
            worktree_dir=args.worktree_dir,
            branch_name=args.branch,
            allow_dirty=args.allow_dirty,
            dry_run=args.dry_run,
        )
    elif args.command == "agent-resume":
        cmd_agent_resume(
            target_id=args.target_id,
            runner=args.runner,
            prompt=args.prompt,
            timeout_seconds=args.timeout_seconds or None,
            dry_run=args.dry_run,
        )
    elif args.command == "backlog":
        if args.backlog_cmd == "list":
            cmd_backlog_list()
        elif args.backlog_cmd == "add":
            cmd_backlog_add(
                title=args.title, level=args.level, priority=args.priority,
                req=args.req, source=args.source, note=args.note,
                item_type=args.item_type, gate=args.backlog_gate, run=args.run,
            )
        elif args.backlog_cmd == "done":
            cmd_backlog_done(bl_id=args.bl_id, commit_hash=args.commit_hash)
        elif args.backlog_cmd == "reject":
            cmd_backlog_reject(bl_id=args.bl_id, reason=args.reason)
        else:
            p_backlog.print_help()
    elif args.command == "export":
        cmd_export(output=args.output)
    elif args.command == "upgrade":
        cmd_upgrade()
    elif args.command == "version":
        cmd_version()
    elif args.command == "release":
        cmd_release(target=args.target)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()



