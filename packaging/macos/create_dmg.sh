#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_PATH="$ROOT_DIR/dist/JORGE-Books-to-Woocommerce.app"
OUT_DIR="$ROOT_DIR/dist-installer/macos"
DMG_NAME="JORGE-Books-to-Woocommerce.dmg"

if [ ! -d "$APP_PATH" ]; then
  echo "No existe $APP_PATH. Ejecuta antes packaging/scripts/build_macos.sh"
  exit 1
fi

mkdir -p "$OUT_DIR"

if command -v create-dmg >/dev/null 2>&1; then
  create-dmg \
    --overwrite \
    --volname "JORGE - Books to Woocommerce" \
    --window-pos 200 120 \
    --window-size 800 420 \
    --icon-size 100 \
    --icon "JORGE-Books-to-Woocommerce.app" 200 190 \
    --hide-extension "JORGE-Books-to-Woocommerce.app" \
    --app-drop-link 600 185 \
    "$OUT_DIR/$DMG_NAME" \
    "$APP_PATH"
else
  hdiutil create -volname "JORGE - Books to Woocommerce" -srcfolder "$APP_PATH" -ov -format UDZO "$OUT_DIR/$DMG_NAME"
fi

echo "DMG generado en: $OUT_DIR/$DMG_NAME"
