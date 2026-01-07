"""
Onglet Statistiques - Version tactile optimisée
Affichage des statistiques et analyses
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame


class StatisticsTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent)
        self.is_compact_mode = False
        
        # Variables pour les stats
        self.total_sales_var = ttk.StringVar(value="0 Ar")
        self.total_receipts_var = ttk.StringVar(value="0")
        self.avg_sale_var = ttk.StringVar(value="0 Ar")
        self.unique_products_var = ttk.StringVar(value="0")
        
        self.create_widgets()
        self.refresh_statistics()
        
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
        self.refresh_statistics()
    
    def create_widgets(self):
        """Créer les widgets de l'onglet"""
        # Zone scrollable
        container = ScrolledFrame(self.frame, autohide=True)
        container.pack(fill=BOTH, expand=YES, padx=8, pady=(8, 0))
        content = container.container
        
        # Cartes de statistiques
        stats_frame = ttk.Frame(content)
        stats_frame.pack(fill=X, pady=(0, 15))
        
        if self.is_compact_mode:
            # 1 colonne en mode compact
            self._create_stat_card_compact(stats_frame, "💰 VENTES TOTALES", 
                                          self.total_sales_var, "primary", 0)
            self._create_stat_card_compact(stats_frame, "📄 NOMBRE DE REÇUS", 
                                          self.total_receipts_var, "success", 1)
            self._create_stat_card_compact(stats_frame, "📊 VENTE MOYENNE", 
                                          self.avg_sale_var, "warning", 2)
            self._create_stat_card_compact(stats_frame, "📦 PRODUITS UNIQUES", 
                                          self.unique_products_var, "danger", 3)
        else:
            # 2 colonnes en mode normal
            self._create_stat_card(stats_frame, "💰 TOTAL DES VENTES", 
                                  self.total_sales_var, "primary", 0, 0)
            self._create_stat_card(stats_frame, "📄 NOMBRE DE REÇUS", 
                                  self.total_receipts_var, "success", 0, 1)
            self._create_stat_card(stats_frame, "📊 VENTE MOYENNE", 
                                  self.avg_sale_var, "warning", 1, 0)
            self._create_stat_card(stats_frame, "📦 PRODUITS UNIQUES", 
                                  self.unique_products_var, "danger", 1, 1)
        
        # Top produits
        top_frame = ttk.Labelframe(content, text="🏆 Top 5 des produits les plus vendus", 
                                   bootstyle="primary", padding=10)
        top_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        if self.is_compact_mode:
            columns = ('Rang', 'Produit', 'Qté', 'Total')
            widths = {'Rang': 50, 'Produit': 150, 'Qté': 50, 'Total': 80}
        else:
            columns = ('Rang', 'Produit', 'Quantité vendue', 'Revenu total')
            widths = {'Rang': 70, 'Produit': 320, 'Quantité vendue': 130, 'Revenu total': 150}
        
        self.top_products_tree = ttk.Treeview(top_frame, columns=columns, 
                                              show='headings', height=6, bootstyle="info")
        
        # Style tactile
        style = ttk.Style()
        font_size = 10 if self.is_compact_mode else 11
        style.configure("stats.Treeview", font=("", font_size), rowheight=32)
        style.configure("stats.Treeview.Heading", font=("", font_size, "bold"))
        self.top_products_tree.configure(style="stats.Treeview")
        
        for col in columns:
            self.top_products_tree.heading(col, text=col)
            if col in ['Rang', 'Quantité vendue', 'Qté']:
                align = CENTER
            elif col in ['Revenu total', 'Total']:
                align = E
            else:
                align = W
            self.top_products_tree.column(col, width=widths.get(col, 100), anchor=align, minwidth=40)
        
        self.top_products_tree.pack(fill=BOTH, expand=YES)
        
        # Zone FIXE pour le bouton actualiser
        self._create_fixed_button()
    
    def _create_fixed_button(self):
        """Créer le bouton fixe"""
        ttk.Separator(self.frame, orient=HORIZONTAL).pack(fill=X, padx=8)
        
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=X, side=BOTTOM, padx=8, pady=8)
        
        ttk.Button(btn_frame, text="🔄 Actualiser les statistiques", 
                  command=self.refresh_statistics, bootstyle="info").pack(
                      fill=X, ipady=10)
    
    def _create_stat_card(self, parent, title, variable, style, row, col):
        """Créer une carte de statistique (mode normal)"""
        card = ttk.Frame(parent, bootstyle=style)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        
        ttk.Label(card, text=title, font=("", 11, "bold"), 
                 bootstyle=f"inverse-{style}").pack(pady=(12, 5))
        ttk.Label(card, textvariable=variable, font=("", 24, "bold"), 
                 bootstyle=style).pack(pady=(5, 12))
    
    def _create_stat_card_compact(self, parent, title, variable, style, row):
        """Créer une carte de statistique (mode compact)"""
        card = ttk.Frame(parent, bootstyle=style)
        card.pack(fill=X, pady=5)
        
        ttk.Label(card, text=title, font=("", 10, "bold"), 
                 bootstyle=f"inverse-{style}").pack(pady=(8, 3))
        ttk.Label(card, textvariable=variable, font=("", 20, "bold"), 
                 bootstyle=style).pack(pady=(3, 8))
    
    def refresh_statistics(self):
        """Rafraîchir les statistiques"""
        stats = self.controller.get_statistics()
        currency = self.controller.db.get_setting('currency', 'Ar')
        
        self.total_sales_var.set(f"{stats['total_sales']:,.0f} {currency}")
        self.total_receipts_var.set(f"{stats['total_receipts']}")
        self.avg_sale_var.set(f"{stats['avg_sale']:,.0f} {currency}")
        self.unique_products_var.set(f"{stats['unique_products']}")
        
        # Top produits
        for item in self.top_products_tree.get_children():
            self.top_products_tree.delete(item)
        
        top_products = self.controller.get_top_products(5)
        
        for i, product in enumerate(top_products, 1):
            name, count, revenue = product
            
            if self.is_compact_mode:
                values = (
                    f"#{i}",
                    name,
                    count,
                    f"{revenue:,.0f}"
                )
            else:
                values = (
                    f"#{i}",
                    name,
                    count,
                    f"{revenue:,.0f} {currency}"
                )
            
            self.top_products_tree.insert('', 'end', values=values)