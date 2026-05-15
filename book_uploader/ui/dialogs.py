from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QFormLayout,
    QTabWidget, QWidget, QGroupBox, QRadioButton, QButtonGroup, QComboBox,
    QDoubleSpinBox, QSpinBox, QScrollArea, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QFontDatabase
import re
import subprocess
from pathlib import Path

import requests


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
    return "Times New Roman"


class AppSplashDialog(QDialog):
    """Splash/About modal reutilizable para branding de la app."""

    def __init__(self, app_name, website_url, version, splash_image_path=None, parent=None):
        super().__init__(parent)
        self.serif_font_family = _pick_serif_font_family()
        self.app_name = app_name
        self.website_url = website_url
        self.version = version
        self.splash_image_path = splash_image_path

        self.setWindowTitle("Acerca de la aplicacion")
        self.setModal(True)
        # 640x480 de imagen + espacio cómodo para textos y botones sin superposiciones.
        self.setFixedSize(700, 760)
        self.setStyleSheet(self._get_stylesheet())

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 22)
        layout.setSpacing(12)

        splash_label = QLabel()
        splash_label.setAlignment(Qt.AlignCenter)
        splash_label.setFixedSize(640, 480)
        splash_label.setPixmap(self._load_splash_pixmap())
        layout.addWidget(splash_label, alignment=Qt.AlignCenter)
        layout.addSpacing(8)

        title_label = QLabel(self.app_name)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont(self.serif_font_family, 13, QFont.Bold))
        layout.addWidget(title_label)

        website_label = QLabel(f"Web: {self.website_url}")
        website_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(website_label)

        version_label = QLabel(f"Version: {self.version}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        check_updates_btn = QPushButton("Check for updates")
        check_updates_btn.setMinimumWidth(190)
        check_updates_btn.clicked.connect(self.check_for_updates)
        actions_layout.addWidget(check_updates_btn)

        close_btn = QPushButton("Cerrar")
        close_btn.setMinimumWidth(160)
        close_btn.clicked.connect(self.accept)
        actions_layout.addWidget(close_btn)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)

    def show_for(self, duration_ms):
        """Muestra el modal por N milisegundos y se cierra solo."""
        from PyQt5.QtCore import QTimer

        QTimer.singleShot(duration_ms, self.accept)
        self.exec_()

    def _load_splash_pixmap(self):
        """Carga imagen de splash o genera placeholder 640x480."""
        if self.splash_image_path:
            pixmap = QPixmap(self.splash_image_path)
            if not pixmap.isNull():
                # No recortar: mantener imagen completa dentro del área 640x480.
                return pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return self._build_placeholder_pixmap()

    def _build_placeholder_pixmap(self):
        """Placeholder visual para que el splash sea util sin assets finales."""
        pixmap = QPixmap(640, 480)
        pixmap.fill(QColor("#1f2632"))

        painter = QPainter(pixmap)
        painter.fillRect(0, 0, 640, 240, QColor("#243447"))
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont(self.serif_font_family, 24, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "SPLASH PLACEHOLDER\n640 x 480")
        painter.end()

        return pixmap

    def _repo_root(self):
        """Devuelve la ruta raíz del proyecto (2 niveles encima de ui/)."""
        return Path(__file__).resolve().parents[2]

    def _has_internet_connection(self):
        """Comprueba conectividad saliente mínima."""
        try:
            requests.get("https://github.com", timeout=5)
            return True
        except requests.RequestException:
            return False

    def _parse_version_tuple(self, value):
        """Convierte v1.2.3 o 1.2.3 en tupla comparable."""
        if not isinstance(value, str):
            return ()
        raw = value.strip().lower().lstrip('v')
        numbers = re.findall(r'\d+', raw)
        if not numbers:
            return ()
        return tuple(int(x) for x in numbers)

    def _latest_remote_tag(self):
        """Consulta tags remotos de origin vía git y devuelve la versión más alta."""
        repo_root = self._repo_root()
        cmd = ["git", "-C", str(repo_root), "ls-remote", "--tags", "--refs", "origin"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
        if proc.returncode != 0:
            return None

        tags = []
        for line in proc.stdout.splitlines():
            if "refs/tags/" not in line:
                continue
            tag_name = line.split("refs/tags/", 1)[1].strip()
            version_tuple = self._parse_version_tuple(tag_name)
            if version_tuple:
                tags.append((version_tuple, tag_name))

        if not tags:
            return None

        tags.sort(key=lambda item: item[0])
        return tags[-1][1]

    def check_for_updates(self):
        """Comprueba si existe una versión superior en origin/tags."""
        if not self._has_internet_connection():
            QMessageBox.warning(
                self,
                "Sin conexión",
                "No hay conexión a internet.\nConéctate para comprobar actualizaciones."
            )
            return

        try:
            remote_tag = self._latest_remote_tag()
            if not remote_tag:
                QMessageBox.information(
                    self,
                    "Actualizaciones",
                    "No se pudieron leer tags remotos de git en origin."
                )
                return

            local_tuple = self._parse_version_tuple(self.version)
            remote_tuple = self._parse_version_tuple(remote_tag)
            if remote_tuple > local_tuple:
                QMessageBox.information(
                    self,
                    "Actualización disponible",
                    f"Hay una versión superior disponible en git: {remote_tag}\n"
                    f"Versión actual: {self.version}"
                )
            else:
                QMessageBox.information(
                    self,
                    "App actualizada",
                    f"No hay actualizaciones disponibles.\n"
                    f"Versión actual: {self.version}"
                )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo comprobar actualizaciones: {exc}"
            )

    def _get_stylesheet(self):
        return """
            QDialog {
                background-color: #10151f;
                font-family: "Libre Serif", "Times New Roman", "Times", "Liberation Serif", "DejaVu Serif", "Noto Serif";
            }
            QLabel {
                color: #e3edf7;
            }
            QPushButton {
                background-color: #B0642C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9D5726;
            }
        """


