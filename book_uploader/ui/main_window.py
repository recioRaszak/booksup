from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QTabWidget,
    QScrollArea, QMessageBox, QProgressDialog, QTableWidget, QTableWidgetItem,
    QFileDialog, QHeaderView, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtWidgets import QFormLayout

import sys
import os
from pathlib import Path
import requests

from book_uploader.database.db import Database
from book_uploader.api.openbooks import OpenBooksAPI, ExternalBookSourcesAPI
from book_uploader.api.google_books import GoogleBooksAPI
from book_uploader.api.woocommerce import WooCommerceAPI
from book_uploader.utils.helpers import (
    get_cover_path, validate_isbn, format_price, truncate_text, get_covers_dir
)
from book_uploader.ui.dialogs import SiteSettingsDialog


class CategoriesLoadThread(QThread):
    """Thread para cargar categorías sin bloquear UI"""
    
    categories_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, site):
        super().__init__()
        self.site = site
    
    def run(self):
        try:
            from book_uploader.api.woocommerce import WooCommerceAPI
            api = WooCommerceAPI(
                self.site['url'],
                self.site['consumer_key'],
                self.site['consumer_secret'],
                self.site.get('wp_username'),
                self.site.get('wp_password')
            )
            categories = api.get_categories()
            if categories:
                # Extraer id y nombre de categorías
                categories_info = [
                    {'id': cat.get('id'), 'name': cat.get('name', '')}
                    for cat in categories
                    if cat.get('id')
                ]
                self.categories_loaded.emit(categories_info)
            else:
                self.error_occurred.emit("No se pudieron cargar las categorías")
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar categorías: {str(e)}")


class BrandLoadThread(QThread):
    """Thread para cargar marcas desde el plugin de WordPress"""
    
    brands_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, site):
        super().__init__()
        self.site = site
    
    def run(self):
        try:
            from book_uploader.api.woocommerce import WooCommerceAPI
            api = WooCommerceAPI(
                self.site['url'],
                self.site['consumer_key'],
                self.site['consumer_secret'],
                self.site.get('wp_username'),
                self.site.get('wp_password')
            )
            brands = api.get_brands()
            if brands:
                self.brands_loaded.emit(brands)
            else:
                self.error_occurred.emit("No se pudieron cargar las marcas")
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar marcas: {str(e)}")


class BookFetchThread(QThread):
    """Thread para buscar información del libro sin bloquear UI"""
    
    book_data_fetched = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, isbn):
        super().__init__()
        self.isbn = isbn
    
    def run(self):
        try:
            # Intentar primero con OpenLibrary
            book_info = OpenBooksAPI.get_book_by_isbn(self.isbn)
            
            if book_info:
                if not book_info.get('publisher') or not book_info.get('cover_url'):
                    fallback = ExternalBookSourcesAPI.get_book_by_isbn(self.isbn)
                    if fallback:
                        for key, value in fallback.items():
                            if value and not book_info.get(key):
                                book_info[key] = value
                self.book_data_fetched.emit(book_info)
                return

            # Intentar con Google Books
            book_info = GoogleBooksAPI.get_book_by_isbn(self.isbn)
            if book_info and (not book_info.get('publisher') or not book_info.get('cover_url')):
                fallback = ExternalBookSourcesAPI.get_book_by_isbn(self.isbn)
                if fallback:
                    for key, value in fallback.items():
                        if value and not book_info.get(key):
                            book_info[key] = value

            if book_info:
                self.book_data_fetched.emit(book_info)
            else:
                self.error_occurred.emit("No se encontró información para este ISBN")
        except Exception as e:
            self.error_occurred.emit(f"Error al buscar: {str(e)}")


