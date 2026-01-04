"""
Interface graphique principale avec ttkbootstrap
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import messagebox, filedialog
import os
import platform
from datetime import datetime

class MainWindow:
    def __init__(self, controller):
        self.controller = controller
        
        # Créer la fenêtre principale
        self.root = ttk.Window(
            title="💼 Générateur de Reçus Pro",
            themename="cosmo",  # Theme moderne: cosmo, flatly, litera, minty, lumen
            size=(1400, 900)
        )
        
        # Centrer la fenêtre
        self.root.place_window_center()
        
        # Variables
        self.search_var = ttk.StringVar()
        self.search_var.trace('w', self.on_product_search)
        
        # Créer l'interface
        self.create_widgets()
        
        # Charger les données initiales
        self.refresh_current_items()
        self.update_receipt_number()
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Onglets
        self.create_new_receipt_tab()
        self.create_history_tab()
        self.create_products_tab()
        self.create_statistics_tab()
        self.create_settings_tab()
    
    def create_new_receipt_tab(self):
        """Onglet nouvelle facture"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="➕ Nouveau Reçu")
        
        # Container principal avec scroll
        container = ScrolledFrame(tab, autohide=True)
        container.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Frame pour le contenu
        content = container.container
        
        # ========== Section 1: Informations du reçu ==========
        info_frame = ttk.Labelframe(content, text="📄 Informations du reçu", bootstyle="primary", padding=15)
        info_frame.pack(fill=X, pady=(0, 15))
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=X)
        
        # Numéro de reçu
        ttk.Label(info_grid, text="N° Reçu:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.receipt_number_var = ttk.StringVar()
        receipt_entry = ttk.Entry(info_grid, textvariable=self.receipt_number_var, state="readonly", width=20, font=("Helvetica", 10))
        receipt_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        # Date
        ttk.Label(info_grid, text="Date:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky=W, padx=15, pady=5)
        self.date_var = ttk.StringVar(value=datetime.now().strftime('%d/%m/%Y'))
        date_entry = ttk.Entry(info_grid, textvariable=self.date_var, state="readonly", width=15, font=("Helvetica", 10))
        date_entry.grid(row=0, column=3, sticky=W, padx=5, pady=5)
        
        # ========== Section 2: Informations client ==========
        client_frame = ttk.Labelframe(content, text="👤 Informations Client (Optionnel)", bootstyle="info", padding=15)
        client_frame.pack(fill=X, pady=(0, 15))
        
        client_grid = ttk.Frame(client_frame)
        client_grid.pack(fill=X)
        
        # Nom du client
        ttk.Label(client_grid, text="Nom du client:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.client_name_var = ttk.StringVar()
        ttk.Entry(client_grid, textvariable=self.client_name_var, width=35).grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        # Téléphone
        ttk.Label(client_grid, text="Téléphone:").grid(row=0, column=2, sticky=W, padx=15, pady=5)
        self.client_phone_var = ttk.StringVar()
        ttk.Entry(client_grid, textvariable=self.client_phone_var, width=25).grid(row=0, column=3, sticky=W, padx=5, pady=5)
        
        # ========== Section 3: Ajouter des articles ==========
        product_frame = ttk.Labelframe(content, text="🛒 Ajouter des Articles", bootstyle="success", padding=15)
        product_frame.pack(fill=X, pady=(0, 15))
        
        # Suggestion de produit
        self.suggestion_label = ttk.Label(product_frame, text="", bootstyle="info", font=("Helvetica", 9, "italic"))
        self.suggestion_label.pack(fill=X, pady=(0, 10))
        
        product_grid = ttk.Frame(product_frame)
        product_grid.pack(fill=X)
        
        # Nom du produit avec autocomplétion
        ttk.Label(product_grid, text="Nom du produit:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.product_name_entry = ttk.Entry(product_grid, textvariable=self.search_var, width=40, font=("Helvetica", 10))
        self.product_name_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        # Liste déroulante pour autocomplétion
        self.autocomplete_frame = ttk.Frame(product_grid)
        self.autocomplete_frame.grid(row=1, column=1, sticky=W+E, padx=5)
        self.autocomplete_listbox = None
        
        # Quantité
        ttk.Label(product_grid, text="Quantité:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky=W, padx=15, pady=5)
        self.quantity_var = ttk.StringVar(value="1")
        quantity_spin = ttk.Spinbox(product_grid, from_=1, to=10000, textvariable=self.quantity_var, width=15)
        quantity_spin.grid(row=0, column=3, sticky=W, padx=5, pady=5)
        
        # Prix unitaire
        ttk.Label(product_grid, text="Prix Unitaire:", font=("Helvetica", 10, "bold")).grid(row=0, column=4, sticky=W, padx=15, pady=5)
        self.unit_price_var = ttk.StringVar()
        unit_price_entry = ttk.Entry(product_grid, textvariable=self.unit_price_var, width=20, font=("Helvetica", 10))
        unit_price_entry.grid(row=0, column=5, sticky=W, padx=5, pady=5)
        
        # Bouton ajouter
        add_btn = ttk.Button(
            product_frame, 
            text="➕ Ajouter l'article",
            command=self.add_item,
            bootstyle="success",
            width=20
        )
        add_btn.pack(pady=(10, 0))
        
        # ========== Section 4: Liste des articles ==========
        items_frame = ttk.Labelframe(content, text="📋 Articles du reçu", bootstyle="secondary", padding=15)
        items_frame.pack(fill=BOTH, expand=YES, pady=(0, 15))
        
        # Treeview pour les articles
        columns = ('Produit', 'Qté', 'Prix Unit.', 'Total')
        self.items_tree = ttk.Treeview(items_frame, columns=columns, show='headings', height=8, bootstyle="info")
        
        for col in columns:
            self.items_tree.heading(col, text=col)
        
        # Largeurs des colonnes
        self.items_tree.column('Produit', width=400)
        self.items_tree.column('Qté', width=100, anchor=CENTER)
        self.items_tree.column('Prix Unit.', width=150, anchor=E)
        self.items_tree.column('Total', width=150, anchor=E)
        
        self.items_tree.pack(fill=BOTH, expand=YES, side=LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=VERTICAL, command=self.items_tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        
        # Boutons pour gérer les articles
        items_btn_frame = ttk.Frame(items_frame)
        items_btn_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(items_btn_frame, text="🗑️ Retirer l'article", command=self.remove_item, bootstyle="danger").pack(side=LEFT, padx=5)
        ttk.Button(items_btn_frame, text="🔄 Vider tout", command=self.clear_items, bootstyle="warning").pack(side=LEFT)
        
        # ========== Section 5: Total ==========
        total_frame = ttk.Frame(content)
        total_frame.pack(fill=X, pady=(0, 15))
        
        total_label_frame = ttk.Label(
            total_frame, 
            text="TOTAL À PAYER",
            font=("Helvetica", 16, "bold"),
            bootstyle="inverse-primary",
            anchor=CENTER,
            padding=10
        )
        total_label_frame.pack(fill=X)
        
        self.total_var = ttk.StringVar(value="0 Ar")
        total_amount = ttk.Label(
            total_frame,
            textvariable=self.total_var,
            font=("Helvetica", 32, "bold"),
            bootstyle="primary",
            anchor=CENTER,
            padding=10
        )
        total_amount.pack(fill=X)
        
        # ========== Section 6: Actions ==========
        action_frame = ttk.Frame(content)
        action_frame.pack(fill=X)
        
        ttk.Button(
            action_frame, 
            text="📄 Générer et Enregistrer le Reçu",
            command=self.generate_receipt,
            bootstyle="primary",
            width=30
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="💾 Enregistrer sans PDF",
            command=self.save_receipt_only,
            bootstyle="success",
            width=25
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="🔄 Nouveau Reçu",
            command=self.reset_form,
            bootstyle="secondary",
            width=20
        ).pack(side=LEFT, padx=5)
    
    def create_history_tab(self):
        """Onglet historique"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Historique")
        
        # Container
        container = ttk.Frame(tab)
        container.pack(fill=BOTH, expand=YES, padx=15, pady=15)
        
        # Barre de recherche
        search_frame = ttk.Frame(container)
        search_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(search_frame, text="🔍 Rechercher:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=5)
        self.history_search_var = ttk.StringVar()
        self.history_search_var.trace('w', lambda *args: self.search_history())
        ttk.Entry(search_frame, textvariable=self.history_search_var, width=50).pack(side=LEFT, padx=5)
        
        ttk.Button(search_frame, text="🔄 Actualiser", command=self.refresh_history, bootstyle="info").pack(side=LEFT, padx=5)
        
        # Treeview pour l'historique
        columns = ('N° Reçu', 'Date', 'Client', 'Total', 'Créé le')
        self.history_tree = ttk.Treeview(container, columns=columns, show='headings', height=20, bootstyle="info")
        
        for col in columns:
            self.history_tree.heading(col, text=col)
        
        self.history_tree.column('N° Reçu', width=150)
        self.history_tree.column('Date', width=120)
        self.history_tree.column('Client', width=250)
        self.history_tree.column('Total', width=150, anchor=E)
        self.history_tree.column('Créé le', width=180)
        
        self.history_tree.pack(fill=BOTH, expand=YES, side=LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient=VERTICAL, command=self.history_tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Boutons d'action
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        ttk.Button(btn_frame, text="👁️ Voir les détails", command=self.view_receipt_details, bootstyle="primary").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="📄 Régénérer PDF", command=self.regenerate_receipt, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Supprimer", command=self.delete_receipt, bootstyle="danger").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="📁 Ouvrir dossier exports", command=self.open_exports_folder, bootstyle="info").pack(side=LEFT, padx=5)
        
        # Charger l'historique
        self.refresh_history()
    
    def create_products_tab(self):
        """Onglet produits"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📦 Produits")
        
        container = ttk.Frame(tab)
        container.pack(fill=BOTH, expand=YES, padx=15, pady=15)
        
        # Info
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            info_frame,
            text="📦 Base de données des produits - L'application apprend automatiquement",
            font=("Helvetica", 11, "bold"),
            bootstyle="info"
        ).pack()
        
        # Treeview
        columns = ('Produit', 'Prix moyen', 'Utilisé', 'Dernière utilisation')
        self.products_tree = ttk.Treeview(container, columns=columns, show='headings', height=20, bootstyle="info")
        
        for col in columns:
            self.products_tree.heading(col, text=col)
        
        self.products_tree.column('Produit', width=400)
        self.products_tree.column('Prix moyen', width=150, anchor=E)
        self.products_tree.column('Utilisé', width=120, anchor=CENTER)
        self.products_tree.column('Dernière utilisation', width=180)
        
        self.products_tree.pack(fill=BOTH, expand=YES, side=LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient=VERTICAL, command=self.products_tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        
        # Boutons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        ttk.Button(btn_frame, text="🔄 Actualiser", command=self.refresh_products, bootstyle="info").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Supprimer le produit", command=self.delete_product, bootstyle="danger").pack(side=LEFT, padx=5)
        
        self.refresh_products()
    
    def create_statistics_tab(self):
        """Onglet statistiques"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Statistiques")
        
        container = ScrolledFrame(tab, autohide=True)
        container.pack(fill=BOTH, expand=YES, padx=15, pady=15)
        
        content = container.container
        
        # Cartes de statistiques
        stats_frame = ttk.Frame(content)
        stats_frame.pack(fill=X, pady=(0, 20))
        
        # Variables pour les stats
        self.total_sales_var = ttk.StringVar(value="0 Ar")
        self.total_receipts_var = ttk.StringVar(value="0")
        self.avg_sale_var = ttk.StringVar(value="0 Ar")
        self.unique_products_var = ttk.StringVar(value="0")
        
        # Créer 4 cartes
        self.create_stat_card(stats_frame, "💰 TOTAL DES VENTES", self.total_sales_var, "primary", 0, 0)
        self.create_stat_card(stats_frame, "📄 NOMBRE DE REÇUS", self.total_receipts_var, "success", 0, 1)
        self.create_stat_card(stats_frame, "📊 VENTE MOYENNE", self.avg_sale_var, "warning", 1, 0)
        self.create_stat_card(stats_frame, "📦 PRODUITS UNIQUES", self.unique_products_var, "danger", 1, 1)
        
        # Top produits
        top_frame = ttk.Labelframe(content, text="🏆 Top 5 des produits les plus vendus", bootstyle="primary", padding=15)
        top_frame.pack(fill=BOTH, expand=YES, pady=(0, 15))
        
        columns = ('Rang', 'Produit', 'Quantité vendue', 'Revenu total')
        self.top_products_tree = ttk.Treeview(top_frame, columns=columns, show='headings', height=7, bootstyle="info")
        
        for col in columns:
            self.top_products_tree.heading(col, text=col)
        
        self.top_products_tree.column('Rang', width=80, anchor=CENTER)
        self.top_products_tree.column('Produit', width=350)
        self.top_products_tree.column('Quantité vendue', width=150, anchor=CENTER)
        self.top_products_tree.column('Revenu total', width=180, anchor=E)
        
        self.top_products_tree.pack(fill=BOTH, expand=YES)
        
        # Bouton actualiser
        ttk.Button(content, text="🔄 Actualiser les statistiques", command=self.refresh_statistics, bootstyle="info", width=30).pack(pady=10)
        
        self.refresh_statistics()
    
    def create_stat_card(self, parent, title, variable, style, row, col):
        """Créer une carte de statistique"""
        card = ttk.Frame(parent, bootstyle=style)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        
        ttk.Label(card, text=title, font=("Helvetica", 10, "bold"), bootstyle=f"inverse-{style}").pack(pady=(15, 5))
        ttk.Label(card, textvariable=variable, font=("Helvetica", 28, "bold"), bootstyle=style).pack(pady=(5, 15))
    
    def create_settings_tab(self):
        """Onglet paramètres"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Paramètres")
        
        container = ScrolledFrame(tab, autohide=True)
        container.pack(fill=BOTH, expand=YES, padx=15, pady=15)
        
        content = container.container
        
        # Section entreprise
        company_frame = ttk.Labelframe(content, text="🏢 Informations de l'entreprise", bootstyle="primary", padding=15)
        company_frame.pack(fill=X, pady=(0, 15))
        
        # Variables de paramètres
        self.settings_vars = {}
        
        settings_fields = [
            ('company_name', 'Nom de l\'entreprise'),
            ('company_address', 'Adresse (utilisez \\n pour les retours à la ligne)'),
            ('company_phone', 'Téléphone'),
            ('company_email', 'Email'),
            ('company_nif', 'NIF'),
            ('company_stat', 'STAT'),
            ('company_rc', 'R.C'),
            ('company_ce', 'CE'),
            ('company_cif', 'CIF')
        ]
        
        for key, label in settings_fields:
            frame = ttk.Frame(company_frame)
            frame.pack(fill=X, pady=5)
            
            ttk.Label(frame, text=label + ":", width=30, anchor=W).pack(side=LEFT, padx=5)
            var = ttk.StringVar()
            self.settings_vars[key] = var
            ttk.Entry(frame, textvariable=var, width=60).pack(side=LEFT, padx=5, fill=X, expand=YES)
        
        # Section préférences
        pref_frame = ttk.Labelframe(content, text="⚙️ Préférences", bootstyle="info", padding=15)
        pref_frame.pack(fill=X, pady=(0, 15))
        
        # Devise
        currency_frame = ttk.Frame(pref_frame)
        currency_frame.pack(fill=X, pady=5)
        ttk.Label(currency_frame, text="Devise:", width=30, anchor=W).pack(side=LEFT, padx=5)
        self.settings_vars['currency'] = ttk.StringVar()
        currency_combo = ttk.Combobox(
            currency_frame,
            textvariable=self.settings_vars['currency'],
            values=['Ar', '€', '$', 'FCFA'],
            width=20,
            state="readonly"
        )
        currency_combo.pack(side=LEFT, padx=5)
        
        # Largeur papier
        paper_frame = ttk.Frame(pref_frame)
        paper_frame.pack(fill=X, pady=5)
        ttk.Label(paper_frame, text="Largeur papier (mm):", width=30, anchor=W).pack(side=LEFT, padx=5)
        self.settings_vars['paper_width'] = ttk.StringVar()
        paper_combo = ttk.Combobox(
            paper_frame,
            textvariable=self.settings_vars['paper_width'],
            values=['58', '80'],
            width=20,
            state="readonly"
        )
        paper_combo.pack(side=LEFT, padx=5)
        
        # Type de reçu
        type_frame = ttk.Frame(pref_frame)
        type_frame.pack(fill=X, pady=5)
        ttk.Label(type_frame, text="Type de vente:", width=30, anchor=W).pack(side=LEFT, padx=5)
        self.settings_vars['receipt_type'] = ttk.StringVar()
        ttk.Entry(type_frame, textvariable=self.settings_vars['receipt_type'], width=60).pack(side=LEFT, padx=5, fill=X, expand=YES)
        
        # Bouton sauvegarder
        ttk.Button(content, text="💾 Enregistrer les paramètres", command=self.save_settings, bootstyle="success", width=30).pack(pady=15)
        
        # Zone dangereuse
        danger_frame = ttk.Labelframe(content, text="🗑️ Zone dangereuse", bootstyle="danger", padding=15)
        danger_frame.pack(fill=X)
        
        ttk.Label(danger_frame, text="⚠️ Ces actions sont irréversibles !", bootstyle="danger", font=("Helvetica", 10, "bold")).pack(pady=10)
        
        btn_frame = ttk.Frame(danger_frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="Effacer l'historique", command=self.clear_history, bootstyle="danger").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Effacer les produits", command=self.clear_products, bootstyle="danger").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Réinitialiser tout", command=self.reset_all, bootstyle="danger").pack(side=LEFT, padx=5)
        
        # Charger les paramètres
        self.load_settings()
    
    # ========== Méthodes pour l'onglet Nouveau Reçu ==========
    
    def on_product_search(self, *args):
        """Gérer la recherche de produits"""
        query = self.search_var.get()
        
        if not query:
            if self.autocomplete_listbox:
                self.autocomplete_listbox.destroy()
                self.autocomplete_listbox = None
            self.suggestion_label.config(text="")
            return
        
        # Rechercher les produits
        products = self.controller.search_products(query)
        
        if products:
            # Afficher la liste d'autocomplétion
            if not self.autocomplete_listbox:
                self.autocomplete_listbox = ttk.Treeview(
                    self.autocomplete_frame,
                    columns=('name', 'price'),
                    show='tree headings',
                    height=min(5, len(products)),
                    bootstyle="info"
                )
                self.autocomplete_listbox.heading('name', text='Produit')
                self.autocomplete_listbox.heading('price', text='Prix')
                self.autocomplete_listbox.column('#0', width=0, stretch=NO)
                self.autocomplete_listbox.column('name', width=300)
                self.autocomplete_listbox.column('price', width=150)
                self.autocomplete_listbox.pack(fill=X)
                self.autocomplete_listbox.bind('<<TreeviewSelect>>', self.on_autocomplete_select)
            
            # Vider et remplir la liste
            for item in self.autocomplete_listbox.get_children():
                self.autocomplete_listbox.delete(item)
            
            for product in products:
                name, price, count, last_used = product
                self.autocomplete_listbox.insert('', 'end', values=(name, f"{price:.2f} Ar"))
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
            
            # Afficher la suggestion
            self.suggestion_label.config(text=f"💡 Prix habituel: {price_text} Ar")
            
            # Fermer la liste
            if self.autocomplete_listbox:
                self.autocomplete_listbox.destroy()
                self.autocomplete_listbox = None
            
            # Focus sur la quantité
            self.quantity_var.set("1")
    
    def add_item(self):
        """Ajouter un article"""
        name = self.search_var.get().strip()
        
        try:
            quantity = float(self.quantity_var.get())
            unit_price = float(self.unit_price_var.get())
        except ValueError:
            messagebox.showerror("Erreur", "Quantité et prix doivent être des nombres valides")
            return
        
        success, result = self.controller.add_item(name, quantity, unit_price)
        
        if success:
            self.refresh_current_items()
            
            # Réinitialiser le formulaire
            self.search_var.set("")
            self.quantity_var.set("1")
            self.unit_price_var.set("")
            self.suggestion_label.config(text="")
            
            self.product_name_entry.focus()
        else:
            messagebox.showerror("Erreur", result)
    
    def remove_item(self):
        """Retirer un article"""
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un article à retirer")
            return
        
        index = self.items_tree.index(selection[0])
        self.controller.remove_item(index)
        self.refresh_current_items()
    
    def clear_items(self):
        """Vider tous les articles"""
        if messagebox.askyesno("Confirmation", "Vider tous les articles ?"):
            self.controller.clear_current_items()
            self.refresh_current_items()
    
    def refresh_current_items(self):
        """Rafraîchir l'affichage des articles"""
        # Vider le treeview
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        # Remplir avec les articles actuels
        items = self.controller.get_current_items()
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        for item in items:
            self.items_tree.insert('', 'end', values=(
                item['name'],
                f"{item['quantity']:.0f}",
                f"{item['unit_price']:,.2f} {currency}",
                f"{item['total']:,.2f} {currency}"
            ))
        
        # Mettre à jour le total
        total = self.controller.get_current_total()
        self.total_var.set(f"{total:,.2f} {currency}")
    
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
            messagebox.showinfo("Succès", f"Reçu généré avec succès !\n\nFichier: {result}")
            self.reset_form()
            self.refresh_history()
            self.refresh_statistics()
            
            # Proposer d'ouvrir le fichier
            if messagebox.askyesno("Ouvrir le reçu", "Voulez-vous ouvrir le reçu PDF ?"):
                self.open_file(result)
        else:
            messagebox.showerror("Erreur", result)
    
    def save_receipt_only(self):
        """Enregistrer sans générer le PDF"""
        # À implémenter si nécessaire
        messagebox.showinfo("Info", "Cette fonctionnalité sera ajoutée prochainement")
    
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
    
    # ========== Méthodes pour l'onglet Historique ==========
    
    def refresh_history(self):
        """Rafraîchir l'historique"""
        # Vider le treeview
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Charger les reçus
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
            
            self.history_tree.insert('', 'end', values=(
                number,
                formatted_date,
                client or "Client",
                f"{total:,.2f} {currency}",
                formatted_created
            ), tags=(receipt_id,))
    
    def search_history(self):
        """Rechercher dans l'historique"""
        query = self.history_search_var.get()
        
        # Vider le treeview
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Rechercher
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
            
            self.history_tree.insert('', 'end', values=(
                number,
                formatted_date,
                client or "Client",
                f"{total:,.2f} {currency}",
                formatted_created
            ), tags=(receipt_id,))
    
    def view_receipt_details(self):
        """Voir les détails d'un reçu"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un reçu")
            return
        
        receipt_id = self.history_tree.item(selection[0])['tags'][0]
        receipt = self.controller.get_receipt_details(receipt_id)
        
        if receipt:
            details = f"Reçu: {receipt['receipt_number']}\n"
            details += f"Date: {receipt['date']}\n"
            details += f"Client: {receipt['client_name']}\n"
            details += f"Téléphone: {receipt['client_phone']}\n\n"
            details += "Articles:\n"
            
            currency = self.controller.db.get_setting('currency', 'Ar')
            for item in receipt['items']:
                details += f"- {item['name']}: {item['quantity']} x {item['unit_price']} = {item['total']} {currency}\n"
            
            details += f"\nTotal: {receipt['total']} {currency}"
            
            messagebox.showinfo("Détails du reçu", details)
    
    def regenerate_receipt(self):
        """Régénérer un reçu"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un reçu")
            return
        
        receipt_id = self.history_tree.item(selection[0])['tags'][0]
        success, result = self.controller.regenerate_receipt(receipt_id)
        
        if success:
            messagebox.showinfo("Succès", f"Reçu régénéré !\n\n{result}")
            if messagebox.askyesno("Ouvrir", "Voulez-vous ouvrir le reçu ?"):
                self.open_file(result)
        else:
            messagebox.showerror("Erreur", result)
    
    def delete_receipt(self):
        """Supprimer un reçu"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un reçu")
            return
        
        if messagebox.askyesno("Confirmation", "Supprimer ce reçu ?"):
            receipt_id = self.history_tree.item(selection[0])['tags'][0]
            self.controller.delete_receipt(receipt_id)
            self.refresh_history()
            self.refresh_statistics()
            messagebox.showinfo("Succès", "Reçu supprimé")
    
    def open_exports_folder(self):
        """Ouvrir le dossier des exports"""
        exports_path = os.path.abspath('exports')
        
        if not os.path.exists(exports_path):
            os.makedirs(exports_path)
        
        if platform.system() == 'Windows':
            os.startfile(exports_path)
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open "{exports_path}"')
        else:  # Linux
            os.system(f'xdg-open "{exports_path}"')
    
    # ========== Méthodes pour l'onglet Produits ==========
    
    def refresh_products(self):
        """Rafraîchir la liste des produits"""
        # Vider le treeview
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Charger les produits
        products = self.controller.get_all_products()
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        for product in products:
            product_id, name, avg_price, count, total_sold, last_used = product
            
            try:
                last_used_obj = datetime.fromisoformat(last_used)
                formatted_last = last_used_obj.strftime('%d/%m/%Y %H:%M')
            except:
                formatted_last = last_used or "N/A"
            
            self.products_tree.insert('', 'end', values=(
                name,
                f"{avg_price:,.2f} {currency}",
                f"{count} fois",
                formatted_last
            ), tags=(product_id,))
    
    def delete_product(self):
        """Supprimer un produit"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un produit")
            return
        
        if messagebox.askyesno("Confirmation", "Supprimer ce produit ?"):
            product_id = self.products_tree.item(selection[0])['tags'][0]
            self.controller.delete_product(product_id)
            self.refresh_products()
            self.refresh_statistics()
            messagebox.showinfo("Succès", "Produit supprimé")
    
    # ========== Méthodes pour l'onglet Statistiques ==========
    
    def refresh_statistics(self):
        """Rafraîchir les statistiques"""
        stats = self.controller.get_statistics()
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        self.total_sales_var.set(f"{stats['total_sales']:,.2f} {currency}")
        self.total_receipts_var.set(f"{stats['total_receipts']}")
        self.avg_sale_var.set(f"{stats['avg_sale']:,.2f} {currency}")
        self.unique_products_var.set(f"{stats['unique_products']}")
        
        # Top produits
        for item in self.top_products_tree.get_children():
            self.top_products_tree.delete(item)
        
        top_products = self.controller.get_top_products(5)
        
        for i, product in enumerate(top_products, 1):
            name, count, revenue = product
            self.top_products_tree.insert('', 'end', values=(
                f"#{i}",
                name,
                count,
                f"{revenue:,.2f} {currency}"
            ))
    
    # ========== Méthodes pour l'onglet Paramètres ==========
    
    def load_settings(self):
        """Charger les paramètres"""
        settings = self.controller.get_settings()
        
        for key, var in self.settings_vars.items():
            value = settings.get(key, '')
            # Remplacer les \n réels par \\n pour l'affichage
            if key == 'company_address':
                value = value.replace('\n', '\\n')
            var.set(value)
    
    def save_settings(self):
        """Sauvegarder les paramètres"""
        settings_dict = {}
        
        for key, var in self.settings_vars.items():
            value = var.get()
            # Remplacer \\n par de vrais retours à la ligne
            if key == 'company_address':
                value = value.replace('\\n', '\n')
            settings_dict[key] = value
        
        self.controller.save_settings(settings_dict)
        messagebox.showinfo("Succès", "Paramètres enregistrés !")
    
    def clear_history(self):
        """Effacer l'historique"""
        if messagebox.askyesno("Confirmation", "⚠️ Supprimer TOUT l'historique ?\nCette action est irréversible !"):
            self.controller.db.clear_all_receipts()
            self.refresh_history()
            self.refresh_statistics()
            messagebox.showinfo("Succès", "Historique effacé")
    
    def clear_products(self):
        """Effacer les produits"""
        if messagebox.askyesno("Confirmation", "⚠️ Supprimer TOUS les produits ?\nCette action est irréversible !"):
            self.controller.db.clear_all_products()
            self.refresh_products()
            self.refresh_statistics()
            messagebox.showinfo("Succès", "Produits effacés")
    
    def reset_all(self):
        """Réinitialiser tout"""
        if messagebox.askyesno("Confirmation", "⚠️ RÉINITIALISER TOUTES LES DONNÉES ?\nCette action est irréversible !"):
            if messagebox.askyesno("Dernière confirmation", "Êtes-vous VRAIMENT sûr ?"):
                self.controller.clear_all_data()
                self.refresh_history()
                self.refresh_products()
                self.refresh_statistics()
                self.reset_form()
                messagebox.showinfo("Succès", "Toutes les données ont été réinitialisées")
    
    # ========== Utilitaires ==========
    
    def open_file(self, filepath):
        """Ouvrir un fichier"""
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open "{filepath}"')
        else:  # Linux
            os.system(f'xdg-open "{filepath}"')
    
    def run(self):
        """Lancer l'application"""
        self.root.mainloop()
