"""
Onglet Historique - Version tactile optimisée
Affichage et gestion de l'historique des reçus
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime
import platform
import os


class HistoryTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent)
        self.is_compact_mode = False
        
        self.history_search_var = ttk.StringVar()
        self.history_search_var.trace('w', lambda *args: self.search_history())
        
        self.create_widgets()
        self.refresh_history()
        
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
        self.create_widgets()
        self.refresh_history()
    
    def create_widgets(self):
        """Créer les widgets de l'onglet"""
        # Zone scrollable
        scroll_container = ttk.Frame(self.frame)
        scroll_container.pack(fill=BOTH, expand=YES, padx=8, pady=(8, 0))
        
        # Barre de recherche
        self._create_search_bar(scroll_container)
        
        # Treeview
        self._create_treeview(scroll_container)
        
        # Zone FIXE pour les boutons
        self._create_fixed_buttons()
    
    def _create_search_bar(self, parent):
        """Créer la barre de recherche"""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=X, pady=(0, 10))
        
        font_size = 10 if self.is_compact_mode else 11
        
        if self.is_compact_mode:
            # Version compacte verticale
            ttk.Label(search_frame, text="🔍 Rechercher:", 
                     font=("", font_size, "bold")).pack(anchor=W, pady=2)
            ttk.Entry(search_frame, textvariable=self.history_search_var, 
                     font=("", font_size)).pack(fill=X, ipady=5, pady=2)
            ttk.Button(search_frame, text="🔄 Actualiser", 
                      command=self.refresh_history, bootstyle="info").pack(
                          fill=X, ipady=8, pady=2)
        else:
            # Version normale horizontale
            ttk.Label(search_frame, text="🔍 Rechercher:", 
                     font=("", font_size, "bold")).pack(side=LEFT, padx=5)
            ttk.Entry(search_frame, textvariable=self.history_search_var, 
                     font=("", font_size)).pack(side=LEFT, fill=X, expand=YES, padx=5)
            ttk.Button(search_frame, text="🔄 Actualiser", 
                      command=self.refresh_history, bootstyle="info", 
                      width=15).pack(side=LEFT, padx=5, ipady=8)
    
    def _create_treeview(self, parent):
        """Créer le treeview"""
        if self.is_compact_mode:
            columns = ('N° Reçu', 'Date', 'Total')
            widths = {'N° Reçu': 120, 'Date': 100, 'Total': 100}
        else:
            columns = ('N° Reçu', 'Date', 'Client', 'Total', 'Créé le')
            widths = {'N° Reçu': 130, 'Date': 110, 'Client': 220, 'Total': 130, 'Créé le': 150}
        
        self.history_tree = ttk.Treeview(parent, columns=columns, 
                                         show='headings', height=15, bootstyle="info")
        
        # Style tactile
        style = ttk.Style()
        font_size = 10 if self.is_compact_mode else 11
        style.configure("history.Treeview", font=("", font_size), rowheight=32)
        style.configure("history.Treeview.Heading", font=("", font_size, "bold"))
        self.history_tree.configure(style="history.Treeview")
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            align = E if col == 'Total' else W
            self.history_tree.column(col, width=widths.get(col, 100), anchor=align, minwidth=50)
        
        self.history_tree.pack(fill=BOTH, expand=YES, side=LEFT)
        
        scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=self.history_tree.yview, 
                                 bootstyle="round")
        scrollbar.pack(side=RIGHT, fill=Y, padx=2)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
    
    def _create_fixed_buttons(self):
        """Créer la zone de boutons fixe"""
        ttk.Separator(self.frame, orient=HORIZONTAL).pack(fill=X, padx=8)
        
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, side=BOTTOM, padx=8, pady=8)
        
        if self.is_compact_mode:
            # Boutons empilés
            ttk.Button(btn_frame, text="👁️ Voir détails", 
                      command=self.view_receipt_details, bootstyle="primary").pack(
                          fill=X, ipady=12, pady=2)
            ttk.Button(btn_frame, text="📄 Régénérer PDF", 
                      command=self.regenerate_receipt, bootstyle="success").pack(
                          fill=X, ipady=12, pady=2)
            ttk.Button(btn_frame, text="🖨️ Réimprimer (Thermique)", 
                      command=self.reprint_thermal_receipt, bootstyle="info").pack(
                          fill=X, ipady=12, pady=2)
            ttk.Button(btn_frame, text="🖨️ Réimprimer (Laser A6)", 
                      command=self.reprint_laser_receipt, bootstyle="warning").pack(
                          fill=X, ipady=12, pady=2)
            ttk.Button(btn_frame, text="🗑️ Supprimer", 
                      command=self.delete_receipt, bootstyle="danger").pack(
                          fill=X, ipady=12, pady=2)
            ttk.Button(btn_frame, text="📁 Ouvrir dossier", 
                      command=self.open_exports_folder, bootstyle="secondary").pack(
                          fill=X, ipady=12, pady=2)
        else:
            # Boutons côte à côte (3 lignes)
            # Ligne 1
            row1 = ttk.Frame(btn_frame)
            row1.pack(fill=X, pady=2)
            
            ttk.Button(row1, text="👁️ Voir détails", 
                      command=self.view_receipt_details, bootstyle="primary", 
                      width=18).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            ttk.Button(row1, text="📄 Régénérer PDF", 
                      command=self.regenerate_receipt, bootstyle="success", 
                      width=18).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            
            # Ligne 2
            row2 = ttk.Frame(btn_frame)
            row2.pack(fill=X, pady=2)
            
            ttk.Button(row2, text="🖨️ Thermique", 
                      command=self.reprint_thermal_receipt, bootstyle="info", 
                      width=18).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            ttk.Button(row2, text="🖨️ Laser (A6)", 
                      command=self.reprint_laser_receipt, bootstyle="warning", 
                      width=18).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            
            # Ligne 3
            row3 = ttk.Frame(btn_frame)
            row3.pack(fill=X, pady=2)
            
            ttk.Button(row3, text="🗑️ Supprimer", 
                      command=self.delete_receipt, bootstyle="danger", 
                      width=15).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            ttk.Button(row3, text="📁 Dossier", 
                      command=self.open_exports_folder, bootstyle="secondary", 
                      width=15).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
    
    def refresh_history(self):
        """Rafraîchir l'historique"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        receipts = self.controller.get_all_receipts()
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        for receipt in receipts:
            receipt_id, number, date, client, total, created = receipt
            
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except:
                formatted_date = date
            
            try:
                created_obj = datetime.fromisoformat(created)
                formatted_created = created_obj.strftime('%d/%m/%Y %H:%M')
            except:
                formatted_created = created
            
            if self.is_compact_mode:
                values = (
                    number,
                    formatted_date,
                    f"{total:,.0f}"
                )
            else:
                values = (
                    number,
                    formatted_date,
                    client or "Client",
                    f"{total:,.0f} {currency}",
                    formatted_created
                )
            
            self.history_tree.insert('', 'end', values=values, tags=(receipt_id,))
    
    def search_history(self):
        """Rechercher dans l'historique"""
        query = self.history_search_var.get()
        
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        if query:
            receipts = self.controller.search_receipts(query)
        else:
            receipts = self.controller.get_all_receipts()
        
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        for receipt in receipts:
            receipt_id, number, date, client, total, created = receipt
            
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except:
                formatted_date = date
            
            try:
                created_obj = datetime.fromisoformat(created)
                formatted_created = created_obj.strftime('%d/%m/%Y %H:%M')
            except:
                formatted_created = created
            
            if self.is_compact_mode:
                values = (number, formatted_date, f"{total:,.0f}")
            else:
                values = (number, formatted_date, client or "Client", 
                         f"{total:,.0f} {currency}", formatted_created)
            
            self.history_tree.insert('', 'end', values=values, tags=(receipt_id,))
    
    def view_receipt_details(self):
        """Voir les détails d'un reçu"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un reçu", 
                                 parent=self.frame)
            return
        
        receipt_id = self.history_tree.item(selection[0])['tags'][0]
        receipt = self.controller.get_receipt_details(receipt_id)
        
        if receipt:
            details = f"Reçu: {receipt['receipt_number']}\n"
            details += f"Date: {receipt['date']}\n"
            details += f"Client: {receipt['client_name']}\n"
            if receipt['client_phone']:
                details += f"Téléphone: {receipt['client_phone']}\n"
            details += "\nArticles:\n"
            
            currency = self.controller.db.get_setting('currency', 'Ar')
            for item in receipt['items']:
                details += f"- {item['name']}: {item['quantity']} x {item['unit_price']} = {item['total']} {currency}\n"
            
            details += f"\nTotal: {receipt['total']} {currency}"
            
            messagebox.showinfo("Détails du reçu", details, parent=self.frame)
    
    def regenerate_receipt(self):
        """Régénérer un reçu"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un reçu", 
                                 parent=self.frame)
            return
        
        receipt_id = self.history_tree.item(selection[0])['tags'][0]
        success, result = self.controller.regenerate_receipt(receipt_id)
        
        if success:
            messagebox.showinfo("Succès", f"Reçu régénéré avec succès !\n\n{result}", 
                              parent=self.frame)
            if messagebox.askyesno("Ouvrir", "Voulez-vous ouvrir le reçu ?", 
                                  parent=self.frame):
                self.open_file(result)
        else:
            messagebox.showerror("Erreur", result, parent=self.frame)
    
    def reprint_thermal_receipt(self):
        """Réimprimer un reçu sur l'imprimante thermique"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", 
                                 "Veuillez sélectionner un reçu à réimprimer", 
                                 parent=self.frame)
            return
        
        receipt_id = self.history_tree.item(selection[0])['tags'][0]
        
        if messagebox.askyesno("Confirmation", 
                               "Réimprimer ce reçu sur l'imprimante thermique ?", 
                               parent=self.frame):
            success, message = self.controller.reprint_thermal_receipt(receipt_id)
            
            if success:
                messagebox.showinfo("Succès", message, parent=self.frame)
            else:
                messagebox.showerror("Erreur", message, parent=self.frame)
    
    def reprint_laser_receipt(self):
        """Réimprimer un reçu sur l'imprimante laser (NOUVEAU)"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", 
                                 "Veuillez sélectionner un reçu à réimprimer", 
                                 parent=self.frame)
            return
        
        receipt_id = self.history_tree.item(selection[0])['tags'][0]
        
        if messagebox.askyesno("Confirmation", 
                               "Réimprimer ce reçu sur l'imprimante laser (format A6) ?", 
                               parent=self.frame):
            success, message = self.controller.reprint_laser_receipt(receipt_id)
            
            if success:
                messagebox.showinfo("Succès", message, parent=self.frame)
            else:
                messagebox.showerror("Erreur", message, parent=self.frame)
    
    def delete_receipt(self):
        """Supprimer un reçu"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un reçu", 
                                 parent=self.frame)
            return
        
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce reçu ?", 
                              parent=self.frame):
            receipt_id = self.history_tree.item(selection[0])['tags'][0]
            self.controller.delete_receipt(receipt_id)
            self.refresh_history()
            self.main_window.statistics_tab.refresh_statistics()
            messagebox.showinfo("Succès", "Reçu supprimé avec succès", parent=self.frame)
    
    def open_exports_folder(self):
        """Ouvrir le dossier des exports"""
        exports_path = os.path.abspath('exports')
        
        if not os.path.exists(exports_path):
            os.makedirs(exports_path)
        
        try:
            if platform.system() == 'Windows':
                os.startfile(exports_path)
            elif platform.system() == 'Darwin':
                os.system(f'open "{exports_path}"')
            else:
                os.system(f'xdg-open "{exports_path}"')
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier: {e}", 
                               parent=self.frame)
    
    def open_file(self, filepath):
        """Ouvrir un fichier"""
        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':
                os.system(f'open "{filepath}"')
            else:
                os.system(f'xdg-open "{filepath}"')
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {e}", 
                               parent=self.frame)