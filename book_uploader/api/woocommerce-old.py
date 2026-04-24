import requests
import os
from pathlib import Path
from requests.auth import HTTPBasicAuth


class WooCommerceAPI:
    """API client para WooCommerce REST API"""
    
    def __init__(self, site_url, consumer_key, consumer_secret, wp_username=None, wp_password=None):
        """
        Inicializa el cliente de WooCommerce
        
        Args:
            site_url: URL del sitio (ej: https://misitio.com)
            consumer_key: Consumer key de WooCommerce
            consumer_secret: Consumer secret de WooCommerce
            wp_username: Usuario admin de WordPress (opcional)
            wp_password: Contraseña admin de WordPress (opcional)
        """
        self.site_url = site_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.site_url}/wp-json/wc/v3"
        self.auth = HTTPBasicAuth(consumer_key, consumer_secret)
        
        # Auth para WordPress si se proporciona
        self.wp_auth = None
        if wp_username and wp_password:
            self.wp_auth = HTTPBasicAuth(wp_username, wp_password)
    
    def test_connection(self):
        """Prueba la conexión con WooCommerce"""
        try:
            response = requests.get(
                f"{self.api_url}/products",
                auth=self.auth,
                timeout=5,
                params={'per_page': 1}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False
    
    def create_product(self, product_data):
        """
        Crea un nuevo producto en WooCommerce
        
        Args:
            product_data: Diccionario con datos del producto
            
        Returns:
            Respuesta de la API o None en caso de error
        """
        try:
            # Preparar datos del producto
            payload = {
                'name': product_data.get('title', ''),
                'description': self._build_description(product_data),
                'regular_price': str(product_data.get('price', '0')),
                'manage_stock': True,
                'stock_quantity': product_data.get('stock', 1),
                'status': 'publish'
            }
            
            # Agregar categorías si existen
            if product_data.get('categories'):
                payload['categories'] = [
                    {'id': int(cat_id)}
                    for cat_id in product_data['categories']
                    if cat_id
                ]

            # Agregar breve descripción / excerpt
            if product_data.get('short_description'):
                payload['short_description'] = product_data['short_description']

            # Agregar dimensiones si se especifican
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
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error al crear producto: {response.status_code}")
                print(response.text)
                return None
        
        except Exception as e:
            print(f"Excepción al crear producto: {e}")
            return None
    
    def upload_media(self, image_path):
        """Sube una imagen al endpoint WP Media y devuelve el objeto media."""
        if not self.wp_auth:
            print("Error: Se requieren credenciales de administrador de WordPress para subir imágenes")
            return None

        try:
            if not os.path.exists(image_path):
                return None

            file_name = os.path.basename(image_path)
            import mimetypes
            content_type, _ = mimetypes.guess_type(image_path)
            headers = {
                'Content-Disposition': f'attachment; filename="{file_name}"',
            }
            if content_type:
                headers['Content-Type'] = content_type

            with open(image_path, 'rb') as img_file:
                response = requests.post(
                    f"{self.site_url}/wp-json/wp/v2/media",
                    headers=headers,
                    data=img_file,
                    auth=self.wp_auth,
                    timeout=20
                )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error al subir media: {response.status_code} {response.text}")
                return None
        except Exception as e:
            print(f"Excepción al subir media: {e}")
            return None

    def set_product_featured_image(self, product_id, media_id):
        """Actualiza el producto para establecer la imagen destacada."""
        try:
            response = requests.put(
                f"{self.api_url}/products/{product_id}",
                json={
                    'featured_media': int(media_id),
                    'images': [{'id': int(media_id), 'position': 0}]
                },
                auth=self.auth,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            print(f"Error al establecer imagen destacada: {response.status_code} {response.text}")
            return None
        except Exception as e:
            print(f"Excepción al establecer imagen destacada: {e}")
            return None

    def _build_description(self, product_data):
        """Construye la descripción del producto con HTML"""
        desc = f"<p><strong>Autor:</strong> {product_data.get('author', 'N/A')}</p>"
        desc += f"<p><strong>Editorial:</strong> {product_data.get('publisher', 'N/A')}</p>"
        desc += f"<p><strong>Formato:</strong> {product_data.get('format', 'N/A')}</p>"
        
        if product_data.get('edition_year'):
            desc += f"<p><strong>Año Edición:</strong> {product_data['edition_year']}</p>"
        
        if product_data.get('isbn'):
            desc += f"<p><strong>ISBN:</strong> {product_data['isbn']}</p>"
        
        return desc
    
    def get_categories(self):
        """Obtiene las categorías disponibles en WooCommerce"""
        try:
            response = requests.get(
                f"{self.api_url}/products/categories",
                auth=self.auth,
                timeout=5,
                params={'per_page': 100}
            )
            
            if response.status_code == 200:
                return response.json()
            return []
        
        except Exception as e:
            print(f"Error al obtener categorías: {e}")
            return []

    def get_brands(self):
        """Obtiene marcas desde el plugin de endpoints personalizado"""
        try:
            response = requests.get(
                f"{self.site_url}/wp-json/book-uploader/v1/brands",
                auth=self.auth,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error al obtener marcas: {e}")
            return []

    def create_brand(self, brand_name):
        """Crea una marca/product_brand en WordPress a través del plugin"""
        try:
            response = requests.post(
                f"{self.site_url}/wp-json/book-uploader/v1/brands",
                auth=self.auth,
                json={'name': brand_name},
                timeout=10
            )
            if response.status_code in [200, 201]:
                return response.json()
            print(f"Error al crear marca: {response.status_code} {response.text}")
            return None
        except Exception as e:
            print(f"Error al crear marca: {e}")
            return None

    def assign_brand_to_product(self, product_id, brand_id):
        """Asocia una marca product_brand a un producto"""
        try:
            response = requests.post(
                f"{self.site_url}/wp-json/book-uploader/v1/products/{product_id}/brand",
                auth=self.auth,
                json={'brand_id': int(brand_id)},
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error al asignar marca: {e}")
            return False

    def get_or_create_brand(self, brand_name):
        """Busca una marca por nombre o la crea si no existe"""
        brands = self.get_brands()
        for brand in brands:
            if brand.get('name', '').lower() == brand_name.lower():
                return brand.get('id')

        created = self.create_brand(brand_name)
        if created:
            return created.get('id')
        return None

    def update_product(self, product_id, update_data):
        """
        Actualiza un producto existente en WooCommerce
        
        Args:
            product_id: ID del producto
            update_data: Diccionario con datos a actualizar
            
        Returns:
            Respuesta de la API o None en caso de error
        """
        try:
            response = requests.put(
                f"{self.api_url}/products/{product_id}",
                json=update_data,
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error al actualizar producto: {response.status_code}")
                print(response.text)
                return None
        
        except Exception as e:
            print(f"Excepción al actualizar producto: {e}")
            return None


class BatchProductUploader:
    """Utilidad para subir múltiples productos"""
    
    def __init__(self, site_url, consumer_key, consumer_secret):
        self.api = WooCommerceAPI(site_url, consumer_key, consumer_secret)
        self.results = []
    
    def upload_product(self, product_data):
        """Sube un producto individual"""
        try:
            # Crear producto
            product_response = self.api.create_product(product_data)
            
            if not product_response:
                return {
                    'success': False,
                    'error': 'No se pudo crear el producto'
                }
            
            product_id = product_response.get('id')
            
            # Subir imagen si existe
            image_result = None
            if product_data.get('cover_image_path') and os.path.exists(product_data['cover_image_path']):
                image_result = self.api.upload_product_image(product_id, product_data['cover_image_path'])
            
            return {
                'success': True,
                'product_id': product_id,
                'product_name': product_response.get('name'),
                'image_uploaded': image_result is not None
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
