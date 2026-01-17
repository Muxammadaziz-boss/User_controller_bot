# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.0.5] - 2026-01-15

### Security
- **CRITICAL**: Removed all hardcoded API tokens from `config.py`
  - Telegram API credentials
  - OpenRouter/Gemini API keys
  - GitHub tokens
  - All secrets now loaded from `.env` file only
- Added HMAC-SHA256 authentication for device registration and heartbeat messages
- Added rate limiting for admin endpoints (30 req/min default, 5 req/min for sensitive ops)
- Added checksum verification for auto-update files
- Auto-update now **disabled by default** for security

### Added
- `security.py` - New security module with:
  - `HMACAuth` class for message signing/verification
  - `RateLimiter` class with sliding window
  - `verify_file_checksum()` for update integrity
  - `@admin_only` and `@rate_limit` decorators
- `services/` package - Business logic layer:
  - `DeviceService` - Device management with HMAC support
  - `HeartbeatService` - Async/threaded monitoring
  - `AIService` - Unified AI provider wrapper
- `handlers/` package - Modular handler registration:
  - `admin_handlers.py` - Command handlers
  - `callback_handlers.py` - Callback query handlers
- `entrypoint.py` - New minimal startup script
- `tests/` package - Unit tests:
  - `test_security.py` - HMAC, rate limiter, checksum tests
  - `test_database.py` - Database CRUD tests
  - `test_device_service.py` - Service layer tests
- `.github/workflows/ci.yml` - GitHub Actions CI pipeline
- Database migration system with version tracking

### Changed
- `config.py`:
  - Version bumped to 3.0.5
  - Default values changed to `<MUST_SET_IN_ENV>`
  - Added `HMAC_SECRET` configuration
  - Added `AUTO_UPDATE_VERIFY_CHECKSUM` flag
  - Stricter validation for missing env vars
- `database.py`:
  - WAL journaling enabled for better concurrency
  - Added indices on `last_seen`, `status`, `timestamp` columns
  - Added `_run_migrations()` for schema versioning
  - Cache size increased to 64MB
- `.env`:
  - Added `HMAC_SECRET` variable

### Fixed
- Potential race conditions in database access (WAL mode)
- Memory leaks in heartbeat monitoring

### Deprecated
- Direct usage of `bot.py` - use `entrypoint.py` instead
- Original `handlers.py` kept for backward compatibility

---

## [3.0.4] - 2026-01-13

### Added
- Server-client communication improvements
- Heartbeat system integration

### Security
- ⚠️ **WARNING**: This version contains hardcoded API tokens - upgrade to 3.0.5

---

## Required Environment Variables

```env
# Mandatory
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_ID=your_admin_id
HMAC_SECRET=your_random_32byte_hex

# Optional
OPENROUTER_API_KEY=your_key
GEMINI_API_KEY=your_key
GITHUB_TOKEN=your_token
AUTO_UPDATE_ENABLED=true
```

---

## Migration Guide from 3.0.4

1. Backup your `.env` file
2. Replace all files with v3.0.5
3. Add `HMAC_SECRET` to `.env`:
   ```
   HMAC_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
   ```
4. Run `python entrypoint.py` instead of `python bot.py`
5. (Optional) Run tests: `pytest tests/ -v`
