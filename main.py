#!/usr/bin/env python3
"""
Générateur de Reçus Pro
Application desktop pour générer des reçus thermiques (58mm, 80mm)
Avec autocomplétion intelligente et base de données locale
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from models.database import Database
from utils.pdf_generator import ReceiptGenerator
from controllers.receipt_controller import ReceiptController
from views.main_window import MainWindow

def main():
    """Point d'entrée principal de l'application"""
    print("🚀 Démarrage de l'application...")
    
    # Initialiser la base de données
    db = Database("data/receipts.db")
    print("✅ Base de données initialisée")
    
    # Initialiser le générateur PDF avec les paramètres
    settings = db.get_all_settings()
    pdf_generator = ReceiptGenerator(settings)
    print("✅ Générateur PDF initialisé")
    
    # Initialiser le contrôleur
    controller = ReceiptController(db, pdf_generator)
    print("✅ Contrôleur initialisé")
    
    # Créer et lancer l'interface graphique
    print("✅ Lancement de l'interface graphique...")
    app = MainWindow(controller)
    app.run()

if __name__ == "__main__":
    main()
