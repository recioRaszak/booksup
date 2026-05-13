from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QFormLayout
)
from PyQt5.QtCore import Qt
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