class CoverDownloadThread(QThread):
    """Thread para descargar la portada sin bloquear UI"""
    
    cover_downloaded = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, cover_url, output_path):
        super().__init__()
        self.cover_url = cover_url
        self.output_path = output_path
    
    def run(self):
        try:
            result = OpenBooksAPI.download_cover(self.cover_url, self.output_path)
            if result:
                self.cover_downloaded.emit(result)
            else:
                # Intentar con Google Books si hay ISBN
                # Pero cover_url es de OpenLibrary, si falla, no tenemos URL de Google
                # Para simplificar, por ahora solo OpenLibrary
                self.error_occurred.emit("No se pudo descargar la portada")
        except Exception as e:
            self.error_occurred.emit(f"Error al descargar: {str(e)}")


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.current_site = None
        self.cover_url = None
        self.cover_path = None
        self.book_fetch_thread = None
        self.cover_download_thread = None
        
        self.setWindowTitle("📚 Book Uploader - WooCommerce")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(self._get_stylesheet())
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Encabezado con selector de sitio
        header_layout = QHBoxLayout()
        
        site_label = QLabel("Sitio WooCommerce:")
        site_label.setFont(QFont("Arial", 11, QFont.Bold))
        header_layout.addWidget(site_label)
        
        self.site_combo = QComboBox()
        self.site_combo.currentIndexChanged.connect(self.on_site_changed)
        header_layout.addWidget(self.site_combo)
        
        settings_btn = QPushButton("⚙️ Configurar Sitios")
        settings_btn.clicked.connect(self.open_site_settings)
        header_layout.addWidget(settings_btn)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab 1: Agregar libro
        self.add_book_tab = self.create_add_book_tab()
        tabs.addTab(self.add_book_tab, "➕ Agregar Libro")
        
        # Tab 2: Historial
        self.history_tab = self.create_history_tab()
        tabs.addTab(self.history_tab, "📋 Historial")
        
        main_layout.addWidget(tabs)
        self.statusBar().showMessage("Listo")
        
        self.refresh_sites()
    
    def create_add_book_tab(self):
        """Crea la pestaña de agregar libro"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area para mejor manejo de espacio
        self.add_book_scroll = QScrollArea()
        self.add_book_scroll.setWidgetResizable(True)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(10)
        
        # EAN/ISBN (Campo crítico)
        ean_label = QLabel("📱 EAN/ISBN:")
        ean_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        ean_layout = QHBoxLayout()
        self.ean_input = QLineEdit()
        self.ean_input.setPlaceholderText("Escanea el código de barras aquí...")
        self.ean_input.setStyleSheet("QLineEdit { font-size: 14px; padding: 8px; }")
        self.ean_input.returnPressed.connect(self.fetch_book_info)
        
        fetch_btn = QPushButton("🔍 Buscar")
        fetch_btn.clicked.connect(self.fetch_book_info)
        
        ean_layout.addWidget(self.ean_input)
        ean_layout.addWidget(fetch_btn)
        
        form_layout.addRow(ean_label, ean_layout)
        
        # Título
        title_label = QLabel("Título:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título del libro")
        form_layout.addRow(title_label, self.title_input)
        
        # Autor
        author_label = QLabel("Autor:")
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Nombre del autor")
        form_layout.addRow(author_label, self.author_input)
        
        # Editorial
        publisher_label = QLabel("Editorial:")
        self.publisher_input = QLineEdit()
        self.publisher_input.setPlaceholderText("Nombre de la editorial")
        form_layout.addRow(publisher_label, self.publisher_input)

        # Marca / Product Brand
        brand_label = QLabel("Marca / Editorial (product_brand):")
        self.brand_input = QComboBox()
        self.brand_input.setEditable(True)
        self.brand_input.setInsertPolicy(QComboBox.NoInsert)
        self.brand_input.setPlaceholderText("Selecciona o escribe la editorial")
        form_layout.addRow(brand_label, self.brand_input)
        
        # Formato
        format_label = QLabel("Formato:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(OpenBooksAPI.get_book_formats())
        form_layout.addRow(format_label, self.format_combo)

        # Categorías
        categories_label = QLabel("Categorías:")
        self.categories_list = QListWidget()
        self.categories_list.setMaximumHeight(100)
        self.categories_list.setEnabled(False)
        # Activar multiselección con checkboxes
        form_layout.addRow(categories_label, self.categories_list)

        # Extracto
        excerpt_label = QLabel("Extracto:")
        self.excerpt_input = QTextEdit()
        self.excerpt_input.setPlaceholderText("Texto breve para la descripción corta del producto")
        self.excerpt_input.setMaximumHeight(100)
        form_layout.addRow(excerpt_label, self.excerpt_input)

        # Dimensiones
        dimensions_label = QLabel("Dimensiones (cm):")
        dimensions_layout = QHBoxLayout()
        self.length_input = QDoubleSpinBox()
        self.length_input.setMinimum(0.0)
        self.length_input.setMaximum(999.9)
        self.length_input.setDecimals(1)
        self.length_input.setSuffix(" L")
        self.length_input.setStyleSheet("max-width: 100px;")
        self.width_input = QDoubleSpinBox()
        self.width_input.setMinimum(0.0)
        self.width_input.setMaximum(999.9)
        self.width_input.setDecimals(1)
        self.width_input.setSuffix(" W")
        self.width_input.setStyleSheet("max-width: 100px;")
        self.height_input = QDoubleSpinBox()
        self.height_input.setMinimum(0.0)
        self.height_input.setMaximum(999.9)
        self.height_input.setDecimals(1)
        self.height_input.setSuffix(" H")
        self.height_input.setStyleSheet("max-width: 100px;")
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setMinimum(0.0)
        self.weight_input.setMaximum(9999.9)
        self.weight_input.setDecimals(1)
        self.weight_input.setSuffix(" kg")
        self.weight_input.setStyleSheet("max-width: 100px;")
        dimensions_layout.addWidget(self.length_input)
        dimensions_layout.addWidget(self.width_input)
        dimensions_layout.addWidget(self.height_input)
        dimensions_layout.addWidget(self.weight_input)
        dimensions_layout.addStretch()
        form_layout.addRow(dimensions_label, dimensions_layout)
        
        # Año de edición
        year_label = QLabel("Año de Edición:")
        year_layout = QHBoxLayout()
        self.year_spin = QSpinBox()
        self.year_spin.setMinimum(1900)
        self.year_spin.setMaximum(2100)
        self.year_spin.setValue(2024)
        self.year_spin.setStyleSheet("max-width: 100px;")
        clear_year_btn = QPushButton("Limpiar")
        clear_year_btn.clicked.connect(lambda: self.year_spin.setValue(2024))
        year_layout.addWidget(self.year_spin)
        year_layout.addWidget(clear_year_btn)
        year_layout.addStretch()
        form_layout.addRow(year_label, year_layout)
        
        # Precio
        price_label = QLabel("Precio (€):")
        price_layout = QHBoxLayout()
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.0)
        self.price_input.setMaximum(10000.0)
        self.price_input.setValue(4.0)
        self.price_input.setDecimals(2)
        self.price_input.setStyleSheet("max-width: 150px;")
        price_layout.addWidget(self.price_input)
        price_layout.addStretch()
        form_layout.addRow(price_label, price_layout)
        
        # Stock
        stock_label = QLabel("Stock:")
        stock_layout = QHBoxLayout()
        self.stock_spin = QSpinBox()
        self.stock_spin.setMinimum(1)
        self.stock_spin.setValue(1)
        self.stock_spin.setStyleSheet("max-width: 100px;")
        stock_layout.addWidget(self.stock_spin)
        stock_layout.addStretch()
        form_layout.addRow(stock_label, stock_layout)
        
        # Portada
        cover_label = QLabel("Portada:")
        cover_layout = QVBoxLayout()
        
        self.cover_preview = QLabel()
        self.cover_preview.setMinimumHeight(150)
        self.cover_preview.setStyleSheet("border: 2px solid #ccc; background-color: #f5f5f5;")
        self.cover_preview.setAlignment(Qt.AlignCenter)
        
        self.cover_label_text = QLabel("Sin portada seleccionada")
        self.cover_label_text.setAlignment(Qt.AlignCenter)
        self.cover_preview.setText("Sin imagen")
        
        cover_button_layout = QHBoxLayout()
        self.download_cover_btn = QPushButton("⬇️ Descargar autom.")
        self.download_cover_btn.clicked.connect(self.download_cover)
        self.download_cover_btn.setEnabled(False)
        
        self.upload_cover_btn = QPushButton("📁 Seleccionar archivo")
        self.upload_cover_btn.clicked.connect(self.select_cover_file)
        
        cover_button_layout.addWidget(self.download_cover_btn)
        cover_button_layout.addWidget(self.upload_cover_btn)
        cover_button_layout.addStretch()
        
        cover_layout.addWidget(self.cover_preview)
        cover_layout.addLayout(cover_button_layout)
        
        form_layout.addRow(cover_label, cover_layout)
        
        self.add_book_scroll.setWidget(form_widget)
        layout.addWidget(self.add_book_scroll)
        
        # Botones de acción
        action_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🔄 Limpiar formulario")
        clear_btn.clicked.connect(self.clear_form)
        action_layout.addWidget(clear_btn)
        
        action_layout.addStretch()
        
        upload_btn = QPushButton("✅ Subir a WooCommerce")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        upload_btn.setMinimumHeight(40)
        upload_btn.clicked.connect(self.upload_product)
        action_layout.addWidget(upload_btn)
        
        layout.addLayout(action_layout)
        
        return widget
    
    def create_history_tab(self):
        """Crea la pestaña de historial"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Título", "Autor", "Precio", "Fecha", "Estado"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.history_table)
        
        return widget
    
    def refresh_sites(self):
        """Recarga la lista de sitios"""
        self.site_combo.blockSignals(True)
        self.site_combo.clear()
        
        sites = self.db.get_all_sites()
        
        if sites:
            for site in sites:
                self.site_combo.addItem(site['name'], site['id'])
            self.current_site = sites[0]
        else:
            self.site_combo.addItem("[ Sin sitios configurados ]", None)
            self.current_site = None
        
        self.site_combo.blockSignals(False)
        self.on_site_changed()
    
    def on_site_changed(self):
        """Se ejecuta cuando cambia el sitio seleccionado"""
        site_id = self.site_combo.currentData()
        if site_id:
            self.current_site = self.db.get_site(site_id)
            self.refresh_history()
            # Cargar categorías y marcas del sitio
            self.load_categories()
            self.load_brands()
        else:
            self.current_site = None
    
    def load_categories(self):
        """Carga las categorías disponibles del sitio"""
        if not self.current_site:
            return
        
        self.categories_list.clear()
        self.categories_list.setEnabled(False)
        self.set_status("Cargando categorías del sitio...")
        self.categories_load_thread = CategoriesLoadThread(self.current_site)
        self.categories_load_thread.categories_loaded.connect(self.on_categories_loaded)
        self.categories_load_thread.error_occurred.connect(self.on_categories_error)
        self.categories_load_thread.start()

    def load_brands(self):
        """Carga las marcas disponibles del sitio"""
        if not self.current_site:
            return
        
        self.brand_input.clear()
        self.brand_input.setEnabled(False)
        self.set_status("Cargando marcas del sitio...")
        self.brand_load_thread = BrandLoadThread(self.current_site)
        self.brand_load_thread.brands_loaded.connect(self.on_brands_loaded)
        self.brand_load_thread.error_occurred.connect(self.on_brands_error)
        self.brand_load_thread.start()

    def on_brands_loaded(self, brands):
        """Se ejecuta cuando se cargan las marcas"""
        self.brand_input.clear()
        self.brand_input.setEnabled(True)
        for brand in brands:
            self.brand_input.addItem(brand.get('name', ''), brand.get('id'))
        self.set_status("Marcas cargadas")

    def on_brands_error(self, error):
        """Se ejecuta si hay error al cargar marcas"""
        self.brand_input.setEnabled(True)
        self.set_status(f"Error cargando marcas: {error}")
    
    def on_categories_loaded(self, categories):
        """Se ejecuta cuando se cargan las categorías"""
        self.categories_list.clear()
        for category in categories:
            item = QListWidgetItem(category['name'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, category['id'])
            self.categories_list.addItem(item)
        self.categories_list.setEnabled(True)
        self.set_status("Categorías cargadas")
    
    def on_categories_error(self, error):
        """Se ejecuta si hay error al cargar categorías"""
        self.categories_list.setEnabled(True)
        self.set_status(f"Error cargando categorías: {error}")
    
    def refresh_history(self):
        """Refresca el historial de productos"""
        if not self.current_site:
            return
        
        products = self.db.get_products_by_site(self.current_site['id'])
        
        self.history_table.setRowCount(0)
        
        for product in products:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            self.history_table.setItem(row, 0, QTableWidgetItem(product['title']))
            self.history_table.setItem(row, 1, QTableWidgetItem(product['author'] or 'N/A'))
            self.history_table.setItem(row, 2, QTableWidgetItem(f"€{product['price']}"))
            self.history_table.setItem(row, 3, QTableWidgetItem(product['created_at'][:10]))
            
            status = "✅ Subido" if product['woocommerce_id'] else "⏳ Pendiente"
            self.history_table.setItem(row, 4, QTableWidgetItem(status))
    
    def fetch_book_info(self):
        """Busca información del libro por ISBN/EAN"""
        ean = self.ean_input.text().strip()
        
        if not ean:
            QMessageBox.warning(self, "Error", "Por favor ingresa un EAN/ISBN")
            return
        
        if not validate_isbn(ean):
            QMessageBox.warning(self, "Error", "Formato de ISBN inválido")
            return
        
        # Mostrar que se está buscando
        self.fetch_btn_status = True
        
        # Crear y ejecutar thread
        self.book_fetch_thread = BookFetchThread(ean)
        self.book_fetch_thread.book_data_fetched.connect(self.on_book_data_fetched)
        self.book_fetch_thread.error_occurred.connect(self.on_fetch_error)
        self.set_status("Buscando datos del libro...")
        self.book_fetch_thread.start()
    
    def on_book_data_fetched(self, book_info):
        """Se ejecuta cuando se obtiene la información del libro"""
        self.title_input.setText(book_info.get('title', ''))
        self.author_input.setText(book_info.get('author', ''))
        self.publisher_input.setText(book_info.get('publisher', ''))
        self.format_combo.setCurrentText(book_info.get('format', 'Tapa blanda'))
        
        if book_info.get('edition_year'):
            self.year_spin.setValue(book_info['edition_year'])

        # Limpiar portada anterior al cargar info nueva
        self.cover_path = None
        self.cover_preview.setPixmap(QPixmap())
        self.cover_preview.setText("Sin imagen")
        self.cover_url = None
        
        # Descargar portada automáticamente si está disponible
        if book_info.get('cover_url'):
            self.cover_url = book_info['cover_url']
            self.download_cover_btn.setEnabled(True)
            self.set_status("Datos cargados. Descargando portada automática...")
            self.download_cover()
        else:
            self.download_cover_btn.setEnabled(False)
            self.set_status("Datos cargados. Selecciona una portada manualmente.")
    
    def on_fetch_error(self, error):
        """Se ejecuta en caso de error al buscar"""
        self.set_status(f"Error al buscar libro: {error}")
        QMessageBox.warning(self, "Error", error)
    
    def download_cover(self):
        """Descarga la portada del libro"""
        if not self.cover_url:
            self.set_status("No hay URL de portada disponible")
            QMessageBox.warning(self, "Error", "No hay URL de portada disponible")
            return
        
        ean = self.ean_input.text().strip()
        output_path = str(get_cover_path(ean))
        self.set_status("Descargando portada...")
        self.cover_download_thread = CoverDownloadThread(self.cover_url, output_path)
        self.cover_download_thread.cover_downloaded.connect(self.on_cover_downloaded)
        self.cover_download_thread.error_occurred.connect(self.on_download_error)
        self.cover_download_thread.start()
    
    def on_cover_downloaded(self, path):
        """Se ejecuta cuando se descarga la portada"""
        self.cover_path = path
        self.display_cover(path)
        self.set_status("Portada descargada correctamente")
    
    def on_download_error(self, error):
        """Se ejecuta en caso de error al descargar"""
        self.set_status(f"Error al descargar portada: {error}")
        QMessageBox.warning(self, "Error", error)
    
    def select_cover_file(self):
        """Permite seleccionar un archivo de portada"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar portada", "", "Imágenes (*.jpg *.jpeg *.png)"
        )
        
        if file_path:
            self.cover_path = file_path
            self.display_cover(file_path)
    
    def display_cover(self, path):
        """Muestra la portada en la UI"""
        try:
            pixmap = QPixmap(path)
            scaled_pixmap = pixmap.scaledToHeight(150, Qt.SmoothTransformation)
            self.cover_preview.setPixmap(scaled_pixmap)
        except:
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen")
    
    def clear_form(self):
        """Limpia todos los campos del formulario"""
        self.ean_input.clear()
        self.title_input.clear()
        self.author_input.clear()
        self.publisher_input.clear()
        self.format_combo.setCurrentIndex(0)
        # Desmarcar todas las categorías
        for i in range(self.categories_list.count()):
            self.categories_list.item(i).setCheckState(Qt.Unchecked)
        self.length_input.setValue(0.0)
        self.width_input.setValue(0.0)
        self.height_input.setValue(0.0)
        self.weight_input.setValue(0.0)
        self.year_spin.setValue(2024)
        self.price_input.setValue(4.0)
        self.stock_spin.setValue(1)
        self.cover_path = None
        self.cover_url = None
        self.cover_preview.setText("Sin imagen")
        self.download_cover_btn.setEnabled(False)
        self.ean_input.setFocus()

    def clear_book_fields(self):
        """Limpia solo los campos del libro que cambian con cada ISBN"""
        self.ean_input.clear()
        self.title_input.clear()
        self.author_input.clear()
        self.publisher_input.clear()
        self.year_spin.setValue(2024)
        self.excerpt_input.clear()
        self.cover_path = None
        self.cover_url = None
        self.cover_preview.setPixmap(QPixmap())
        self.cover_preview.setText("Sin imagen")
        self.download_cover_btn.setEnabled(False)
        # Mantener dimensiones, precio y categorías para el próximo producto.
        # Tras la subida exitosa, volver al inicio del formulario y enfocar ISBN.
        if hasattr(self, 'add_book_scroll') and self.add_book_scroll:
            self.add_book_scroll.verticalScrollBar().setValue(0)
        QTimer.singleShot(0, lambda: self.ean_input.setFocus(Qt.OtherFocusReason))
    
    def upload_product(self):
        """Sube el producto a WooCommerce"""
        if not self.current_site:
            QMessageBox.warning(self, "Error", "Por favor selecciona un sitio primero")
            return
        
        # Validar campos
        if not self.ean_input.text().strip():
            QMessageBox.warning(self, "Error", "El EAN/ISBN es obligatorio")
            return
        
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Error", "El título es obligatorio")
            return
        
        # Preparar datos del producto
        product_data = {
            'title': f"{self.title_input.text()} - {self.author_input.text()} - {self.publisher_input.text()}",
            'author': self.author_input.text(),
            'publisher': self.publisher_input.text(),
            'brand_name': self._get_selected_brand_name(),
            'brand_id': self._get_selected_brand_id(),
            'format': self.format_combo.currentText(),
            'edition_year': self.year_spin.value() if self.year_spin.value() > 1900 else None,
            'price': self.price_input.value(),
            'stock': self.stock_spin.value(),
            'isbn': self.ean_input.text().strip(),
            'cover_image_path': self.cover_path,
            'categories': self._get_selected_categories(),
            'short_description': self.excerpt_input.toPlainText().strip() or self._build_short_description(),
            'length': self.length_input.value() or None,
            'width': self.width_input.value() or None,
            'height': self.height_input.value() or None,
            'weight': self.weight_input.value() or None
        }
        
        # Crear thread de subida
        upload_thread = ProductUploadThread(self.current_site, product_data)
        upload_thread.upload_complete.connect(self.on_upload_complete)
        upload_thread.upload_error.connect(self.on_upload_error)
        
        # Crear diálogo de progreso sin modal para poder cerrar
        progress = ProgressDialog(self)
        progress.setModal(False)
        progress.show()
        
        upload_thread.start()
        self.upload_thread = upload_thread
        self.progress_dialog = progress
        self.set_status("Subiendo producto...")
    
    def on_upload_complete(self, result):
        """Se ejecuta cuando la subida es completa"""
        if self.progress_dialog:
            self.progress_dialog.accept()  # Cerrar correctamente el QMessageBox
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
        
        if result['success']:
            # Guardar en base de datos
            self.db.save_product(
                self.current_site['id'],
                self.ean_input.text(),
                self.title_input.text(),
                self.author_input.text(),
                self.publisher_input.text(),
                self.format_combo.currentText(),
                self.year_spin.value() if self.year_spin.value() > 1900 else None,
                self.price_input.value(),
                self.cover_path,
                result.get('product_id')
            )
            
            QMessageBox.information(self, "Éxito", 
                f"Producto '{result['product_name']}' subido correctamente a WooCommerce")
            self.set_status("Producto subido correctamente")
            
            self.refresh_history()
            self.clear_book_fields()
        else:
            self.set_status(f"Error al subir producto: {result.get('error')}")
            QMessageBox.critical(self, "Error", f"Error al subir: {result.get('error')}")
    
    def _get_selected_categories(self):
        """Obtiene las categorías seleccionadas del QListWidget"""
        categories = []
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            if item.checkState() == Qt.Checked:
                category_id = item.data(Qt.UserRole)
                if category_id:
                    categories.append(category_id)
        return categories

    def _get_selected_brand_id(self):
        """Obtiene el ID de marca seleccionado si existe"""
        brand_id = self.brand_input.currentData()
        return int(brand_id) if brand_id else None

    def _get_selected_brand_name(self):
        """Obtiene el nombre de la marca/editorial ingresada"""
        return self.brand_input.currentText().strip()

    def _build_short_description(self):
        """Genera un short description automático si no hay extracto manual"""
        if self.excerpt_input.toPlainText().strip():
            return self.excerpt_input.toPlainText().strip()

        parts = []
        if self.title_input.text().strip():
            parts.append(self.title_input.text().strip())
        if self.author_input.text().strip():
            parts.append(f"por {self.author_input.text().strip()}")
        if self.publisher_input.text().strip():
            parts.append(f"Editorial {self.publisher_input.text().strip()}")
        if self.format_combo.currentText():
            parts.append(self.format_combo.currentText())
        return ' · '.join(parts)[:250]

    def set_status(self, message, timeout=5000):
        """Muestra un mensaje de estado en la barra de estado"""
        self.statusBar().showMessage(message, timeout)

    def on_upload_error(self, error):
        """Se ejecuta en caso de error """
        if self.progress_dialog:
            self.progress_dialog.accept()  # Cerrar correctamente el QMessageBox
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
        self.set_status(f"Error al subir producto: {error}", 0)
        QMessageBox.critical(self, "Error", f"Error al subir: {error}")
    
    def open_site_settings(self):
        """Abre el diálogo de configuración de sitios"""
        dialog = SiteSettingsDialog(self, self.db)
        if dialog.exec_():
            self.refresh_sites()
    
    def _get_stylesheet(self):
        """Retorna el stylesheet de la aplicación"""
        return """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 20px;
                border: 1px solid #555;
            }
            QTabBar::tab:selected {
                background-color: #1976D2;
                color: white;
            }
            QTableWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                gridline-color: #555;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
            }
        """


class ProductUploadThread(QThread):
    """Thread para subir producto sin bloquear UI"""
    
    upload_complete = pyqtSignal(dict)
    upload_error = pyqtSignal(str)
    
    def __init__(self, site, product_data):
        super().__init__()
        self.site = site
        self.product_data = product_data
    
    def run(self):
        try:
            api = WooCommerceAPI(
                self.site['url'],
                self.site['consumer_key'],
                self.site['consumer_secret'],
                self.site.get('wp_username'),
                self.site.get('wp_password')
            )
            
            # Si hay imagen, subirla primero a WordPress Media
            image_url = None
            media_id = None
            image_url = None
            if self.product_data.get('cover_image_path'):
                if not api.wp_auth:
                    self.upload_error.emit("Se requieren credenciales de administrador de WordPress para subir imágenes")
                    return
                media_response = api.upload_media(self.product_data['cover_image_path'])
                if media_response:
                    media_id = media_response.get('id')
                    image_url = media_response.get('source_url')
                    print(f"Media subida: id={media_id}, url={image_url}")
                else:
                    print("Error al subir imagen a media")
            
            # Preparar datos del producto
            product_payload = {
                'name': self.product_data.get('title', ''),
                'description': self._build_product_description(self.product_data),
                'regular_price': str(self.product_data.get('price', '0')),
                'manage_stock': True,
                'stock_quantity': self.product_data.get('stock', 1),
                'status': 'publish'
            }

            isbn = (self.product_data.get('isbn') or '').strip()
            if isbn:
                product_payload['sku'] = isbn
            
            # Agregar categorías si existen
            if self.product_data.get('categories'):
                product_payload['categories'] = [
                    {'id': int(cat_id)}
                    for cat_id in self.product_data['categories']
                    if cat_id
                ]

            # Agregar breve descripción / excerpt
            if self.product_data.get('short_description'):
                product_payload['short_description'] = self.product_data['short_description']

            # Agregar dimensiones si se especifican
            if any(self.product_data.get(dim) for dim in ('length', 'width', 'height')):
                product_payload['dimensions'] = {
                    'length': str(self.product_data.get('length', '') or ''),
                    'width': str(self.product_data.get('width', '') or ''),
                    'height': str(self.product_data.get('height', '') or '')
                }
            
            # Agregar imagen destacada si se subió
            if media_id:
                product_payload['images'] = [{'id': int(media_id), 'position': 0}]
                product_payload['featured_media'] = int(media_id)
            elif image_url:
                product_payload['images'] = [{'src': image_url, 'position': 0}]
            
            product_data = api.create_product_with_sku_retry(product_payload)

            if product_data:
                product_id = product_data.get('id')
                
                # Si el plugin de marcas está disponible, asignar marca
                brand_id = self.product_data.get('brand_id')
                brand_name = self.product_data.get('brand_name')
                if brand_name and not brand_id:
                    brand_id = api.get_or_create_brand(brand_name)
                if brand_name and brand_id:
                    api.assign_brand_to_product(product_id, brand_id)

                # Fallback: si subimos media_id y el producto no mostró imagen, forzarlo
                if media_id and not product_data.get('images'):
                    print(f"Forzando featured_media con id {media_id}")
                    api.set_product_featured_image(product_id, media_id)
                    product_data = requests.get(
                        f"{api.api_url}/products/{product_id}",
                        auth=api.auth,
                        timeout=10
                    ).json()
                
                self.upload_complete.emit({
                    'success': True,
                    'product_id': product_id,
                    'product_name': product_data.get('name'),
                    'image_uploaded': bool(media_id or image_url)
                })
            else:
                error_message = api.last_error or "No se pudo crear el producto"
                print(f"Error al crear producto: {error_message}")
                self.upload_error.emit(error_message)
        
        except Exception as e:
            print(f"Excepción: {e}")
            self.upload_error.emit(str(e))
    
    def _build_product_description(self, product_data):
        """Construye la descripción del producto con HTML"""
        desc = f"<p><strong>Autor:</strong> {product_data.get('author', 'N/A')}</p>"
        desc += f"<p><strong>Editorial:</strong> {product_data.get('publisher', 'N/A')}</p>"
        desc += f"<p><strong>Formato:</strong> {product_data.get('format', 'N/A')}</p>"
        
        if product_data.get('edition_year'):
            desc += f"<p><strong>Año Edición:</strong> {product_data['edition_year']}</p>"
        
        if product_data.get('isbn'):
            desc += f"<p><strong>ISBN:</strong> {product_data['isbn']}</p>"
        
        return desc


class ProgressDialog(QMessageBox):
    """Diálogo de progreso simple"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Subiendo...")
        self.setText("Subiendo producto a WooCommerce...\nPor favor espera.")
        self.setIcon(QMessageBox.Information)
        self.setStandardButtons(QMessageBox.StandardButton.NoButton)  # Sin botones
