#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-build.txt

ICON_PATH="$ROOT_DIR/packaging/assets/app-icon-macos.icns"
ICON_ARG=""
if [ -f "$ICON_PATH" ]; then
    ICON_ARG="--icon $ICON_PATH"
fi

pyinstaller --noconfirm --clean --windowed \
  --name "JORGE-Books-to-Woocommerce" \
  --add-data "book_uploader:book_uploader" \
  $ICON_ARG \
  main.py

echo Build macOS finalizado. Revisa dist/JORGE-Books-to-Woocommerce.app
