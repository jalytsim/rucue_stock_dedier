"""
Onglet Paramètres - Version tactile optimisée
Gestion des paramètres de l'application
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import messagebox


class SettingsTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent)
        self.settings_vars = {}
        self.is_compact_mode = False
        
        self.create_widgets()
        self.load_settings()
        
        # Détecter le redimensionnement
        self.frame.bind('<Configure>', self.on_resize)
    
    def on_resize(self, event):
        """Détecter le redimensionnement"""
        if event.widget == self.frame:
            width = event.width
            should_be_compact = width < 900
            
            if should_be_compact != self.is_compact_mode:
                self.is_compact_mode = should_be_compact
                self.reorganize_layout()
    
    def reorganize_layout(self):
        """Réorganiser le layout"""
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.settings_vars = {}
        self.create_widgets()
        self.load_settings()
    
    def create_widgets(self):
        """Créer les widgets de l'onglet"""
        # Zone scrollable
        container = ScrolledFrame(self.frame, autohide=True)
        container.pack(fill=BOTH, expand=YES, padx=8, pady=(8, 0))
        content = container.container
        
        # Section entreprise
        self._create_company_section(content)
        
        # Section préférences
        self._create_preferences_section(content)
        
        # Section imprimante thermique
        self._create_thermal_printer_section(content)
        
        # Section imprimante LASER (NOUVEAU)
        self._create_laser_printer_section(content)
        
        # Zone dangereuse
        self._create_danger_zone(content)
        
        # Zone FIXE pour le bouton sauvegarder
        self._create_fixed_save_button()
    
    def _create_company_section(self, parent):
        """Section informations entreprise"""
        company_frame = ttk.Labelframe(parent, text="🏢 Informations de l'entreprise", 
                                       bootstyle="primary", padding=10)
        company_frame.pack(fill=X, pady=(0, 10))
        
        font_size = 10 if self.is_compact_mode else 11
        
        settings_fields = [
            ('company_name', 'Nom de l\'entreprise'),
            ('company_address', 'Adresse (\\n pour retours ligne)'),
            ('company_phone', 'Téléphone'),
            ('company_email', 'Email'),
            ('company_nif', 'NIF'),
            ('company_stat', 'STAT'),
            ('company_rc', 'R.C'),
            ('company_ce', 'CE'),
            ('company_cif', 'CIF')
        ]
        
        for key, label in settings_fields:
            if self.is_compact_mode:
                # Mode compact: vertical
                frame = ttk.Frame(company_frame)
                frame.pack(fill=X, pady=3)
                
                ttk.Label(frame, text=label + ":", font=("", font_size, "bold")).pack(
                    anchor=W, pady=1)
                var = ttk.StringVar()
                self.settings_vars[key] = var
                ttk.Entry(frame, textvariable=var, font=("", font_size)).pack(
                    fill=X, ipady=5)
            else:
                # Mode normal: horizontal
                frame = ttk.Frame(company_frame)
                frame.pack(fill=X, pady=4)
                
                ttk.Label(frame, text=label + ":", width=30, anchor=W, 
                         font=("", font_size)).pack(side=LEFT, padx=5)
                var = ttk.StringVar()
                self.settings_vars[key] = var
                ttk.Entry(frame, textvariable=var, font=("", font_size)).pack(
                    side=LEFT, padx=5, fill=X, expand=YES, ipady=4)
    
    def _create_preferences_section(self, parent):
        """Section préférences"""
        pref_frame = ttk.Labelframe(parent, text="⚙️ Préférences", 
                                    bootstyle="info", padding=10)
        pref_frame.pack(fill=X, pady=(0, 10))
        
        font_size = 10 if self.is_compact_mode else 11
        
        # Devise
        if self.is_compact_mode:
            ttk.Label(pref_frame, text="Devise:", font=("", font_size, "bold")).pack(
                anchor=W, pady=1)
            self.settings_vars['currency'] = ttk.StringVar()
            ttk.Combobox(pref_frame, textvariable=self.settings_vars['currency'],
                        values=['Ar', '€', '$', 'FCFA'], font=("", font_size), 
                        state="readonly").pack(fill=X, ipady=5, pady=2)
        else:
            currency_frame = ttk.Frame(pref_frame)
            currency_frame.pack(fill=X, pady=4)
            ttk.Label(currency_frame, text="Devise:", width=30, anchor=W, 
                     font=("", font_size)).pack(side=LEFT, padx=5)
            self.settings_vars['currency'] = ttk.StringVar()
            ttk.Combobox(currency_frame, textvariable=self.settings_vars['currency'],
                        values=['Ar', '€', '$', 'FCFA'], width=20, 
                        state="readonly", font=("", font_size)).pack(side=LEFT, padx=5, ipady=4)
        
        # Largeur papier
        if self.is_compact_mode:
            ttk.Label(pref_frame, text="Largeur papier (mm):", 
                     font=("", font_size, "bold")).pack(anchor=W, pady=1)
            self.settings_vars['paper_width'] = ttk.StringVar()
            ttk.Combobox(pref_frame, textvariable=self.settings_vars['paper_width'],
                        values=['58', '80'], font=("", font_size), 
                        state="readonly").pack(fill=X, ipady=5, pady=2)
        else:
            paper_frame = ttk.Frame(pref_frame)
            paper_frame.pack(fill=X, pady=4)
            ttk.Label(paper_frame, text="Largeur papier (mm):", width=30, anchor=W, 
                     font=("", font_size)).pack(side=LEFT, padx=5)
            self.settings_vars['paper_width'] = ttk.StringVar()
            ttk.Combobox(paper_frame, textvariable=self.settings_vars['paper_width'],
                        values=['58', '80'], width=20, state="readonly", 
                        font=("", font_size)).pack(side=LEFT, padx=5, ipady=4)
        
        # Type de reçu
        if self.is_compact_mode:
            ttk.Label(pref_frame, text="Type de vente:", 
                     font=("", font_size, "bold")).pack(anchor=W, pady=1)
            self.settings_vars['receipt_type'] = ttk.StringVar()
            ttk.Entry(pref_frame, textvariable=self.settings_vars['receipt_type'], 
                     font=("", font_size)).pack(fill=X, ipady=5, pady=2)
        else:
            type_frame = ttk.Frame(pref_frame)
            type_frame.pack(fill=X, pady=4)
            ttk.Label(type_frame, text="Type de vente:", width=30, anchor=W, 
                     font=("", font_size)).pack(side=LEFT, padx=5)
            self.settings_vars['receipt_type'] = ttk.StringVar()
            ttk.Entry(type_frame, textvariable=self.settings_vars['receipt_type'], 
                     font=("", font_size)).pack(side=LEFT, padx=5, fill=X, expand=YES, ipady=4)
    
    def _create_thermal_printer_section(self, parent):
        """Section imprimante thermique"""
        thermal_frame = ttk.Labelframe(parent, text="🖨️ Imprimante Thermique", 
                                      bootstyle="success", padding=10)
        thermal_frame.pack(fill=X, pady=(0, 10))
        
        font_size = 10 if self.is_compact_mode else 11
        
        ttk.Label(thermal_frame, text="Configuration imprimante XP-Q300", 
                 font=("", font_size), bootstyle="secondary").pack(anchor=W, pady=5)
        
        if self.is_compact_mode:
            ttk.Button(thermal_frame, text="🔍 Tester connexion thermique",
                      command=self.test_thermal_connection, 
                      bootstyle="success-outline").pack(fill=X, ipady=8, pady=2)
        else:
            ttk.Button(thermal_frame, text="🔍 Tester connexion thermique",
                      command=self.test_thermal_connection, 
                      bootstyle="success-outline", width=25).pack(pady=5, ipady=8)
    
    def _create_laser_printer_section(self, parent):
        """Section imprimante laser (NOUVEAU)"""
        laser_frame = ttk.Labelframe(parent, text="🖨️ Imprimante Laser", 
                                    bootstyle="warning", padding=10)
        laser_frame.pack(fill=X, pady=(0, 10))
        
        font_size = 10 if self.is_compact_mode else 11
        
        # Activer impression laser
        if self.is_compact_mode:
            laser_enabled_frame = ttk.Frame(laser_frame)
            laser_enabled_frame.pack(fill=X, pady=5)
            
            ttk.Label(laser_enabled_frame, text="Activer impression laser:", 
                     font=("", font_size, "bold")).pack(anchor=W, pady=1)
            
            self.laser_enabled_var = ttk.BooleanVar()
            ttk.Checkbutton(laser_enabled_frame, variable=self.laser_enabled_var, 
                           bootstyle="warning-round-toggle").pack(anchor=W, pady=2)
        else:
            laser_enabled_frame = ttk.Frame(laser_frame)
            laser_enabled_frame.pack(fill=X, pady=5)
            
            ttk.Label(laser_enabled_frame, text="Activer impression laser:", 
                     font=("", font_size)).pack(side=LEFT, padx=(0, 10))
            
            self.laser_enabled_var = ttk.BooleanVar()
            ttk.Checkbutton(laser_enabled_frame, variable=self.laser_enabled_var, 
                           bootstyle="warning-round-toggle").pack(side=LEFT)
        
        # Nom de l'imprimante
        if self.is_compact_mode:
            ttk.Label(laser_frame, text="Nom de l'imprimante:", 
                     font=("", font_size, "bold")).pack(anchor=W, pady=1)
            self.settings_vars['laser_printer_name'] = ttk.StringVar()
            ttk.Entry(laser_frame, textvariable=self.settings_vars['laser_printer_name'], 
                     font=("", font_size)).pack(fill=X, ipady=5, pady=2)
            ttk.Label(laser_frame, text="Ex: HP_LaserJet_1022n", 
                     font=("", 9), bootstyle="secondary").pack(anchor=W)
        else:
            laser_name_frame = ttk.Frame(laser_frame)
            laser_name_frame.pack(fill=X, pady=5)
            
            ttk.Label(laser_name_frame, text="Nom de l'imprimante:", 
                     width=30, anchor=W, font=("", font_size)).pack(side=LEFT, padx=5)
            self.settings_vars['laser_printer_name'] = ttk.StringVar()
            ttk.Entry(laser_name_frame, textvariable=self.settings_vars['laser_printer_name'], 
                     font=("", font_size)).pack(side=LEFT, padx=5, fill=X, expand=YES, ipady=4)
            
            ttk.Label(laser_frame, text="Ex: HP_LaserJet_1022n", 
                     font=("", 9), bootstyle="secondary").pack(anchor=W, padx=5)
        
        # Format papier
        if self.is_compact_mode:
            ttk.Label(laser_frame, text="Format papier:", 
                     font=("", font_size, "bold")).pack(anchor=W, pady=1)
            self.settings_vars['laser_paper_format'] = ttk.StringVar()
            ttk.Combobox(laser_frame, textvariable=self.settings_vars['laser_paper_format'],
                        values=["A6", "A5", "A4"], state="readonly",
                        font=("", font_size)).pack(fill=X, ipady=5, pady=2)
        else:
            format_frame = ttk.Frame(laser_frame)
            format_frame.pack(fill=X, pady=5)
            
            ttk.Label(format_frame, text="Format papier:", 
                     width=30, anchor=W, font=("", font_size)).pack(side=LEFT, padx=5)
            self.settings_vars['laser_paper_format'] = ttk.StringVar()
            ttk.Combobox(format_frame, textvariable=self.settings_vars['laser_paper_format'],
                        values=["A6", "A5", "A4"], state="readonly",
                        font=("", font_size)).pack(side=LEFT, padx=5, fill=X, expand=YES, ipady=4)
        
        # Boutons de test
        if self.is_compact_mode:
            ttk.Button(laser_frame, text="🔍 Tester connexion laser",
                      command=self.test_laser_connection, 
                      bootstyle="warning-outline").pack(fill=X, ipady=8, pady=2)
            
            ttk.Button(laser_frame, text="🖨️ Imprimer test laser",
                      command=self.test_laser_print, 
                      bootstyle="warning").pack(fill=X, ipady=8, pady=2)
        else:
            laser_test_frame = ttk.Frame(laser_frame)
            laser_test_frame.pack(fill=X, pady=(10, 0))
            
            ttk.Button(laser_test_frame, text="🔍 Tester connexion laser",
                      command=self.test_laser_connection, 
                      bootstyle="warning-outline", width=25).pack(side=LEFT, padx=5, ipady=8)
            
            ttk.Button(laser_test_frame, text="🖨️ Imprimer test laser",
                      command=self.test_laser_print, 
                      bootstyle="warning", width=25).pack(side=LEFT, padx=5, ipady=8)
    
    def _create_danger_zone(self, parent):
        """Zone dangereuse"""
        danger_frame = ttk.Labelframe(parent, text="🗑️ Zone dangereuse", 
                                      bootstyle="danger", padding=10)
        danger_frame.pack(fill=X, pady=(0, 10))
        
        font_size = 10 if self.is_compact_mode else 11
        
        ttk.Label(danger_frame, text="⚠️ Ces actions sont irréversibles !", 
                 bootstyle="danger", font=("", font_size, "bold")).pack(pady=8)
        
        if self.is_compact_mode:
            # Boutons empilés
            ttk.Button(danger_frame, text="Effacer l'historique", 
                      command=self.clear_history, bootstyle="danger").pack(
                          fill=X, ipady=10, pady=2)
            ttk.Button(danger_frame, text="Effacer les produits", 
                      command=self.clear_products, bootstyle="danger").pack(
                          fill=X, ipady=10, pady=2)
            ttk.Button(danger_frame, text="Réinitialiser tout", 
                      command=self.reset_all, bootstyle="danger").pack(
                          fill=X, ipady=10, pady=2)
        else:
            # Boutons côte à côte
            btn_frame = ttk.Frame(danger_frame)
            btn_frame.pack()
            
            ttk.Button(btn_frame, text="Effacer l'historique", 
                      command=self.clear_history, bootstyle="danger", 
                      width=18).pack(side=LEFT, padx=3, ipady=8)
            ttk.Button(btn_frame, text="Effacer les produits", 
                      command=self.clear_products, bootstyle="danger", 
                      width=18).pack(side=LEFT, padx=3, ipady=8)
            ttk.Button(btn_frame, text="Réinitialiser tout", 
                      command=self.reset_all, bootstyle="danger", 
                      width=18).pack(side=LEFT, padx=3, ipady=8)
    
    def _create_fixed_save_button(self):
        """Créer le bouton sauvegarder fixe"""
        ttk.Separator(self.frame, orient=HORIZONTAL).pack(fill=X, padx=8)
        
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, side=BOTTOM, padx=8, pady=8)
        
        ttk.Button(btn_frame, text="💾 Enregistrer les paramètres", 
                  command=self.save_settings, bootstyle="success").pack(
                      fill=X, ipady=12)
    
    def load_settings(self):
        """Charger les paramètres"""
        settings = self.controller.get_settings()
        
        for key, var in self.settings_vars.items():
            value = settings.get(key, '')
            if key == 'company_address':
                value = value.replace('\n', '\\n')
            var.set(value)
        
        # Charger les paramètres laser (NOUVEAU)
        self.laser_enabled_var.set(settings.get('laser_enabled', 'true') == 'true')
    
    def save_settings(self):
        """Sauvegarder les paramètres"""
        settings_dict = {}
        
        for key, var in self.settings_vars.items():
            value = var.get()
            if key == 'company_address':
                value = value.replace('\\n', '\n')
            settings_dict[key] = value
        
        # Ajouter les paramètres laser (NOUVEAU)
        settings_dict['laser_enabled'] = 'true' if self.laser_enabled_var.get() else 'false'
        
        self.controller.save_settings(settings_dict)
        messagebox.showinfo("Succès", "Paramètres enregistrés avec succès !", 
                          parent=self.frame)
    
    def test_thermal_connection(self):
        """Tester la connexion à l'imprimante thermique"""
        success, message = self.controller.test_thermal_printer()
        
        if success:
            messagebox.showinfo("Succès", message, parent=self.frame)
        else:
            messagebox.showerror("Erreur", message, parent=self.frame)
    
    def test_laser_connection(self):
        """Tester la connexion à l'imprimante laser (NOUVEAU)"""
        success, message = self.controller.test_laser_printer()
        
        if success:
            messagebox.showinfo("Succès", message, parent=self.frame)
        else:
            messagebox.showerror("Erreur", message, parent=self.frame)
    
    def test_laser_print(self):
        """Imprimer un reçu de test sur l'imprimante laser (NOUVEAU)"""
        try:
            from models.laser_printer import LaserPrinter
            settings = self.controller.get_settings()
            printer = LaserPrinter(settings)
            
            success, message = printer.test_print()
            
            if success:
                messagebox.showinfo("Succès", message, parent=self.frame)
            else:
                messagebox.showerror("Erreur", message, parent=self.frame)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de test: {str(e)}", 
                               parent=self.frame)
    
    def clear_history(self):
        """Effacer l'historique"""
        if messagebox.askyesno("Confirmation", 
                              "⚠️ Supprimer TOUT l'historique ?\n\nCette action est irréversible !", 
                              parent=self.frame):
            self.controller.db.clear_all_receipts()
            self.main_window.history_tab.refresh_history()
            self.main_window.statistics_tab.refresh_statistics()
            messagebox.showinfo("Succès", "Historique effacé avec succès", 
                              parent=self.frame)
    
    def clear_products(self):
        """Effacer les produits"""
        if messagebox.askyesno("Confirmation", 
                              "⚠️ Supprimer TOUS les produits ?\n\nCette action est irréversible !", 
                              parent=self.frame):
            self.controller.db.clear_all_products()
            self.main_window.products_tab.refresh_products()
            self.main_window.statistics_tab.refresh_statistics()
            messagebox.showinfo("Succès", "Produits effacés avec succès", 
                              parent=self.frame)
    
    def reset_all(self):
        """Réinitialiser tout"""
        if messagebox.askyesno("Confirmation", 
                              "⚠️ RÉINITIALISER TOUTES LES DONNÉES ?\n\nCette action est irréversible !", 
                              parent=self.frame):
            if messagebox.askyesno("Dernière confirmation", 
                                  "Êtes-vous VRAIMENT sûr de vouloir tout supprimer ?", 
                                  parent=self.frame):
                self.controller.clear_all_data()
                self.main_window.history_tab.refresh_history()
                self.main_window.products_tab.refresh_products()
                self.main_window.statistics_tab.refresh_statistics()
                self.main_window.new_receipt_tab.reset_form()
                messagebox.showinfo("Succès", "Toutes les données ont été réinitialisées", 
                                  parent=self.frame)