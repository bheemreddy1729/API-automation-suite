"""Azure OpenAI connection (base) — the engine's default model backend.

LangGraph has no model wrapper of its own; it composes with LangChain chat models, so we use
``langchain-openai``'s ``AzureChatOpenAI``. Per :class:`TaskKind` we pick a deployment
(coding / reasoning / classification) — that's how the model router maps to real models.

Config comes from env (fill ``engine/.env`` from ``.env.example``); **nothing is hardcoded**.
The ``langchain_openai`` import is lazy so the core package + isolation tests don't require it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from .router import TaskKind

# --- env var names (fill engine/.env) ---------------------------------------
ENV_ENDPOINT = "AZURE_OPENAI_ENDPOINT"
ENV_API_KEY = "AZURE_OPENAI_API_KEY"
ENV_API_VERSION = "AZURE_OPENAI_API_VERSION"          # optional with the Azure v1 GA API
DEFAULT_API_VERSION = "2024-10-21"                    # recent stable GA; override via env

DEPLOYMENT_ENV: dict[TaskKind, str] = {
    TaskKind.CODE_GENERATION: "AZURE_OPENAI_DEPLOYMENT_CODING",
    TaskKind.REASONING: "AZURE_OPENAI_DEPLOYMENT_REASONING",
    TaskKind.CLASSIFICATION: "AZURE_OPENAI_DEPLOYMENT_CLASSIFICATION",
}

_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    """Best-effort load of engine/.env (git-ignored). No error if python-dotenv is absent."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    try:
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv(usecwd=True))
    except Exception:
        pass
    _ENV_LOADED = True


@dataclass(frozen=True, slots=True)
class AzureSettings:
    endpoint: str
    api_key: str
    api_version: str

    @classmethod
    def from_env(cls) -> "AzureSettings":
        _ensure_env_loaded()
        endpoint = os.getenv(ENV_ENDPOINT, "").strip()
        api_key = os.getenv(ENV_API_KEY, "").strip()
        api_version = os.getenv(ENV_API_VERSION, "").strip() or DEFAULT_API_VERSION
        missing = [n for n, v in ((ENV_ENDPOINT, endpoint), (ENV_API_KEY, api_key)) if not v]
        if missing:
            raise RuntimeError(
                f"Azure OpenAI not configured — set {', '.join(missing)} in engine/.env "
                "(see .env.example)."
            )
        return cls(endpoint=endpoint, api_key=api_key, api_version=api_version)


def deployment_for(task: TaskKind) -> str:
    _ensure_env_loaded()
    env_name = DEPLOYMENT_ENV[task]
    deployment = os.getenv(env_name, "").strip()
    if not deployment:
        raise RuntimeError(
            f"set {env_name} in engine/.env to the Azure deployment for the {task.value} model"
        )
    return deployment


def build_chat_model(task: TaskKind, *, temperature: float = 0.0):
    """Build an ``AzureChatOpenAI`` for ``task``'s deployment.

    Lazy-imports ``langchain_openai`` and raises a clear error if the package isn't installed
    or the Azure config/creds are missing. Returns a LangChain chat model usable directly by
    LangGraph nodes.
    """
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError as exc:  # pragma: no cover - env guidance
        raise RuntimeError(
            "langchain-openai is not installed — run `pip install -e .[dev]` in engine/."
        ) from exc

    settings = AzureSettings.from_env()
    return AzureChatOpenAI(
        azure_endpoint=settings.endpoint,
        api_key=settings.api_key,
        api_version=settings.api_version,
        azure_deployment=deployment_for(task),
        temperature=temperature,
    )


def verify_config() -> dict[str, bool]:
    """Report which required settings are present (booleans only — never prints secret values).

    Useful as a pre-flight: ``python -m qa_agent.models.azure_openai``.
    """
    _ensure_env_loaded()
    status = {
        ENV_ENDPOINT: bool(os.getenv(ENV_ENDPOINT, "").strip()),
        ENV_API_KEY: bool(os.getenv(ENV_API_KEY, "").strip()),
    }
    for env_name in DEPLOYMENT_ENV.values():
        status[env_name] = bool(os.getenv(env_name, "").strip())
    return status


if __name__ == "__main__":  # pragma: no cover - manual pre-flight
    print(f"API version: {os.getenv(ENV_API_VERSION, '').strip() or DEFAULT_API_VERSION} (default if blank)")
    for name, present in verify_config().items():
        print(f"  {'set ' if present else 'MISSING'}  {name}")
