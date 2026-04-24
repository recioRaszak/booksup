# 🚀 INICIO RÁPIDO - Book Uploader

## Paso 1: Instalación (primera vez)

En Linux/Mac:
```bash
cd /home/israel/Documents/DEV/Wordpress\ Book\ Uploader
bash install.sh
```

En Windows:
```cmd
cd C:\ruta\a\Wordpress Book Uploader
install.bat
```

## Paso 2: Ejecutar la aplicación

En Linux/Mac:
```bash
source venv/bin/activate
python main.py
```

En Windows:
```cmd
venv\Scripts\activate
python main.py
```

## Paso 3: Configurar tu sitio WooCommerce

1. **Abre la aplicación**
2. Haz clic en **"⚙️ Configurar Sitios"**
3. Rellena los datos (necesitas las credenciales de WooCommerce):

   **¿Dónde obtener las credenciales?**
   - Panel WordPress → WooCommerce → Ajustes → API
   - "REST API" → "Generar nuevo token API"
   - Description: "Book Uploader"
   - User: Tu usuario (admin)
   - Permissions: Read/Write
   - ¡Copia la Consumer Key y Consumer Secret!

4. Pega en el formulario:
   - **Nombre**: Mi Tienda (o el nombre que prefieras)
   - **URL**: https://misitio.com
   - **Consumer Key**: (pégala aquí)
   - **Consumer Secret**: (pégala aquí)

5. **"🔗 Probar Conexión"** → Debe decir ✅ exitosa
6. **"✅ Agregar Sitio"**

## Paso 4: Cargar tu primer libro

1. **Selecciona el sitio** en el combo de arriba
2. **Pestaña "➕ Agregar Libro"**
3. **Escanea el código de barras** del libro (EAN/ISBN)
   - O escribe el número manualmente
4. **Presiona Enter** o haz clic en "🔍 Buscar"
5. La app obtiene automáticamente:
   - ✓ Título
   - ✓ Autor
   - ✓ Editorial
   - ✓ Formato
   - ✓ Año
6. **Ajusta el precio** si es necesario (default: €4.00)
7. **Descarga la portada**: "⬇️ Descargar autom."
8. **Sube a WooCommerce**: "✅ Subir a WooCommerce"
9. ✅ ¡Listo! Revisa en tu Web de WooCommerce

## ⚡ Flujo optimizado para muchos libros

1. Ten lista la lista de libros (con códigos de barras)
2. Abre Book Uploader
3. Para cada libro:
   ```
   Escanea → Enter → Ajusta precio → Descarga portada → Sube
   ```
4. **La app está diseñada para este ciclo rápido**

## 🎯 Consejos

- ✅ **Precisa el precio por defecto** en el first lugar si todos cuestan lo mismo
- ✅ **Verifica en WooCommerce** después de subir unos pocos
- ✅ **Si el ISBN no se encuentra**: Busca manual la info y completa el formulario
- ✅ **Las portadas se guardan locales** en `~/.book_uploader/covers/`
- ✅ **El historial muestra todo** lo que has subido

## 📱 Con lector de códigos de barras

Si tienes un lector USB:
1. Haz clic en el campo EAN
2. Escanea el código
3. El campo se rellena automáticamente
4. Presiona Enter
5. ¡Automático!

## ❓ Si algo va mal

**"Connection refused"**: Verifica que WooCommerce esté activo  
**"API Error"**: Comprueba las credenciales (Consumer Key/Secret)  
**"ISBN no encontrado"**: El libro puede no estar en OpenLibrary, completa manual  
**"Sin portada"**: Selecciona un archivo local

## 🆘 Problemas comunes

| Problema | Solución |
|----------|----------|
| "ModuleNotFoundError" | Ejecuta `source venv/bin/activate` primero |
| No se muestra ventana | Intenta: `python3 main.py` en lugar de `python main.py` |
| Credenciales rechazadas | Regenera un nuevo token en WooCommerce |
| La app se congela | Es normal, está subiendo. Espera. |

---

**¡Ya estás listo para subir libros! 🎉**
