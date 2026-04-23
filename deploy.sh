#!/usr/bin/env bash
#
# AI on Snowflake — Deploy Script (Container Runtime)
#
# Prerequisites:
#   - Snowflake CLI (snow) v3.14.0+ or uvx installed
#   - A named connection configured: snow connection add
#   - The setup.sql script has been run to create the database, schema, stage, and compute pool
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh <connection_name>

set -euo pipefail

CONNECTION="${1:?Usage: ./deploy.sh <snow_cli_connection_name>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== AI on Snowflake — Deployment ==="
echo "Connection: ${CONNECTION}"
echo ""

SNOW_CMD="snow"
SNOW_VERSION=$($SNOW_CMD --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "0.0.0")
MAJOR=$(echo "$SNOW_VERSION" | cut -d. -f1)
MINOR=$(echo "$SNOW_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 14 ]); then
  echo "Snow CLI $SNOW_VERSION detected (< 3.14.0). Using uvx for deployment..."
  SNOW_CMD="uvx --from snowflake-cli snow"
fi

cd "$SCRIPT_DIR"
$SNOW_CMD streamlit deploy --replace --connection "${CONNECTION}"

echo ""
echo "Done! Open your Snowflake account and navigate to Projects > Streamlit to find 'AI Cost Monitor'."