class SiteSettingsDialog(QDialog):
    """Diálogo para configurar sitios WooCommerce"""
    
    def __init__(self, parent, db):
        super().__init__(parent)
        self.serif_font_family = _pick_serif_font_family()
        self.db = db
        self.editing_site_id = None  # Para saber si estamos editando
        self.setWindowTitle("⚙️ Configurar Sitios WooCommerce")
        self.setGeometry(100, 100, 900, 500)
        self.setStyleSheet(self._get_stylesheet())
        
        self.init_ui()
        self.refresh_sites_table()
    
    def init_ui(self):
        """Inicializa la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Sección de nuevo sitio
        new_site_label = QLabel("Agregar Nuevo Sitio")
        new_site_label.setFont(QFont(self.serif_font_family, 12, QFont.Bold))
        layout.addWidget(new_site_label)
        
        form_layout = QFormLayout()
        
        # Nombre del sitio
        name_label = QLabel("Nombre del Sitio:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Mi Tienda, Librería Online")
        form_layout.addRow(name_label, self.name_input)
        
        # URL del sitio
        url_label = QLabel("URL WooCommerce:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ej: https://misitio.com")
        form_layout.addRow(url_label, self.url_input)
        
        # Consumer Key
        key_label = QLabel("Consumer Key:")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("API Key de WooCommerce")
        self.key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(key_label, self.key_input)
        
        # Consumer Secret
        secret_label = QLabel("Consumer Secret:")
        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("API Secret de WooCommerce")
        self.secret_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(secret_label, self.secret_input)
        
        # WP Username (opcional)
        wp_user_label = QLabel("Usuario WordPress (NO nombre de la aplicación):")
        self.wp_user_input = QLineEdit()
        self.wp_user_input.setPlaceholderText("Tu usuario WP real (ej: israel)")
        form_layout.addRow(wp_user_label, self.wp_user_input)


        # WP Password (opcional)
        wp_pass_label = QLabel("Contraseña de aplicación (NO contraseña de admin):")
        self.wp_pass_input = QLineEdit()
        self.wp_pass_input.setPlaceholderText("Application Password sin espacios")
        self.wp_pass_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(wp_pass_label, self.wp_pass_input)
        
        # Botón de prueba de conexión
        test_conexion_btn = QPushButton("🔗 Probar Conexión")
        test_conexion_btn.clicked.connect(self.test_connection)
        form_layout.addRow("", test_conexion_btn)
        
        # Botón de agregar/actualizar
        self.action_btn = QPushButton("✅ Agregar Sitio")
        self.action_btn.setMinimumHeight(35)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.action_btn.clicked.connect(self.add_or_update_site)
        form_layout.addRow("", self.action_btn)
        
        layout.addLayout(form_layout)
        
        # Línea separadora
        separator = QLabel("-" * 60)
        layout.addWidget(separator)
        
        # Sección de sitios existentes
        existing_label = QLabel("Sitios Configurados")
        existing_label.setFont(QFont(self.serif_font_family, 12, QFont.Bold))
        layout.addWidget(existing_label)
        
        # Tabla de sitios
        self.sites_table = QTableWidget()
        self.sites_table.setColumnCount(5)
        self.sites_table.setHorizontalHeaderLabels(["Nombre", "URL", "Estado", "Editar", "Eliminar"])
        self.sites_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sites_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.sites_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.sites_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.sites_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.sites_table.verticalHeader().setDefaultSectionSize(46)
        self.sites_table.setAlternatingRowColors(True)
        self.sites_table.setShowGrid(False)
        self.sites_table.setWordWrap(True)
        self.sites_table.setMinimumHeight(200)
        
        layout.addWidget(self.sites_table)
        
        # Botón de cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def refresh_sites_table(self):
        """Refresca la tabla de sitios"""
        sites = self.db.get_all_sites()
        
        self.sites_table.setRowCount(0)
        
        for site in sites:
            row = self.sites_table.rowCount()
            self.sites_table.insertRow(row)
            
            # Nombre
            self.sites_table.setItem(row, 0, QTableWidgetItem(site['name']))
            
            # URL
            self.sites_table.setItem(row, 1, QTableWidgetItem(site['url']))
            
            # Estado (placeholder)
            self.sites_table.setItem(row, 2, QTableWidgetItem("✅ Configurado"))
            
            # Botón de eliminar
            delete_btn = QPushButton("🗑️ Eliminar")
            delete_btn.setMaximumWidth(100)
            delete_btn.clicked.connect(lambda checked, site_id=site['id']: self.delete_site(site_id))
            delete_btn.setStyleSheet("background-color: #f44336; color: white;")
            self.sites_table.setCellWidget(row, 3, delete_btn)
    
    def add_or_update_site(self):
        """Agrega un nuevo sitio o actualiza uno existente"""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        key = self.key_input.text().strip()
        secret = self.secret_input.text().strip()
        wp_user = self.wp_user_input.text().strip()
        wp_pass = self.wp_pass_input.text().strip()
        
        # Validar campos obligatorios
        if not all([name, url, key, secret]):
            QMessageBox.warning(self, "Error", "Nombre, URL, Consumer Key y Consumer Secret son obligatorios")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if self.editing_site_id:
            # Actualizar sitio existente
            success = self.db.update_site(self.editing_site_id, name, url, key, secret, wp_user, wp_pass)
            if success:
                QMessageBox.information(self, "Éxito", "Sitio actualizado correctamente")
                self.reset_form()
                self.refresh_sites_table()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el sitio")
        else:
            # Agregar nuevo sitio
            success, message = self.db.add_site(name, url, key, secret, wp_user, wp_pass)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.reset_form()
                self.refresh_sites_table()
            else:
                QMessageBox.warning(self, "Error", message)
    
    def edit_site(self, site_id):
        """Carga un sitio para editar"""
        site = self.db.get_site(site_id)
        if site:
            self.name_input.setText(site['name'])
            self.url_input.setText(site['url'])
            self.key_input.setText(site['consumer_key'])
            self.secret_input.setText(site['consumer_secret'])
            self.wp_user_input.setText(site.get('wp_username', ''))
            self.wp_pass_input.setText(site.get('wp_password', ''))
            self.editing_site_id = site_id
            self.action_btn.setText("🔄 Actualizar Sitio")
    
    def delete_site(self, site_id):
        """Elimina un sitio"""
        reply = QMessageBox.question(
            self, "Confirmar", 
            "¿Estás seguro de que deseas eliminar este sitio?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_site(site_id)
            self.refresh_sites_table()
            QMessageBox.information(self, "Éxito", "Sitio eliminado correctamente")
    
    def reset_form(self):
        """Limpia el formulario y resetea el modo de edición"""
        self.name_input.clear()
        self.url_input.clear()
        self.key_input.clear()
        self.secret_input.clear()
        self.wp_user_input.clear()
        self.wp_pass_input.clear()
        self.editing_site_id = None
        self.action_btn.setText("✅ Agregar Sitio")
    
    def test_connection(self):
        """Prueba la conexión con WooCommerce"""
        url = self.url_input.text().strip()
        key = self.key_input.text().strip()
        secret = self.secret_input.text().strip()
        wp_user = self.wp_user_input.text().strip()
        wp_pass = self.wp_pass_input.text().strip()
        
        if not all([url, key, secret]):
            QMessageBox.warning(self, "Error", "Completa URL, Key y Secret")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        from book_uploader.api.woocommerce import WooCommerceAPI
        
        api = WooCommerceAPI(url, key, secret, wp_user if wp_user else None, wp_pass if wp_pass else None)
        
        if api.test_connection():
            QMessageBox.information(self, "Éxito", "¡Conexión exitosa con WooCommerce!")
        else:
            QMessageBox.warning(self, "Error", "No se pudo conectar. Verifica los datos.")
    
    def refresh_sites_table(self):
        """Actualiza la tabla de sitios existentes"""
        self.sites_table.setRowCount(0)
        sites = self.db.get_all_sites()
        
        for row, site in enumerate(sites):
            self.sites_table.insertRow(row)
            self.sites_table.setRowHeight(row, 46)
            
            # Nombre
            name_item = QTableWidgetItem(site['name'])
            name_item.setForeground(Qt.white)
            self.sites_table.setItem(row, 0, name_item)
            
            # URL
            url_item = QTableWidgetItem(site['url'])
            url_item.setForeground(Qt.white)
            self.sites_table.setItem(row, 1, url_item)
            
            # Estado (simulado)
            status_item = QTableWidgetItem("✅ Configurado")
            status_item.setForeground(Qt.white)
            self.sites_table.setItem(row, 2, status_item)
            
            # Botón Editar
            edit_btn = QPushButton("✏️ Editar")
            edit_btn.setMinimumHeight(34)
            edit_btn.setMinimumWidth(110)
            edit_btn.clicked.connect(lambda checked, sid=site['id']: self.edit_site(sid))
            self.sites_table.setCellWidget(row, 3, edit_btn)
            
            # Botón Eliminar
            delete_btn = QPushButton("🗑️ Eliminar")
            delete_btn.setMinimumHeight(34)
            delete_btn.setMinimumWidth(110)
            delete_btn.setStyleSheet("background-color: #c62828; color: #ffffff;")
            delete_btn.clicked.connect(lambda checked, sid=site['id']: self.delete_site(sid))
            self.sites_table.setCellWidget(row, 4, delete_btn)
    
    def _get_stylesheet(self):
        """Retorna el stylesheet"""
        return """
            QDialog {
                background-color: #efefef;
                font-family: "Libre Serif", "Times New Roman", "Times", "Liberation Serif", "DejaVu Serif", "Noto Serif";
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #333;
            }
            QPushButton {
                background-color: #B0642C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9D5726;
            }
            QTableWidget {
                border: 1px solid #2f3640;
                background-color: #1f2329;
                alternate-background-color: #262b33;
                color: #f2f2f2;
                selection-background-color: #2d5ea8;
                selection-color: #ffffff;
                gridline-color: transparent;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #353b45;
                color: #f2f2f2;
            }
            QHeaderView::section {
                background-color: #171a1f;
                color: #f7f7f7;
                padding: 8px;
                border: 1px solid #2f3640;
                font-weight: bold;
            }
        """


# ── Thread auxiliar para cargar custom fields ────────────────────────────────

class _CustomFieldsLoader(QThread):
    """Carga los metacampos de producto desde el sitio WooCommerce activo."""

    fields_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, site: dict):
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
                self.site.get('wp_password'),
            )
            response = api.get_product_meta_fields()
            fields = response.get('fields', []) if isinstance(response, dict) else []
            self.fields_loaded.emit(fields)
        except Exception as exc:
            self.error_occurred.emit(str(exc))


# ── Diálogo de ajustes de la aplicación ──────────────────────────────────────

class AppSettingsDialog(QDialog):
    """Diálogo central de ajustes: apariencia, accesibilidad, idioma y defaults."""

    # Emitido cuando se guardan ajustes de tema / fuente para que la ventana
    # principal los aplique en caliente.
    settings_applied = pyqtSignal()

    def __init__(self, parent, db, current_site: dict | None = None):
        super().__init__(parent)
        from book_uploader.utils.i18n import tr, LANGUAGE_OPTIONS, get_language
        self._tr = tr
        self._lang_options = LANGUAGE_OPTIONS
        self._get_language = get_language

        self.db = db
        self.current_site = current_site
        self.serif_font_family = _pick_serif_font_family()
        self._custom_fields_widgets: list[dict] = []  # {key, label, widget}
        self._loader_thread: _CustomFieldsLoader | None = None

        self.setWindowTitle(tr('settings.title'))
        self.setMinimumSize(640, 580)
        self.setModal(True)
        self._apply_stylesheet()
        self._init_ui()
        self._load_current_values()

    # ── Construcción de la UI ────────────────────────────────────────────────

    def _init_ui(self):
        tr = self._tr
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.tabs.addTab(self._build_appearance_tab(), tr('settings.appearance'))
        self.tabs.addTab(self._build_accessibility_tab(), tr('settings.accessibility'))
        self.tabs.addTab(self._build_language_tab(), tr('settings.language'))
        self.tabs.addTab(self._build_defaults_tab(), tr('settings.defaults'))

        # Botones inferiores
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(16, 10, 16, 14)
        btn_bar.addStretch()

        save_btn = QPushButton(tr('app.save'))
        save_btn.setMinimumWidth(130)
        save_btn.clicked.connect(self._on_save)
        btn_bar.addWidget(save_btn)

        cancel_btn = QPushButton(tr('app.cancel'))
        cancel_btn.setMinimumWidth(110)
        cancel_btn.setObjectName('secondary')
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addWidget(cancel_btn)

        root.addLayout(btn_bar)

    # ── Tab Apariencia ───────────────────────────────────────────────────────

    def _build_appearance_tab(self) -> QWidget:
        tr = self._tr
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        group = QGroupBox(tr('settings.theme'))
        group.setFont(QFont(self.serif_font_family, 10, QFont.Bold))
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(10)

        self._theme_group = QButtonGroup(self)
        self._radio_dark = QRadioButton(tr('settings.theme_dark'))
        self._radio_light = QRadioButton(tr('settings.theme_light'))
        self._theme_group.addButton(self._radio_dark, 0)
        self._theme_group.addButton(self._radio_light, 1)

        # Preview visual de cada tema
        for radio, preview_color, text_color in [
            (self._radio_dark, '#2b2b2b', '#ffffff'),
            (self._radio_light, '#f5f5f5', '#212121'),
        ]:
            row = QHBoxLayout()
            swatch = QLabel()
            swatch.setFixedSize(40, 22)
            swatch.setStyleSheet(
                f'background-color:{preview_color}; border:1px solid #888; border-radius:3px;'
            )
            row.addWidget(swatch)
            row.addWidget(radio)
            row.addStretch()
            g_layout.addLayout(row)

        layout.addWidget(group)
        layout.addStretch()
        return page

    # ── Tab Accesibilidad ────────────────────────────────────────────────────

    def _build_accessibility_tab(self) -> QWidget:
        tr = self._tr
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        group = QGroupBox(tr('settings.font_size'))
        group.setFont(QFont(self.serif_font_family, 10, QFont.Bold))
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(10)

        self._font_group = QButtonGroup(self)
        self._radio_font_normal = QRadioButton(tr('settings.font_normal'))
        self._radio_font_large = QRadioButton(tr('settings.font_large'))
        self._font_group.addButton(self._radio_font_normal, 0)
        self._font_group.addButton(self._radio_font_large, 1)

        for radio, sample_pt in [
            (self._radio_font_normal, 9),
            (self._radio_font_large, 11),
        ]:
            row = QHBoxLayout()
            sample = QLabel('Aa')
            sample.setFont(QFont(self.serif_font_family, sample_pt))
            sample.setFixedWidth(36)
            row.addWidget(sample)
            row.addWidget(radio)
            row.addStretch()
            g_layout.addLayout(row)

        layout.addWidget(group)
        layout.addStretch()
        return page

    # ── Tab Idioma ───────────────────────────────────────────────────────────

    def _build_language_tab(self) -> QWidget:
        tr = self._tr
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel(tr('settings.language_label'))
        lbl.setFont(QFont(self.serif_font_family, 10, QFont.Bold))
        layout.addWidget(lbl)

        self._lang_combo = QComboBox()
        for code, name in self._lang_options:
            self._lang_combo.addItem(name, userData=code)
        layout.addWidget(self._lang_combo)

        note = QLabel(tr('settings.language_restart_note'))
        note.setWordWrap(True)
        note.setObjectName('note')
        layout.addWidget(note)

        layout.addStretch()
        return page

    # ── Tab Valores por defecto ──────────────────────────────────────────────

    def _build_defaults_tab(self) -> QWidget:
        tr = self._tr
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(18)

        desc = QLabel(tr('settings.defaults_desc'))
        desc.setWordWrap(True)
        desc.setObjectName('note')
        layout.addWidget(desc)

        # ── Campos nativos WooCommerce ──
        native_group = QGroupBox(tr('settings.defaults_native'))
        native_group.setFont(QFont(self.serif_font_family, 10, QFont.Bold))
        native_form = QFormLayout(native_group)
        native_form.setSpacing(10)

        self._def_price = QDoubleSpinBox()
        self._def_price.setRange(0.0, 99999.0)
        self._def_price.setDecimals(2)
        self._def_price.setMaximumWidth(150)
        native_form.addRow(tr('settings.defaults_price'), self._def_price)

        self._def_stock = QSpinBox()
        self._def_stock.setRange(0, 99999)
        self._def_stock.setMaximumWidth(120)
        native_form.addRow(tr('settings.defaults_stock'), self._def_stock)

        self._def_weight = QDoubleSpinBox()
        self._def_weight.setRange(0.0, 9999.0)
        self._def_weight.setDecimals(2)
        self._def_weight.setMaximumWidth(150)
        native_form.addRow(tr('settings.defaults_weight'), self._def_weight)

        self._def_length = QDoubleSpinBox()
        self._def_length.setRange(0.0, 9999.0)
        self._def_length.setDecimals(1)
        self._def_length.setMaximumWidth(150)
        native_form.addRow(tr('settings.defaults_length'), self._def_length)

        self._def_width = QDoubleSpinBox()
        self._def_width.setRange(0.0, 9999.0)
        self._def_width.setDecimals(1)
        self._def_width.setMaximumWidth(150)
        native_form.addRow(tr('settings.defaults_width'), self._def_width)

        self._def_height = QDoubleSpinBox()
        self._def_height.setRange(0.0, 9999.0)
        self._def_height.setDecimals(1)
        self._def_height.setMaximumWidth(150)
        native_form.addRow(tr('settings.defaults_height'), self._def_height)

        self._def_status = QComboBox()
        self._def_status.addItem(tr('settings.defaults_status_draft'), userData='draft')
        self._def_status.addItem(tr('settings.defaults_status_publish'), userData='publish')
        self._def_status.setMaximumWidth(220)
        native_form.addRow(tr('settings.defaults_status'), self._def_status)

        self._def_catalog = QComboBox()
        for key, label_key in [
            ('visible', 'settings.defaults_catalog_visible'),
            ('catalog', 'settings.defaults_catalog_catalog'),
            ('search',  'settings.defaults_catalog_search'),
            ('hidden',  'settings.defaults_catalog_hidden'),
        ]:
            self._def_catalog.addItem(tr(label_key), userData=key)
        self._def_catalog.setMaximumWidth(220)
        native_form.addRow(tr('settings.defaults_catalog_visibility'), self._def_catalog)

        self._def_tax = QComboBox()
        for key, label_key in [
            ('taxable',  'settings.defaults_tax_taxable'),
            ('shipping', 'settings.defaults_tax_shipping'),
            ('none',     'settings.defaults_tax_none'),
        ]:
            self._def_tax.addItem(tr(label_key), userData=key)
        self._def_tax.setMaximumWidth(220)
        native_form.addRow(tr('settings.defaults_tax_status'), self._def_tax)

        layout.addWidget(native_group)

        # ── Campos personalizados ──
        self._custom_group = QGroupBox(tr('settings.defaults_custom'))
        self._custom_group.setFont(QFont(self.serif_font_family, 10, QFont.Bold))
        self._custom_layout = QVBoxLayout(self._custom_group)
        self._custom_layout.setSpacing(8)

        self._custom_state_label = QLabel()
        self._custom_state_label.setWordWrap(True)
        self._custom_state_label.setObjectName('note')
        self._custom_layout.addWidget(self._custom_state_label)

        self._load_custom_btn = QPushButton(tr('settings.defaults_load_custom'))
        self._load_custom_btn.clicked.connect(self._load_custom_fields)
        self._custom_layout.addWidget(self._load_custom_btn)

        # Contenedor dinámico donde se insertarán los campos cargados
        self._custom_fields_container = QWidget()
        self._custom_fields_form = QFormLayout(self._custom_fields_container)
        self._custom_fields_form.setSpacing(8)
        self._custom_layout.addWidget(self._custom_fields_container)

        self._update_custom_state()
        layout.addWidget(self._custom_group)
        layout.addStretch()
        return page

    # ── Estado del bloque de custom fields ──────────────────────────────────

    def _update_custom_state(self):
        tr = self._tr
        if self.current_site is None:
            self._custom_state_label.setText(tr('settings.defaults_no_site'))
            self._load_custom_btn.setVisible(False)
        else:
            self._custom_state_label.setText('')
            self._load_custom_btn.setVisible(True)

    def _load_custom_fields(self):
        if self.current_site is None:
            return
        tr = self._tr
        self._load_custom_btn.setEnabled(False)
        self._custom_state_label.setText(tr('settings.defaults_custom_loading'))

        self._loader_thread = _CustomFieldsLoader(self.current_site)
        self._loader_thread.fields_loaded.connect(self._on_custom_fields_loaded)
        self._loader_thread.error_occurred.connect(self._on_custom_fields_error)
        self._loader_thread.start()

    def _on_custom_fields_loaded(self, fields: list):
        tr = self._tr
        self._load_custom_btn.setEnabled(True)

        # Limpiar campos previos
        self._custom_fields_widgets.clear()
        while self._custom_fields_form.rowCount():
            self._custom_fields_form.removeRow(0)

        if not fields:
            self._custom_state_label.setText(
                tr('settings.defaults_custom_loaded') + ' (0 campos encontrados)'
            )
            return

        self._custom_state_label.setText(tr('settings.defaults_custom_loaded'))

        saved_defaults = {
            r['field_key']: r['value']
            for r in self.db.get_all_field_defaults(field_type='custom')
        }

        for field in fields:
            key = field.get('key') or field.get('meta_key', '')
            label = field.get('label') or key
            if not key:
                continue

            widget = QLineEdit()
            widget.setPlaceholderText(field.get('placeholder', ''))
            widget.setText(saved_defaults.get(key, ''))
            self._custom_fields_form.addRow(QLabel(label), widget)
            self._custom_fields_widgets.append({'key': key, 'label': label, 'widget': widget})

    def _on_custom_fields_error(self, error: str):
        tr = self._tr
        self._load_custom_btn.setEnabled(True)
        self._custom_state_label.setText(
            tr('settings.defaults_custom_error').format(error=error)
        )

    # ── Carga de valores guardados ───────────────────────────────────────────

    def _load_current_values(self):
        settings = self.db.get_all_settings()

        # Tema
        theme = settings.get('theme', 'dark')
        self._radio_dark.setChecked(theme == 'dark')
        self._radio_light.setChecked(theme == 'light')

        # Fuente
        font_size = settings.get('font_size', 'normal')
        self._radio_font_normal.setChecked(font_size == 'normal')
        self._radio_font_large.setChecked(font_size == 'large')

        # Idioma
        current_lang = settings.get('language', self._get_language())
        for i in range(self._lang_combo.count()):
            if self._lang_combo.itemData(i) == current_lang:
                self._lang_combo.setCurrentIndex(i)
                break

        # Valores por defecto (campos nativos)
        def _f(key, fallback='0'):
            return self.db.get_field_default(key) or fallback

        self._def_price.setValue(float(_f('price', '4.0')))
        self._def_stock.setValue(int(_f('stock', '1')))
        self._def_weight.setValue(float(_f('weight', '0.0')))
        self._def_length.setValue(float(_f('length', '0.0')))
        self._def_width.setValue(float(_f('width', '0.0')))
        self._def_height.setValue(float(_f('height', '0.0')))

        self._set_combo_by_data(self._def_status, _f('status', 'draft'))
        self._set_combo_by_data(self._def_catalog, _f('catalog_visibility', 'visible'))
        self._set_combo_by_data(self._def_tax, _f('tax_status', 'taxable'))

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    # ── Guardar ──────────────────────────────────────────────────────────────

    def _on_save(self):
        tr = self._tr

        old_lang = self.db.get_setting('language', 'es')
        old_theme = self.db.get_setting('theme', 'dark')
        old_font = self.db.get_setting('font_size', 'normal')

        # Ajustes de app
        theme = 'dark' if self._radio_dark.isChecked() else 'light'
        font_size = 'large' if self._radio_font_large.isChecked() else 'normal'
        language = self._lang_combo.currentData() or 'es'

        self.db.set_setting('theme', theme)
        self.db.set_setting('font_size', font_size)
        self.db.set_setting('language', language)

        # Defaults nativos
        native_map = {
            'price':              str(self._def_price.value()),
            'stock':              str(self._def_stock.value()),
            'weight':             str(self._def_weight.value()),
            'length':             str(self._def_length.value()),
            'width':              str(self._def_width.value()),
            'height':             str(self._def_height.value()),
            'status':             self._def_status.currentData(),
            'catalog_visibility': self._def_catalog.currentData(),
            'tax_status':         self._def_tax.currentData(),
        }
        for key, value in native_map.items():
            self.db.set_field_default(key, value, label=key, field_type='native')

        # Defaults de custom fields (si se cargaron)
        if self._custom_fields_widgets:
            self.db.delete_field_defaults_by_type('custom')
            for entry in self._custom_fields_widgets:
                val = entry['widget'].text().strip()
                self.db.set_field_default(
                    entry['key'], val, label=entry['label'], field_type='custom'
                )

        # Avisar al padre para que aplique tema/fuente en caliente
        self.settings_applied.emit()

        # Si cambia el idioma, informar al usuario
        if language != old_lang:
            QMessageBox.information(
                self,
                tr('settings.language'),
                tr('app.restart_required'),
            )

        QMessageBox.information(self, tr('app.settings'), tr('settings.saved_ok'))
        self.accept()

    # ── Stylesheet ───────────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet(self._get_stylesheet())

    def _get_stylesheet(self) -> str:
        return """
            QDialog {
                background-color: #efefef;
                font-family: "Libre Serif", "Times New Roman", "Liberation Serif",
                             "DejaVu Serif", "Noto Serif", serif;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #f7f7f7;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #333333;
                padding: 8px 18px;
                border: 1px solid #cccccc;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #f7f7f7;
                color: #1565C0;
                font-weight: bold;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #444444;
            }
            QLabel {
                color: #333333;
            }
            QLabel#note {
                color: #666666;
                font-style: italic;
                font-size: 11px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #bbbbbb;
                border-radius: 4px;
                padding: 5px 7px;
                background-color: #ffffff;
                color: #212121;
            }
            QRadioButton {
                color: #333333;
                spacing: 8px;
            }
            QPushButton {
                background-color: #B0642C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 7px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9D5726;
            }
            QPushButton#secondary {
                background-color: #757575;
            }
            QPushButton#secondary:hover {
                background-color: #616161;
            }
        """

