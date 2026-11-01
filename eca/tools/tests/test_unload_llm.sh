#!/usr/bin/env bash
#
# test_unload_llm.sh — test suite for tools/unload_llm.sh
#
# The tests run the script against a local stub of the llama.cpp router API
# (GET /models, POST /models/unload) implemented in python3, so no real model
# is ever touched.
#
# Coverage (mirrors the documented spec in tools/unload_llm.md):
#   happy path  - unload all loaded models; unload a specific model
#   edge cases  - nothing loaded; --help
#   error cases - model id not loaded; mixed valid/invalid ids;
#                 server unreachable; unload rejected by the server
#
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../unload_llm.sh"
TMP="$(mktemp -d)"
PASS=0
FAIL=0
STUB_PID=""
BASE=""

cleanup() {
  if [ -n "$STUB_PID" ]; then
    kill "$STUB_PID" 2>/dev/null
    wait "$STUB_PID" 2>/dev/null
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# stub server
# ---------------------------------------------------------------------------

write_stub() {
  cat > "$TMP/stub.py" <<'PYEOF'
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MODELS = json.load(open(sys.argv[1]))
LOG = sys.argv[2]

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/models":
            self._send(200, {"data": [
                {"id": m["id"], "status": {"value": m["status"]}} for m in MODELS
            ]})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/models/unload":
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n) or b"{}")
            mid = req.get("model", "")
            with open(LOG, "a", newline="\n") as f:
                f.write(mid + "\n")
            for m in MODELS:
                if m["id"] == mid and m["status"] == "loaded":
                    m["status"] = "unloaded"
                    self._send(200, {"ok": True})
                    return
            self._send(400, {"error": {"code": 400, "message": "model is not found",
                                       "type": "invalid_request_error"}})
        else:
            self._send(404, {"error": "not found"})

srv = HTTPServer(("127.0.0.1", 0), Handler)
print("PORT", srv.server_address[1], flush=True)
srv.serve_forever()
PYEOF
}

# start_stub <state-json>
# Starts the stub, waits until it accepts connections, sets $BASE.
start_stub() {
  printf '%s' "$1" > "$TMP/state.json"
  : > "$TMP/unload.log"
  : > "$TMP/stub.out"
  python3 "$TMP/stub.py" "$TMP/state.json" "$TMP/unload.log" > "$TMP/stub.out" 2>&1 &
  STUB_PID=$!
  BASE=""
  for _ in $(seq 1 50); do
    local port
    port="$(sed -n 's/^PORT //p' "$TMP/stub.out" | tail -n 1)"
    if [ -n "$port" ] && curl -s -o /dev/null "http://127.0.0.1:$port/models"; then
      BASE="http://127.0.0.1:$port"
      return 0
    fi
    sleep 0.2
  done
  printf 'stub failed to start\n' >&2
  cat "$TMP/stub.out" >&2
  return 1
}

stop_stub() {
  if [ -n "$STUB_PID" ]; then
    kill "$STUB_PID" 2>/dev/null
    wait "$STUB_PID" 2>/dev/null
    STUB_PID=""
  fi
}

# run_script [args...]
# Runs the script with LLM_API_BASE pointing at the stub; sets $OUT and $RC.
run_script() {
  OUT="$(LLM_API_BASE="$BASE" bash "$SCRIPT" "$@" 2>&1)"
  RC=$?
}

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    PASS=$((PASS + 1))
    printf 'ok   %s\n' "$label"
  else
    FAIL=$((FAIL + 1))
    printf 'FAIL %s\n     expected: %s\n     actual:   %s\n' "$label" "$expected" "$actual"
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  case "$haystack" in
  *"$needle"*)
    PASS=$((PASS + 1))
    printf 'ok   %s\n' "$label"
    ;;
  *)
    FAIL=$((FAIL + 1))
    printf 'FAIL %s\n     missing: %s\n     actual:   %s\n' "$label" "$needle" "$haystack"
    ;;
  esac
}

sorted_unloads() {
  sort "$TMP/unload.log"
}

# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

