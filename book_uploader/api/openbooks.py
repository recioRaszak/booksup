import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
import os


class OpenBooksAPI:
    """Consultar información de libros usando OpenLibrary API"""
    
    BASE_URL = "https://openlibrary.org"
    
    @staticmethod
    def get_book_by_isbn(isbn):
        """
        Obtiene información de un libro por ISBN
        ISBN puede ser ISBN-10 o ISBN-13 (o convertirlo a ISBN sin guiones)
        """
        try:
            # Limpiar el ISBN (remover guiones y espacios)
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            
            # Intentar con OpenLibrary API/books
            url = f"{OpenBooksAPI.BASE_URL}/api/books?bibkeys=ISBN:{clean_isbn}&jscmd=data&format=json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    key = list(data.keys())[0]
                    book_data = data[key]
                    return OpenBooksAPI._parse_openlibrary_data(book_data)

            # Fallback OpenLibrary Search API: algunos ISBN aparecen aqui aunque api/books no devuelva.
            search_url = f"{OpenBooksAPI.BASE_URL}/search.json?isbn={clean_isbn}&limit=1"
            search_response = requests.get(search_url, timeout=5)
            if search_response.status_code == 200:
                search_data = search_response.json()
                docs = search_data.get('docs', []) if isinstance(search_data, dict) else []
                if docs:
                    return OpenBooksAPI._parse_openlibrary_search_doc(docs[0])
            
            return None
        except Exception as e:
            print(f"Error al buscar en OpenLibrary: {e}")
            return None

    @staticmethod
    def _parse_openlibrary_search_doc(doc):
        """Parsea un resultado de OpenLibrary Search API."""
        try:
            return {
                'title': doc.get('title', '') or '',
                'author': ', '.join(doc.get('author_name', [])[:3]) if isinstance(doc.get('author_name'), list) else '',
                'publisher': (doc.get('publisher', [''])[0] if isinstance(doc.get('publisher'), list) and doc.get('publisher') else ''),
                'edition_year': (doc.get('first_publish_year') if isinstance(doc.get('first_publish_year'), int) else None),
                'format': 'Tapa blanda',
                'cover_url': f"https://covers.openlibrary.org/b/isbn/{doc.get('isbn', [''])[0]}-M.jpg" if isinstance(doc.get('isbn'), list) and doc.get('isbn') else None,
            }
        except Exception as e:
            print(f"Error al parsear search doc de OpenLibrary: {e}")
            return None
    
    @staticmethod
    def _parse_openlibrary_data(data):
        """Parsea la respuesta de OpenLibrary"""
        try:
            book_info = {
                'title': data.get('title', ''),
                'author': ', '.join([author.get('name', '') for author in data.get('authors', [])]),
                'publisher': data.get('publishers', [{}])[0].get('name', '') if data.get('publishers') else '',
                'edition_year': None,
                'format': 'Tapa blanda',  # Default
                'cover_url': None
            }
            
            # Obtener año de publicación
            if 'publish_date' in data:
                try:
                    year_str = str(data['publish_date']).split()[-1]
                    book_info['edition_year'] = int(year_str)
                except:
                    pass
            
            # Obtener URL de la portada
            if 'cover' in data and 'medium' in data['cover']:
                book_info['cover_url'] = data['cover']['medium']
            
            return book_info
        except Exception as e:
            print(f"Error al parsear datos: {e}")
            return None
    
    @staticmethod
    def download_cover(cover_url, output_path):
        """
        Descarga la imagen de la portada
        
        Args:
            cover_url: URL de la imagen
            output_path: Ruta donde guardar la imagen
            
        Returns:
            Ruta del archivo guardado o None
        """
        try:
            if not cover_url:
                return None
            
            response = requests.get(cover_url, timeout=5)
            if response.status_code == 200:
                # Crear directorio si no existe
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Guardar imagen
                img = Image.open(BytesIO(response.content))
                img.save(output_path)
                return output_path
            
            return None
        except Exception as e:
            print(f"Error al descargar portada: {e}")
            return None
    
    @staticmethod
    def get_book_formats():
        """Retorna los formatos comunes de libros"""
        return [
            'Tapa dura',
            'Tapa blanda',
            'Bolsillo',
            'E-book',
            'Cartoné',
            'Otro'
        ]


