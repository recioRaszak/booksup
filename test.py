#!/usr/bin/env python3
"""
Script de test para verificar que todos los módulos funcionan correctamente
"""

import sys
from pathlib import Path

# Añadir el proyecto al path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_imports():
    """Prueba que todos los módulos se importan correctamente"""
    print("🧪 Probando importaciones...")
    
    try:
        from book_uploader.database.db import Database
        print("  ✓ Database importado")
    except ImportError as e:
        print(f"  ✗ Error importando Database: {e}")
        return False
    
    try:
        from book_uploader.api.openbooks import OpenBooksAPI, GoogleBooksAPI
        print("  ✓ OpenBooks API importado")
    except ImportError as e:
        print(f"  ✗ Error importando OpenBooks: {e}")
        return False
    
    try:
        from book_uploader.api.woocommerce import WooCommerceAPI
        print("  ✓ WooCommerce API importado")
    except ImportError as e:
        print(f"  ✗ Error importando WooCommerce: {e}")
        return False
    
    try:
        from book_uploader.utils.helpers import get_data_dir, get_covers_dir
        print("  ✓ Helpers importado")
    except ImportError as e:
        print(f"  ✗ Error importando Helpers: {e}")
        return False
    
    return True

def test_database():
    """Prueba la base de datos"""
    print("\n🧪 Probando base de datos...")
    
    try:
        from book_uploader.database.db import Database
        
        db = Database()
        print("  ✓ Base de datos inicializada")
        
        # Obtener sitios
        sites = db.get_all_sites()
        print(f"  ✓ Se pueden leer sitios (actualmente: {len(sites)})")
        
        return True
    except Exception as e:
        print(f"  ✗ Error en base de datos: {e}")
        return False

def test_openbooks():
    """Prueba la API de OpenBooks"""
    print("\n🧪 Probando API de OpenLibrary...")
    
    try:
        from book_uploader.api.openbooks import OpenBooksAPI
        
        # Prueba con un ISBN conocido (El Quijote)
        print("  Buscando ISBN: 9788408016786 (El Quijote)...")
        book_info = OpenBooksAPI.get_book_by_isbn("9788408016786")
        
        if book_info:
            print(f"  ✓ Libro encontrado:")
            print(f"    - Título: {book_info.get('title')}")
            print(f"    - Autor: {book_info.get('author')}")
            print(f"    - Editorial: {book_info.get('publisher')}")
            return True
        else:
            print("  ⚠ ISBN no encontrado (esto puede ser normal)")
            return True  # No es error crítico
    except Exception as e:
        print(f"  ✗ Error en OpenBooks API: {e}")
        return False

def test_directories():
    """Prueba que se crean los directorios necesarios"""
    print("\n🧪 Probando directorios...")
    
    try:
        from book_uploader.utils.helpers import get_data_dir, get_covers_dir
        
        data_dir = get_data_dir()
        covers_dir = get_covers_dir()
        
        print(f"  ✓ Data dir: {data_dir}")
        print(f"  ✓ Covers dir: {covers_dir}")
        
        if data_dir.exists() and covers_dir.exists():
            print("  ✓ Directorios creados correctamente")
            return True
        else:
            print("  ✗ No se crearon los directorios")
            return False
    except Exception as e:
        print(f"  ✗ Error creando directorios: {e}")
        return False

def main():
    print("=" * 50)
    print("📚 Book Uploader - Suite de Tests")
    print("=" * 50)
    
    results = []
    
    results.append(("Importaciones", test_imports()))
    results.append(("Base de datos", test_database()))
    results.append(("OpenBooks API", test_openbooks()))
    results.append(("Directorios", test_directories()))
    
    print("\n" + "=" * 50)
    print("📊 Resultados")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{passed}/{total} tests pasados")
    
    if passed == total:
        print("\n✅ ¡Todo está funcionando correctamente!")
        print("Puedes ejecutar: python main.py")
        return 0
    else:
        print("\n⚠️ Hay algunos problemas. Revisa arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
