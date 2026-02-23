#!/usr/bin/env bash
# Provision NVFlare workspace with mTLS certificates and startup kits.
#
# This script uses NVFlare's provisioning tool to generate:
# - Root CA certificate
# - Server startup kit (with server cert)
# - Client startup kits (one per hospital)
# - Admin startup kit
#
# Usage:
#   chmod +x scripts/provision_nvflare.sh
#   ./scripts/provision_nvflare.sh
#
# Prerequisites:
#   pip install nvflare>=2.5.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FL_DIR="$PROJECT_DIR/fl_pipeline"
PROVISION_DIR="$FL_DIR/provision"
OUTPUT_DIR="$FL_DIR/workspace"

echo "=============================================="
echo " NVFlare Provisioning"
echo " Project config: $PROVISION_DIR/project.yml"
echo " Output dir:     $OUTPUT_DIR"
echo "=============================================="

# Check nvflare is installed
if ! python -c "import nvflare" 2>/dev/null; then
    echo "ERROR: NVFlare is not installed. Install with:"
    echo "  pip install nvflare>=2.5.0"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run NVFlare provisioning
echo ""
echo "Running NVFlare provision tool..."
python -m nvflare.lighter.provision \
    -p "$PROVISION_DIR/project.yml" \
    -w "$OUTPUT_DIR"

echo ""
echo "=============================================="
echo " Provisioning complete!"
echo ""
echo " Generated startup kits:"
ls -la "$OUTPUT_DIR"/*/startup/ 2>/dev/null || echo "  (check $OUTPUT_DIR for output)"
echo ""
echo " To start the FL server:"
echo "   cd $OUTPUT_DIR/server/startup && ./start.sh"
echo ""
echo " To start FL clients:"
echo "   cd $OUTPUT_DIR/trauma_center/startup && ./start.sh"
echo "   cd $OUTPUT_DIR/pulmonology_clinic/startup && ./start.sh"
echo "   cd $OUTPUT_DIR/general_hospital/startup && ./start.sh"
echo ""
echo " To start admin console:"
echo "   cd $OUTPUT_DIR/admin@healthcare_fl/startup && ./fl_admin.sh"
echo "=============================================="
