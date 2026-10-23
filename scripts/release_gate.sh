#!/usr/bin/env bash
# Single reproducible release-candidate test run.
#
# Prerequisites:
#   - API running against the intended staging/development database, e.g.
#       RATE_LIMIT_ENABLED=false .venv/Scripts/python.exe -m uvicorn server:app \
#         --app-dir backend --host 127.0.0.1 --port 8073
#   - backend/.env present (DEFAULT_DEMO_PASSWORD is read from it for the legacy suites)
#   - a local MongoDB for the integration suite (PACIO_TEST_MONGO_URL)
#
# Usage:  bash scripts/release_gate.sh 2>&1 | tee /tmp/release_gate.log
set -u
cd "$(dirname "$0")/.." || exit 1

BASE_URL="${REACT_APP_BACKEND_URL:-http://127.0.0.1:8073}"
MONGO_URI="${PACIO_TEST_MONGO_URL:-mongodb://127.0.0.1:27017}"
PY=".venv/Scripts/python.exe"
[ -x "$PY" ] || PY=".venv/bin/python"
# The hermetic suites seed their own demo password; the legacy suites log into the running
# server, which was seeded from backend/.env. Keep the two values separate - exporting the
# legacy password globally makes the hardening/tenant fixtures log in with the wrong value.
TEST_DEMO_PASSWORD="demo-password-for-tests"
LEGACY_DEMO_PASSWORD="${DEFAULT_DEMO_PASSWORD:-$(grep -m1 '^DEFAULT_DEMO_PASSWORD=' backend/.env 2>/dev/null | cut -d= -f2-)}"
export DEFAULT_DEMO_PASSWORD="$TEST_DEMO_PASSWORD"

echo "HEAD=$(git rev-parse --short HEAD) branch=$(git branch --show-current) tree=$(git status --porcelain | wc -l) changed-file(s)"
echo "server=${BASE_URL} mongo=${MONGO_URI} tests=hardening+tenant+mongo+legacy"

echo "=== hardening ==="
"$PY" -m pytest backend/tests/test_hardening.py -q -p no:cacheprovider
echo "EXIT_HARDENING=$?"

echo "=== tenant isolation ==="
"$PY" -m pytest backend/tests/test_tenant_isolation.py -q -p no:cacheprovider
echo "EXIT_TENANT=$?"

echo "=== real mongodb integration ==="
PACIO_TEST_MONGO_URL="$MONGO_URI" "$PY" -m pytest backend/tests/test_mongo_integration.py -q -p no:cacheprovider
echo "EXIT_MONGO=$?"

echo "=== legacy feature suites (requires live server) ==="
DEFAULT_DEMO_PASSWORD="$LEGACY_DEMO_PASSWORD" REACT_APP_BACKEND_URL="$BASE_URL" "$PY" -m pytest backend/tests/test_careeros_v2.py backend/tests/test_careeros_v21.py -q -p no:cacheprovider
echo "EXIT_LEGACY=$?"

echo "=== done ==="
