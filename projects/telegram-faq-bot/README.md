# Offline Telegram FAQ Matcher (demo)

Small FAQ answer engine that runs without the internet.
Answers **only** from a local FAQ file. If nothing matches confidently — a polite fallback, never invented facts.

> Demo / sample project. Not a case for a named client.

## What you get

- Deterministic FAQ data (`data/faq.json`, `data/faq.csv`)
- Conservative fuzzy matching (token overlap + bigrams, tunable threshold)
- Offline interactive CLI
- Optional Telegram long-polling adapter (needs **your** BotFather token; not required for the demo)
- Unit tests (`unittest`)

No API keys, no client data, no hosting required for the offline demo.

## Requirements

- Python 3.10+ (stdlib only)

## Quick start

```bash
cd projects/telegram-faq-bot
python3 -m src.cli
```

Single query:

```bash
python3 -m src.cli --once "What are your opening hours?"
python3 -m src.cli --once "What is the weather in Dublin?"
```

Reload FAQ in the interactive session with `/reload`. Exit with `/quit`.

## Optional Telegram adapter

```bash
export TELEGRAM_BOT_TOKEN='your-token-here'
python3 -m src.telegram_adapter
```

Without `TELEGRAM_BOT_TOKEN`, the adapter exits with a clear message. The offline CLI still works.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Design choices

- **No generative answers** — only text from the FAQ (or the fixed fallback)
- **Conservative threshold** (default `0.62`)
- **Stdlib only**

---

# Офлайн FAQ-матчер для Telegram (демо)

Відповідає лише з локального FAQ. Без вигаданих фактів. Це демо-зразок підходу, не кейс іменованого клієнта.

```bash
cd projects/telegram-faq-bot
python3 -m src.cli
python3 -m unittest discover -s tests -v
```
