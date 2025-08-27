#!/usr/bin/env bash
set -euo pipefail
echo "== PRODUCTION PREFLIGHT =="

: "${DATABASE_URL:?Missing DATABASE_URL}"
: "${OBS_STRICT:?Missing OBS_STRICT}"
: "${QWEN_TRANSPORT:?Missing QWEN_TRANSPORT}"
: "${OLLAMA_URL:?Missing OLLAMA_URL}"
: "${QWEN_MODEL_TAG:?Missing QWEN_MODEL_TAG}"

# 1) DB must be the approved production host
if ! echo "$DATABASE_URL" | grep -E "zelda_arsredovisning" >/dev/null; then
  echo "❌ DATABASE_URL must target zelda_arsredovisning"; exit 12; fi

# 2) Corpus size must be large enough (≥100, expected 200 on H100)  
DOCS=$(PGPASSWORD='Zelda4Ever!' psql "$DATABASE_URL" -XtAc "SELECT COUNT(*) FROM arsredovisning_documents;" || echo "0")
if [ -z "$DOCS" ] || [ "$DOCS" -lt 100 ]; then
  echo "❌ Expected ≥100 docs in production DB, found: $DOCS"; exit 13; fi

# 2b) DSN host validation - only allow H100 tunnel or direct H100
if ! echo "$DATABASE_URL" | grep -E "localhost:15432|45\.135\.56\.10" >/dev/null; then
  echo "❌ DATABASE_URL must use H100 tunnel (localhost:15432) or direct H100 host"; exit 19; fi

# 2c) Block common faux DB hosts
if echo "$DATABASE_URL" | grep -E "127\.0\.0\.1:5432|127\.0\.0\.1:5433|localhost:5432|localhost:5433" >/dev/null; then
  echo "❌ Faux/local DB detected. Production must use H100 DB only"; exit 20; fi

# 3) Ollama parity & model pin
OLLAMA_VERSION=$(ollama --version 2>/dev/null || true)
if ! echo "$OLLAMA_VERSION" | grep -E "0\.1[1-9]\.|1\." >/dev/null; then
  echo "❌ Ollama server too old: $OLLAMA_VERSION"; exit 14; fi

if ! curl -s "$OLLAMA_URL/api/tags" | grep -q "\"name\":\"${QWEN_MODEL_TAG}\""; then
  echo "❌ Model $QWEN_MODEL_TAG not installed on Ollama"; exit 15; fi

# 4) No "simulation" code sneaking in (ban time.sleep in pipeline code paths)
if grep -R --line-number -E "time\.sleep\(" scripts src | grep -v tests | grep -v "retry_backoff" | grep -v preflight.sh >/dev/null; then
  echo "❌ Banned simulation sleep() detected in production code path"; exit 16; fi

# 5) Strict mode must be ON, salvage OFF
if [ "${OBS_STRICT}" != "1" ]; then echo "❌ OBS_STRICT must be 1"; exit 17; fi
if [ "${JSON_SALVAGE:-0}" != "0" ]; then echo "❌ JSON_SALVAGE must be 0 in prod"; exit 18; fi

# 6) Gemini availability (if twin mode enabled)
if [ "${TWIN_AGENTS:-1}" = "1" ]; then
  : "${GEMINI_API_KEY:?Missing GEMINI_API_KEY for twin mode}"
fi

echo "✅ PREFLIGHT PASSED"