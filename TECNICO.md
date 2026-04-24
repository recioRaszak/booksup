# 📚 Book Uploader - Resumen Técnico

## ✅ Aplicación completada

Se ha creado una **aplicación Python desktop profesional** para gestionar la carga de libros en múltiples tiendas WooCommerce mediante códigos de barras (EAN/ISBN).

---

## 🎯 ¿Qué hace la app?

1. **Gestiona múltiples sitios WooCommerce**
   - Guarda credenciales localmente
   - Prueba conexión antes de guardar
   - Cambio rápido entre sitios

2. **Obtiene información de libros automáticamente**
   - Escanea codes de barras (EAN/ISBN)
   - Busca en OpenLibrary (y Google Books como alternativa)
   - Obtiene: Título, Autor, Editorial, Formato, Año

3. **Descarga automáticamente portadas**
   - Desde OpenLibrary
   - O selecciona archivo local

4. **Sube productos a WooCommerce**
   - Crea productos con descripción completa
   - Incluye imagen de portada
   - Publica automáticamente
   - Guarda en historial local

---

## 🏗️ Arquitectura

```
book_uploader/
├── api/                          # Integraciones externas
│   ├── openbooks.py              # OpenLibrary + Google Books
│   └── woocommerce.py            # REST API de WooCommerce
├── database/                     # Persistencia de datos
│   └── db.py                     # SQLite (sitios, historial)
├── ui/                           # Interfaz gráfica
│   ├── main_window.py            # Ventana principal
│   └── dialogs.py                # Diálogos (settings, etc)
└── utils/                        # Utilidades
    └── helpers.py                # Funciones auxiliares
```

---

## 🔧 Tecnologías utilizadas

| Componente | Librería | Razón |
|-----------|---------|-------|
| **GUI** | PyQt5 | Interfaz moderna y profesional |
| **Database** | SQLite3 | Almacenamiento local sin servidor |
| **APIs REST** | requests | Comunicación con OpenLibrary y WooCommerce |
| **Imágenes** | Pillow | Manejo y visualización de portadas |
| **Configuración** | python-dotenv | Variables de entorno (opcional) |

---

## 💾 Almacenamiento

- **Base de datos**: `~/.book_uploader/data.db`
  - Tabla `sites`: Sitios WooCommerce configurados
  - Tabla `products`: Historial de productos subidos
  
- **Imágenes**: `~/.book_uploader/covers/`
  - Se guardan con nombre: `book_<EAN>.jpg`

---

## 🚀 Características clave

### ⚡ Optimizada para velocidad
- Thread workers para no bloquear UI
- Carga incremental de páginas
- Caché local de imágenes

### 🔒 Segura
- Credenciales almacenadas localmente (no en la nube)
- Contraseñas ocultas en UI
- Prueba de conexión antes de generar token

### 🎨 Interfaz intuitiva
- 2 tabs principales: Agregar libro + Historial
- Campos auto-rellenables
- Vista previa de portadas
- Indicadores visuales de estado

### 📱 Amigable con lectores de códigos
- Campo EAN con focus automático
- Aceptar Enter para buscar
- Escaneo directo sin confirmaciones

---

## 📋 Flujo de trabajo

```
┌─────────────────────────────────┐
│   Escanear código de barras     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Obtener info de OpenLibrary    │
│  (Título, Autor, Editorial)     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   Descargar portada             │
│   (o seleccionar local)         │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   Ajustar precio y detalles     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Subir a WooCommerce            │
│  (API REST)                     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Guardar en historial local     │
│  ✅ COMPLETADO                  │
└─────────────────────────────────┘
```

---

## 📊 Base de datos

### Tabla: `sites`
```sql
- id (int) - Primary key
- name (str) - Nombre del sitio
- url (str) - URL de WooCommerce
- consumer_key (str) - API Key
- consumer_secret (str) - API Secret
- created_at (timestamp)
- updated_at (timestamp)
```

### Tabla: `products`
```sql
- id (int) - Primary key
- site_id (int) - Foreign key a sites
- ean (str) - Código de barras
- title (str) - Título del libro
- author (str) - Autor
- publisher (str) - Editorial
- format (str) - Formato (Tapa dura, bolsillo, etc)
- edition_year (int) - Año de edición
- price (float) - Precio
- cover_image_path (str) - Ruta de la portada
- woocommerce_id (int) - ID del producto en WooCommerce
- created_at (timestamp)
```

