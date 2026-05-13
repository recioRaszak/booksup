# CI secrets para firma y notarizacion

Configura estos secrets en GitHub: Settings -> Secrets and variables -> Actions.

## Windows code signing

- WIN_SIGN_CERT_PFX_BASE64
  Contenido base64 del certificado PFX de firma de codigo.
- WIN_SIGN_CERT_PASSWORD
  Password del PFX.
- WIN_SIGN_TIMESTAMP_URL (opcional)
  URL de timestamp RFC3161. Si no se define, usa http://timestamp.digicert.com.

## Apple code signing y notarizacion

- APPLE_SIGN_CERT_P12_BASE64
  Certificado .p12 en base64 (Developer ID Application).
- APPLE_SIGN_CERT_PASSWORD
  Password del .p12.
- APPLE_SIGN_IDENTITY
  Identidad exacta de codesign, por ejemplo:
  Developer ID Application: Tu Empresa (TEAMID)
- APPLE_NOTARY_APPLE_ID
  Apple ID con permisos de notarizacion.
- APPLE_NOTARY_APP_PASSWORD
  App-specific password del Apple ID.
- APPLE_NOTARY_TEAM_ID
  Team ID de Apple Developer.

## Flujo recomendado

1. Crear/actualizar secrets.
2. Crear tag release, por ejemplo v0.9.2.
3. Workflow firmado:
   .github/workflows/release-installers-signed.yml
4. Verificar en GitHub Release que se adjunten .deb, .exe y .dmg.

Si faltan secrets, la workflow sigue generando artefactos sin firma para no bloquear entregas internas.
