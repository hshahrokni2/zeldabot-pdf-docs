# RUNBOOK — NEVER AGAIN (Do not compact)
**Search token:** #NEVERAGAIN_BRFPARADISE_RIMA

## One‑PDF Smoke Test
set -a; source .env.production; set +a
bash scripts/preflight.sh  # or the inline preflight block in this file
RUN_ID="RUN_$(date +%s)"; python scripts/run_prod.py --run-id "$RUN_ID" --limit 1 --doc-id "<ID>"
tail -n 100 artifacts/calls_log.ndjson | grep "$RUN_ID"
cat artifacts/acceptance/$RUN_ID/summary.json || true

## Gates (Sjöstaden‑2, 2024) — source: verified GT
Assets 301,339,818 | Debt 99,538,124 | Cash 7,335,586 | Org 769606‑2533 | Chair Rolf Johansson | Auditor Katarina Nyberg / HQV.  (See GT file)  