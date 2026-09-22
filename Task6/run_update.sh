#!/usr/bin/env bash
#
# Wrapper for the daily index update (intended for cron).
#
# - Locks against overlapping runs.
# - Uses the project's Python environment.
# - Appends stdout/stderr to logs/cron.log.
# - Retries once on failure.
#
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

PYTHON="python3"
UPDATE="update_index.py"
LOCK="$SCRIPT_DIR/logs/update.lock"
CRON_LOG="$SCRIPT_DIR/logs/cron.log"
MAX_RETRIES=1

mkdir -p "$SCRIPT_DIR/logs"

# --- prevent overlapping runs -------------------------------------------------
if [ -e "$LOCK" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] previous run still active ($LOCK), skipping" >> "$CRON_LOG"
    exit 0
fi
trap 'rm -f "$LOCK"' EXIT
touch "$LOCK"

# --- run with retry -----------------------------------------------------------
attempt=0
while true; do
    attempt=$((attempt + 1))
    {
        echo "===== $(date '+%Y-%m-%d %H:%M:%S') run attempt $attempt ====="
        "$PYTHON" "$UPDATE"
    } >> "$CRON_LOG" 2>&1
    status=$?

    if [ "$status" -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] update succeeded" >> "$CRON_LOG"
        break
    fi

    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] update failed with code $status" >> "$CRON_LOG"
    if [ "$attempt" -gt "$MAX_RETRIES" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] giving up after $attempt attempts" >> "$CRON_LOG"
        exit "$status"
    fi
    sleep 30
done

exit 0