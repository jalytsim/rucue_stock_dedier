"""
Interface graphique principale - Point d'entrée
Avec barre de statut : date/heure, ventes du jour, batterie, ressources système
"""
import traceback
from datetime import datetime
from tkinter import messagebox

import psutil
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.formatting import fmt_long_date, fmt_money
from views.ui_helpers import Toast, setup_styles
from views.tabs.new_receipt_tab import NewReceiptTab
from views.tabs.history_tab import HistoryTab
from views.tabs.products_tab import ProductsTab
from views.tabs.statistics_tab import StatisticsTab
from views.tabs.settings_tab import SettingsTab


class MainWindow:
    def __init__(self, controller):
        self.controller = controller

        self.root = ttk.Window(title="Générateur de Reçus Pro", themename="cosmo",
                               minsize=(800, 600))
        setup_styles(self.root)
        self.toast = Toast(self.root)

        # Les erreurs inattendues s'affichent au lieu de disparaître dans la console
        self.root.report_callback_exception = self._on_callback_error

        self.is_fullscreen = True
        self.root.attributes('-fullscreen', True)

        # Échap quitte seulement le plein écran (avant : fermait l'appli et perdait le reçu en cours)
        self.root.bind("<Escape>", lambda e: self.set_fullscreen(False))
        self.root.bind("<F11>", lambda e: self.set_fullscreen(not self.is_fullscreen))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        for i in range(5):
            self.root.bind(f"<Control-Key-{i + 1}>", lambda e, idx=i: self.notebook.select(idx))

        self.create_widgets()

        self.new_receipt_tab.refresh_current_items()
        self.new_receipt_tab.update_receipt_number()
        self.new_receipt_tab.focus_product()

        self._today_cache = (None, "")
        self.update_status_bar()

    # ---------- Fenêtre ----------

    def set_fullscreen(self, value):
        self.is_fullscreen = value
        self.root.attributes('-fullscreen', value)
        if not value:
            self.root.state('zoomed') if self.root.tk.call('tk', 'windowingsystem') == 'win32' \
                else self.root.geometry("1200x800")

    def on_close(self):
        if self.controller.get_current_items():
            if not messagebox.askyesno(
                    "Quitter", "Un reçu est en cours et n'a pas été enregistré.\n\nQuitter quand même ?",
                    parent=self.root):
                return
        self.root.destroy()

    def _on_callback_error(self, exc, val, tb):
        detail = "".join(traceback.format_exception(exc, val, tb))
        try:
            print(detail)
        except Exception:
            pass
        messagebox.showerror("Erreur inattendue", f"{val}\n\n{detail[-1500:]}", parent=self.root)

    # ---------- Widgets ----------

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=YES)

        self.create_status_bar(main_frame)

        self.notebook = ttk.Notebook(main_frame, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=(10, 0))

        self.new_receipt_tab = NewReceiptTab(self.notebook, self.controller, self)
        self.history_tab = HistoryTab(self.notebook, self.controller, self)
        self.products_tab = ProductsTab(self.notebook, self.controller, self)
        self.statistics_tab = StatisticsTab(self.notebook, self.controller, self)
        self.settings_tab = SettingsTab(self.notebook, self.controller, self)

        self.notebook.add(self.new_receipt_tab.frame, text="  ➕  Nouveau reçu  ")
        self.notebook.add(self.history_tab.frame, text="  🧾  Historique  ")
        self.notebook.add(self.products_tab.frame, text="  📦  Produits  ")
        self.notebook.add(self.statistics_tab.frame, text="  📊  Statistiques  ")
        self.notebook.add(self.settings_tab.frame, text="  ⚙  Paramètres  ")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        current = self.notebook.index("current")
        if current == 0:
            self.new_receipt_tab.focus_product()
        elif current == 1:
            self.history_tab.focus_search()
        elif current == 3:
            self.statistics_tab.refresh_statistics()

    def create_status_bar(self, parent):
        status_frame = ttk.Frame(parent, bootstyle="dark", padding=(12, 6))
        status_frame.pack(fill=X, side=BOTTOM)

        def label(side, size=10, bold=False):
            lbl = ttk.Label(status_frame, text="", bootstyle="inverse-dark",
                            font=("", size, "bold" if bold else "normal"))
            lbl.pack(side=side, padx=10)
            return lbl

        self.datetime_label = label(LEFT, 11, True)
        self.today_label = label(LEFT, 11, True)

        ttk.Label(status_frame, text="Échap : quitter le plein écran  •  F11 : plein écran",
                  bootstyle="inverse-dark", font=("", 9)).pack(side=RIGHT, padx=10)
        self.ram_label = label(RIGHT)
        self.cpu_label = label(RIGHT)
        self.battery_label = label(RIGHT)

    def _today_summary(self):
        """Résumé des ventes du jour (recalculé au plus toutes les 10 s)"""
        now = datetime.now()
        stamp, text = self._today_cache
        if stamp is None or (now - stamp).total_seconds() >= 10:
            try:
                stats = self.controller.get_statistics()
                currency = self.controller.get_currency()
                count = stats['today_receipts']
                text = (f"Aujourd'hui : {count} reçu{'s' if count > 1 else ''} • "
                        f"{fmt_money(stats['today_sales'], currency)}")
            except Exception:
                text = ""
            self._today_cache = (now, text)
        return text

    def invalidate_today(self):
        self._today_cache = (None, "")

    def update_status_bar(self):
        try:
            now = datetime.now()
            self.datetime_label.config(text=f"{fmt_long_date(now)}  •  {now:%H:%M:%S}")
            self.today_label.config(text=self._today_summary())

            battery = psutil.sensors_battery()
            if battery:
                if battery.power_plugged:
                    text = f"🔌 {battery.percent:.0f}% (en charge)"
                else:
                    text = f"🔋 {battery.percent:.0f}%"
                    secs = battery.secsleft
                    if secs not in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN) and secs > 0:
                        text += f" ({secs // 3600}h{(secs % 3600) // 60:02d})"
                    if battery.percent <= 20:
                        text = "⚠ " + text
                self.battery_label.config(text=text)
            else:
                self.battery_label.config(text="")

            self.cpu_label.config(text=f"CPU {psutil.cpu_percent(interval=0):.0f}%")
            self.ram_label.config(text=f"RAM {psutil.virtual_memory().percent:.0f}%")
        except Exception as e:
            try:
                print(f"Erreur mise à jour statut: {e}")
            except Exception:
                pass

        self.root.after(1000, self.update_status_bar)

    # ---------- Rafraîchissement ----------

    def refresh_all_tabs(self):
        """Rafraîchir tous les onglets après une modification"""
        self.invalidate_today()
        self.history_tab.refresh_history()
        self.products_tab.refresh_products()
        self.statistics_tab.refresh_statistics()
        self.new_receipt_tab.refresh_current_items()
        self.new_receipt_tab.update_receipt_number()
        self.new_receipt_tab.apply_settings()

    def run(self):
        self.root.mainloop()
