#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_APP="$ROOT_DIR/dist/JORGE-Books-to-Woocommerce"
PKG_ROOT="$ROOT_DIR/dist-installer/linux/deb-root"
PKG_NAME="jorge-books-to-woocommerce"
VERSION="0.9.2"
ARCH="amd64"

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb no esta instalado. Instala dpkg-dev en Ubuntu/Debian."
  exit 1
fi

if [ ! -d "$DIST_APP" ]; then
  echo "No existe $DIST_APP. Ejecuta antes packaging/scripts/build_linux.sh"
  exit 1
fi

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/DEBIAN"
mkdir -p "$PKG_ROOT/opt/$PKG_NAME"
mkdir -p "$PKG_ROOT/usr/share/applications"
mkdir -p "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps"

cp -R "$DIST_APP"/* "$PKG_ROOT/opt/$PKG_NAME/"
cp "$ROOT_DIR/packaging/linux/JORGE-Books-to-Woocommerce.desktop" "$PKG_ROOT/usr/share/applications/"

if [ -f "$ROOT_DIR/packaging/assets/app-icon-linux.png" ]; then
  cp "$ROOT_DIR/packaging/assets/app-icon-linux.png" "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps/jorge-books-to-woocommerce.png"
fi

cat > "$PKG_ROOT/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: JORGE Team <noreply@wham-vintage.com>
Description: JORGE - Books to Woocommerce
 Uploader de libros para WooCommerce.
EOF

chmod 755 "$PKG_ROOT/opt/$PKG_NAME/JORGE-Books-to-Woocommerce"

OUT_DIR="$ROOT_DIR/dist-installer/linux"
mkdir -p "$OUT_DIR"

dpkg-deb --build "$PKG_ROOT" "$OUT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "DEB generado en: $OUT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"
