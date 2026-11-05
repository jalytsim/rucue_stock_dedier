#!/usr/bin/env python3
"""
Générateur de Reçus Pro
Application desktop pour générer des reçus thermiques
"""

import os
import sys
from pathlib import Path


def get_base_dir():
    """Dossier de l'application (à côté de l'exécutable si packagé avec PyInstaller)"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()

# Les chemins relatifs (data/, exports/) doivent pointer vers le dossier de l'application,
# même si elle est lancée depuis un raccourci ou un autre répertoire.
os.chdir(BASE_DIR)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from models.database import Database
from utils.pdf_generator import ReceiptGenerator
from controllers.receipt_controller import ReceiptController
from views.main_window import MainWindow


def log(message):
    """print() qui ne plante pas sur une console non UTF-8 ou absente (exe fenêtré)"""
    try:
        print(message)
    except Exception:
        pass


def main():
    """Point d'entrée principal de l'application"""
    log("Démarrage de l'application...")

    db = Database(BASE_DIR / "data" / "receipts.db")
    log("Base de données initialisée")

    pdf_generator = ReceiptGenerator(db.get_all_settings())
    controller = ReceiptController(db, pdf_generator)

    log("Lancement de l'interface graphique...")
    app = MainWindow(controller)
    app.run()


if __name__ == "__main__":
    main()
