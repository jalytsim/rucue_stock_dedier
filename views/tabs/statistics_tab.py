"""
Onglet Statistiques - indicateurs clés et meilleurs produits
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.formatting import fmt_money
from views.ui_helpers import empty_state, make_tree, row_tag

CARDS = [
    # (clé, titre, couleur)
    ("today", "AUJOURD'HUI", "primary"),
    ("month", "CE MOIS", "info"),
    ("total", "TOTAL DES VENTES", "success"),
    ("avg", "PANIER MOYEN", "warning"),
]


class StatisticsTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding=10)

        self.card_vars = {key: (ttk.StringVar(value="—"), ttk.StringVar(value="")) for key, _, _ in CARDS}
        self.cards = []
        self._columns = None

        self.create_widgets()
        self.refresh_statistics()

    def create_widgets(self):
        self.cards_frame = ttk.Frame(self.frame)
        self.cards_frame.pack(fill=X, pady=(0, 12))
        bg = ttk.Style().colors.light
        for key, title, color in CARDS:
            value_var, sub_var = self.card_vars[key]
            card = ttk.Frame(self.cards_frame, bootstyle="light", padding=(16, 12))
            ttk.Frame(card, bootstyle=color, width=5).pack(side=LEFT, fill=Y, padx=(0, 14))
            inner = ttk.Frame(card, bootstyle="light")
            inner.pack(side=LEFT, fill=BOTH, expand=YES)
            ttk.Label(inner, text=title, font=("", 10, "bold"), foreground=ttk.Style().colors.secondary,
                      background=bg).pack(anchor=W)
            ttk.Label(inner, textvariable=value_var, font=("", 22, "bold"), bootstyle=color,
                      background=bg).pack(anchor=W, pady=(2, 0))
            ttk.Label(inner, textvariable=sub_var, font=("", 10), background=bg,
                      foreground=ttk.Style().colors.secondary).pack(anchor=W)
            self.cards.append(card)
        self.cards_frame.bind("<Configure>", self._layout_cards)
        self._layout_cards(width=1200)

        top = ttk.Labelframe(self.frame, text=" Meilleurs produits (chiffre d'affaires) ",
                             bootstyle="primary", padding=10)
        top.pack(fill=BOTH, expand=YES)
        columns = [
            ("rank", "Rang", 70, CENTER, False),
            ("name", "Produit", 320, W, True),
            ("count", "Nb de ventes", 130, CENTER, False),
            ("revenue", "Chiffre d'affaires", 180, E, False),
        ]
        tree_frame, self.top_products_tree = make_tree(top, columns, height=10)
        tree_frame.pack(fill=BOTH, expand=YES)

    def _layout_cards(self, event=None, width=None):
        width = event.width if event else width
        cols = 4 if width >= 1100 else 2
        if cols == self._columns:
            return
        self._columns = cols
        for i in range(4):
            self.cards_frame.columnconfigure(i, weight=1 if i < cols else 0, uniform="card" if i < cols else "")
        for i, card in enumerate(self.cards):
            card.grid(row=i // cols, column=i % cols, sticky=NSEW, padx=6, pady=6)

    def refresh_statistics(self):
        stats = self.controller.get_statistics()
        currency = self.controller.get_currency()

        def plural(n, word):
            return f"{n} {word}{'s' if n > 1 else ''}"

        values = {
            "today": (fmt_money(stats['today_sales'], currency), plural(stats['today_receipts'], "reçu")),
            "month": (fmt_money(stats['month_sales'], currency), plural(stats['month_receipts'], "reçu")),
            "total": (fmt_money(stats['total_sales'], currency), plural(stats['total_receipts'], "reçu")),
            "avg": (fmt_money(stats['avg_sale'], currency), plural(stats['unique_products'], "produit") + " connus"),
        }
        for key, (value, sub) in values.items():
            self.card_vars[key][0].set(value)
            self.card_vars[key][1].set(sub)

        self.top_products_tree.delete(*self.top_products_tree.get_children())
        for i, (name, count, revenue) in enumerate(self.controller.get_top_products(10)):
            medal = f"{i + 1}"
            self.top_products_tree.insert('', END, tags=(row_tag(i),), values=(
                medal, name, count or 0, fmt_money(revenue or 0, currency)))
        empty_state(self.top_products_tree, "Pas encore de ventes")
