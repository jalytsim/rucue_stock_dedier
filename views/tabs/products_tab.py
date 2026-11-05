"""
Onglet Produits - produits mémorisés automatiquement à chaque vente
"""
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Querybox

from utils.formatting import fmt_datetime, fmt_money, fmt_qty, parse_number
from views.ui_helpers import ButtonBar, empty_state, make_tree, row_tag


class ProductsTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding=10)

        self.search_var = ttk.StringVar()
        self.summary_var = ttk.StringVar()
        self.products = {}

        self.create_widgets()
        self.refresh_products()
        self.search_var.trace_add('write', lambda *a: self.refresh_products())

    def create_widgets(self):
        top = ttk.Frame(self.frame)
        top.pack(fill=X, pady=(0, 8))
        ttk.Label(top, text="🔍", font=("", 14)).pack(side=LEFT, padx=(0, 6))
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, font=("", 13))
        self.search_entry.pack(side=LEFT, fill=X, expand=YES, ipady=4)
        self.search_entry.bind("<Escape>", lambda e: self.search_var.set(""))
        ttk.Label(top, text="Les produits sont mémorisés automatiquement à chaque vente",
                  style="Muted.TLabel").pack(side=LEFT, padx=10)

        columns = [
            ("name", "Produit", 320, W, True),
            ("price", "Dernier prix", 140, E, False),
            ("count", "Ventes", 90, CENTER, False),
            ("revenue", "Chiffre d'affaires", 170, E, False),
            ("last", "Dernière vente", 160, CENTER, False),
        ]
        tree_frame, self.products_tree = make_tree(self.frame, columns, height=14, selectmode="browse")
        tree_frame.pack(fill=BOTH, expand=YES)
        self.products_tree.bind("<Double-1>", lambda e: self.edit_price())
        self.products_tree.bind("<Return>", lambda e: self.edit_price())
        self.products_tree.bind("<Delete>", lambda e: self.delete_product())
        self.products_tree.bind("<<TreeviewSelect>>", lambda e: self._update_buttons())

        ttk.Label(self.frame, textvariable=self.summary_var, style="Muted.TLabel").pack(anchor=W, pady=(6, 4))

        bar = ButtonBar(self.frame, wide_columns=3, narrow_columns=3)
        bar.pack(fill=X)
        self.edit_btn = bar.add("✏  Modifier le prix", self.edit_price, "primary")
        self.delete_btn = bar.add("🗑  Supprimer", self.delete_product, "danger-outline")
        bar.add("↻  Actualiser", self.refresh_products, "secondary-outline")
        self._update_buttons()

    def _update_buttons(self):
        state = NORMAL if self.products_tree.selection() else DISABLED
        self.edit_btn.configure(state=state)
        self.delete_btn.configure(state=state)

    def refresh_products(self):
        query = self.search_var.get().strip()
        products = self.controller.get_all_products(query)
        currency = self.controller.get_currency()

        self.products_tree.delete(*self.products_tree.get_children())
        self.products = {}
        for i, (product_id, name, price, count, total_sold, last_used) in enumerate(products):
            iid = str(product_id)
            self.products[iid] = (name, price)
            self.products_tree.insert('', END, iid=iid, tags=(row_tag(i),), values=(
                name, fmt_money(price, currency), count or 0, fmt_money(total_sold or 0, currency),
                fmt_datetime(last_used) or "—"))

        n = len(products)
        self.summary_var.set(f"{n} produit{'s' if n > 1 else ''}" if n else "")
        empty_state(self.products_tree,
                    f"Aucun produit ne correspond à « {query} »" if query else
                    "Aucun produit pour l'instant\nIls apparaîtront ici après votre première vente")
        self._update_buttons()

    def _selected(self):
        selection = self.products_tree.selection()
        if not selection:
            self.main_window.toast.show("Sélectionnez d'abord un produit", "warning")
            return None, None
        return selection[0], self.products.get(selection[0])

    def edit_price(self):
        iid, product = self._selected()
        if not product:
            return
        name, price = product
        value = Querybox.get_string(prompt=f"Nouveau prix pour « {name} » :", title="Modifier le prix",
                                    initialvalue=fmt_qty(price), parent=self.frame.winfo_toplevel())
        if value is None:
            return
        try:
            new_price = parse_number(value)
            if new_price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Prix invalide", "Le prix doit être un nombre supérieur à 0.", parent=self.frame)
            return
        self.controller.update_product_price(int(iid), new_price)
        self.refresh_products()
        self.products_tree.selection_set(iid)
        self.main_window.toast.show(f"Prix de « {name} » mis à jour")

    def delete_product(self):
        iid, product = self._selected()
        if not product:
            return
        if messagebox.askyesno("Supprimer le produit",
                               f"Supprimer « {product[0]} » de la liste des produits ?\n\n"
                               "Les reçus déjà enregistrés ne sont pas modifiés.",
                               icon="warning", parent=self.frame):
            self.controller.delete_product(int(iid))
            self.refresh_products()
            self.main_window.statistics_tab.refresh_statistics()
            self.main_window.toast.show("Produit supprimé")
