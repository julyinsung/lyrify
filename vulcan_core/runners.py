"""Runner selection and metadata helpers for Vulcan-Anvil Ex."""

import os
import re
import shutil
import subprocess


INDEPENDENT_REVIEW_RUNNERS = [
    "codex-cli",
    "codex",
    "claude-cli",
    "claude",
    "antigravity-cli",
    "antigravity",
    "agy",
    "manual",
]
INDEPENDENT_REVIEW_EXEC_RUNNERS = [
    "codex-cli",
    "codex",
    "claude-cli",
    "claude",
    "antigravity-cli",
    "antigravity",
    "agy",
]
EXEC_RUNNERS = ["codex-cli", "codex", "claude-cli", "claude", "antigravity-cli", "antigravity", "agy"]


def _slugify(value):
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-zA-Z가-힣_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "run"


def normalize_exec_runner(runner):
    return {
        "codex": "codex-cli",
        "claude": "claude-cli",
        "antigravity": "antigravity-cli",
        "agy": "antigravity-cli",
    }.get(runner, runner)


def runner_log_slug(runner):
    return {
        "codex-cli": "codex",
        "claude-cli": "claude",
        "antigravity-cli": "antigravity",
    }.get(normalize_exec_runner(runner), _slugify(runner))


def runner_log_ext(runner):
    return {
        "codex-cli": "jsonl",
        "claude-cli": "json",
        "antigravity-cli": "txt",
    }.get(normalize_exec_runner(runner), "txt")


def runner_model_source(runner):
    return {
        "codex-cli": "cli-argument",
        "claude-cli": "cli-argument",
        "antigravity-cli": "agy-config-inherited",
    }.get(normalize_exec_runner(runner), "runner-config")


def runner_empty_output(stdout, stderr):
    return not (stdout or "").strip() and not (stderr or "").strip()


def antigravity_executable():
    return shutil.which("agy.exe") or shutil.which("agy")


def default_execution_branch(run_id, runner):
    runner_slug = _slugify(normalize_exec_runner(runner))
    return f"codex/run-{run_id.lower()}-{runner_slug}"


def default_execution_worktree_path(project_dir, run_id, runner):
    runner_slug = _slugify(normalize_exec_runner(runner))
    return os.path.abspath(os.path.join(project_dir, ".vulcan", "worktrees", f"{run_id}-{runner_slug}"))


def command_version(command, timeout_seconds=10):
    exe = shutil.which(command)
    if not exe:
        return None
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return (result.stdout or result.stderr or "").strip()


def runner_default_config(name, version=None):
    if name == "codex-cli":
        return {
            "name": "codex-cli",
            "model": "gpt-5.5",
            "effort": "high",
            "sandbox": "workspace-write",
            "version": version,
        }
    if name == "claude-cli":
        return {
            "name": "claude-cli",
            "model": "claude-opus-4-7",
            "effort": "high",
            "version": version,
        }
    if name == "antigravity-cli":
        return {
            "name": "antigravity-cli",
            "model": "gemini-3.5-flash",
            "effort": "high",
            "sandbox": "workspace-write",
            "version": version,
        }
    return {
        "name": name,
        "model": None,
        "effort": "high",
        "version": version,
    }


def detect_runtime_runners():
    runners = []
    codex_version = command_version("codex")
    claude_version = command_version("claude")
    antigravity_version = command_version("antigravity")
    if antigravity_version is None:
        antigravity_version = command_version("agy")
    if codex_version is not None:
        runners.append(runner_default_config("codex-cli", codex_version or None))
    if claude_version is not None:
        runners.append(runner_default_config("claude-cli", claude_version or None))
    if antigravity_version is not None:
        runners.append(runner_default_config("antigravity-cli", antigravity_version or None))
    return runners


def normalize_runtime_runners(runtime_config):
    available = runtime_config.get("available_runners", [])
    if isinstance(available, list):
        return [runner for runner in available if isinstance(runner, dict) and runner.get("name")]
    if isinstance(available, dict):
        normalized = []
        for name, values in available.items():
            if not isinstance(values, dict) or not values.get("available"):
                continue
            runner = runner_default_config(name, values.get("version"))
            for key in ("model", "effort", "reasoning_effort", "sandbox"):
                if key in values:
                    runner[key] = values[key]
            normalized.append(runner)
        return normalized
    return []


def runtime_runner_names(config):
    return [runner["name"] for runner in normalize_runtime_runners(config.get("runtime", {}))]


def runtime_runner_config(config, runner_name):
    target = normalize_exec_runner(runner_name)
    for runner in normalize_runtime_runners(config.get("runtime", {})):
        if normalize_exec_runner(runner.get("name")) == target:
            return runner
    return runner_default_config(target)


def runtime_default_runner(config):
    names = runtime_runner_names(config)
    normalized_names = [normalize_exec_runner(name) for name in names]
    if "codex-cli" in normalized_names:
        return "codex-cli"
    if "claude-cli" in normalized_names:
        return "claude-cli"
    if "antigravity-cli" in normalized_names:
        return "antigravity-cli"
    if names:
        return normalize_exec_runner(names[0])
    return "manual"


def runtime_role_runner(config, role):
    names = runtime_runner_names(config)
    normalized_names = [normalize_exec_runner(name) for name in names]
    default_runner = runtime_default_runner(config)
    if default_runner == "manual":
        return "manual"
    if role in ("build-backend", "build", "evidence") and "codex-cli" in normalized_names:
        return "codex-cli"
    if role in ("build-frontend", "review", "pr-cross-validation") and "claude-cli" in normalized_names:
        return "claude-cli"
    if role in ("review", "pr-cross-validation", "build-frontend") and "antigravity-cli" in normalized_names:
        return "antigravity-cli"
    return default_runner


def runtime_runner_families(config):
    families = set()
    for name in runtime_runner_names(config):
        normalized = normalize_exec_runner(name)
        if normalized == "codex-cli":
            families.add("codex")
        elif normalized == "claude-cli":
            families.add("claude")
        elif normalized == "antigravity-cli":
            families.add("gemini")
        else:
            families.add(normalized)
    return families


def runtime_capability(config, capability):
    names = runtime_runner_names(config)
    families = runtime_runner_families(config)
    if capability == "same_runner_independent_review":
        return bool(names)
    if capability == "cross_model_validation":
        return len(families) >= 2
    if capability == "parallel_worktrees":
        return bool(names)
    if capability == "parallel_cross_runner_work":
        return len(families) >= 2
    return False

