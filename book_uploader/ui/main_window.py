from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QTabWidget,
    QScrollArea, QMessageBox, QProgressDialog, QTableWidget, QTableWidgetItem,
    QFileDialog, QHeaderView, QListWidget, QListWidgetItem, QGroupBox, QAction,
    QToolBox, QCheckBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon, QFontDatabase
from PyQt5.QtWidgets import QFormLayout

import sys
import os
import html
from pathlib import Path
import requests

from book_uploader import APP_NAME, APP_WEBSITE, __version__
from book_uploader.database.db import Database
from book_uploader.api.openbooks import OpenBooksAPI, ExternalBookSourcesAPI
from book_uploader.api.google_books import GoogleBooksAPI
from book_uploader.api.woocommerce import WooCommerceAPI
from book_uploader.utils.helpers import (
    get_cover_path, validate_isbn, format_price, truncate_text, get_covers_dir
)
from book_uploader.ui.dialogs import SiteSettingsDialog, AppSplashDialog, AppSettingsDialog


def _pick_serif_font_family():
    serif_stack = [
        "Libre Serif",
        "Times New Roman",
        "Times",
        "Liberation Serif",
        "DejaVu Serif",
        "Noto Serif",
    ]
    available = set(QFontDatabase().families())
    for family in serif_stack:
        if family in available:
            return family
    return QApplication.font().family()


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


class ProductMetaFieldsLoadThread(QThread):
    """Thread para cargar metacampos de producto sin bloquear UI"""

    fields_loaded = pyqtSignal(list)
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
            response = api.get_product_meta_fields()
            fields = response.get('fields', []) if isinstance(response, dict) else []
            self.fields_loaded.emit(fields)
        except Exception as e:
            self.error_occurred.emit(f"Error al cargar custom fields: {str(e)}")


class BookFetchThread(QThread):
    """Thread para buscar información del libro sin bloquear UI"""
    
    book_data_fetched = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    source_changed = pyqtSignal(str)
    
    def __init__(self, isbn):
        super().__init__()
        self.isbn = isbn
    
    def run(self):
        try:
            self.source_changed.emit("OpenLibrary")
            # Intentar primero con OpenLibrary (incluye fallback interno search API)
            book_info = OpenBooksAPI.get_book_by_isbn(self.isbn)
            
            if book_info:
                if not book_info.get('publisher') or not book_info.get('cover_url'):
                    self.source_changed.emit("Fuentes externas (Hamelyn, Casa del Libro, IberLibro, WorldCat)")
                    fallback = ExternalBookSourcesAPI.get_book_by_isbn(self.isbn)
                    if fallback:
                        for key, value in fallback.items():
                            if value and not book_info.get(key):
                                book_info[key] = value
                self.book_data_fetched.emit(book_info)
                return

            # Intentar con Google Books
            self.source_changed.emit("Google Books")
            book_info = GoogleBooksAPI.get_book_by_isbn(self.isbn)
            if book_info and (not book_info.get('publisher') or not book_info.get('cover_url')):
                self.source_changed.emit("Fuentes externas (Hamelyn, Casa del Libro, IberLibro, WorldCat)")
                fallback = ExternalBookSourcesAPI.get_book_by_isbn(self.isbn)
                if fallback:
                    for key, value in fallback.items():
                        if value and not book_info.get(key):
                            book_info[key] = value

            if book_info:
                self.book_data_fetched.emit(book_info)
            else:
                self.source_changed.emit("Fuentes externas (Hamelyn, Casa del Libro, IberLibro, WorldCat)")
                external_only, source_name = ExternalBookSourcesAPI.get_book_by_isbn_with_source(self.isbn)
                if external_only:
                    if source_name:
                        self.source_changed.emit(source_name)
                    self.book_data_fetched.emit(external_only)
                    return
                
                # Si no se encuentra con el ISBN tal cual, intentar con prefijo 978 
                # (para ISBNs de 10 dígitos o incompletos sin prefijo)
                clean_isbn = self.isbn.replace('-', '').replace(' ', '')
                if len(clean_isbn) == 10 and clean_isbn.isdigit():
                    self.source_changed.emit("Reintentando con prefijo ISBN-13 (978)...")
                    isbn_with_prefix = f"978{clean_isbn}"
                    external_with_prefix, source_name = ExternalBookSourcesAPI.get_book_by_isbn_with_source(isbn_with_prefix)
                    if external_with_prefix:
                        if source_name:
                            self.source_changed.emit(source_name)
                        self.book_data_fetched.emit(external_with_prefix)
                        return
                
                self.error_occurred.emit("No se encontró información para este ISBN en ninguna fuente disponible")
        except Exception as e:
            self.error_occurred.emit(f"Error al buscar: {str(e)}")


