import subprocess
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from views.tabs.new_receipt_tab import NewReceiptTab
from views.tabs.history_tab import HistoryTab
from views.tabs.products_tab import ProductsTab
from views.tabs.statistics_tab import StatisticsTab
from views.tabs.settings_tab import SettingsTab


class MainWindow:
    def __init__(self, controller):
        self.controller = controller
        self.keyboard_process = None  # Pour gérer Onboard

        # Créer la fenêtre principale en plein écran
        self.root = ttk.Window(
            title="💼 Générateur de Reçus Pro",
            themename="cosmo"
        )
        
        # Activer le plein écran
        self.root.attributes('-fullscreen', True)
        
        # Quitter le plein écran / fermer l'application avec Échap
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        # Créer le bouton clavier virtuel
        self.create_keyboard_button()
        
        # Créer l'interface principale
        self.create_widgets()
        
        # Initialisation initiale
        self.new_receipt_tab.refresh_current_items()
        self.new_receipt_tab.update_receipt_number()
    
    def create_keyboard_button(self):
        """Créer un bouton pour afficher / cacher le clavier virtuel"""
        self.keyboard_btn = ttk.Button(
            self.root, text="Afficher / Cacher le clavier virtuel",
            command=self.toggle_keyboard,
            bootstyle="success-outline"
        )
        # On place le bouton en haut
        self.keyboard_btn.pack(side=TOP, pady=5)

    def toggle_keyboard(self):
        """Afficher ou cacher le clavier virtuel Onboard"""
        if self.keyboard_process is None:
            # Lancer Onboard
            try:
                self.keyboard_process = subprocess.Popen(["onboard"])
            except FileNotFoundError:
                print("Onboard n'est pas installé. Faites : sudo apt install onboard")
        else:
            # Fermer Onboard
            self.keyboard_process.terminate()
            self.keyboard_process = None
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Créer chaque onglet via des modules dédiés
        self.new_receipt_tab = NewReceiptTab(self.notebook, self.controller, self)
        self.history_tab = HistoryTab(self.notebook, self.controller, self)
        self.products_tab = ProductsTab(self.notebook, self.controller, self)
        self.statistics_tab = StatisticsTab(self.notebook, self.controller, self)
        self.settings_tab = SettingsTab(self.notebook, self.controller, self)
        
        # Ajouter les onglets au notebook
        self.notebook.add(self.new_receipt_tab.frame, text="➕ Nouveau Reçu")
        self.notebook.add(self.history_tab.frame, text="📋 Historique")
        self.notebook.add(self.products_tab.frame, text="📦 Produits")
        self.notebook.add(self.statistics_tab.frame, text="📊 Statistiques")
        self.notebook.add(self.settings_tab.frame, text="⚙️ Paramètres")
    
    def refresh_all_tabs(self):
        """Rafraîchir tous les onglets après une modification"""
        self.history_tab.refresh_history()
        self.products_tab.refresh_products()
        self.statistics_tab.refresh_statistics()
    
    def run(self):
        """Lancer l'application"""
        self.root.mainloop()


# Exemple d'utilisation
if __name__ == "__main__":
    # Ici, controller peut être un objet vide ou ton vrai controller
    class DummyController:
        pass

    app = MainWindow(DummyController())
    app.run()
