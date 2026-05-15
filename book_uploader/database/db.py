import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime


class Database:
    """Gestión de base de datos local SQLite"""
    
    def __init__(self):
        self.db_path = Path.home() / '.book_uploader' / 'data.db'
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Inicializa la base de datos con las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de sitios WooCommerce
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                consumer_key TEXT NOT NULL,
                consumer_secret TEXT NOT NULL,
                wp_username TEXT,
                wp_password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Agregar columnas nuevas si la tabla ya existía sin ellas
        cursor.execute("PRAGMA table_info(sites)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if 'wp_username' not in existing_columns:
            cursor.execute('ALTER TABLE sites ADD COLUMN wp_username TEXT')
        if 'wp_password' not in existing_columns:
            cursor.execute('ALTER TABLE sites ADD COLUMN wp_password TEXT')
        
        # Tabla de productos subidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                ean TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                publisher TEXT,
                format TEXT,
                edition_year INTEGER,
                price REAL,
                cover_image_path TEXT,
                woocommerce_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites(id)
            )
        ''')

        # Tabla de ajustes de la aplicación (clave → valor)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # Tabla de valores por defecto para campos de producto
        # field_type: 'native' = campos WooCommerce nativos,
        #             'custom' = campos personalizados del sitio
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS field_defaults (
                field_key  TEXT PRIMARY KEY,
                field_type TEXT NOT NULL DEFAULT 'native',
                label      TEXT,
                value      TEXT NOT NULL DEFAULT ''
            )
        ''')

        conn.commit()
        conn.close()
    
    def add_site(self, name, url, consumer_key, consumer_secret, wp_username=None, wp_password=None):
        """Agrega un nuevo sitio WooCommerce"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO sites (name, url, consumer_key, consumer_secret, wp_username, wp_password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, url, consumer_key, consumer_secret, wp_username, wp_password))
            conn.commit()
            return True, "Sitio agregado correctamente"
        except sqlite3.IntegrityError:
            return False, "Ya existe un sitio con ese nombre"
        finally:
            conn.close()
    
    def get_all_sites(self):
        """Obtiene todos los sitios configurados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sites ORDER BY id ASC')
        sites = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sites
    
    def get_site(self, site_id):
        """Obtiene información de un sitio específico"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sites WHERE id = ?', (site_id,))
        site = cursor.fetchone()
        conn.close()
        return dict(site) if site else None
    
    def update_site(self, site_id, name, url, consumer_key, consumer_secret, wp_username=None, wp_password=None):
        """Actualiza un sitio existente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE sites 
                SET name = ?, url = ?, consumer_key = ?, consumer_secret = ?, wp_username = ?, wp_password = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (name, url, consumer_key, consumer_secret, wp_username, wp_password, site_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def save_product(self, site_id, ean, title, author, publisher, format_type, 
                    edition_year, price, cover_image_path, woocommerce_id=None):
        """Guarda información de un producto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products 
            (site_id, ean, title, author, publisher, format, edition_year, price, cover_image_path, woocommerce_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (site_id, ean, title, author, publisher, format_type, edition_year, price, cover_image_path, woocommerce_id))
        
        conn.commit()
        conn.close()
    
    def get_products_by_site(self, site_id):
        """Obtiene todos los productos de un sitio"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE site_id = ? ORDER BY created_at DESC', (site_id,))
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return products

    # ── Ajustes de la aplicación ──────────────────────────────────────────────

    def get_setting(self, key: str, default: str = '') -> str:
        """Devuelve el valor de un ajuste o *default* si no existe."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Guarda o actualiza un ajuste."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO app_settings (key, value) VALUES (?, ?) '
            'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
            (key, value)
        )
        conn.commit()
        conn.close()

    def get_all_settings(self) -> dict:
        """Devuelve todos los ajustes como diccionario {key: value}."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM app_settings')
        result = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return result

    # ── Valores por defecto de campos ─────────────────────────────────────────

    def get_field_default(self, field_key: str) -> str:
        """Devuelve el valor por defecto de un campo, o '' si no existe."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM field_defaults WHERE field_key = ?', (field_key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ''

    def set_field_default(self, field_key: str, value: str,
                          label: str = '', field_type: str = 'native') -> None:
        """Guarda o actualiza el valor por defecto de un campo."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO field_defaults (field_key, field_type, label, value) VALUES (?, ?, ?, ?) '
            'ON CONFLICT(field_key) DO UPDATE SET value = excluded.value, '
            'label = excluded.label, field_type = excluded.field_type',
            (field_key, field_type, label, value)
        )
        conn.commit()
        conn.close()

    def get_all_field_defaults(self, field_type: str = None) -> list:
        """Devuelve todos los defaults de campos, opcionalmente filtrados por tipo."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if field_type:
            cursor.execute(
                'SELECT * FROM field_defaults WHERE field_type = ? ORDER BY field_key',
                (field_type,)
            )
        else:
            cursor.execute('SELECT * FROM field_defaults ORDER BY field_type, field_key')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def delete_field_defaults_by_type(self, field_type: str) -> None:
        """Elimina todos los defaults de un tipo determinado (útil al recargar custom fields)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM field_defaults WHERE field_type = ?', (field_type,))
        conn.commit()
        conn.close()

    def delete_site(self, site_id: int) -> None:
        """Elimina un sitio por id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sites WHERE id = ?', (site_id,))
        conn.commit()
        conn.close()