class IsbnCandidatesFetchThread(QThread):
    """Thread para buscar posibles ISBN por texto libre."""

    candidates_fetched = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    source_changed = pyqtSignal(str)

    def __init__(self, query_text):
        super().__init__()
        self.query_text = query_text

    def run(self):
        try:
            candidates = []
            seen = set()

            self.source_changed.emit("OpenLibrary (busqueda por texto)")
            openlibrary_candidates = OpenBooksAPI.search_isbn_candidates(self.query_text, max_results=12)
            for candidate in openlibrary_candidates:
                isbn = candidate.get('isbn', '')
                if isbn and isbn not in seen:
                    seen.add(isbn)
                    candidates.append(candidate)

            if len(candidates) < 12:
                self.source_changed.emit("Google Books (busqueda por texto)")
                google_candidates = GoogleBooksAPI.search_isbn_candidates(self.query_text, max_results=12)
                for candidate in google_candidates:
                    isbn = candidate.get('isbn', '')
                    if isbn and isbn not in seen:
                        seen.add(isbn)
                        candidates.append(candidate)
                        if len(candidates) >= 12:
                            break

            self.candidates_fetched.emit(candidates[:12])
        except Exception as e:
            self.error_occurred.emit(f"Error buscando candidatos ISBN: {str(e)}")


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
    
    def __init__(self, app_name=APP_NAME, app_website=APP_WEBSITE, app_version=__version__, splash_image_path=None):
        super().__init__()
        self.db = Database()
        self.current_site = None
        self.cover_url = None
        self.cover_path = None
        self.book_fetch_thread = None
        self.cover_download_thread = None
        self.book_search_progress = None
        self.advanced_meta_rows = []
        self.wpsso_rows = []
        self.serif_font_family = _pick_serif_font_family()
        self.wpsso_defaults = [
            {
                'slug': 'gtin13',
                'meta_key': '_wpsso_product_gtin13',
                'label': 'GTIN13',
                'type': 'text',
                'placeholder': 'Se completa desde ISBN de 13 digitos'
            },
            {
                'slug': 'mpn',
                'meta_key': '_wpsso_product_mpn',
                'label': 'MPN',
                'type': 'text',
                'placeholder': 'Se recomienda usar ISBN si no hay otro codigo'
            },
            {
                'slug': 'brand',
                'meta_key': '_wpsso_product_brand',
                'label': 'Marca',
                'type': 'text',
                'placeholder': 'Se completa con Marca/Editorial del producto'
            },
            {
                'slug': 'condition',
                'meta_key': '_wpsso_product_condition',
                'label': 'Condicion',
                'type': 'choice',
                'choices': [('new', 'new'), ('used', 'used'), ('refurbished', 'refurbished')]
            },
            {
                'slug': 'availability',
                'meta_key': '_wpsso_product_availability',
                'label': 'Availability',
                'type': 'choice',
                'choices': [('in stock', 'in stock'), ('out of stock', 'out of stock'), ('preorder', 'preorder')]
            },
            {
                'slug': 'google_category',
                'meta_key': '_wpsso_product_google_product_category',
                'label': 'Google Product Category',
                'type': 'text',
                'placeholder': 'Ejemplo: Media > Books'
            },
            {
                'slug': 'gender',
                'meta_key': '_wpsso_product_gender',
                'label': 'Genero (Google)',
                'type': 'choice',
                'choices': [('', 'Sin valor'), ('male', 'male'), ('female', 'female'), ('unisex', 'unisex')]
            },
            {
                'slug': 'age_group',
                'meta_key': '_wpsso_product_age_group',
                'label': 'Age Group (Google)',
                'type': 'choice',
                'choices': [('', 'Sin valor'), ('newborn', 'newborn'), ('infant', 'infant'), ('toddler', 'toddler'), ('kids', 'kids'), ('adult', 'adult')]
            },
            {
                'slug': 'color',
                'meta_key': '_wpsso_product_color',
                'label': 'Color',
                'type': 'text',
                'placeholder': 'Opcional'
            },
            {
                'slug': 'size',
                'meta_key': '_wpsso_product_size',
                'label': 'Talla',
                'type': 'text',
                'placeholder': 'Opcional'
            },
            {
                'slug': 'material',
                'meta_key': '_wpsso_product_material',
                'label': 'Material',
                'type': 'text',
                'placeholder': 'Opcional'
            },
        ]
        self.app_name = app_name
        self.app_website = app_website
        self.app_version = app_version
        self.splash_image_path = splash_image_path

        # ── Ajustes persistentes ──────────────────────────────────────────
        self._load_app_settings()

        self.setWindowTitle(f"📚 {self.app_name}")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(self._get_stylesheet())
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz"""
        self._setup_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Encabezado con selector de sitio
        header_layout = QHBoxLayout()
        
        site_label = QLabel("Sitio WooCommerce:")
        site_label.setFont(QFont(self.serif_font_family, 11, QFont.Bold))
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
        self.apply_form_defaults()

    def _setup_menu_bar(self):
        """Crea menú superior con acciones de ayuda/about."""
        menubar = self.menuBar()

        # Menú Ajustes
        settings_menu = menubar.addMenu("Ajustes")
        app_settings_action = QAction("⚙️ Preferencias de la app", self)
        app_settings_action.triggered.connect(self.open_app_settings)
        settings_menu.addAction(app_settings_action)

        ayuda_menu = menubar.addMenu("Ayuda")

        about_action = QAction("Acerca de", self)
        about_action.triggered.connect(self.show_about_dialog)
        ayuda_menu.addAction(about_action)

    def show_startup_splash(self, duration_ms=2600):
        """Muestra splash modal por unos segundos al iniciar la app."""
        splash = AppSplashDialog(
            app_name=self.app_name,
            website_url=self.app_website,
            version=self.app_version,
            splash_image_path=self.splash_image_path,
            parent=self
        )
        splash.show_for(duration_ms)

    def show_about_dialog(self):
        """Abre el modal About desde el menú superior."""
        splash = AppSplashDialog(
            app_name=self.app_name,
            website_url=self.app_website,
            version=self.app_version,
            splash_image_path=self.splash_image_path,
            parent=self
        )
        splash.exec_()
    
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

        # Zona superior de busqueda (separada visualmente del resto del formulario)
        search_group = QGroupBox("Busqueda de libro")
        search_group_layout = QVBoxLayout(search_group)

        self.search_tabs = QTabWidget()

        # Tab 1: Busqueda directa por ISBN/EAN
        search_isbn_tab = QWidget()
        search_isbn_layout = QVBoxLayout(search_isbn_tab)

        ean_help_label = QLabel("ISBN directo (escaneado o escrito manualmente)")
        ean_help_label.setStyleSheet("color: #555555; font-style: italic;")
        search_isbn_layout.addWidget(ean_help_label)
        
        # EAN/ISBN (Campo crítico)
        ean_label = QLabel("📱 EAN/ISBN:")
        ean_label.setFont(QFont(self.serif_font_family, 10, QFont.Bold))
        
        ean_layout = QHBoxLayout()
        self.ean_input = QLineEdit()
        self.ean_input.setPlaceholderText("Escanea el código de barras aquí...")
        self.ean_input.setStyleSheet("QLineEdit { font-size: 14px; padding: 8px; }")
        self.ean_input.returnPressed.connect(self.fetch_book_info)
        
        fetch_btn = QPushButton("🔍 Buscar")
        fetch_btn.clicked.connect(self.fetch_book_info)
        
        ean_layout.addWidget(self.ean_input)
        ean_layout.addWidget(fetch_btn)

        ean_row = QHBoxLayout()
        ean_row.addWidget(ean_label)
        ean_row.addLayout(ean_layout)
        search_isbn_layout.addLayout(ean_row)
        
        # Nota de ayuda sobre formatos de ISBN
        isbn_help = QLabel(
            "<small><b>Formatos de ISBN aceptados:</b><br/>"
            "• ISBN-13 (13 dígitos): <code>978-84-12345-67-8</code> o sin guiones<br/>"
            "• ISBN-10 (10 dígitos): <code>8412345678</code> (antiguo, todavía válido)<br/>"
            "• Sin prefijo: Si solo tienes los números sin \"978\", puedo buscar así también<br/>"
            "• Códigos frecuentes: 978 (libros españoles e internacionales), 979 (libros digitales)<br/>"
            "<i>Si el ISBN no se encuentra, buscaré en Hamelyn, Casa del Libro, IberLibro y WorldCat</i></small>"
        )
        isbn_help.setWordWrap(True)
        isbn_help.setStyleSheet(
            "QLabel { color: #666666; background-color: #f5f5f5; padding: 8px; border-radius: 4px; }"
            "small { font-size: 11px; }"
            "code { background-color: #e8e8e8; padding: 2px 4px; border-radius: 2px; font-family: monospace; }"
        )
        search_isbn_layout.addWidget(isbn_help)

        self.search_tabs.addTab(search_isbn_tab, "ISBN directo")

        # Tab 2: Busqueda textual para obtener ISBN candidatos
        search_text_tab = QWidget()
        search_text_layout = QVBoxLayout(search_text_tab)

        search_text_intro = QLabel(
            "Busqueda opcional por texto libre (titulo + autor + editorial)."
        )
        search_text_intro.setWordWrap(True)
        search_text_intro.setStyleSheet("color: #555555; font-style: italic;")
        search_text_layout.addWidget(search_text_intro)

        query_row = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Ejemplo: El nombre de la rosa Umberto Eco Lumen")
        self.query_input.returnPressed.connect(self.search_isbn_candidates)
        self.query_input.setStyleSheet("QLineEdit { font-size: 14px; padding: 8px; }")
        query_row.addWidget(self.query_input)

        self.search_candidates_btn = QPushButton("🔎 Buscar posibles ISBN")
        self.search_candidates_btn.clicked.connect(self.search_isbn_candidates)
        query_row.addWidget(self.search_candidates_btn)
        search_text_layout.addLayout(query_row)

        self.isbn_candidates_list = QListWidget()
        self.isbn_candidates_list.setMinimumHeight(140)
        self.isbn_candidates_list.itemDoubleClicked.connect(self.use_selected_isbn_candidate)
        search_text_layout.addWidget(self.isbn_candidates_list)

        candidates_actions = QHBoxLayout()
        self.use_candidate_btn = QPushButton("✅ Usar ISBN seleccionado")
        self.use_candidate_btn.clicked.connect(self.use_selected_isbn_candidate)
        candidates_actions.addWidget(self.use_candidate_btn)

        self.clear_candidates_btn = QPushButton("🧹 Limpiar candidatos")
        self.clear_candidates_btn.clicked.connect(self.clear_isbn_candidates)
        candidates_actions.addWidget(self.clear_candidates_btn)
        candidates_actions.addStretch()
        search_text_layout.addLayout(candidates_actions)

        self.search_tabs.addTab(search_text_tab, "Busqueda por texto")
        search_group_layout.addWidget(self.search_tabs)
        form_layout.addRow(search_group)

        # Separador visible entre zona de busqueda y zona de datos del libro
        visual_separator = QLabel("──────────── Datos del libro (resultado y edicion) ────────────")
        visual_separator.setStyleSheet(
            "QLabel { color: #8f8f8f; background-color: #f0f0f0; "
            "font-weight: bold; padding: 8px 10px; border: 1px solid #d8d8d8; border-radius: 4px; }"
        )
        form_layout.addRow(visual_separator)
        
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

        # Descripción larga
        content_label = QLabel("Descripción larga:")
        self.long_description_input = QTextEdit()
        self.long_description_input.setPlaceholderText("Reseña o descripción completa del libro")
        self.long_description_input.setMaximumHeight(180)
        form_layout.addRow(content_label, self.long_description_input)

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

        # Sección avanzada
        advanced_title = QLabel("──────── Opciones avanzadas ────────")
        advanced_title.setStyleSheet("color: #bdbdbd;")
        form_layout.addRow(advanced_title)

        self.advanced_group = QGroupBox("Activar zona avanzada")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(self.advanced_group)

        advanced_hint = QLabel(
            "Compatibilidad integrada con ACF y WPSSO Google Merchant. "
            "Solo se enviaran metadatos con valor."
        )
        advanced_hint.setWordWrap(True)
        advanced_layout.addWidget(advanced_hint)

        advanced_actions = QHBoxLayout()
        self.reload_meta_fields_btn = QPushButton("🔄 Recargar campos ACF")
        self.reload_meta_fields_btn.clicked.connect(self.load_product_meta_fields)
        advanced_actions.addWidget(self.reload_meta_fields_btn)

        self.wpsso_autofill_btn = QPushButton("⚙️ Autocompletar WPSSO")
        self.wpsso_autofill_btn.clicked.connect(lambda: self._apply_wpsso_autofill(force=True))
        advanced_actions.addWidget(self.wpsso_autofill_btn)

        advanced_actions.addStretch()
        advanced_layout.addLayout(advanced_actions)

        self.advanced_tabs = QTabWidget()

        # Tab 1: Campos personalizados (ACF/meta)
        self.advanced_custom_tab = QWidget()
        custom_layout = QVBoxLayout(self.advanced_custom_tab)
        custom_intro = QLabel("Campos personalizados por grupos ACF (desplegables) y metacampos detectados.")
        custom_intro.setWordWrap(True)
        custom_layout.addWidget(custom_intro)

        self.advanced_meta_groups_toolbox = QToolBox()
        custom_layout.addWidget(self.advanced_meta_groups_toolbox)

        self.advanced_tabs.addTab(self.advanced_custom_tab, "Campos personalizados")

        # Tab 2: WPSSO Google Merchant
        self.advanced_wpsso_tab = QWidget()
        wpsso_layout = QVBoxLayout(self.advanced_wpsso_tab)

        self.wpsso_autofill_checkbox = QCheckBox("Autocompletar valores WPSSO desde datos WooCommerce")
        self.wpsso_autofill_checkbox.setChecked(True)
        wpsso_layout.addWidget(self.wpsso_autofill_checkbox)

        wpsso_reco = QLabel(
            "Recomendaciones:\n"
            "- GTIN13 y MPN se completan desde ISBN cuando es posible.\n"
            "- Marca se completa desde marca/editorial.\n"
            "- Condicion y availability se sugieren automaticamente.\n"
            "- Revisa los metakeys si tu instalacion WPSSO usa variantes."
        )
        wpsso_reco.setWordWrap(True)
        wpsso_layout.addWidget(wpsso_reco)

        self.wpsso_form_container = QWidget()
        self.wpsso_form_layout = QFormLayout(self.wpsso_form_container)
        self.wpsso_form_layout.setSpacing(8)
        wpsso_layout.addWidget(self.wpsso_form_container)

        self.advanced_tabs.addTab(self.advanced_wpsso_tab, "WPSSO Google Merchant")
        advanced_layout.addWidget(self.advanced_tabs)

        self._init_wpsso_fields()

        form_layout.addRow(self.advanced_group)
        
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
            self.load_product_meta_fields()
        else:
            self.current_site = None
            self._render_advanced_meta_fields([])
    
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

    def load_product_meta_fields(self):
        """Carga custom fields de producto (ACF + meta) desde endpoint del plugin"""
        if not self.current_site:
            return

        self.reload_meta_fields_btn.setEnabled(False)
        self.set_status("Cargando custom fields de productos...")
        self.meta_fields_load_thread = ProductMetaFieldsLoadThread(self.current_site)
        self.meta_fields_load_thread.fields_loaded.connect(self.on_product_meta_fields_loaded)
        self.meta_fields_load_thread.error_occurred.connect(self.on_product_meta_fields_error)
        self.meta_fields_load_thread.start()

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

    def on_product_meta_fields_loaded(self, fields):
        """Se ejecuta cuando se cargan los custom fields avanzados"""
        self.reload_meta_fields_btn.setEnabled(True)
        self._render_advanced_meta_fields(fields)
        self._apply_wpsso_autofill(force=False)
        if fields and not self.advanced_group.isChecked():
            self.advanced_group.setChecked(True)
        if fields:
            self.set_status(f"Custom fields cargados: {len(fields)}")
        else:
            self.set_status("Sin custom fields detectados")

    def on_product_meta_fields_error(self, error):
        """Se ejecuta si hay error al cargar custom fields"""
        self.reload_meta_fields_btn.setEnabled(True)
        
        # Intenta debug endpoint para diagnosticar
        try:
            from book_uploader.api.woocommerce import WooCommerceAPI
            api = WooCommerceAPI(
                self.current_site['url'],
                self.current_site['consumer_key'],
                self.current_site['consumer_secret'],
                self.current_site.get('wp_username'),
                self.current_site.get('wp_password')
            )
            debug_result = api.debug_plugin_status()
            
            if debug_result.get('plugin_active'):
                # Plugin está activo pero hay otro error
                error_msg = f"Error en custom fields: {error}"
            else:
                # Plugin no está activo
                user_info = debug_result.get('current_user', {})
                error_msg = (
                    f"🔴 Plugin Book Uploader no detectado o no activo en: {self.current_site['url']}\n\n"
                    f"Usuario actual: {user_info.get('login', 'N/A')} (ID: {user_info.get('ID', '?')})\n"
                    f"Edit Posts: {debug_result.get('capabilities', {}).get('edit_posts', False)}\n\n"
                    f"Pasos:\n"
                    f"1. Verifica que wp-book-uploader-endpoints.php esté en wp-content/plugins/\n"
                    f"2. Activa el plugin en WordPress Admin\n"
                    f"3. Recarga la app y vuelve a intentar"
                )
        except Exception as e:
            error_msg = (
                f"No se pudo verificar estado del plugin. Error: {str(e)}\n\n"
                f"Por favor verifica:\n"
                f"1. Que wp-book-uploader-endpoints.php esté activado en WordPress\n"
                f"2. Que las credenciales WP sean correctas (usuario real + app password)"
            )
        
        self._render_advanced_meta_fields([])
        self.set_status(f"Error cargando custom fields", 0)
        QMessageBox.warning(self, "Error al cargar campos avanzados", error_msg)

    
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
    
    def fetch_book_info(self, isbn_override=None):
        """Busca información del libro por ISBN/EAN"""
        ean = (isbn_override or self.ean_input.text()).strip()

        if isbn_override:
            self.ean_input.setText(ean)
        
        if not ean:
            QMessageBox.warning(self, "Error", "Por favor ingresa un EAN/ISBN")
            return
        
        if not validate_isbn(ean):
            QMessageBox.warning(self, "Error", "Formato de ISBN inválido")
            return
        
        # Mostrar que se está buscando
        self.fetch_btn_status = True
        self.show_book_search_progress("Iniciando busqueda...")
        
        # Crear y ejecutar thread
        self.book_fetch_thread = BookFetchThread(ean)
        self.book_fetch_thread.book_data_fetched.connect(self.on_book_data_fetched)
        self.book_fetch_thread.error_occurred.connect(self.on_fetch_error)
        self.book_fetch_thread.source_changed.connect(self.on_book_source_changed)
        self.set_status("Buscando datos del libro...")
        self.book_fetch_thread.start()

    def search_isbn_candidates(self):
        """Busca posibles ISBN a partir de texto libre."""
        query_text = self.query_input.text().strip()
        if len(query_text) < 3:
            QMessageBox.warning(self, "Busqueda por texto", "Escribe al menos 3 caracteres para buscar")
            return

        self.show_book_search_progress("OpenLibrary (busqueda por texto)")
        self.isbn_candidates_thread = IsbnCandidatesFetchThread(query_text)
        self.isbn_candidates_thread.candidates_fetched.connect(self.on_isbn_candidates_fetched)
        self.isbn_candidates_thread.error_occurred.connect(self.on_fetch_error)
        self.isbn_candidates_thread.source_changed.connect(self.on_book_source_changed)
        self.set_status("Buscando posibles ISBN...")
        self.isbn_candidates_thread.start()

    def on_isbn_candidates_fetched(self, candidates):
        """Muestra candidatos ISBN tras una busqueda por texto."""
        if self.book_search_progress:
            self.book_search_progress.close()
            self.book_search_progress.deleteLater()
            self.book_search_progress = None

        self.isbn_candidates_list.clear()
        for candidate in candidates:
            isbn = candidate.get('isbn', '')
            title = candidate.get('title', '').strip()
            author = candidate.get('author', '').strip()
            publisher = candidate.get('publisher', '').strip()

            label_parts = [isbn]
            if title:
                label_parts.append(title)
            if author:
                label_parts.append(author)
            if publisher:
                label_parts.append(publisher)

            item = QListWidgetItem(" | ".join(label_parts))
            item.setData(Qt.UserRole, isbn)
            self.isbn_candidates_list.addItem(item)

        if candidates:
            self.set_status(f"Se encontraron {len(candidates)} ISBN candidatos")
            self.isbn_candidates_list.setCurrentRow(0)
        else:
            self.set_status("No se encontraron candidatos ISBN con esa busqueda")
            QMessageBox.information(
                self,
                "Sin resultados",
                "No se encontraron ISBN candidatos. Prueba con menos palabras o solo titulo + autor."
            )

    def use_selected_isbn_candidate(self):
        """Usa el ISBN seleccionado y dispara la busqueda normal por ISBN."""
        item = self.isbn_candidates_list.currentItem()
        if not item:
            QMessageBox.information(self, "Selecciona un ISBN", "Elige un candidato de la lista primero")
            return

        selected_isbn = item.data(Qt.UserRole)
        if not selected_isbn:
            QMessageBox.warning(self, "ISBN invalido", "El candidato seleccionado no tiene ISBN valido")
            return

        self.search_tabs.setCurrentIndex(0)
        self.fetch_book_info(isbn_override=selected_isbn)

    def clear_isbn_candidates(self):
        """Limpia resultados de busqueda textual de ISBN."""
        self.isbn_candidates_list.clear()

    def show_book_search_progress(self, initial_message):
        """Muestra un aviso no bloqueante con la fuente actual de busqueda."""
        if self.book_search_progress:
            self.book_search_progress.close()
            self.book_search_progress.deleteLater()

        self.book_search_progress = QProgressDialog(self)
        self.book_search_progress.setWindowTitle("Busqueda de ISBN")
        self.book_search_progress.setLabelText(f"Buscando ISBN en: {initial_message}")
        self.book_search_progress.setCancelButton(None)
        self.book_search_progress.setRange(0, 0)
        self.book_search_progress.setAutoClose(False)
        self.book_search_progress.setAutoReset(False)
        self.book_search_progress.setWindowModality(Qt.NonModal)
        self.book_search_progress.show()

    def on_book_source_changed(self, source_name):
        """Actualiza mensaje de progreso con la fuente de busqueda actual."""
        self.set_status(f"Buscando ISBN en: {source_name}...")
        if self.book_search_progress:
            self.book_search_progress.setLabelText(f"Buscando ISBN en: {source_name}")
    
    def on_book_data_fetched(self, book_info):
        """Se ejecuta cuando se obtiene la información del libro"""
        if self.book_search_progress:
            self.book_search_progress.close()
            self.book_search_progress.deleteLater()
            self.book_search_progress = None

        self.title_input.setText(book_info.get('title', ''))
        self.author_input.setText(book_info.get('author', ''))
        self.publisher_input.setText(book_info.get('publisher', ''))
        self.format_combo.setCurrentText(book_info.get('format', 'Tapa blanda'))

        raw_description = book_info.get('description', '')
        clean_description = self._clean_book_description(raw_description)
        self.excerpt_input.setText(self._build_excerpt_from_description(clean_description))
        self.long_description_input.setText(clean_description)
        
        if book_info.get('edition_year'):
            self.year_spin.setValue(book_info['edition_year'])

        self._apply_wpsso_autofill(force=False)

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
        if self.book_search_progress:
            self.book_search_progress.close()
            self.book_search_progress.deleteLater()
            self.book_search_progress = None

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
        if hasattr(self, 'query_input'):
            self.query_input.clear()
        if hasattr(self, 'isbn_candidates_list'):
            self.isbn_candidates_list.clear()
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
        self.excerpt_input.clear()
        self.long_description_input.clear()
        self.cover_path = None
        self.cover_url = None
        self.cover_preview.setText("Sin imagen")
        self.download_cover_btn.setEnabled(False)
        self.advanced_group.setChecked(False)
        for row in self.advanced_meta_rows:
            self._clear_advanced_meta_input(row.get('input'))
        for row in self.wpsso_rows:
            self._clear_advanced_meta_input(row.get('input'))
        self._apply_wpsso_autofill(force=False)
        self.ean_input.setFocus()

    def clear_book_fields(self):
        """Limpia solo los campos del libro que cambian con cada ISBN"""
        self.ean_input.clear()
        self.title_input.clear()
        self.author_input.clear()
        self.publisher_input.clear()
        self.year_spin.setValue(2024)
        self.excerpt_input.clear()
        self.long_description_input.clear()
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
            'long_description': self.long_description_input.toPlainText().strip() or self._build_long_description(),
            'length': self.length_input.value() or None,
            'width': self.width_input.value() or None,
            'height': self.height_input.value() or None,
            'weight': self.weight_input.value() or None,
            'advanced_meta_entries': self._get_filled_advanced_meta(),
            'wpsso_meta_entries': self._get_filled_wpsso_meta()
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

    def _build_long_description(self):
        """Genera una descripción larga cuando no hay reseña original disponible."""
        manual_long = self.long_description_input.toPlainText().strip()
        if manual_long:
            return manual_long

        if self.excerpt_input.toPlainText().strip():
            return self.excerpt_input.toPlainText().strip()

        fallback = []
        if self.title_input.text().strip():
            fallback.append(f"{self.title_input.text().strip()}")
        if self.author_input.text().strip():
            fallback.append(f"Autor: {self.author_input.text().strip()}")
        if self.publisher_input.text().strip():
            fallback.append(f"Editorial: {self.publisher_input.text().strip()}")
        if self.format_combo.currentText():
            fallback.append(f"Formato: {self.format_combo.currentText()}")
        if self.year_spin.value() > 1900:
            fallback.append(f"Año de edición: {self.year_spin.value()}")

        return '\n'.join(fallback).strip()

    def _clean_book_description(self, text):
        """Normaliza descripción de APIs a texto legible."""
        if isinstance(text, dict):
            text = text.get('value', '')
        if not isinstance(text, str):
            return ''

        cleaned = text.replace('\r\n', '\n').replace('\r', '\n').strip()
        # Mantener texto en bruto: solo normalizamos espacios duplicados por línea.
        cleaned_lines = [' '.join(line.split()) for line in cleaned.split('\n')]
        cleaned = '\n'.join([line for line in cleaned_lines if line])
        return cleaned

    def _build_excerpt_from_description(self, description_text):
        """Construye extracto corto desde una descripción original."""
        if not description_text:
            return self._build_short_description()

        snippet = description_text.split('\n', 1)[0].strip()
        if len(snippet) > 250:
            snippet = snippet[:247].rstrip() + '...'
        return snippet

    def _render_advanced_meta_fields(self, fields):
        """Renderiza dinámicamente los campos avanzados de metadatos."""
        existing_values = {
            row['key']: self._get_advanced_meta_input_value(row.get('input'))
            for row in self.advanced_meta_rows
            if row.get('input')
        }

        while self.advanced_meta_groups_toolbox.count() > 0:
            self.advanced_meta_groups_toolbox.removeItem(0)

        self.advanced_meta_rows = []

        if not fields:
            empty_page = QWidget()
            empty_layout = QVBoxLayout(empty_page)
            empty_label = QLabel("No se detectaron custom fields en el sitio.")
            empty_label.setStyleSheet("color: #bdbdbd;")
            empty_layout.addWidget(empty_label)
            empty_layout.addStretch()
            self.advanced_meta_groups_toolbox.addItem(empty_page, "Sin campos")
            return

        fields_by_group = {}
        for field in fields:
            group_name = str(field.get('group_name') or 'Otros metacampos')
            if group_name not in fields_by_group:
                fields_by_group[group_name] = []
            fields_by_group[group_name].append(field)

        for group_name, group_fields in fields_by_group.items():
            group_widget = QWidget()
            group_layout = QFormLayout(group_widget)
            group_layout.setSpacing(8)

            for field in group_fields:
                key = str(field.get('key', '')).strip()
                if not key:
                    continue

                label_text = str(field.get('label') or key)
                source = str(field.get('source') or 'meta')
                field_type = str(field.get('type') or 'text')
                acf_field_key = str(field.get('acf_field_key') or '').strip()
                field_choices = field.get('choices')

                row_label = QLabel(f"{label_text} ({key}) [{source}:{field_type}]")
                if field_type in ('select', 'radio', 'button_group', 'checkbox', 'true_false', 'boolean'):
                    row_input = QComboBox()
                    row_input.addItem('Sin valor', '')

                    if field_type in ('true_false', 'boolean'):
                        row_input.addItem('Si', '1')
                        row_input.addItem('No', '0')
                    else:
                        if isinstance(field_choices, dict):
                            for option_value, option_label in field_choices.items():
                                row_input.addItem(str(option_label), str(option_value))
                        elif isinstance(field_choices, list):
                            for option_value in field_choices:
                                row_input.addItem(str(option_value), str(option_value))

                    row_input.setToolTip('Opcional: deja "Sin valor" para no enviar')
                else:
                    row_input = QLineEdit()
                    row_input.setPlaceholderText("Opcional: deja vacío para no enviar")

                if key in existing_values and existing_values[key]:
                    self._set_advanced_meta_input_value(row_input, existing_values[key])

                group_layout.addRow(row_label, row_input)
                self.advanced_meta_rows.append({
                    'key': key,
                    'source': source,
                    'type': field_type,
                    'acf_field_key': acf_field_key,
                    'choices': field_choices,
                    'group_name': group_name,
                    'input': row_input
                })

            self.advanced_meta_groups_toolbox.addItem(group_widget, group_name)

    def _init_wpsso_fields(self):
        """Inicializa campos de compatibilidad WPSSO Google Merchant."""
        self.wpsso_rows = []
        while self.wpsso_form_layout.rowCount() > 0:
            self.wpsso_form_layout.removeRow(0)

        for field in self.wpsso_defaults:
            row_label = QLabel(f"{field['label']} ({field['meta_key']})")
            if field.get('type') == 'choice':
                row_input = QComboBox()
                for option_value, option_label in field.get('choices', []):
                    row_input.addItem(option_label, option_value)
            else:
                row_input = QLineEdit()
                row_input.setPlaceholderText(field.get('placeholder', 'Opcional'))

            self.wpsso_form_layout.addRow(row_label, row_input)
            self.wpsso_rows.append({
                'slug': field['slug'],
                'key': field['meta_key'],
                'input': row_input
            })

    def _compute_wpsso_defaults(self):
        """Calcula valores sugeridos de WPSSO desde datos base del producto."""
        isbn = ''.join(ch for ch in (self.ean_input.text().strip() or '') if ch.isdigit())
        stock = self.stock_spin.value() if hasattr(self, 'stock_spin') else 0

        defaults = {
            'brand': self._get_selected_brand_name() or self.publisher_input.text().strip(),
            'mpn': isbn,
            'condition': 'new',
            'availability': 'in stock' if stock > 0 else 'out of stock',
            'google_category': 'Media > Books',
        }

        if len(isbn) == 13:
            defaults['gtin13'] = isbn

        return defaults

    def _apply_wpsso_autofill(self, force=False):
        """Aplica sugerencias WPSSO a campos vacíos o todos si force=True."""
        if not hasattr(self, 'wpsso_rows'):
            return
        if not force and hasattr(self, 'wpsso_autofill_checkbox') and not self.wpsso_autofill_checkbox.isChecked():
            return

        defaults = self._compute_wpsso_defaults()
        for row in self.wpsso_rows:
            slug = row.get('slug')
            widget = row.get('input')
            value = defaults.get(slug)
            if value is None:
                continue

            current = self._get_advanced_meta_input_value(widget)
            if force or not current:
                self._set_advanced_meta_input_value(widget, value)

    def _get_filled_wpsso_meta(self):
        """Obtiene metadatos WPSSO con relleno automático opcional."""
        if not hasattr(self, 'advanced_group') or not self.advanced_group.isChecked():
            return []

        defaults = self._compute_wpsso_defaults() if self.wpsso_autofill_checkbox.isChecked() else {}
        entries = []
        for row in self.wpsso_rows:
            slug = row.get('slug')
            key = row.get('key')
            widget = row.get('input')
            value = self._get_advanced_meta_input_value(widget)

            if not value and slug in defaults:
                value = str(defaults[slug]).strip()

            if not value:
                continue

            entries.append({
                'key': key,
                'value': value
            })

        return entries

    def _get_filled_advanced_meta(self):
        """Devuelve solo metacampos avanzados con valor para enviarlos al crear producto."""
        if not hasattr(self, 'advanced_group') or not self.advanced_group.isChecked():
            return []

        filled = []
        for row in self.advanced_meta_rows:
            raw_value = self._get_advanced_meta_input_value(row.get('input'))
            if not raw_value:
                continue
            filled.append({
                'key': row['key'],
                'value': raw_value,
                'acf_field_key': row.get('acf_field_key', '')
            })
        return filled

    def _get_advanced_meta_input_value(self, widget):
        """Obtiene valor normalizado desde QLineEdit/QComboBox de campos avanzados."""
        if isinstance(widget, QComboBox):
            data = widget.currentData()
            if data is None:
                return ''
            return str(data).strip()

        if isinstance(widget, QLineEdit):
            return widget.text().strip()

        return ''

    def _set_advanced_meta_input_value(self, widget, value):
        """Restaura valor previo en QLineEdit/QComboBox de campos avanzados."""
        normalized = str(value).strip()
        if isinstance(widget, QComboBox):
            index = widget.findData(normalized)
            if index < 0:
                index = widget.findText(normalized)
            if index >= 0:
                widget.setCurrentIndex(index)
            return

        if isinstance(widget, QLineEdit):
            widget.setText(normalized)

    def _clear_advanced_meta_input(self, widget):
        """Limpia valor de QLineEdit/QComboBox en campos avanzados."""
        if isinstance(widget, QComboBox):
            widget.setCurrentIndex(0)
            return

        if isinstance(widget, QLineEdit):
            widget.clear()

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

    def open_app_settings(self):
        """Abre el diálogo de ajustes de la aplicación."""
        dialog = AppSettingsDialog(self, self.db, current_site=self.current_site)
        dialog.settings_applied.connect(self._on_settings_applied)
        dialog.exec_()

    def _on_settings_applied(self):
        """Aplica en caliente los nuevos ajustes de tema y fuente."""
        self._load_app_settings()
        self.setStyleSheet(self._get_stylesheet())
        # Actualizar también la barra de estado para dar feedback visual
        self.statusBar().showMessage("Ajustes aplicados", 3000)

    def _load_app_settings(self):
        """Carga los ajustes persistentes desde la base de datos."""
        from book_uploader.utils.i18n import set_language
        settings = self.db.get_all_settings()
        self._theme = settings.get('theme', 'dark')
        self._font_large = settings.get('font_size', 'normal') == 'large'
        lang = settings.get('language', 'es')
        set_language(lang)

    def apply_form_defaults(self):
        """Aplica los valores por defecto guardados a los campos del formulario."""
        def _f(key, fallback=''):
            return self.db.get_field_default(key) or fallback

        try:
            price_val = float(_f('price', '4.0'))
            self.price_input.setValue(price_val)
        except (ValueError, AttributeError):
            pass

        try:
            stock_val = int(float(_f('stock', '1')))
            self.stock_spin.setValue(stock_val)
        except (ValueError, AttributeError):
            pass

        for attr, key in [
            ('weight_input', 'weight'),
            ('length_input', 'length'),
            ('width_input', 'width'),
            ('height_input', 'height'),
        ]:
            try:
                widget = getattr(self, attr, None)
                if widget:
                    widget.setValue(float(_f(key, '0.0')))
            except (ValueError, AttributeError):
                pass

    def _get_stylesheet(self):
        """Retorna el stylesheet de la aplicación según tema y tamaño de fuente."""
        theme = getattr(self, '_theme', 'dark')
        font_large = getattr(self, '_font_large', False)
        base_pt = 11 if font_large else 9

        if theme == 'light':
            return self._stylesheet_light(base_pt)
        return self._stylesheet_dark(base_pt)

    def _stylesheet_dark(self, base_pt: int) -> str:
        return f"""
            QMainWindow, QWidget {{
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: "Libre Serif", "Times New Roman", "Times",
                             "Liberation Serif", "DejaVu Serif", "Noto Serif";
                font-size: {base_pt}pt;
            }}
            QLabel {{
                color: #ffffff;
                font-size: {base_pt}pt;
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                background-color: #3c3c3c;
                color: #ffffff;
                font-size: {base_pt}pt;
            }}
            QPushButton {{
                background-color: #B0642C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: {base_pt}pt;
            }}
            QPushButton:hover {{
                background-color: #9D5726;
            }}
            QPushButton:pressed {{
                background-color: #7F461F;
            }}
            QTabWidget::pane {{
                border: 1px solid #555;
                background-color: #2b2b2b;
            }}
            QTabBar::tab {{
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 20px;
                border: 1px solid #555;
                font-size: {base_pt}pt;
            }}
            QTabBar::tab:selected {{
                background-color: #1976D2;
                color: white;
            }}
            QTableWidget {{
                background-color: #3c3c3c;
                color: #ffffff;
                gridline-color: #555;
                font-size: {base_pt}pt;
            }}
            QHeaderView::section {{
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                font-size: {base_pt}pt;
            }}
            QGroupBox {{
                border: 1px solid #555;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 8px;
                color: #e0e0e0;
                font-size: {base_pt}pt;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                color: #cccccc;
            }}
            QScrollArea {{
                background-color: #2b2b2b;
                border: none;
            }}
            QMenuBar {{
                background-color: #1e1e1e;
                color: #ffffff;
                font-size: {base_pt}pt;
            }}
            QMenuBar::item:selected {{
                background-color: #3a3a3a;
            }}
            QMenu {{
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                font-size: {base_pt}pt;
            }}
            QMenu::item:selected {{
                background-color: #1976D2;
            }}
        """

    def _stylesheet_light(self, base_pt: int) -> str:
        return f"""
            QMainWindow, QWidget {{
                background-color: #f5f5f5;
                color: #212121;
                font-family: "Libre Serif", "Times New Roman", "Times",
                             "Liberation Serif", "DejaVu Serif", "Noto Serif";
                font-size: {base_pt}pt;
            }}
            QLabel {{
                color: #212121;
                font-size: {base_pt}pt;
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 6px;
                background-color: #ffffff;
                color: #212121;
                font-size: {base_pt}pt;
            }}
            QPushButton {{
                background-color: #B0642C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: {base_pt}pt;
            }}
            QPushButton:hover {{
                background-color: #9D5726;
            }}
            QPushButton:pressed {{
                background-color: #7F461F;
            }}
            QTabWidget::pane {{
                border: 1px solid #bdbdbd;
                background-color: #ffffff;
            }}
            QTabBar::tab {{
                background-color: #e0e0e0;
                color: #424242;
                padding: 8px 20px;
                border: 1px solid #bdbdbd;
                font-size: {base_pt}pt;
            }}
            QTabBar::tab:selected {{
                background-color: #1976D2;
                color: white;
            }}
            QTableWidget {{
                background-color: #ffffff;
                color: #212121;
                gridline-color: #e0e0e0;
                alternate-background-color: #f9f9f9;
                font-size: {base_pt}pt;
            }}
            QHeaderView::section {{
                background-color: #eeeeee;
                color: #424242;
                border: 1px solid #bdbdbd;
                font-size: {base_pt}pt;
            }}
            QGroupBox {{
                border: 1px solid #bdbdbd;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 8px;
                background-color: #ffffff;
                color: #424242;
                font-size: {base_pt}pt;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                color: #616161;
            }}
            QScrollArea {{
                background-color: #f5f5f5;
                border: none;
            }}
            QMenuBar {{
                background-color: #e8e8e8;
                color: #212121;
                font-size: {base_pt}pt;
            }}
            QMenuBar::item:selected {{
                background-color: #d5d5d5;
            }}
            QMenu {{
                background-color: #ffffff;
                color: #212121;
                border: 1px solid #bdbdbd;
                font-size: {base_pt}pt;
            }}
            QMenu::item:selected {{
                background-color: #1976D2;
                color: #ffffff;
            }}
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

            if self.product_data.get('weight'):
                product_payload['weight'] = str(self.product_data.get('weight'))

            # Meta personalizados: enviar solo los campos rellenados.
            advanced_meta_entries = self.product_data.get('advanced_meta_entries') or []
            wpsso_meta_entries = self.product_data.get('wpsso_meta_entries') or []
            meta_data = []
            for entry in advanced_meta_entries:
                key = str(entry.get('key', '')).strip()
                value = str(entry.get('value', '')).strip()
                acf_field_key = str(entry.get('acf_field_key', '')).strip()
                if not key or value == '':
                    continue

                meta_data.append({'key': key, 'value': value})

                # Para ACF, guardar también el metacampo privado con el field key.
                if acf_field_key:
                    meta_data.append({'key': f"_{key}", 'value': acf_field_key})

            for entry in wpsso_meta_entries:
                key = str(entry.get('key', '')).strip()
                value = str(entry.get('value', '')).strip()
                if not key or value == '':
                    continue
                meta_data.append({'key': key, 'value': value})

            if meta_data:
                product_payload['meta_data'] = meta_data
            
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
        long_description = (product_data.get('long_description') or '').strip()
        if long_description:
            paragraphs = [p.strip() for p in long_description.split('\n') if p.strip()]
            if paragraphs:
                return ''.join(f"<p>{html.escape(p)}</p>" for p in paragraphs)

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
