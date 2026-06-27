"""Read-only configuration for the Jira Cloud REST client.

Mirrors the engine's env-resolution convention (first hit wins): explicit ``-D``-style override is
n/a in Python, so order is **env var (UPPER_SNAKE_CASE) → engine/.env → default**. Secrets
(``JIRA_API_TOKEN``) come only from env / the git-ignored ``engine/.env`` — never a checked-in file.

This is the Python analogue of the Java ``com.laerdal.api.jira.JiraConfig`` (the port reference).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

ENV_BASE_URL = "JIRA_BASE_URL"
ENV_EMAIL = "JIRA_EMAIL"
ENV_API_TOKEN = "JIRA_API_TOKEN"
ENV_PROJECT_KEY = "JIRA_PROJECT_KEY"
ENV_TIMEOUT_MS = "JIRA_TIMEOUT_MS"

DEFAULT_BASE_URL = "https://laerdal.atlassian.net"
DEFAULT_PROJECT_KEY = "LBVOICESER"
DEFAULT_TIMEOUT_MS = 30000

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


def _get(name: str, default: str = "") -> str:
    _ensure_env_loaded()
    return (os.getenv(name) or default).strip()


@dataclass(frozen=True, slots=True)
class JiraConfig:
    base_url: str
    email: str
    api_token: str
    project_key: str
    timeout_ms: int

    @classmethod
    def from_env(cls) -> "JiraConfig":
        base_url = _get(ENV_BASE_URL, DEFAULT_BASE_URL).rstrip("/")
        email = _get(ENV_EMAIL)
        api_token = _get(ENV_API_TOKEN)
        project_key = _get(ENV_PROJECT_KEY, DEFAULT_PROJECT_KEY)
        timeout_raw = _get(ENV_TIMEOUT_MS, str(DEFAULT_TIMEOUT_MS))
        try:
            timeout_ms = int(timeout_raw)
        except ValueError:
            timeout_ms = DEFAULT_TIMEOUT_MS
        return cls(base_url=base_url, email=email, api_token=api_token,
                   project_key=project_key, timeout_ms=timeout_ms)

    def require_credentials(self) -> None:
        """Raise a clear error if email/token are missing (mirrors the Java guard)."""
        missing = [n for n, v in ((ENV_EMAIL, self.email), (ENV_API_TOKEN, self.api_token)) if not v]
        if missing:
            raise RuntimeError(
                f"Jira not configured — set {', '.join(missing)} in engine/.env "
                "(API token from https://id.atlassian.com/manage-profile/security/api-tokens)."
            )


def verify_config() -> dict[str, bool]:
    """Report which Jira settings are present (booleans only — never prints the token)."""
    cfg = JiraConfig.from_env()
    return {
        ENV_BASE_URL: bool(cfg.base_url),
        ENV_EMAIL: bool(cfg.email),
        ENV_API_TOKEN: bool(cfg.api_token),
        ENV_PROJECT_KEY: bool(cfg.project_key),
    }


if __name__ == "__main__":  # pragma: no cover - manual pre-flight
    for name, present in verify_config().items():
        print(f"  {'set    ' if present else 'MISSING'}  {name}")
