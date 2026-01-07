"""
Onglet Produits - Version tactile optimisée
Gestion de la base de données des produits
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime


class ProductsTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent)
        self.is_compact_mode = False
        
        self.create_widgets()
        self.refresh_products()
        
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
        self.refresh_products()
    
    def create_widgets(self):
        """Créer les widgets de l'onglet"""
        # Zone scrollable
        scroll_container = ttk.Frame(self.frame)
        scroll_container.pack(fill=BOTH, expand=YES, padx=8, pady=(8, 0))
        
        # Info
        info_frame = ttk.Frame(scroll_container)
        info_frame.pack(fill=X, pady=(0, 10))
        
        font_size = 10 if self.is_compact_mode else 11
        ttk.Label(info_frame, 
                 text="📦 Base de données des produits - Apprentissage automatique",
                 font=("", font_size, "bold"), bootstyle="info").pack()
        
        # Treeview
        if self.is_compact_mode:
            columns = ('Produit', 'Prix', 'Qté')
            widths = {'Produit': 200, 'Prix': 90, 'Qté': 60}
        else:
            columns = ('Produit', 'Prix moyen', 'Utilisé', 'Dernière utilisation')
            widths = {'Produit': 350, 'Prix moyen': 130, 'Utilisé': 100, 'Dernière utilisation': 160}
        
        self.products_tree = ttk.Treeview(scroll_container, columns=columns, 
                                          show='headings', height=15, bootstyle="info")
        
        # Style tactile
        style = ttk.Style()
        font_size = 10 if self.is_compact_mode else 11
        style.configure("products.Treeview", font=("", font_size), rowheight=32)
        style.configure("products.Treeview.Heading", font=("", font_size, "bold"))
        self.products_tree.configure(style="products.Treeview")
        
        for col in columns:
            self.products_tree.heading(col, text=col)
            if col == 'Produit':
                align = W
            elif col in ['Utilisé', 'Qté']:
                align = CENTER
            else:
                align = E
            self.products_tree.column(col, width=widths.get(col, 100), anchor=align, minwidth=50)
        
        self.products_tree.pack(fill=BOTH, expand=YES, side=LEFT)
        
        # Scrollbar tactile
        scrollbar = ttk.Scrollbar(scroll_container, orient=VERTICAL, 
                                 command=self.products_tree.yview, bootstyle="round")
        scrollbar.pack(side=RIGHT, fill=Y, padx=2)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        
        # Zone FIXE pour les boutons
        self._create_fixed_buttons()
    
    def _create_fixed_buttons(self):
        """Créer la zone de boutons fixe"""
        ttk.Separator(self.frame, orient=HORIZONTAL).pack(fill=X, padx=8)
        
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, side=BOTTOM, padx=8, pady=8)
        
        if self.is_compact_mode:
            # Boutons empilés
            ttk.Button(btn_frame, text="🔄 Actualiser", 
                      command=self.refresh_products, bootstyle="info").pack(
                          fill=X, ipady=12, pady=2)
            ttk.Button(btn_frame, text="🗑️ Supprimer", 
                      command=self.delete_product, bootstyle="danger").pack(
                          fill=X, ipady=12, pady=2)
        else:
            # Boutons côte à côte
            ttk.Button(btn_frame, text="🔄 Actualiser", 
                      command=self.refresh_products, bootstyle="info", 
                      width=20).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            ttk.Button(btn_frame, text="🗑️ Supprimer le produit", 
                      command=self.delete_product, bootstyle="danger", 
                      width=20).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
    
    def refresh_products(self):
        """Rafraîchir la liste des produits"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        products = self.controller.get_all_products()
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        for product in products:
            product_id, name, avg_price, count, total_sold, last_used = product
            
            try:
                last_used_obj = datetime.fromisoformat(last_used)
                formatted_last = last_used_obj.strftime('%d/%m/%Y %H:%M')
            except:
                formatted_last = last_used or "N/A"
            
            if self.is_compact_mode:
                values = (
                    name,
                    f"{avg_price:,.0f}",
                    f"{count}"
                )
            else:
                values = (
                    name,
                    f"{avg_price:,.0f} {currency}",
                    f"{count} fois",
                    formatted_last
                )
            
            self.products_tree.insert('', 'end', values=values, tags=(product_id,))
    
    def delete_product(self):
        """Supprimer un produit"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit", 
                                 parent=self.frame)
            return
        
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce produit ?", 
                              parent=self.frame):
            product_id = self.products_tree.item(selection[0])['tags'][0]
            self.controller.delete_product(product_id)
            self.refresh_products()
            self.main_window.statistics_tab.refresh_statistics()
            messagebox.showinfo("Succès", "Produit supprimé avec succès", parent=self.frame)