#!/usr/bin/env bash
# Convierte el icono PNG base a .ico (Windows), .icns (macOS) y .png (Linux launcher)
# Requiere: imagemagick (convert)
# Opcional: icnsutils (iconutil) - solo para macOS en macOS

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_PNG="$ROOT_DIR/book_uploader/resources/Jorge_app_icon.png"
ASSETS_DIR="$ROOT_DIR/packaging/assets"

# Crear directorio de assets si no existe
mkdir -p "$ASSETS_DIR"

# Verificar que existe el PNG fuente
if [ ! -f "$SRC_PNG" ]; then
    echo "ERROR: No se encontró $SRC_PNG"
    exit 1
fi

# Verificar que 'convert' está disponible
if ! command -v convert &> /dev/null; then
    echo "ERROR: 'convert' (ImageMagick) no está instalado"
    echo "  En Debian/Ubuntu: sudo apt-get install imagemagick"
    echo "  En macOS: brew install imagemagick"
    exit 1
fi

echo "[*] Generando iconos desde: $SRC_PNG"

# ────────────────────────────────────────────────────────────────────────────
# Windows .ico (múltiples resoluciones)
# ────────────────────────────────────────────────────────────────────────────
echo "[*] Generando .ico para Windows..."
convert "$SRC_PNG" -resize 256x256 "$ASSETS_DIR/app-icon-256.png"
convert "$SRC_PNG" -resize 128x128 "$ASSETS_DIR/app-icon-128.png"
convert "$SRC_PNG" -resize 64x64   "$ASSETS_DIR/app-icon-64.png"
convert "$SRC_PNG" -resize 48x48   "$ASSETS_DIR/app-icon-48.png"
convert "$SRC_PNG" -resize 32x32   "$ASSETS_DIR/app-icon-32.png"
convert "$SRC_PNG" -resize 16x16   "$ASSETS_DIR/app-icon-16.png"
convert "$ASSETS_DIR/app-icon-256.png" "$ASSETS_DIR/app-icon-128.png" \
        "$ASSETS_DIR/app-icon-64.png" "$ASSETS_DIR/app-icon-48.png" \
        "$ASSETS_DIR/app-icon-32.png" "$ASSETS_DIR/app-icon-16.png" \
        "$ASSETS_DIR/app-icon-win.ico"
rm -f "$ASSETS_DIR/app-icon-"*.png
echo "    ✓ $ASSETS_DIR/app-icon-win.ico"

# ────────────────────────────────────────────────────────────────────────────
# macOS .icns (solo si iconutil está disponible)
# ────────────────────────────────────────────────────────────────────────────
if command -v iconutil &> /dev/null; then
    echo "[*] Generando .icns para macOS..."
    mkdir -p "$ASSETS_DIR/icon.iconset"
    for size in 16 32 64 128 256 512; do
      convert "$SRC_PNG" -resize ${size}x${size} "$ASSETS_DIR/icon.iconset/icon_${size}x${size}.png"
      convert "$SRC_PNG" -resize $((size*2))x$((size*2)) "$ASSETS_DIR/icon.iconset/icon_${size}x${size}@2x.png"
    done
    iconutil -c icns "$ASSETS_DIR/icon.iconset" -o "$ASSETS_DIR/app-icon-mac.icns"
    rm -rf "$ASSETS_DIR/icon.iconset"
    echo "    ✓ $ASSETS_DIR/app-icon-mac.icns"
else
    echo "[!] iconutil no disponible - usando PNG para macOS (PyInstaller lo puede usar directamente)"
    convert "$SRC_PNG" -resize 512x512 "$ASSETS_DIR/app-icon-mac.png"
    echo "    ~ $ASSETS_DIR/app-icon-mac.png"
fi

# ────────────────────────────────────────────────────────────────────────────
# Linux .png (launcher)
# ────────────────────────────────────────────────────────────────────────────
echo "[*] Generando .png para Linux..."
convert "$SRC_PNG" -resize 256x256 "$ASSETS_DIR/app-icon-linux.png"
echo "    ✓ $ASSETS_DIR/app-icon-linux.png"

# ────────────────────────────────────────────────────────────────────────────
# Resumen
# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "✓ Iconos generados en: $ASSETS_DIR"
ls -lh "$ASSETS_DIR"/app-icon-* | awk '{print "  " $9 " (" $5 ")"}'
echo ""
