import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
import os


class GoogleBooksAPI:
    """Consultar información de libros usando Google Books API"""
    
    BASE_URL = "https://www.googleapis.com/books/v1"
    
    @staticmethod
    def get_book_by_isbn(isbn):
        """
        Obtiene información de un libro por ISBN usando Google Books
        """
        try:
            # Limpiar el ISBN
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            
            url = f"{GoogleBooksAPI.BASE_URL}/volumes?q=isbn:{clean_isbn}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and data['items']:
                    book_data = data['items'][0]['volumeInfo']
                    return GoogleBooksAPI._parse_google_data(book_data)
            
            return None
        except Exception as e:
            print(f"Error al buscar en Google Books: {e}")
            return None
    
    @staticmethod
    def _parse_google_data(data):
        """Parsea la respuesta de Google Books"""
        try:
            book_info = {
                'title': data.get('title', ''),
                'author': ', '.join(data.get('authors', [])),
                'publisher': data.get('publisher', ''),
                'edition_year': None,
                'format': 'Tapa blanda',  # Default
                'cover_url': None
            }
            
            # Obtener año
            if 'publishedDate' in data:
                try:
                    year_str = data['publishedDate'][:4]
                    book_info['edition_year'] = int(year_str)
                except:
                    pass
            
            # Obtener URL de la portada
            if 'imageLinks' in data and 'thumbnail' in data['imageLinks']:
                book_info['cover_url'] = data['imageLinks']['thumbnail']
            
            return book_info
        except Exception as e:
            print(f"Error al parsear datos de Google: {e}")
            return None
    
    @staticmethod
    def download_cover(cover_url, output_path):
        """
        Descarga la imagen de la portada desde Google Books
        """
        try:
            if not cover_url:
                return None
            
            # Google Books thumbnails are small, try to get larger
            cover_url = cover_url.replace('zoom=1', 'zoom=2')
            
            response = requests.get(cover_url, timeout=5)
            if response.status_code == 200:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                img = Image.open(BytesIO(response.content))
                img.save(output_path)
                return output_path
            
            return None
        except Exception as e:
            print(f"Error al descargar portada de Google: {e}")
            return None