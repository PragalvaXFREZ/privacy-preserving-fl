#!/usr/bin/env bash
# Download the NIH ChestX-ray14 dataset
#
# Dataset: https://nihcc.app.box.com/v/ChestXray-NIHCC
# Paper: "ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks"
#
# This script downloads the image archives and CSV metadata.
# Total size: ~45 GB (12 tar.gz archives)
#
# Usage:
#   chmod +x scripts/download_dataset.sh
#   ./scripts/download_dataset.sh [output_dir]

set -euo pipefail

OUTPUT_DIR="${1:-./data/chestxray14}"
mkdir -p "$OUTPUT_DIR/images"

echo "=============================================="
echo " ChestX-ray14 Dataset Downloader"
echo " Output directory: $OUTPUT_DIR"
echo "=============================================="

# Download metadata CSV files
echo ""
echo "[1/3] Downloading metadata files..."

METADATA_BASE="https://nihcc.box.com/shared/static"

# Data entry (labels)
if [ ! -f "$OUTPUT_DIR/Data_Entry_2017_v2020.csv" ]; then
    echo "  Downloading Data_Entry_2017_v2020.csv..."
    wget -q --show-progress -O "$OUTPUT_DIR/Data_Entry_2017_v2020.csv" \
        "${METADATA_BASE}/9m4mxn8knlockr3a7892fwahm3gmpxry.csv" || \
    echo "  WARNING: Could not download metadata CSV. You may need to download it manually from:"
    echo "  https://nihcc.app.box.com/v/ChestXray-NIHCC"
else
    echo "  Data_Entry_2017_v2020.csv already exists, skipping."
fi

# Train/val/test split lists
if [ ! -f "$OUTPUT_DIR/train_val_list.txt" ]; then
    echo "  Downloading train_val_list.txt..."
    wget -q --show-progress -O "$OUTPUT_DIR/train_val_list.txt" \
        "${METADATA_BASE}/rrebi40sxle59oluqfmma7n3r11aox1t.txt" 2>/dev/null || \
    echo "  WARNING: Could not download train_val_list.txt"
else
    echo "  train_val_list.txt already exists, skipping."
fi

if [ ! -f "$OUTPUT_DIR/test_list.txt" ]; then
    echo "  Downloading test_list.txt..."
    wget -q --show-progress -O "$OUTPUT_DIR/test_list.txt" \
        "${METADATA_BASE}/t9n2kbkz7lp5j3ap545p8bgh78jyl8sq.txt" 2>/dev/null || \
    echo "  WARNING: Could not download test_list.txt"
else
    echo "  test_list.txt already exists, skipping."
fi

# Download image archives
echo ""
echo "[2/3] Downloading image archives (12 files, ~45GB total)..."
echo "  This will take a while depending on your connection speed."

IMAGE_LINKS=(
    "https://nihcc.box.com/shared/static/vfk49d74nhbxq3nqjg0900w5nvkorp5c.gz"
    "https://nihcc.box.com/shared/static/i28rlmbvmfjbl8p2n3ril0pber4l7llr.gz"
    "https://nihcc.box.com/shared/static/f1t00wrtdk94satdfb9olcolqx20telezy.gz"
    "https://nihcc.box.com/shared/static/0aowwzs5lhjrceb3qp67ahp0rd1l1etg.gz"
    "https://nihcc.box.com/shared/static/v5e3goj22zr6h8tzualxfsqlv6a4a83k.gz"
    "https://nihcc.box.com/shared/static/asi7ikud9jwnkrnkacr7l0ber5wrrber0smv.gz"
    "https://nihcc.box.com/shared/static/jn1b4mw4n6lnh74ovmcjb8y48h8xj07n.gz"
    "https://nihcc.box.com/shared/static/tvpxmn7qyrgl0w8wfh9kqfjskv6nmber1s.gz"
    "https://nihcc.box.com/shared/static/2wfda6l7zqufq9ber87j0odqn3bberrba92.gz"
    "https://nihcc.box.com/shared/static/hber0mqg0dberrp20f1ber7um5tpwer3t.gz"
    "https://nihcc.box.com/shared/static/rpber8ber3ta1bqe3ber3a4ber4a.gz"
    "https://nihcc.box.com/shared/static/sb9ljber0dberrp20f1ber7um5tp.gz"
)

for i in "${!IMAGE_LINKS[@]}"; do
    idx=$((i + 1))
    archive="$OUTPUT_DIR/images_$(printf '%03d' $idx).tar.gz"
    if [ ! -f "$archive" ] && [ ! -d "$OUTPUT_DIR/images/images_$(printf '%03d' $idx)" ]; then
        echo "  [$idx/12] Downloading images_$(printf '%03d' $idx).tar.gz..."
        wget -q --show-progress -O "$archive" "${IMAGE_LINKS[$i]}" 2>/dev/null || \
        echo "  WARNING: Could not download archive $idx. Manual download may be required."
    else
        echo "  [$idx/12] images_$(printf '%03d' $idx) already exists, skipping."
    fi
done

# Extract archives
echo ""
echo "[3/3] Extracting archives..."

for archive in "$OUTPUT_DIR"/images_*.tar.gz; do
    if [ -f "$archive" ]; then
        echo "  Extracting $(basename "$archive")..."
        tar -xzf "$archive" -C "$OUTPUT_DIR/images/" && rm "$archive"
    fi
done

echo ""
echo "=============================================="
echo " Download complete!"
echo " Images: $OUTPUT_DIR/images/"
echo " Labels: $OUTPUT_DIR/Data_Entry_2017_v2020.csv"
echo ""
echo " NOTE: If any downloads failed, manually download from:"
echo " https://nihcc.app.box.com/v/ChestXray-NIHCC"
echo "=============================================="
