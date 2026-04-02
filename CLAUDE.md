# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SilicaAnimus is a Discord bot for the "La Voie du Thalos" association. It manages member verification by cross-referencing HelloAsso (membership payments) with a Google Sheets spreadsheet, and synchronizes the "Membre" role on Discord accordingly.

## Commands

All commands run from within the `src/` directory. The project uses a local virtualenv at `src/.venv/`.

**Setup:**
```bash
cd src
pip install -e .
```

**Run the bot:**
```bash
cd src && python -m SilicaAnimus
```

**Run all tests:**
```bash
cd src && pytest
```

**Run a single test:**
```bash
cd src && pytest tests/test_file.py::test_function_name
```

**Linting (via pre-commit):**
```bash
pre-commit run --all-files
```

Pre-commit enforces: trailing whitespace, end-of-file newlines, YAML syntax, no large files, and flake8. It runs only on files under `src/`.

**Docker build:**
```bash
docker buildx build --platform linux/arm64/v8,linux/amd64 -t silicaanimus:0.0.2 --load .
```

**Docker run:**
```bash
docker run -it --env-file .env silicaanimus:0.0.1
```

## Architecture

The entrypoint is `src/SilicaAnimus/__main__.py` → `main()` → instantiates `SilicaAnimus` and calls `await silica_animus.run()`.

**`SilicaAnimus` (orchestrator, `silica_animus.py`):**  
Creates the three clients and runs `DiscordClient` and `HelloAssoClient` concurrently in an `asyncio.TaskGroup`. Has a `discord_only=True` mode that skips external API clients.

**`DiscordClient` (`discord_client.py`):**  
Wraps `ThalosBot` (a `discord.ext.commands.Bot` subclass). All slash commands and context menus are registered as module-level `@app_commands` functions and added to the guild's command tree in `setup_hook`. Commands are guild-scoped (not global). Also runs the `weekly_message` task (a `tasks.loop(minutes=1)` that fires on configured weekday/time). `ThalosBot.parent_client` points back to the `DiscordClient` instance, which is how commands reach `helloasso_client` and `gsheet_client`.

**`HelloAssoClient` (`helloasso_client.py`):**  
OAuth2 REST client using Python's `urllib`. Fetches a token on `start()` and schedules an auto-refresh via `asyncio.get_event_loop().call_later`. Membership checks paginate through the HelloAsso orders API.

**`GoogleSheetsClient` (`google_sheets_client.py`):**  
Uses a Google service account to read/write the membership spreadsheet. The spreadsheet columns are: `Nom (last), Prénom (first), Discord nick, Adhérent N-1 (Oui/""), Adhérent N (Oui/"")`. The `MemberInfo` dataclass is the shared data model.

**`utils.py`:**  
`normalize_name(name)` strips quotes/spaces, lowercases, and removes accents (via `unidecode`). Used for all name comparisons to be resilient to formatting differences.

## Environment Variables

A `.env` file is required (never committed; `.env.7z` is the encrypted backup). Required variables:

| Variable | Purpose |
|---|---|
| `DISCORD_TOKEN` | Discord bot OAuth2 token |
| `HELLOASSO_CLIENT_ID` / `HELLOASSO_CLIENT_SECRET` | HelloAsso API credentials |
| `HELLOASSO_TOKEN_URL` | HelloAsso OAuth2 token endpoint |
| `HELLOASSO_API_URL` | HelloAsso API base URL |
| `HELLOASSO_ORGANIZATIONSLUG` | Organization identifier in HelloAsso |
| `HELLOASSO_MEMBERSHIP_FORM_SLUG` | Membership form identifier |
| `GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH` | Path to Google service account JSON key |
| `GOOGLE_SPREADSHEET_ID` | Google Sheets spreadsheet ID |
| `GOOGLE_SHEET_ID` | Sheet tab name within the spreadsheet |
| `WEEKLY_MESSAGE_THREAD_ID` | Discord thread ID for weekly message |
| `WEEKLY_MESSAGE_CONTENT` | Content of weekly message |
| `WEEKLY_MESSAGE_WEEKDAYS` | Comma-separated weekdays (0=Mon…6=Sun) |
| `WEEKLY_MESSAGE_HOUR` / `WEEKLY_MESSAGE_MINUTE` | Time to send the weekly message |

## Tests

Most integration tests require real API credentials from `.env`. Tests that hit live APIs are marked `@pytest.mark.skip`. The `test_discord_client_connection` test is not skipped and will attempt a real Discord connection. `pytest-asyncio` is used for all async tests.
