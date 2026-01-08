"""
Onglet Nouveau Reçu - Version optimisée avec boutons fixes visibles
Interface responsive avec zone de boutons toujours accessible
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import messagebox
from datetime import datetime
import platform
import os


class NewReceiptTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        
        # Frame principal
        self.frame = ttk.Frame(parent)
        
        # Variables
        self.search_var = ttk.StringVar()
        self.search_var.trace('w', self.on_product_search)
        
        self.receipt_number_var = ttk.StringVar()
        self.date_var = ttk.StringVar(value=datetime.now().strftime('%d/%m/%Y'))
        self.client_name_var = ttk.StringVar()
        self.client_phone_var = ttk.StringVar()
        self.quantity_var = ttk.StringVar(value="1")
        self.unit_price_var = ttk.StringVar()
        self.total_var = ttk.StringVar(value="0 Ar")
        
        self.autocomplete_listbox = None
        self.is_compact_mode = False
        
        # Créer l'interface
        self.create_widgets()
        
        # Détecter le redimensionnement
        self.frame.bind('<Configure>', self.on_resize)
    
    def on_resize(self, event):
        """Détecter le redimensionnement et réorganiser si nécessaire"""
        if event.widget == self.frame:
            width = event.width
            
            # Seuil pour passer en mode compact (900px)
            should_be_compact = width < 900
            
            if should_be_compact != self.is_compact_mode:
                self.is_compact_mode = should_be_compact
                self.reorganize_layout()
    
    def reorganize_layout(self):
        """Réorganiser complètement le layout selon le mode"""
        # Détruire le contenu existant
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # Recréer avec le bon layout
        self.create_widgets()
    
    def create_widgets(self):
        """Créer les widgets avec zone scrollable et boutons fixes"""
        # Zone scrollable pour le contenu
        scroll_container = ScrolledFrame(self.frame, autohide=True)
        scroll_container.pack(fill=BOTH, expand=YES, padx=8, pady=(8, 0))
        content = scroll_container.container
        
        # Créer le contenu scrollable
        if self.is_compact_mode:
            self._create_compact_content(content)
        else:
            self._create_normal_content(content)
        
        # Zone FIXE pour le total et les boutons (NON scrollable)
        self._create_fixed_footer(self.frame)
    
    def _create_normal_content(self, parent):
        """Contenu normal scrollable"""
        self._create_header_section_normal(parent)
        self._create_product_section_normal(parent)
        self._create_items_list_section(parent, height=4)
    
    def _create_compact_content(self, parent):
        """Contenu compact scrollable"""
        self._create_header_section_compact(parent)
        self._create_product_section_compact(parent)
        self._create_items_list_section(parent, height=3)
    
    # ========== Layout Normal ==========
    
    def _create_header_section_normal(self, parent):
        """En-tête normal avec textes larges"""
        header_frame = ttk.Labelframe(parent, text="📄 Nouveau Reçu", 
                                      bootstyle="primary", padding=10)
        header_frame.pack(fill=X, pady=(0, 10))
        
        # Ligne 1: Numéro et date
        row1 = ttk.Frame(header_frame)
        row1.pack(fill=X, pady=4)
        
        ttk.Label(row1, text="N° Reçu:", font=("", 12, "bold"), width=10).pack(side=LEFT)
        ttk.Entry(row1, textvariable=self.receipt_number_var, 
                 state="readonly", width=15, font=("", 12)).pack(side=LEFT, padx=(0, 15))
        
        ttk.Label(row1, text="Date:", font=("", 12, "bold")).pack(side=LEFT, padx=(0, 8))
        ttk.Entry(row1, textvariable=self.date_var, 
                 state="readonly", width=14, font=("", 12)).pack(side=LEFT)
        
        # Ligne 2: Client
        row2 = ttk.Frame(header_frame)
        row2.pack(fill=X, pady=4)
        
        ttk.Label(row2, text="Client:", font=("", 12, "bold"), width=10).pack(side=LEFT)
        ttk.Entry(row2, textvariable=self.client_name_var, 
                 font=("", 12)).pack(side=LEFT, fill=X, expand=YES, padx=(0, 15))
        
        ttk.Label(row2, text="Téléphone:", font=("", 12, "bold")).pack(side=LEFT, padx=(0, 8))
        ttk.Entry(row2, textvariable=self.client_phone_var, 
                 width=16, font=("", 12)).pack(side=LEFT)
    
    def _create_product_section_normal(self, parent):
        """Section produit avec champs et boutons larges"""
        product_frame = ttk.Labelframe(parent, text="🛒 Ajouter Article", 
                                       bootstyle="success", padding=10)
        product_frame.pack(fill=X, pady=(0, 10))
        
        # Suggestion
        self.suggestion_label = ttk.Label(product_frame, text="", 
                                         bootstyle="info", font=("", 10, "italic"))
        self.suggestion_label.pack(fill=X, pady=(0, 6))
        
        # Ligne 1: Produit
        row1 = ttk.Frame(product_frame)
        row1.pack(fill=X, pady=4)
        
        ttk.Label(row1, text="Produit:", font=("", 12, "bold"), width=10).pack(side=LEFT)
        self.product_name_entry = ttk.Entry(row1, textvariable=self.search_var, 
                                            font=("", 12))
        self.product_name_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 8))
        
        # Autocomplétion
        self.autocomplete_frame = ttk.Frame(product_frame)
        self.autocomplete_frame.pack(fill=X, pady=4)
        
        # Ligne 2: Quantité et Prix
        row2 = ttk.Frame(product_frame)
        row2.pack(fill=X, pady=4)
        
        ttk.Label(row2, text="Quantité:", font=("", 12, "bold"), width=10).pack(side=LEFT)
        ttk.Spinbox(row2, from_=1, to=10000, textvariable=self.quantity_var, 
                   width=12, font=("", 12)).pack(side=LEFT, padx=(0, 15))
        
        ttk.Label(row2, text="Prix Unit.:", font=("", 12, "bold")).pack(side=LEFT, padx=(0, 8))
        ttk.Entry(row2, textvariable=self.unit_price_var, 
                 width=16, font=("", 12)).pack(side=LEFT, fill=X, expand=YES)
        
        # BOUTON TACTILE LARGE
        ttk.Button(product_frame, text="➕ AJOUTER L'ARTICLE", command=self.add_item, 
                  bootstyle="success").pack(fill=X, ipady=10, pady=(6, 0))
    
    # ========== Layout Compact ==========
    
    def _create_header_section_compact(self, parent):
        """En-tête compact avec champs TACTILES"""
        header_frame = ttk.Labelframe(parent, text="📄 Reçu", 
                                      bootstyle="primary", padding=8)
        header_frame.pack(fill=X, pady=(0, 8))
        
        # Tout en vertical avec espacement tactile
        for label, var in [
            ("N° Reçu:", self.receipt_number_var),
            ("Date:", self.date_var),
            ("Client:", self.client_name_var),
            ("Téléphone:", self.client_phone_var)
        ]:
            row = ttk.Frame(header_frame)
            row.pack(fill=X, pady=3)
            ttk.Label(row, text=label, font=("", 11, "bold")).pack(anchor=W, pady=1)
            state = "readonly" if label in ["N° Reçu:", "Date:"] else "normal"
            entry = ttk.Entry(row, textvariable=var, state=state, font=("", 11))
            entry.pack(fill=X, ipady=5)
    
    def _create_product_section_compact(self, parent):
        """Section produit compacte TACTILE"""
        product_frame = ttk.Labelframe(parent, text="🛒 Article", 
                                       bootstyle="success", padding=8)
        product_frame.pack(fill=X, pady=(0, 8))
        
        # Suggestion
        self.suggestion_label = ttk.Label(product_frame, text="", 
                                         bootstyle="info", font=("", 9, "italic"))
        self.suggestion_label.pack(fill=X, pady=(0, 4))
        
        # Produit
        ttk.Label(product_frame, text="Produit:", font=("", 11, "bold")).pack(anchor=W, pady=1)
        self.product_name_entry = ttk.Entry(product_frame, textvariable=self.search_var, 
                                            font=("", 11))
        self.product_name_entry.pack(fill=X, ipady=5, pady=2)
        
        # Autocomplétion
        self.autocomplete_frame = ttk.Frame(product_frame)
        self.autocomplete_frame.pack(fill=X, pady=2)
        
        # Quantité
        ttk.Label(product_frame, text="Quantité:", font=("", 11, "bold")).pack(anchor=W, pady=1)
        ttk.Spinbox(product_frame, from_=1, to=10000, textvariable=self.quantity_var, 
                   font=("", 11)).pack(fill=X, ipady=5, pady=2)
        
        # Prix
        ttk.Label(product_frame, text="Prix Unitaire:", font=("", 11, "bold")).pack(anchor=W, pady=1)
        ttk.Entry(product_frame, textvariable=self.unit_price_var, 
                 font=("", 11)).pack(fill=X, ipady=5, pady=2)
        
        # BOUTON TACTILE PLEINE LARGEUR
        ttk.Button(product_frame, text="➕ AJOUTER", command=self.add_item, 
                  bootstyle="success").pack(fill=X, ipady=10, pady=(6, 0))
    
    # ========== Section Liste ==========
    
    def _create_items_list_section(self, parent, height=4):
        """Section liste des articles avec lignes TACTILES"""
        items_frame = ttk.Labelframe(parent, text="📋 Articles du Reçu", 
                                     bootstyle="secondary", padding=8)
        items_frame.pack(fill=BOTH, expand=YES, pady=(0, 8))
        
        # Style de police pour le tableau
        style = ttk.Style()
        
        # Treeview avec hauteur de ligne tactile
        if self.is_compact_mode:
            columns = ('Produit', 'Qté', 'Prix', 'Total')
            widths = {'Produit': 140, 'Qté': 45, 'Prix': 75, 'Total': 75}
            font_size = 10
        else:
            columns = ('Produit', 'Qté', 'Prix Unit.', 'Total')
            widths = {'Produit': 280, 'Qté': 70, 'Prix Unit.': 110, 'Total': 110}
            font_size = 11
        
        self.items_tree = ttk.Treeview(items_frame, columns=columns, 
                                       show='headings', height=height, bootstyle="info")
        
        # Configuration avec police plus grande
        style.configure("Treeview", font=("", font_size), rowheight=32)
        style.configure("Treeview.Heading", font=("", font_size, "bold"))
        
        for col in columns:
            self.items_tree.heading(col, text=col)
            align = CENTER if col == 'Qté' else (E if 'Prix' in col or 'Total' in col else W)
            self.items_tree.column(col, width=widths.get(col, 100), anchor=align, minwidth=50)
        
        self.items_tree.pack(fill=BOTH, expand=YES, side=LEFT)
        
        # Scrollbar LARGE pour tactile
        scrollbar = ttk.Scrollbar(items_frame, orient=VERTICAL, command=self.items_tree.yview, 
                                 bootstyle="round")
        scrollbar.pack(side=RIGHT, fill=Y, padx=2)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        
        # Boutons TACTILES
        items_btn_frame = ttk.Frame(items_frame)
        items_btn_frame.pack(fill=X, pady=(6, 0))
        
        if self.is_compact_mode:
            ttk.Button(items_btn_frame, text="🗑️ Retirer", command=self.remove_item, 
                      bootstyle="danger").pack(fill=X, ipady=8, pady=1)
            ttk.Button(items_btn_frame, text="🔄 Vider", command=self.clear_items, 
                      bootstyle="warning").pack(fill=X, ipady=8, pady=1)
        else:
            ttk.Button(items_btn_frame, text="🗑️ Retirer l'Article", command=self.remove_item, 
                      bootstyle="danger", width=18).pack(side=LEFT, padx=3, ipady=8)
            ttk.Button(items_btn_frame, text="🔄 Vider Tout", command=self.clear_items, 
                      bootstyle="warning", width=18).pack(side=LEFT, padx=3, ipady=8)
    
    # ========== Zone FIXE (non scrollable) ==========
    
    def _create_fixed_footer(self, parent):
        """Footer FIXE avec total et boutons toujours visibles"""
        # Séparateur
        ttk.Separator(parent, orient=HORIZONTAL).pack(fill=X, padx=8)
        
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill=X, side=BOTTOM, padx=8, pady=8)
        
        # Total GRAND et VISIBLE
        total_frame = ttk.Frame(footer_frame, bootstyle="primary")
        total_frame.pack(fill=X, pady=(0, 8))
        
        total_label_size = 12 if self.is_compact_mode else 13
        total_value_size = 22 if self.is_compact_mode else 26
        
        ttk.Label(total_frame, text="TOTAL À PAYER", 
                 font=("", total_label_size, "bold"), bootstyle="inverse-primary", 
                 anchor=CENTER, padding=6).pack(fill=X)
        
        ttk.Label(total_frame, textvariable=self.total_var, 
                 font=("", total_value_size, "bold"), bootstyle="primary", 
                 anchor=CENTER, padding=8).pack(fill=X)
        
        # Actions TACTILES TOUJOURS VISIBLES
        if self.is_compact_mode:
            # Mode compact: boutons empilés
            ttk.Button(footer_frame, text="🖨️ Imprimer Thermique", 
                      command=self.print_thermal, bootstyle="info").pack(
                          fill=X, ipady=12, pady=2)
            
            ttk.Button(footer_frame, text="📄 Générer le PDF", 
                      command=self.generate_receipt, bootstyle="primary").pack(
                          fill=X, ipady=12, pady=2)
            
            ttk.Button(footer_frame, text="💾 Enregistrer", 
                      command=self.save_receipt_only, bootstyle="success").pack(
                          fill=X, ipady=12, pady=2)
            
            ttk.Button(footer_frame, text="🔄 Nouveau Reçu", 
                      command=self.reset_form, bootstyle="secondary").pack(
                          fill=X, ipady=12, pady=2)
        else:
            # Mode normal: boutons côte à côte (2 lignes)
            action_frame1 = ttk.Frame(footer_frame)
            action_frame1.pack(fill=X, pady=2)
            
            ttk.Button(action_frame1, text="🖨️ Imprimer Thermique", 
                      command=self.print_thermal, bootstyle="info", 
                      width=25).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            
            ttk.Button(action_frame1, text="📄 Générer PDF", 
                      command=self.generate_receipt, bootstyle="primary", 
                      width=20).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            
            action_frame2 = ttk.Frame(footer_frame)
            action_frame2.pack(fill=X, pady=2)
            
            ttk.Button(action_frame2, text="💾 Enregistrer", 
                      command=self.save_receipt_only, bootstyle="success", 
                      width=20).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
            
            ttk.Button(action_frame2, text="🔄 Nouveau", 
                      command=self.reset_form, bootstyle="secondary", 
                      width=18).pack(side=LEFT, padx=3, ipady=10, fill=X, expand=YES)
    
    # ========== Méthodes fonctionnelles ==========
    
    def on_product_search(self, *args):
        """Gérer la recherche de produits avec résultats TACTILES"""
        query = self.search_var.get()
        
        if not query:
            if self.autocomplete_listbox:
                self.autocomplete_listbox.destroy()
                self.autocomplete_listbox = None
            self.suggestion_label.config(text="")
            return
        
        products = self.controller.search_products(query)
        
        if products:
            if not self.autocomplete_listbox:
                max_height = 3
                self.autocomplete_listbox = ttk.Treeview(
                    self.autocomplete_frame, columns=('name', 'price'),
                    show='tree headings', height=min(max_height, len(products)), 
                    bootstyle="info")
                
                # Police tactile pour autocomplétion
                font_size = 10 if self.is_compact_mode else 11
                style = ttk.Style()
                style.configure("autocomplete.Treeview", font=("", font_size), rowheight=35)
                self.autocomplete_listbox.configure(style="autocomplete.Treeview")
                
                self.autocomplete_listbox.heading('name', text='Produit')
                self.autocomplete_listbox.heading('price', text='Prix')
                self.autocomplete_listbox.column('#0', width=0, stretch=NO)
                width1 = 200 if self.is_compact_mode else 300
                width2 = 90 if self.is_compact_mode else 110
                self.autocomplete_listbox.column('name', width=width1)
                self.autocomplete_listbox.column('price', width=width2)
                self.autocomplete_listbox.pack(fill=X, pady=3)
                self.autocomplete_listbox.bind('<<TreeviewSelect>>', self.on_autocomplete_select)
            
            for item in self.autocomplete_listbox.get_children():
                self.autocomplete_listbox.delete(item)
            
            for product in products:
                name, price, count, last_used = product
                self.autocomplete_listbox.insert('', 'end', values=(name, f"{price:.0f} Ar"))
        else:
            if self.autocomplete_listbox:
                self.autocomplete_listbox.destroy()
                self.autocomplete_listbox = None
            self.suggestion_label.config(text="")
    
    def on_autocomplete_select(self, event):
        """Sélection dans l'autocomplétion"""
        selection = self.autocomplete_listbox.selection()
        if selection:
            item = self.autocomplete_listbox.item(selection[0])
            values = item['values']
            
            product_name = values[0]
            price_text = values[1].replace(' Ar', '')
            
            self.search_var.set(product_name)
            self.unit_price_var.set(price_text)
            self.suggestion_label.config(text=f"💡 Prix: {price_text} Ar")
            
            if self.autocomplete_listbox:
                self.autocomplete_listbox.destroy()
                self.autocomplete_listbox = None
            
            self.quantity_var.set("1")
    
    def add_item(self):
        """Ajouter un article"""
        name = self.search_var.get().strip()
        
        if not name:
            messagebox.showwarning("Attention", "Veuillez entrer un nom de produit", 
                                 parent=self.frame)
            return
        
        try:
            quantity = float(self.quantity_var.get())
            unit_price = float(self.unit_price_var.get())
        except ValueError:
            messagebox.showerror("Erreur", "La quantité et le prix doivent être des nombres valides", 
                               parent=self.frame)
            return
        
        success, result = self.controller.add_item(name, quantity, unit_price)
        
        if success:
            self.refresh_current_items()
            self.search_var.set("")
            self.quantity_var.set("1")
            self.unit_price_var.set("")
            self.suggestion_label.config(text="")
            self.product_name_entry.focus()
        else:
            messagebox.showerror("Erreur", result, parent=self.frame)
    
    def remove_item(self):
        """Retirer un article"""
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un article à retirer", 
                                 parent=self.frame)
            return
        
        index = self.items_tree.index(selection[0])
        self.controller.remove_item(index)
        self.refresh_current_items()
    
    def clear_items(self):
        """Vider tous les articles"""
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment vider tous les articles ?", 
                              parent=self.frame):
            self.controller.clear_current_items()
            self.refresh_current_items()
    
    def refresh_current_items(self):
        """Rafraîchir l'affichage des articles"""
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        items = self.controller.get_current_items()
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        for item in items:
            self.items_tree.insert('', 'end', values=(
                item['name'],
                f"{item['quantity']:.0f}",
                f"{item['unit_price']:,.0f}",
                f"{item['total']:,.0f}"
            ))
        
        total = self.controller.get_current_total()
        self.total_var.set(f"{total:,.0f} {currency}")
    
    def print_thermal(self):
        """Imprimer sur l'imprimante thermique"""
        if not self.controller.get_current_items():
            messagebox.showwarning("Attention", "Veuillez ajouter au moins un article", 
                                 parent=self.frame)
            return
        
        client_name = self.client_name_var.get().strip()
        client_phone = self.client_phone_var.get().strip()
        
        # Demander confirmation
        if not messagebox.askyesno("Confirmation", 
                                   "Imprimer ce reçu sur l'imprimante thermique ?", 
                                   parent=self.frame):
            return
        
        success, result = self.controller.print_thermal_receipt(
            client_name=client_name or "Client",
            client_phone=client_phone,
            payment_method="Espèces"
        )
        
        if success:
            messagebox.showinfo("Succès", result, parent=self.frame)
            self.reset_form()
            self.main_window.refresh_all_tabs()
        else:
            messagebox.showerror("Erreur", result, parent=self.frame)
    
    def generate_receipt(self):
        """Générer et enregistrer le reçu"""
        client_name = self.client_name_var.get().strip()
        client_phone = self.client_phone_var.get().strip()
        
        success, result = self.controller.save_and_generate_receipt(
            client_name=client_name or "Client",
            client_phone=client_phone,
            payment_method="Espèces"
        )
        
        if success:
            messagebox.showinfo("Succès", f"Reçu généré avec succès !\n\nFichier: {result}", 
                              parent=self.frame)
            self.reset_form()
            self.main_window.refresh_all_tabs()
            
            if messagebox.askyesno("Ouvrir le reçu", "Voulez-vous ouvrir le reçu PDF ?", 
                                  parent=self.frame):
                self.open_file(result)
        else:
            messagebox.showerror("Erreur", result, parent=self.frame)
    
    def save_receipt_only(self):
        """Enregistrer sans générer le PDF"""
        if not self.controller.get_current_items():
            messagebox.showwarning("Attention", "Veuillez ajouter au moins un article", 
                                 parent=self.frame)
            return
        
        messagebox.showinfo("Information", "Enregistrement direct en cours de développement...", 
                          parent=self.frame)
    
    def reset_form(self):
        """Réinitialiser le formulaire"""
        self.controller.clear_current_items()
        self.client_name_var.set("")
        self.client_phone_var.set("")
        self.search_var.set("")
        self.quantity_var.set("1")
        self.unit_price_var.set("")
        self.suggestion_label.config(text="")
        self.refresh_current_items()
        self.update_receipt_number()
    
    def update_receipt_number(self):
        """Mettre à jour le numéro de reçu"""
        number = self.controller.db.get_next_receipt_number()
        self.receipt_number_var.set(number)
    
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