#!/usr/bin/env python3
"""
JORGE - Books to Woocommerce
Aplicación para gestionar la carga de libros en múltiples sitios WooCommerce
"""

import sys
from PyQt5.QtWidgets import QApplication
from pathlib import Path
from book_uploader import APP_NAME, APP_WEBSITE, __version__
from book_uploader.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')

    resources_dir = Path(__file__).parent / "book_uploader" / "resources"
    splash_candidates = [
        resources_dir / "JORGE-SPLASH.jpg",
        resources_dir / "JORGE-SPLASH.png",
        resources_dir / "splash-placeholder-640x480.png",
    ]
    splash_image_path = next((path for path in splash_candidates if path.exists()), None)
    
    # Crear y mostrar ventana principal
    window = MainWindow(
        app_name=APP_NAME,
        app_website=APP_WEBSITE,
        app_version=__version__,
        splash_image_path=str(splash_image_path) if splash_image_path else None
    )
    window.show()
    window.show_startup_splash(duration_ms=2600)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
