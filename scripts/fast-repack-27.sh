#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$REPO_ROOT"

PAYLOAD_IMG="${PAYLOAD_IMG:-local-golden/payload.img}"
VENDOR_BOOT_IMG="${VENDOR_BOOT_IMG:-local-golden/vendor_boot.img}"
OUT_VENDOR_BOOT="${OUT_VENDOR_BOOT:-out/vendor_boot_b_patched.img}"

# Fallback paths if local-golden is not yet populated
if [ ! -f "$VENDOR_BOOT_IMG" ] && [ -f "/media/theerathep/New Volume/UniXNU_Lab/old_ios17/local_images/vendor_boot_stock.img" ]; then
    VENDOR_BOOT_IMG="/media/theerathep/New Volume/UniXNU_Lab/old_ios17/local_images/vendor_boot_stock.img"
fi

if [ ! -f "$PAYLOAD_IMG" ]; then
    echo "Error: $PAYLOAD_IMG not found. Please place the Golden payload.img from CI in local-golden/payload.img" >&2
    exit 1
fi

mkdir -p out
cp -f "$PAYLOAD_IMG" out/payload_work.img

echo "[1/3] Injecting updated unixnu.toml into FAT32 payload..."
if [ -f "unixnu.toml" ]; then
    mcopy -o -i out/payload_work.img unixnu.toml ::EFI/UniXNU/unixnu.toml
elif [ -f "board.toml" ]; then
    echo "Note: unixnu.toml not found in root, keeping existing payload config."
fi

# Optional JSON injection for display / GPU diagnostics
if [ -f "build/legacy-display-24A446.json" ]; then
    echo "Injecting updated legacy-display-24A446.json..."
    mcopy -o -i out/payload_work.img build/legacy-display-24A446.json ::EFI/UniXNU/legacy-display-24A446.json
fi

echo "[2/3] Patching vendor_boot image locally..."
python3 scripts/patch-vendor-boot.py \
    --input "$VENDOR_BOOT_IMG" \
    --payload out/payload_work.img \
    --output "$OUT_VENDOR_BOOT"

echo "[3/3] Done! Ready to flash to vendor_boot_b (sde51) in 1.5s."
ls -lh "$OUT_VENDOR_BOOT"
