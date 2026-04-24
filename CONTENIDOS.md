# 📚 BOOK UPLOADER - Índice de Contenidos

## 🗂️ Estructura del Proyecto

```
Wordpress Book Uploader/
├── 📄 main.py                    ← ¡EJECUTA ESTO! (python main.py)
├── 📄 test.py                    ← Tests de verificación
├── 📄 install.sh                 ← Auto-instalador (Linux/Mac)
├── 📄 install.bat                ← Auto-instalador (Windows)
├── 📄 requirements.txt            ← Dependencias Python
├── 
├── 📖 DOCUMENTACION:
├── ├─ README.md                  ← Documentación completa
├── ├─ INICIO_RAPIDO.md           ← Guía rápida (EMPIEZA AQUÍ)
├── ├─ TECNICO.md                 ← Detalles técnicos
├── └─ ARCHIVO_CONENIDOS.md       ← Este archivo
├──
└── 📁 book_uploader/ (El código de la app)
    ├── 📁 api/                   ← Integraciones externas
    │   ├── openbooks.py          ← OpenLibrary + Google Books API
    │   └── woocommerce.py        ← WooCommerce REST API client
    │
    ├── 📁 database/              ← Persistencia de datos
    │   └── db.py                 ← SQLite database manager
    │
    ├── 📁 ui/                    ← Interfaz gráfica
    │   ├── main_window.py        ← Ventana principal + lógica
    │   └── dialogs.py            ← Diálogos (settings, etc)
    │
    ├── 📁 utils/                 ← Utilidades
    │   └── helpers.py            ← Funciones auxiliares
    │
    ├── 📁 resources/             ← Recursos (iconos, etc)
    │
    └── __init__.py               ← Package init
```

---

## 📖 Documentos de Referencia

### Para empezar ahora mismo
👉 **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - Lee esto primero
- Instalación paso a paso
- Cómo configurar WooCommerce
- Primer libro en 5 minutos

### Información completa
📚 **[README.md](README.md)** - Documentación oficial
- Todas las características
- Guía completa de uso
- Troubleshooting
- FAQ

### Detalles técnicos
⚙️ **[TECNICO.md](TECNICO.md)** - Para desarrolladores
- Arquitectura de la app
- APIs utilizadas
- Base de datos
- Posibles mejoras

---

## 🚀 Inicio rápido

### 1. Instalación (primera vez)

**Linux/Mac:**
```bash
cd /path/to/Wordpress\ Book\ Uploader
bash install.sh
```

**Windows:**
```cmd
cd C:\path\to\Wordpress Book Uploader
install.bat
```

### 2. Ejecutar

**Linux/Mac:**
```bash
source venv/bin/activate
python main.py
```

**Windows:**
```cmd
venv\Scripts\activate
python main.py
```

### 3. Configurar sitio

→ Botón **"⚙️ Configurar Sitios"**  
→ Agregar datos de WooCommerce  
→ Probar conexión  
→ Agregar sitio  

### 4. ¡Cargar libros!

→ Pestaña **"➕ Agregar Libro"**  
→ Escanea EAN  
→ Ajusta precio  
→ Descarga portada  
→ Sube a WooCommerce  

---

## 📁 Descripción de Archivos

### Archivos principales (raíz)

| Archivo | Qué es | Cuándo usarlo |
|---------|--------|--------------|
| `main.py` | Punto de entrada | Para ejecutar la app |
| `test.py` | Tests de verificación | Para probar que todo va bien |
| `install.sh` | Script de instalación | Primera vez en Linux/Mac |
| `install.bat` | Script de instalación | Primera vez en Windows |
| `requirements.txt` | Lista de dependencias | Para instalar con pip |
| `.gitignore` | Configuración Git | Si usas control de versiones |

### Módulos de la aplicación

| Archivo | Líneas | Qué hace | Depende de |
|---------|--------|----------|-----------|
| `book_uploader/ui/main_window.py` | ~600 | Ventana principal, formulario | PyQt5, API, DB |
| `book_uploader/ui/dialogs.py` | ~200 | Diálogos (settings, etc) | PyQt5 |
| `book_uploader/api/openbooks.py` | ~120 | Buscar libros por ISBN | requests, Pillow |
| `book_uploader/api/woocommerce.py` | ~160 | Subir a WooCommerce | requests |
| `book_uploader/database/db.py` | ~150 | Base de datos local | sqlite3 |
| `book_uploader/utils/helpers.py` | ~50 | Funciones auxiliares | pathlib |

---

## 🎯 Casos de uso

### Scenario 1: Instalación y primeros pasos
1. Lee: **INICIO_RAPIDO.md**
2. Ejecuta: `bash install.sh` (o `install.bat`)
3. Ejecuta: `python main.py`
4. Configura un sitio
5. Sube tu primer libro

