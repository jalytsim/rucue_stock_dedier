"""
Interface graphique principale - Point d'entrée
Délègue chaque onglet à un module spécialisé
"""
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
        
        # Créer la fenêtre principale
        self.root = ttk.Window(
            title="💼 Générateur de Reçus Pro",
            themename="cosmo",
            size=(1400, 900)
        )
        
        self.root.place_window_center()
        
        # Créer l'interface
        self.create_widgets()
        
        # Initialisation initiale
        self.new_receipt_tab.refresh_current_items()
        self.new_receipt_tab.update_receipt_number()
    
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