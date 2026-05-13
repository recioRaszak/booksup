# Distribucion multiplataforma

## Estado

Si, es factible distribuir esta app para Windows 11, Ubuntu Linux y macOS.
URL oficial configurada en la app: https://agency.wham-vintage.com
Version inicial: 0.9.2

Se ha preparado una base con PyInstaller para generar artefactos por plataforma.

## Requisitos generales

1. Crear/activar entorno virtual
2. Instalar dependencias de app y build
3. Ejecutar script de build en cada SO objetivo

## Scripts listos

- Linux: packaging/scripts/build_linux.sh
- Linux DEB: packaging/scripts/package_linux_deb.sh
- Windows: packaging/scripts/build_windows.bat
- macOS: packaging/scripts/build_macos.sh
- macOS DMG: packaging/macos/create_dmg.sh

## Pipeline CI/CD

Workflow preparado en:

- .github/workflows/release-installers.yml
- .github/workflows/release-installers-signed.yml
- packaging/CI_SECRETS.md

Comportamiento:

- Ejecuta builds en Linux, Windows y macOS
- Genera artefactos de instalacion por plataforma
- Publica .deb, .exe y .dmg en GitHub Release al crear un tag v*
- Pipeline signed: firma Windows y notariza macOS cuando los secrets estan configurados

Ejemplo de tag de release:

- v0.9.2

Cada script genera ejecutable en dist/ con nombre JORGE-Books-to-Woocommerce.

## Iconos y splash

Coloca tus assets en packaging/assets:

- app-icon-linux.png
- app-icon-win.ico
- app-icon-macos.icns

Splash esperado por la app:

- book_uploader/resources/splash-placeholder-640x480.png

Si no existe splash, se dibuja un placeholder automaticamente.

## Instaladores recomendados

### Windows 11

1. Generar exe con build_windows.bat
2. Crear instalador con Inno Setup usando:
	- packaging/installers/windows/JORGE-Books-to-Woocommerce.iss
3. Opcional: firmar ejecutable e instalador (code signing)

### Ubuntu Linux

1. Generar binario con build_linux.sh
2. Empaquetar en .deb con packaging/scripts/package_linux_deb.sh
3. Crear launcher .desktop e icono en /usr/share/icons

### macOS

1. Generar .app con build_macos.sh
2. Crear .dmg con packaging/macos/create_dmg.sh
3. Recomendado: notarizacion y firma con Apple Developer ID

## Importante

- PyInstaller debe ejecutarse en cada plataforma destino.
- No conviene compilar Windows desde Linux ni macOS desde Windows para produccion.
- En macOS moderno, la notarizacion mejora mucho la experiencia de instalacion.
