import requests
import os
import mimetypes
from pathlib import Path
from requests.auth import HTTPBasicAuth


class WooCommerceAPI:
    """API client para WooCommerce REST API"""

    def __init__(self, site_url, consumer_key, consumer_secret, wp_username=None, wp_password=None):
        self.site_url = site_url.rstrip('/')
        self.consumer_key = consumer_key.strip()
        self.consumer_secret = consumer_secret.strip()

        # Auth WooCommerce (consumer key + secret)
        self.api_url = f"{self.site_url}/wp-json/wc/v3"
        self.auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)

        # Auth WordPress para subir imágenes (Application Password)
        self.wp_username = wp_username.strip() if wp_username else None
        self.wp_password = wp_password.strip() if wp_password else None

        if self.wp_username and self.wp_password:
            self.wp_auth = HTTPBasicAuth(self.wp_username, self.wp_password)
        else:
            self.wp_auth = None

        print("\n[DEBUG] WooCommerceAPI inicializado:")
        print("  URL:", self.site_url)
        print("  WP USER:", repr(self.wp_username))
        print("  WP PASS LEN:", len(self.wp_password) if self.wp_password else "None")
        print("  WC KEY LEN:", len(self.consumer_key))
        print("  WC SECRET LEN:", len(self.consumer_secret))

    # ---------------------------------------------------------
    # TEST CONNECTION
    # ---------------------------------------------------------
    def test_connection(self):
        print("\n[DEBUG] Probando conexión con WooCommerce...")
        try:
            response = requests.get(
                f"{self.api_url}/products",
                auth=self.auth,
                timeout=5,
                params={'per_page': 1}
            )
            print("[DEBUG] Código:", response.status_code)
            print("[DEBUG] Respuesta:", response.text[:300])
            return response.status_code == 200
        except Exception as e:
            print("[DEBUG] Error al conectar:", e)
            return False

    # ---------------------------------------------------------
    # FETCH BOOK EXCERPT (OpenLibrary)
    # ---------------------------------------------------------
    def fetch_book_excerpt(self, isbn):
        """Devuelve una sinopsis breve desde OpenLibrary si existe."""
        if not isbn:
            return None

        try:
            url = f"https://openlibrary.org/isbn/{isbn}.json"
            print("[DEBUG] Buscando sinopsis en OpenLibrary:", url)

            r = requests.get(url, timeout=5)

            if r.status_code != 200:
                print("[DEBUG] No hay datos en OpenLibrary")
                return None

            data = r.json()

            desc = data.get("description")

            # Puede venir como string o dict
            if isinstance(desc, dict):
                desc = desc.get("value")

            if desc:
                desc = desc.strip()
                if len(desc) > 500:
                    desc = desc[:500] + "..."
                print("[DEBUG] Sinopsis encontrada")
                return desc

            print("[DEBUG] No hay campo description")
            return None

        except Exception as e:
            print("[DEBUG] Error obteniendo sinopsis:", e)
            return None

    # ---------------------------------------------------------
    # CREATE PRODUCT
    # ---------------------------------------------------------
    def create_product(self, product_data):
        print(f"\n[DEBUG] Creando producto: {product_data.get('title')}")

        # Intentar obtener sinopsis automática si no viene ya
        if not product_data.get('short_description') and product_data.get('isbn'):
            print("[DEBUG] Intentando obtener sinopsis automática...")
            excerpt = self.fetch_book_excerpt(product_data.get('isbn'))
            if excerpt:
                product_data['short_description'] = excerpt
                print("[DEBUG] Sinopsis añadida al producto")

        try:
            payload = {
                'name': product_data.get('title', ''),
                'description': self._build_description(product_data),
                'regular_price': str(product_data.get('price', '0')),
                'manage_stock': True,
                'stock_quantity': product_data.get('stock', 1),
                'status': 'publish'
            }

            isbn = (product_data.get('isbn') or '').strip()
            if isbn:
                payload['sku'] = isbn

            if product_data.get('categories'):
                payload['categories'] = [{'id': int(cid)} for cid in product_data['categories']]

            if product_data.get('short_description'):
                payload['short_description'] = product_data['short_description']

            if any(product_data.get(dim) for dim in ('length', 'width', 'height')):
                payload['dimensions'] = {
                    'length': str(product_data.get('length', '') or ''),
                    'width': str(product_data.get('width', '') or ''),
                    'height': str(product_data.get('height', '') or '')
                }

            response = requests.post(
                f"{self.api_url}/products",
                json=payload,
                auth=self.auth,
                timeout=10
            )

            print("[DEBUG] Código creación producto:", response.status_code)
            print("[DEBUG] Respuesta:", response.text[:500])

            if response.status_code in [200, 201]:
                return response.json()

            print("[DEBUG] Error al crear producto:", response.text)
            return None

        except Exception as e:
            print("[DEBUG] Excepción al crear producto:", e)
            return None

    # ---------------------------------------------------------
    # UPLOAD MEDIA (IMAGEN)
    # ---------------------------------------------------------
    def upload_media(self, image_path):
        print("\n[DEBUG] Subiendo imagen a WordPress...")
        print("[DEBUG] Ruta:", image_path)

        if not self.wp_auth:
            print("[DEBUG] No hay credenciales WP para subir imágenes")
            return None

        if not os.path.exists(image_path):
            print("[DEBUG] ERROR: El archivo NO existe")
            return None

        size = os.path.getsize(image_path)
        print("[DEBUG] Tamaño archivo:", size)

        if size == 0:
            print("[DEBUG] ERROR: Archivo vacío")
            return None

        content_type, _ = mimetypes.guess_type(image_path)
        if not content_type:
            print("[DEBUG] MIME no detectado, forzando image/jpeg")
            content_type = "image/jpeg"

        print("[DEBUG] MIME:", content_type)

        file_name = os.path.basename(image_path)

        headers = {
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Content-Type': content_type
        }

        try:
            with open(image_path, 'rb') as img_file:
                response = requests.post(
                    f"{self.site_url}/wp-json/wp/v2/media",
                    headers=headers,
                    data=img_file,
                    auth=self.wp_auth,
                    timeout=20
                )

            print("[DEBUG] Código WP media:", response.status_code)
            print("[DEBUG] Respuesta WP media:", response.text[:500])

            if response.status_code in [200, 201]:
                media_json = response.json()
                print("[DEBUG] Imagen subida con ID:", media_json.get('id'))
                return media_json

            print("[DEBUG] ERROR al subir media:", response.text)
            return None

        except Exception as e:
            print("[DEBUG] Excepción al subir media:", e)
            return None

    # ---------------------------------------------------------
    # SET FEATURED IMAGE
    # ---------------------------------------------------------
    def set_product_featured_image(self, product_id, media_id):
        print(f"\n[DEBUG] Asignando imagen {media_id} al producto {product_id}")

        try:
            payload = {
                'images': [{'id': int(media_id), 'position': 0}]
            }

            response = requests.put(
                f"{self.api_url}/products/{product_id}",
                json=payload,
                auth=self.auth,
                timeout=10
            )

            print("[DEBUG] Código WC:", response.status_code)
            print("[DEBUG] Respuesta WC:", response.text[:500])

            if response.status_code == 200:
                print("[DEBUG] Imagen asignada correctamente")
                return response.json()

            print("[DEBUG] WooCommerce NO aceptó la imagen")
            return None

        except Exception as e:
            print("[DEBUG] Excepción al asignar imagen:", e)
            return None

    # ---------------------------------------------------------
    # DESCRIPTION BUILDER
    # ---------------------------------------------------------
    def _build_description(self, product_data):
        desc = f"<p><strong>Autor:</strong> {product_data.get('author', 'N/A')}</p>"
        desc += f"<p><strong>Editorial:</strong> {product_data.get('publisher', 'N/A')}</p>"
        desc += f"<p><strong>Formato:</strong> {product_data.get('format', 'N/A')}</p>"

        if product_data.get('edition_year'):
            desc += f"<p><strong>Año Edición:</strong> {product_data['edition_year']}</p>"

        if product_data.get('isbn'):
            desc += f"<p><strong>ISBN:</strong> {product_data['isbn']}</p>"

        return desc
