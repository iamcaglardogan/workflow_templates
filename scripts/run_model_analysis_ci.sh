#!/usr/bin/env bash
# Pull request code runs without write permissions or persisted Git credentials.
set -euo pipefail

report_dir="${RUNNER_TEMP:-$(mktemp -d)}"
report_path="$report_dir/model_analysis_report.md"
log_path="$report_dir/model_analysis.log"
status=0
python3 "$(dirname "$0")/analyze_models.py" --report "$report_path" "$@" > "$log_path" 2>&1 || status=$?
cat "$log_path"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  python3 - "$log_path" "$GITHUB_STEP_SUMMARY" <<'PYTHON'
import html
import pathlib
import sys

report = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
if len(report) > 60000:
    report = report[:60000] + "\n[Report truncated; see full job log.]"
with open(sys.argv[2], "a", encoding="utf-8") as summary:
    summary.write("## Model analysis\n<pre>" + html.escape(report) + "</pre>\n")
PYTHON
fi

# Preserve validation failures and crashes, including logs without a [FAIL] marker.
exit "$status"