### Scenario 2: Solucionar problemas
1. Ejecuta: `python test.py` (para verificar instalación)
2. Lee: **README.md** → Seción Troubleshooting
3. Verifica logs en `~/.book_uploader/`

### Scenario 3: Entender la arquitectura
1. Lee: **TECNICO.md**
2. Revisa: `book_uploader/database/db.py` (estructura datos)
3. Revisa: `book_uploader/ui/main_window.py` (lógica principal)

### Scenario 4: Modificar la app
1. Lee: **TECNICO.md** (arquitectura)
2. Revisa el código fuente
3. Modifica según necesites
4. Ejecuta: `python test.py` (para verificar)

---

## 🔍 Cómo encontrar lo que necesitas

### "¿Cómo instalo?"
→ **INICIO_RAPIDO.md** (Paso 1)

### "¿Cómo configuro WooCommerce?"
→ **INICIO_RAPIDO.md** (Paso 3)

### "¿Cómo cargo un libro?"
→ **INICIO_RAPIDO.md** (Paso 4)

### "¿Qué hace cada módulo?"
→ **TECNICO.md** (Sección Arquitectura)

### "¿Dónde se guardan los datos?"
→ **TECNICO.md** (Sección Almacenamiento)

### "Tengo un error"
→ **README.md** (Sección Troubleshooting)

### "¿Cómo funciona la base de datos?"
→ **TECNICO.md** (Sección Base de datos)

### "¿Qué APIs usa?"
→ **TECNICO.md** (Sección APIs Integradas)

---

## 📊 Estadísticas del proyecto

- **Lenguaje**: Python 3.7+
- **Líneas de código**: ~1,800
- **Módulos**: 8
- **Dependencias externas**: 5
- **Bases de datos**: SQLite local
- **APIs integradas**: 2 (OpenLibrary, WooCommerce)

---

## ⌨️ Comandos útiles

```bash
# Ver ayuda de Python
python test.py --help

# Reinstalar dependencias
pip install -r requirements.txt --upgrade

# Verificar que Python está bien
python -c "import sys; print(sys.version)"

# Listar paquetes instalados
pip list

# Actualizar pip
pip install --upgrade pip
```

---

## 🏗️ Desarrollo

### Estructura de directorios creados en home

```
~/.book_uploader/
├── data.db                    ← Base de datos SQLite
└── covers/                    ← Imágenes descargadas
    ├── book_9788408016786.jpg
    ├── book_9788467562539.jpg
    └── ...
```

### Log de cambios importantes

Ver `git log` si clonaste del repo, o revisar fechas de archivos.

---

## 💡 Tips y trucos

### ⚡ Atajo del teclado
- Escanea código → Presiona **Enter** (no necesitas hacer clic en Buscar)
- Tab para navegar entre campos
- Ctrl+A para seleccionar todo en un campo

### 🚀 Optimizar velocidad

Para subir muchos libros rápido:
1. Copia los ISBNs en un archivo
2. Lee cada ISBN del archivo
3. Escanea en la app
4. Espera a que complete
5. Repite con el siguiente

### 🔒 Seguridad

- Las credenciales se almacenan en `~/.book_uploader/data.db`
- Es una base de datos SQLite local (no en la nube)
- Si compartes computadora, ten cuidado con acceso a home directory

### 📱 Lector de códigos

Los lectores USB funcionan como teclado virtual:
- Haz clic en campo EAN
- Escanea el código
- Se rellena automáticamente
- Presiona Enter para buscar

---

## 🎓 Para aprender más

### Sobre WooCommerce
- [WooCommerce REST API Docs](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [Crear tokens API](https://docs.woocommerce.com/document/managing-api-keys/)

### Sobre OpenLibrary
- [OpenLibrary API](https://openlibrary.org/developers/api)
- [Búsqueda de libros](https://openlibrary.org/search.json?title=Quijote)

### Sobre Python
- [PyQt5 Documentation](https://riverbankcomputing.com/software/pyqt/)
- [requests Library](https://docs.python-requests.org/)

---

## ✅ Checklist antes de empezar

- [ ] Python 3.7+ instalado
- [ ] pip disponible
- [ ] Tiendas WooCommerce configuradas
- [ ] Consumer Key/Secret obtenidos
- [ ] internet funcionando
- [ ] Lector de códigos preparado (opcional)

---

## 🆘 Necesitas ayuda?

1. **Empezar**: Lee **INICIO_RAPIDO.md**
2. **Problemas**: Lee **README.md** → Troubleshooting
3. **Técnico**: Lee **TECNICO.md**
4. **Urgente**: Ejecuta `python test.py`

---

**¡Espero que disfrutes usando Book Uploader! 📚⚡**

Hecho con ❤️ para automatizar tu trabajo de catalogação.
