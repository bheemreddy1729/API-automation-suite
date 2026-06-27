"""Azure OpenAI connection smoke test.

Pre-flights the config, then makes one tiny real chat call against the CLASSIFICATION
deployment and reports a clear, diagnostic outcome:

    python scripts/azure_smoke.py        # from engine/, with the venv active

Exit codes:
    0  connected (got a model reply)
    2  not configured (endpoint/key/deployment missing in engine/.env)
    3  reached Azure but auth failed (401) — endpoint/wiring OK, key wrong/missing
    4  reached Azure but the call was rejected for another reason (e.g. api-version,
       deployment name, or temperature) — wiring OK, see the message
    1  unexpected error

Never prints secret values.
"""
from __future__ import annotations

import sys

from qa_agent.models.azure_openai import build_chat_model, verify_config
from qa_agent.models.router import TaskKind


def main() -> int:
    # Force UTF-8 output so non-ASCII (model replies, glyphs) can't crash on the
    # Windows console codepage (cp1252) and get misclassified as a call failure.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - older/odd streams; ASCII fallbacks below cover it
            pass

    print("== Azure OpenAI pre-flight ==")
    status = verify_config()
    for name, present in status.items():
        print(f"  {'set    ' if present else 'MISSING'}  {name}")

    if not all(status.values()):
        print("\nNot fully configured - fill the MISSING value(s) in engine/.env.")
        return 2

    print("\n== Live connection test (CLASSIFICATION deployment) ==")
    try:
        # temperature=None -> use the model default (gpt-5 reasoning models reject 0.0).
        model = build_chat_model(TaskKind.CLASSIFICATION)
        reply = model.invoke("Reply with the single word: pong")
        text = getattr(reply, "content", reply)
        print(f"  connected OK  model replied: {text!r}")
        return 0
    except Exception as exc:  # noqa: BLE001 - we classify and report
        msg = str(exc)
        low = msg.lower()
        if "401" in msg or "unauthorized" in low or "invalid_api_key" in low or "access denied" in low:
            print(f"  reached Azure, AUTH FAILED (401) — wiring OK, key wrong/missing:\n  {msg}")
            return 3
        if "not configured" in low:
            print(f"  not configured: {msg}")
            return 2
        print(f"  reached Azure, call rejected (wiring OK - check api-version/deployment):\n  {msg}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
