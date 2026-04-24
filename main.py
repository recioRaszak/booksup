#!/usr/bin/env python3
"""
Books Up!
Book Uploader para WooCommerce
Aplicación para gestionar la carga de libros en múltiples sitios WooCommerce
"""

import sys
from PyQt5.QtWidgets import QApplication
from book_uploader.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
