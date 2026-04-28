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

        self.last_error = None

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
    def _extract_error_message(self, response):
        """Extrae un mensaje de error útil desde la respuesta de WooCommerce."""
        try:
            body = response.json()
            if isinstance(body, dict):
                return body.get('message') or body.get('code') or response.text
        except Exception:
            pass
        return response.text

    def _is_retryable_sku_error(self, response):
        """Detecta si el error corresponde a SKU inválido o duplicado."""
        if response.status_code not in (400, 409, 422):
            return False

        text = ""
        code = ""
        message = ""
        try:
            body = response.json()
            if isinstance(body, dict):
                code = str(body.get('code', '')).lower()
                message = str(body.get('message', '')).lower()
            text = response.text.lower()
        except Exception:
            text = response.text.lower()

        combined = f"{code} {message} {text}"
        has_sku = 'sku' in combined
        has_invalid_or_duplicate = any(
            token in combined
            for token in ('invalid', 'duplicate', 'duplicado', 'already exists', 'ya existe', 'used')
        )
        return has_sku and has_invalid_or_duplicate

    def _build_sku_candidates(self, base_sku, max_sku_retries=9):
        """Genera SKUs candidatos: base, base1, base2, ..."""
        base = (base_sku or '').strip()
        if not base:
            return [None]

        candidates = [base]
        for i in range(1, max_sku_retries + 1):
            candidates.append(f"{base}{i}")
        return candidates

    def create_product_with_sku_retry(self, payload, max_sku_retries=9):
        """
        Crea un producto y reintenta con SKU incremental si WooCommerce
        responde que el SKU es inválido o duplicado.
        """
        self.last_error = None
        sku_candidates = self._build_sku_candidates(payload.get('sku'), max_sku_retries=max_sku_retries)

        for attempt, candidate_sku in enumerate(sku_candidates, start=1):
            payload_to_send = dict(payload)
            if candidate_sku:
                payload_to_send['sku'] = candidate_sku
            else:
                payload_to_send.pop('sku', None)

            response = requests.post(
                f"{self.api_url}/products",
                json=payload_to_send,
                auth=self.auth,
                timeout=10
            )

            print("[DEBUG] Código creación producto:", response.status_code)
            print("[DEBUG] Respuesta:", response.text[:500])

            if response.status_code in [200, 201]:
                return response.json()

            retryable = self._is_retryable_sku_error(response)
            has_more_candidates = attempt < len(sku_candidates)

            if retryable and has_more_candidates:
                next_candidate = sku_candidates[attempt]
                print(
                    f"[DEBUG] SKU inválido/duplicado ({candidate_sku}). "
                    f"Reintentando con SKU {next_candidate}"
                )
                continue

            self.last_error = self._extract_error_message(response)
            print("[DEBUG] Error al crear producto:", self.last_error)
            return None

        self.last_error = "No se pudo crear el producto con los reintentos de SKU configurados"
        return None

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

            return self.create_product_with_sku_retry(payload)

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

    def get_categories(self):
        """Obtiene las categorías disponibles en WooCommerce."""
        try:
            response = requests.get(
                f"{self.api_url}/products/categories",
                auth=self.auth,
                timeout=10,
                params={'per_page': 100}
            )

            if response.status_code == 200:
                return response.json()

            self.last_error = self._extract_error_message(response)
            print("[DEBUG] Error al obtener categorías:", self.last_error)
            return []

        except Exception as e:
            self.last_error = str(e)
            print("Error al obtener categorías:", e)
            return []

    def get_brands(self):
        """Obtiene marcas desde el endpoint personalizado del plugin."""
        try:
            response = requests.get(
                f"{self.site_url}/wp-json/book-uploader/v1/brands",
                auth=self.auth,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()

            self.last_error = self._extract_error_message(response)
            print("[DEBUG] Error al obtener marcas:", self.last_error)
            return []
        except Exception as e:
            self.last_error = str(e)
            print("Error al obtener marcas:", e)
            return []

    def create_brand(self, brand_name):
        """Crea una marca/product_brand en WordPress a través del plugin."""
        try:
            response = requests.post(
                f"{self.site_url}/wp-json/book-uploader/v1/brands",
                auth=self.auth,
                json={'name': brand_name},
                timeout=10
            )
            if response.status_code in [200, 201]:
                return response.json()

            self.last_error = self._extract_error_message(response)
            print("[DEBUG] Error al crear marca:", self.last_error)
            return None
        except Exception as e:
            self.last_error = str(e)
            print("Error al crear marca:", e)
            return None

    def assign_brand_to_product(self, product_id, brand_id):
        """Asocia una marca product_brand a un producto."""
        try:
            response = requests.post(
                f"{self.site_url}/wp-json/book-uploader/v1/products/{product_id}/brand",
                auth=self.auth,
                json={'brand_id': int(brand_id)},
                timeout=10
            )
            if response.status_code in [200, 201]:
                return True

            self.last_error = self._extract_error_message(response)
            print("[DEBUG] Error al asignar marca:", self.last_error)
            return False
        except Exception as e:
            self.last_error = str(e)
            print("Error al asignar marca:", e)
            return False

    def get_or_create_brand(self, brand_name):
        """Busca una marca por nombre o la crea si no existe."""
        brands = self.get_brands()
        for brand in brands:
            if brand.get('name', '').lower() == brand_name.lower():
                return brand.get('id')

        created = self.create_brand(brand_name)
        if created:
            return created.get('id')
        return None
