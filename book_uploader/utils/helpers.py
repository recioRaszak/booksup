from pathlib import Path
import os


def get_data_dir():
    """Obtiene el directorio de datos de la aplicación"""
    data_dir = Path.home() / '.book_uploader'
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_covers_dir():
    """Obtiene el directorio para guardar portadas"""
    covers_dir = get_data_dir() / 'covers'
    covers_dir.mkdir(exist_ok=True)
    return covers_dir


def get_cover_filename(ean):
    """Genera un nombre único para la portada"""
    return f"book_{ean}.jpg"


def get_cover_path(ean):
    """Obtiene la ruta completa para una portada"""
    return get_covers_dir() / get_cover_filename(ean)


def validate_isbn(isbn):
    """Valida formato básico de ISBN"""
    clean = isbn.replace('-', '').replace(' ', '')
    return len(clean) in [10, 13] and clean.isdigit()


def format_price(price):
    """Formatea el precio con 2 decimales"""
    try:
        return f"{float(price):.2f}"
    except:
        return "0.00"


def truncate_text(text, max_length=50):
    """Trunca texto para mostrar en UI"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text
