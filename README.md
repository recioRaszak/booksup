# 📚 JORGE - Books to Woocommerce

Una aplicación moderna y ágil para cargar libros masivamente en tus sitios WooCommerce usando códigos de barras (EAN/ISBN).

## 🎯 Características

- ✨ **Lectora de códigos de barras**: Escanea el EAN/ISBN directamente
- 📖 **Búsqueda automática**: Obtiene información del libro desde OpenLibrary
- 🖼️ **Descarga de portadas**: Descarga automáticamente la imagen de la portada
- 🌐 **Soporte multi-sitio**: Gestiona múltiples tiendas WooCommerce
- 💾 **Historial local**: Guarda registro de todos los productos subidos
- ⚡ **Interfaz ágil**: Diseñada para catalogar rápidamente muchos libros
- 🔒 **Credenciales seguras**: Almacenamiento local de API keys

## 📋 Requisitos

- Python 3.7+
- pip (gestor de paquetes de Python)

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd /ruta/a/Wordpress\ Book\ Uploader
```

### 2. Crear entorno virtual (opcional pero recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🏃 Uso

### Iniciar la aplicación

```bash
python main.py
```

Tambien puedes lanzar con:

```bash
./"Jorge Books to Woocommerce"
```

### Configurar sitios WooCommerce

1. **Abre la aplicación**
2. Haz clic en **"⚙️ Configurar Sitios"**
3. Ingresa los datos de tu sitio:
   - **Nombre**: Nombre reconocible para tu tienda
   - **URL**: URL de tu sitio (ej: https://mitienda.com)
   - **Consumer Key**: Obtén desde WooCommerce → Ajustes → API
   - **Consumer Secret**: Obtén desde WooCommerce → Ajustes → API
4. Haz clic en **"🔗 Probar Conexión"** para validar
5. Haz clic en **"✅ Agregar Sitio"**

#### Cómo obtener las credenciales de WooCommerce

1. Ve a **Panel de Control de WordPress**
2. Dirígete a **WooCommerce → Ajustes → API**
3. En la pestaña **Keys/Tokens**, haz clic en **"Generar nuevo token API"**
4. Rellena:
   - **Description**: "Book Uploader"
   - **User**: Tu usuario con permisos de administrador
   - **Permissions**: Elige "Read/Write"
5. Copia la **Consumer key** y **Consumer secret**

### Agregar un libro

1. **Abre la pestaña "➕ Agregar Libro"**
2. **Escanea el código de barras** en el campo EAN/ISBN
   - O ingresa manualmente el código
3. **Haz clic en "🔍 Buscar"** o presiona Enter
4. La aplicación automáticamente completará:
   - Título
   - Autor
   - Editorial
   - Formato
   - Año de edición
5. **Ajusta campos si es necesario**:
   - Precio (default: €4.00)
   - Stock (default: 1)
6. **Descarga la portada**:
   - Haz clic en "⬇️ Descargar autom." para descargar automáticamente
   - O usa "📁 Seleccionar archivo" para elegir una imagen local
7. **Sube el producto** haciendo clic en **"✅ Subir a WooCommerce"**

### Ver historial

La pestaña **"📋 Historial"** muestra todos los productos que has subido, con estado de confirmación.

## 📦 Estructura del Proyecto

```
Wordpress Book Uploader/
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias Python
├── book_uploader/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── openbooks.py        # Integración con OpenLibrary y Google Books
│   │   └── woocommerce.py      # Client REST de WooCommerce
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Ventana principal
│   │   ├── dialogs.py          # Diálogos (configuración, etc)
│   │   └── resources/          # Recursos (iconos, etc)
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py               # SQLite local
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Funciones auxiliares
└── README.md
```

## 🔐 Almacenamiento de Datos

- **Base de datos**: `~/.book_uploader/data.db` (SQLite)
- **Portadas**: `~/.book_uploader/covers/` (Imágenes)
- Los datos se guardan localmente en tu máquina

## 📝 Flujo de trabajo recomendado

1. **Preparación**:
   - Configura todos tus sitios WooCommerce primero
   
2. **Carga rápida**:
   - Selecciona el sitio en el combo
   - Escanea el código de barras
   - Ajusta precio si es necesario
   - Descarga portada
   - Sube el producto
   - **Repite**: La aplicación está optimizada para este ciclo rápido

3. **Control**:
   - Verifica el historial regularmente
   - Revisa en WooCommerce que los productos se crearon correctamente

## ⚙️ Configuración avanzada

### Variables de entorno (opcional)

Crea un archivo `.env` en la raíz del proyecto:

```env
# Ejemplo (no recomendado para producción)
WOOCOMMERCE_API_KEY=ck_...
WOOCOMMERCE_API_SECRET=cs_...
```

### Cambiar sitio por defecto

Edita `book_uploader/utils/helpers.py` para personalizar directorios.

## 🐛 Troubleshooting

### "No se encontró información para este ISBN"
- Verifica que el ISBN esté bien escaneado
- Algunos libros viejos pueden no estar en OpenLibrary
- Intenta buscar en Google Books manualmente

### "Error al conectar a WooCommerce"
- Verifica que el Consumer Key y Secret sean correctos
- Asegúrate de que tu usuario tiene permisos de lectura/escritura
- Verifica que WordPress/WooCommerce esté accesible desde tu red

### "La portada no se descarga"
- Algunos libros pueden no tener portada disponible en OpenLibrary
- Usa la opción "Seleccionar archivo" para cargar una imagen local

### La aplicación se congela
- Significa que se está buscando información o subiendo el producto
- Espera a que complete (barra de progreso)
- Los threads evitan que la UI se bloquee

## 📞 Soporte

Para reportar problemas o sugerir mejoras, crea un issue en el repositorio.

## 📄 Licencia

MIT - Libre para uso personal y comercial

## 🎉 ¡Comienza ahora!

```bash
# 1. Instala las dependencias
pip install -r requirements.txt

# 2. Inicia la aplicación
python main.py

# 3. Configura tu primer sitio
# 4. ¡Empieza a subir libros!
```

---

**Hecho para catalogadores de libros**
