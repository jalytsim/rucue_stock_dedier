"""
Interface graphique principale - Point d'entrée
Avec barre de statut affichant date, heure, batterie et infos système
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
import psutil
import platform

from views.tabs.new_receipt_tab import NewReceiptTab
from views.tabs.history_tab import HistoryTab
from views.tabs.products_tab import ProductsTab
from views.tabs.statistics_tab import StatisticsTab
from views.tabs.settings_tab import SettingsTab


class MainWindow:
    def __init__(self, controller):
        self.controller = controller
        
        # Créer la fenêtre principale en plein écran
        self.root = ttk.Window(
            title="💼 Générateur de Reçus Pro",
            themename="cosmo"
        )
        
        # Activer le plein écran
        self.root.attributes('-fullscreen', True)
        
        # Quitter le plein écran / fermer l'application avec Échap
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # Créer l'interface
        self.create_widgets()
        
        # Initialisation initiale
        self.new_receipt_tab.refresh_current_items()
        self.new_receipt_tab.update_receipt_number()
        
        # Démarrer la mise à jour de la barre de statut
        self.update_status_bar()
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(main_frame, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=(10, 0))
        
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
        
        # ========== BARRE DE STATUT ==========
        self.create_status_bar(main_frame)
    
    def create_status_bar(self, parent):
        """Créer la barre de statut avec infos système"""
        status_frame = ttk.Frame(parent, bootstyle="secondary")
        status_frame.pack(fill=X, padx=10, pady=(5, 10))
        
        # Date et heure
        self.datetime_label = ttk.Label(
            status_frame,
            text="",
            font=("Helvetica", 11, "bold"),
            bootstyle="inverse-secondary"
        )
        self.datetime_label.pack(side=LEFT, padx=10, pady=5)
        
        # Séparateur
        ttk.Separator(status_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)
        
        # Batterie
        self.battery_label = ttk.Label(
            status_frame,
            text="",
            font=("Helvetica", 10),
            bootstyle="inverse-secondary"
        )
        self.battery_label.pack(side=LEFT, padx=10, pady=5)
        
        # Séparateur
        ttk.Separator(status_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)
        
        # CPU
        self.cpu_label = ttk.Label(
            status_frame,
            text="",
            font=("Helvetica", 10),
            bootstyle="inverse-secondary"
        )
        self.cpu_label.pack(side=LEFT, padx=10, pady=5)
        
        # Séparateur
        ttk.Separator(status_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)
        
        # RAM
        self.ram_label = ttk.Label(
            status_frame,
            text="",
            font=("Helvetica", 10),
            bootstyle="inverse-secondary"
        )
        self.ram_label.pack(side=LEFT, padx=10, pady=5)
        
        # Séparateur
        ttk.Separator(status_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)
        
        # Température CPU (si disponible)
        self.temp_label = ttk.Label(
            status_frame,
            text="",
            font=("Helvetica", 10),
            bootstyle="inverse-secondary"
        )
        self.temp_label.pack(side=LEFT, padx=10, pady=5)
    
    def update_status_bar(self):
        """Mettre à jour les informations de la barre de statut"""
        try:
            # Date et heure
            now = datetime.now()
            date_text = now.strftime("%A %d %B %Y • %H:%M:%S")
            self.datetime_label.config(text=f"📅 {date_text}")
            
            # Batterie
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = battery.power_plugged
                
                if plugged:
                    battery_icon = "🔌"
                    battery_text = f"{battery_icon} {percent:.0f}% (En charge)"
                else:
                    # Icônes selon le niveau
                    if percent > 80:
                        battery_icon = "🔋"
                    elif percent > 50:
                        battery_icon = "🔋"
                    elif percent > 20:
                        battery_icon = "🪫"
                    else:
                        battery_icon = "⚠️"
                    
                    # Temps restant
                    secs_left = battery.secsleft
                    if secs_left != psutil.POWER_TIME_UNLIMITED and secs_left > 0:
                        hours = secs_left // 3600
                        mins = (secs_left % 3600) // 60
                        battery_text = f"{battery_icon} {percent:.0f}% ({hours}h{mins:02d})"
                    else:
                        battery_text = f"{battery_icon} {percent:.0f}%"
                
                self.battery_label.config(text=battery_text)
            else:
                self.battery_label.config(text="🔌 Secteur")
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0)
            cpu_text = f"💻 CPU: {cpu_percent:.1f}%"
            self.cpu_label.config(text=cpu_text)
            
            # RAM
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            ram_used_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)
            ram_text = f"🧠 RAM: {ram_percent:.1f}% ({ram_used_gb:.1f}/{ram_total_gb:.1f} Go)"
            self.ram_label.config(text=ram_text)
            
            # Température CPU (si disponible sous Linux)
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # Chercher la température CPU
                        cpu_temp = None
                        for name, entries in temps.items():
                            if 'coretemp' in name.lower() or 'cpu' in name.lower():
                                if entries:
                                    cpu_temp = entries[0].current
                                    break
                        
                        if cpu_temp:
                            if cpu_temp > 80:
                                temp_icon = "🔥"
                            elif cpu_temp > 60:
                                temp_icon = "🌡️"
                            else:
                                temp_icon = "❄️"
                            
                            temp_text = f"{temp_icon} {cpu_temp:.0f}°C"
                            self.temp_label.config(text=temp_text)
                        else:
                            self.temp_label.config(text="")
                    else:
                        self.temp_label.config(text="")
                else:
                    self.temp_label.config(text="")
            except:
                self.temp_label.config(text="")
        
        except Exception as e:
            print(f"Erreur mise à jour statut: {e}")
        
        # Mettre à jour toutes les secondes
        self.root.after(1000, self.update_status_bar)
    
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