"""Optional Telegram adapter.

Requires TELEGRAM_BOT_TOKEN from the environment (user-provided).
Does not hard-code secrets. Not started by default.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.matcher import FaqMatcher, load_faq  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Optional Telegram long-polling adapter for the FAQ matcher"
    )
    parser.add_argument(
        "--faq",
        type=Path,
        default=ROOT / "data" / "faq.json",
        help="Path to FAQ JSON or CSV",
    )
    parser.add_argument("--threshold", type=float, default=0.62)
    args = parser.parse_args(argv)

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print(
            "TELEGRAM_BOT_TOKEN is not set.\n"
            "Create a bot with @BotFather, then:\n"
            "  export TELEGRAM_BOT_TOKEN='your-token-here'\n"
            "  python -m src.telegram_adapter\n"
            "This adapter is optional; the offline CLI works without Telegram.",
            file=sys.stderr,
        )
        return 2

    try:
        import urllib.request
        import urllib.parse
        import json
        import time
    except ImportError as exc:  # pragma: no cover
        print(f"Missing stdlib import: {exc}", file=sys.stderr)
        return 1

    matcher = FaqMatcher(load_faq(args.faq), threshold=args.threshold)
    api = f"https://api.telegram.org/bot{token}"
    offset = 0
    print("Telegram adapter started (Ctrl+C to stop). FAQ answers only — no invented text.")

    def api_call(method: str, payload: dict) -> dict:
        data = urllib.parse.urlencode(payload).encode()
        req = urllib.request.Request(f"{api}/{method}", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())

    while True:
        try:
            updates = api_call(
                "getUpdates",
                {"timeout": 30, "offset": offset, "allowed_updates": json.dumps(["message"])},
            )
        except Exception as exc:  # network / auth errors
            print(f"Telegram API error: {exc}", file=sys.stderr)
            time.sleep(3)
            continue

        if not updates.get("ok"):
            print(f"API not ok: {updates}", file=sys.stderr)
            time.sleep(3)
            continue

        for upd in updates.get("result", []):
            offset = max(offset, int(upd["update_id"]) + 1)
            msg = upd.get("message") or {}
            text = msg.get("text") or ""
            chat = msg.get("chat") or {}
            chat_id = chat.get("id")
            if not chat_id or not text:
                continue
            if text.startswith("/start"):
                reply = (
                    "FAQ bot demo. Ask a question from the knowledge base. "
                    "Unmatched questions get a polite fallback — I never invent answers."
                )
            else:
                result = matcher.match(text)
                reply = result.answer
            try:
                api_call("sendMessage", {"chat_id": chat_id, "text": reply})
            except Exception as exc:
                print(f"sendMessage failed: {exc}", file=sys.stderr)
    # unreachable
    # return 0


if __name__ == "__main__":
    raise SystemExit(main())
