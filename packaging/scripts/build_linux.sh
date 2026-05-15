#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# Generar iconos antes de compilar
"$(dirname "$0")/convert_icons.sh"
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-build.txt

ICON_PATH="$ROOT_DIR/packaging/assets/app-icon-linux.png"
ICON_ARGS=()
if [ -f "$ICON_PATH" ]; then
    ICON_ARGS=("--icon" "$ICON_PATH")
fi

pyinstaller --noconfirm --clean --windowed \
  --name "JORGE-Books-to-Woocommerce" \
  --add-data "book_uploader:book_uploader" \
  "${ICON_ARGS[@]}" \
  "$ROOT_DIR/main.py"

echo "Build Linux finalizado. Revisa dist/JORGE-Books-to-Woocommerce"