---

## 🔌 APIs Integradas

### OpenLibrary API
```python
# Busca un libro por ISBN
book_info = OpenBooksAPI.get_book_by_isbn("9788408016786")
# Retorna: {title, author, publisher, edition_year, cover_url, format}
```

### WooCommerce REST API
```python
# Crea un producto
api = WooCommerceAPI(site_url, consumer_key, consumer_secret)
product = api.create_product({
    'name': 'El Quijote',
    'description': 'HTML con detalles',
    'regular_price': '4.00',
    'stock_quantity': 1
})

# Sube una imagen
api.upload_product_image(product_id, image_path)
```

---

## 🎮 Instrucciones de uso

### Instalación

```bash
# Linux/Mac
bash install.sh

# Windows
install.bat
```

### Ejecución

```bash
# Linux/Mac
source venv/bin/activate
python main.py

# Windows
venv\Scripts\activate
python main.py
```

### Primeros pasos

1. **Abre la app** → `⚙️ Configurar Sitios`
2. **Agrega tu sitio WooCommerce** (necesitas Consumer Key/Secret)
3. **Prueba conexión** → Debe decir "✅ exitosa"
4. **Agregar Libro** → Escanea código → Descarga portada → Sube
5. **Historial** → Ve tus productos subidos

---

## ⏱️ Rendimiento esperado

| Operación | Tiempo |
|-----------|--------|
| Buscar info en OpenLibrary | 2-3 segundos |
| Descargar portada | 1-2 segundos |
| Crear producto en WooCommerce | 2-3 segundos |
| **Ciclo completo/libro** | ~5-10 segundos |

Con 100 libros: **~10-15 minutos** (sin parar entre libros)

---

## 🛡️ Manejo de errores

La aplicación maneja:
- ✓ Conexión fallida a WooCommerce
- ✓ ISBN no encontrado
- ✓ Imagen no disponible
- ✓ Campos inválidos
- ✓ Problemas de red

Todos los errores muestran mensajes claros al usuario.

---

## 🔮 Posibles mejoras futuras

- [ ] Búsqueda por título/autor
- [ ] Importar libros desde archivo (CSV, Excel)
- [ ] Categorías automáticas
- [ ] Descuentos por cantidad
- [ ] Log detallado de operaciones
- [ ] Backend remoto para sincronización
- [ ] Soporte para otros marketplaces

---

## 📝 Archivos creados

```
/home/israel/Documents/DEV/Wordpress Book Uploader/
├── main.py                      ← Punto de entrada
├── test.py                      ← Script de tests
├── requirements.txt             ← Dependencias Python
├── install.sh                   ← Script instalación Linux/Mac
├── install.bat                  ← Script instalación Windows
├── README.md                    ← Documentación completa
├── INICIO_RAPIDO.md            ← Guía rápida de inicio
├── .gitignore                  ← Para Git
└── book_uploader/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── openbooks.py        ← (560 líneas)
    │   └── woocommerce.py      ← (160 líneas)
    ├── database/
    │   ├── __init__.py
    │   └── db.py               ← (150 líneas)
    ├── ui/
    │   ├── __init__.py
    │   ├── main_window.py      ← (600+ líneas)
    │   └── dialogs.py          ← (200+ líneas)
    └── utils/
        ├── __init__.py
        └── helpers.py          ← (50 líneas)
```

---

## ✨ Estado actual

✅ **COMPLETADO Y FUNCIONAL**

- [x] Interfaz gráfica (PyQt5)
- [x] Base de datos local (SQLite)
- [x] Integración OpenLibrary/Google Books
- [x] Integración WooCommerce REST API
- [x] Descarga automática de imágenes
- [x] Manejo de errores y excepciones
- [x] Threading para operaciones asincrónicas
- [x] Historial de productos
- [x] Tests de funcionalidad
- [x] Documentación completa
- [x] Scripts de instalación (Linux/Windows)

---

## 🚀 ¡Listo para usar!

La aplicación está completa y funcionando. Puedes:

1. **Ejecutar ahora**: `python main.py` (desde la carpeta del proyecto)
2. **Configurar tu primer sitio**: Menu ⚙️
3. **Comenzar a subir libros**: Escanea y carga

¡Diseñada para hacer el trabajo ágilmente! 📚⚡