class GoogleBooksAPI:
    """Alternativa: Consultar información usando Google Books API"""
    
    BASE_URL = "https://www.googleapis.com/books/v1"
    
    @staticmethod
    def get_book_by_isbn(isbn, api_key=None):
        """
        Obtiene información de Google Books por ISBN
        Nota: Sin API key funcionará pero con limitaciones de rate limit
        """
        try:
            clean_isbn = isbn.replace('-', '').replace(' ', '')
            
            url = f"{GoogleBooksAPI.BASE_URL}/volumes?q=isbn:{clean_isbn}"
            if api_key:
                url += f"&key={api_key}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('items'):
                    book_data = data['items'][0].get('volumeInfo', {})
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
                'format': 'Tapa blanda',
                'cover_url': None
            }
            
            # Obtener año
            if 'publishedDate' in data:
                try:
                    book_info['edition_year'] = int(data['publishedDate'][:4])
                except:
                    pass
            
            # Obtener portada
            if 'imageLinks' in data and 'thumbnail' in data['imageLinks']:
                book_info['cover_url'] = data['imageLinks']['thumbnail'].replace('&edge=curl', '')
            
            return book_info
        except Exception as e:
            print(f"Error al parsear Google Books: {e}")
            return None


class ExternalBookSourcesAPI:
    """Búsqueda extra en fuentes públicas para completar datos faltantes"""

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    @staticmethod
    def get_book_by_isbn(isbn):
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        for _, source in ExternalBookSourcesAPI.get_sources():
            try:
                result = source(clean_isbn)
                if ExternalBookSourcesAPI._is_useful_result(result):
                    return result
            except Exception as e:
                print(f"Error en fuente externa {source.__name__}: {e}")
        return None

    @staticmethod
    def get_book_by_isbn_with_source(isbn):
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        for source_name, source in ExternalBookSourcesAPI.get_sources():
            try:
                result = source(clean_isbn)
                if ExternalBookSourcesAPI._is_useful_result(result):
                    return result, source_name
            except Exception as e:
                print(f"Error en fuente externa {source.__name__}: {e}")
        return None, None

    @staticmethod
    def get_sources():
        return (
            ('Casa del Libro', ExternalBookSourcesAPI._search_casa_del_libro),
            ('IberLibro', ExternalBookSourcesAPI._search_iberlibro),
        )

    @staticmethod
    def _is_useful_result(result):
        if not isinstance(result, dict):
            return False

        return bool(result.get('title') or result.get('author') or result.get('publisher'))

    @staticmethod
    def _search_casa_del_libro(isbn):
        url = f"https://www.casadellibro.com/busqueda-libros?text={isbn}"
        headers = {'User-Agent': ExternalBookSourcesAPI.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        return ExternalBookSourcesAPI._parse_bookpage(response.text)

    @staticmethod
    def _search_iberlibro(isbn):
        url = f"https://www.iberlibro.com/servlet/SearchResults?kn={isbn}"
        headers = {'User-Agent': ExternalBookSourcesAPI.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        return ExternalBookSourcesAPI._parse_bookpage(response.text)

    @staticmethod
    def _parse_bookpage(html):
        json_ld = ExternalBookSourcesAPI._extract_json_ld(html)
        if json_ld and isinstance(json_ld, dict) and json_ld.get('@type') == 'Book':
            return {
                'title': json_ld.get('name', ''),
                'author': ', '.join(
                    [author.get('name', '') for author in json_ld.get('author', [])]
                    if isinstance(json_ld.get('author'), list) else [json_ld.get('author', {})]
                ).strip(', '),
                'publisher': json_ld.get('publisher', {}).get('name', '') if isinstance(json_ld.get('publisher'), dict) else json_ld.get('publisher', ''),
                'edition_year': ExternalBookSourcesAPI._parse_year(json_ld.get('datePublished')),
                'format': 'Tapa blanda',
                'cover_url': None
            }
        return None

    @staticmethod
    def _extract_json_ld(html):
        import json
        import re
        matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I)
        for match in matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Book':
                            return item
                elif data.get('@type') == 'Book':
                    return data
            except Exception:
                continue
        return None

    @staticmethod
    def _parse_year(value):
        try:
            if isinstance(value, str):
                return int(value[:4])
        except Exception:
            pass
        return None