# happy path: no args -> unload every loaded model
test_happy_path_unload_all() {
  start_stub '[{"id":"model-a","status":"loaded"},{"id":"model-b","status":"loaded"},{"id":"model-c","status":"unloaded"}]'
  run_script
  assert_eq "unload-all: exit code" "0" "$RC"
  assert_eq "unload-all: unload calls (sorted)" "$(printf 'model-a\nmodel-b')" "$(sorted_unloads)"
  assert_contains "unload-all: reports model-a" "Unloaded: model-a" "$OUT"
  assert_contains "unload-all: reports model-b" "Unloaded: model-b" "$OUT"
  assert_contains "unload-all: summary" "Done: 2 model(s) unloaded." "$OUT"
  stop_stub
}

# happy path: specific model id -> only that model is unloaded
test_happy_path_specific_model() {
  start_stub '[{"id":"model-a","status":"loaded"},{"id":"model-b","status":"loaded"}]'
  run_script model-a
  assert_eq "specific: exit code" "0" "$RC"
  assert_eq "specific: only model-a unloaded" "model-a" "$(cat "$TMP/unload.log")"
  assert_contains "specific: reports model-a" "Unloaded: model-a" "$OUT"
  # model-b must remain loaded on the stub
  local models
  models="$(curl -s "$BASE/models")"
  assert_contains "specific: model-b still loaded" '"model-b"' "$models"
  stop_stub
}

# edge case: nothing loaded -> exit 0, "No models loaded.", no unload calls
test_edge_nothing_loaded() {
  start_stub '[{"id":"model-a","status":"unloaded"}]'
  run_script
  assert_eq "nothing-loaded: exit code" "0" "$RC"
  assert_contains "nothing-loaded: message" "No models loaded." "$OUT"
  assert_eq "nothing-loaded: no unload calls" "" "$(cat "$TMP/unload.log")"
  stop_stub
}

# edge case: --help -> exit 0, usage text
test_edge_help() {
  OUT="$(bash "$SCRIPT" --help 2>&1)"
  RC=$?
  assert_eq "help: exit code" "0" "$RC"
  assert_contains "help: usage line" "Usage: unload_llm.sh" "$OUT"
}

# error case: model id not loaded -> exit 1, error reported
test_error_model_not_loaded() {
  start_stub '[{"id":"model-a","status":"loaded"},{"id":"model-b","status":"unloaded"}]'
  run_script model-b
  assert_eq "not-loaded: exit code" "1" "$RC"
  assert_contains "not-loaded: error message" "model not loaded: model-b" "$OUT"
  assert_eq "not-loaded: no unload calls" "" "$(cat "$TMP/unload.log")"
  stop_stub

  # mixed valid + invalid ids: valid one is unloaded, exit 1 overall
  start_stub '[{"id":"model-a","status":"loaded"},{"id":"model-b","status":"unloaded"}]'
  run_script model-a model-b
  assert_eq "mixed: exit code" "1" "$RC"
  assert_eq "mixed: model-a unloaded" "model-a" "$(cat "$TMP/unload.log")"
  assert_contains "mixed: reports model-b error" "model not loaded: model-b" "$OUT"
  stop_stub
}

# error case: server unreachable -> exit 1, error reported
test_error_server_unreachable() {
  BASE="http://127.0.0.1:1"
  OUT="$(LLM_API_BASE="$BASE" bash "$SCRIPT" 2>&1)"
  RC=$?
  assert_eq "unreachable: exit code" "1" "$RC"
  assert_contains "unreachable: error message" "ERROR: cannot list models" "$OUT"
}

# error case: server rejects the unload (already-unloaded duplicate) -> exit 1
test_error_unload_rejected() {
  start_stub '[{"id":"model-a","status":"loaded"}]'
  # the first unload succeeds; the second is rejected by the stub with 400
  run_script model-a model-a
  assert_eq "rejected: exit code" "1" "$RC"
  assert_eq "rejected: two unload attempts" "$(printf 'model-a\nmodel-a')" "$(cat "$TMP/unload.log")"
  assert_contains "rejected: failure reported" "ERROR: failed to unload: model-a" "$OUT"
  stop_stub
}

# ---------------------------------------------------------------------------

write_stub
test_happy_path_unload_all
test_happy_path_specific_model
test_edge_nothing_loaded
test_edge_help
test_error_model_not_loaded
test_error_server_unreachable
test_error_unload_rejected

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
if [ "$FAIL" -eq 0 ]; then
  exit 0
fi
exit 1
