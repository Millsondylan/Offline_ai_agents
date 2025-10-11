#!/usr/bin/env bash
set -euo pipefail

# Emit a minimal unified diff for a new file under insightflow_ai_trading/docs/status
cat << 'EOF'
```diff
diff --git a/docs/status/AGENT_DRY_RUN.txt b/docs/status/AGENT_DRY_RUN.txt
new file mode 100644
--- /dev/null
+++ b/docs/status/AGENT_DRY_RUN.txt
@@ -0,0 +1,3 @@
+This file was added by the offline agent dry-run.
+It verifies that only agent changes are staged and committed.
+Marker: DRY_RUN
```
EOF

