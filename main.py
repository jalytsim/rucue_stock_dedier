#!/usr/bin/env python3
"""
Générateur de Reçus Pro
Application desktop pour générer des reçus thermiques
"""

import sys
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
    
    # Initialiser le générateur PDF
    settings = db.get_all_settings()
    pdf_generator = ReceiptGenerator(settings)
    print("✅ Générateur PDF initialisé")
    
    # Initialiser le contrôleur
    controller = ReceiptController(db, pdf_generator)
    print("✅ Contrôleur initialisé")
    
    # Créer et lancer l'interface
    print("✅ Lancement de l'interface graphique...")
    app = MainWindow(controller)
    app.run()

if __name__ == "__main__":
    main()