"""
Onglet Nouveau Reçu
Mise en page 2 colonnes (saisie | ticket), saisie au clavier, validation en ligne
"""
from datetime import datetime
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.formatting import fmt_amount, fmt_money, fmt_qty, parse_number
from utils.name_formatter import format_client_name
from views.ui_helpers import (ButtonBar, TOUCH_IPADY, busy, empty_state, make_tree,
                              open_path, row_tag)

WIDE_BREAKPOINT = 640  # la fenêtre fait au minimum 800 px : 2 colonnes quasi toujours


class NewReceiptTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding=10)

        self.receipt_number_var = ttk.StringVar()
        self.date_var = ttk.StringVar(value=datetime.now().strftime('%d/%m/%Y'))
        self.client_name_var = ttk.StringVar()
        self.client_preview_var = ttk.StringVar()
        self.search_var = ttk.StringVar()
        self.quantity_var = ttk.StringVar(value="1")
        self.unit_price_var = ttk.StringVar()
        self.line_total_var = ttk.StringVar(value="")
        self.error_var = ttk.StringVar()
        self.total_var = ttk.StringVar(value="0 Ar")
        self.items_title_var = ttk.StringVar(value="Articles du reçu")

        self.currency = self.controller.get_currency()
        self.suggestions = {}          # iid -> (nom, prix)
        self.is_wide = None
        self._suppress_search = False

        self.create_widgets()

        self.client_name_var.trace_add('write', self._update_client_preview)
        self.search_var.trace_add('write', self.on_product_search)
        self.quantity_var.trace_add('write', self._update_line_total)
        self.unit_price_var.trace_add('write', self._update_line_total)

        self.frame.bind('<Configure>', self.on_resize)
        self.frame.bind_all('<Control-p>', self._shortcut_print, add='+')

    # ================= CONSTRUCTION =================

    def create_widgets(self):
        self.left = ttk.Frame(self.frame)
        self.right = ttk.Frame(self.frame)
        self._create_client_card(self.left)
        self._create_article_card(self.left)
        self._create_items_card(self.right)
        self._create_total_and_actions(self.right)
        self._apply_layout(wide=True)

    def _field_label(self, parent, text, hint=None):
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=(6, 2))
        ttk.Label(row, text=text, style="FieldLabel.TLabel").pack(side=LEFT)
        if hint:
            ttk.Label(row, text=hint, style="Muted.TLabel").pack(side=LEFT, padx=(8, 0))
        return row

    def _create_client_card(self, parent):
        card = ttk.Labelframe(parent, text=" Client ", bootstyle="primary", padding=(14, 6, 14, 12))
        card.pack(fill=X, pady=(0, 10))

        meta = ttk.Frame(card)
        meta.pack(fill=X, pady=(2, 0))
        ttk.Label(meta, text="Reçu", style="Muted.TLabel").pack(side=LEFT)
        ttk.Label(meta, textvariable=self.receipt_number_var, font=("", 12, "bold"),
                  bootstyle="primary").pack(side=LEFT, padx=(6, 16))
        ttk.Label(meta, text="Date", style="Muted.TLabel").pack(side=LEFT)
        ttk.Label(meta, textvariable=self.date_var, font=("", 12, "bold")).pack(side=LEFT, padx=6)

        self._field_label(card, "Nom du client", "(optionnel)")
        self.client_entry = ttk.Entry(card, textvariable=self.client_name_var, font=("", 13))
        self.client_entry.pack(fill=X, ipady=4)
        ttk.Label(card, textvariable=self.client_preview_var, style="Muted.TLabel").pack(anchor=W, pady=(3, 0))

        self._field_label(card, "Contact", "tél. et/ou adresse, plusieurs lignes")
        self.client_contact_text = ttk.Text(card, height=2, font=("", 12), wrap=WORD)
        self.client_contact_text.pack(fill=X)
        # Tab passe au champ suivant au lieu d'insérer une tabulation
        self.client_contact_text.bind("<Tab>", lambda e: (self.product_entry.focus_set(), "break")[1])

    def _create_article_card(self, parent):
        card = ttk.Labelframe(parent, text=" Ajouter un article ", bootstyle="success",
                              padding=(14, 6, 14, 12))
        card.pack(fill=X, pady=(0, 10))

        self._field_label(card, "Produit", "tapez pour chercher • ↓ suggestions")
        self.product_entry = ttk.Entry(card, textvariable=self.search_var, font=("", 13))
        self.product_entry.pack(fill=X, ipady=4)
        self.product_entry.bind("<Down>", self._focus_suggestions)
        self.product_entry.bind("<Return>", self._on_product_return)
        self.product_entry.bind("<Escape>", lambda e: (self._hide_suggestions(), "break")[1])

        # Suggestions (affichées seulement si résultats)
        self.suggest_frame = ttk.Frame(card)
        self.suggest_tree = ttk.Treeview(self.suggest_frame, columns=("name", "price"),
                                         show="", height=4, bootstyle="success")
        self.suggest_tree.column("name", anchor=W, stretch=True, width=240)
        self.suggest_tree.column("price", anchor=E, stretch=False, width=130)
        self.suggest_tree.pack(fill=X)
        self.suggest_tree.bind("<ButtonRelease-1>", self._on_suggestion_click)
        self.suggest_tree.bind("<Return>", self._choose_suggestion)
        self.suggest_tree.bind("<Escape>", lambda e: (self._hide_suggestions(), self.product_entry.focus_set()))
        self.suggest_tree.bind("<Up>", self._suggestion_up)

        grid = ttk.Frame(card)
        grid.pack(fill=X, pady=(8, 0))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=2)
        grid.columnconfigure(2, weight=2)

        ttk.Label(grid, text="Quantité", style="FieldLabel.TLabel").grid(row=0, column=0, sticky=W)
        ttk.Label(grid, text=f"Prix unitaire", style="FieldLabel.TLabel").grid(row=0, column=1, sticky=W, padx=(10, 0))
        ttk.Label(grid, text="Sous-total", style="FieldLabel.TLabel").grid(row=0, column=2, sticky=W, padx=(10, 0))

        self.quantity_spin = ttk.Spinbox(grid, from_=1, to=100000, increment=1,
                                         textvariable=self.quantity_var, font=("", 13), width=6)
        self.quantity_spin.grid(row=1, column=0, sticky=EW, ipady=4, pady=(2, 0))
        self.price_entry = ttk.Entry(grid, textvariable=self.unit_price_var, font=("", 13), justify=RIGHT, width=10)
        self.price_entry.grid(row=1, column=1, sticky=EW, padx=(10, 0), ipady=4, pady=(2, 0))
        ttk.Label(grid, textvariable=self.line_total_var, font=("", 13, "bold"),
                  bootstyle="success", anchor=E).grid(row=1, column=2, sticky=EW, padx=(10, 0))

        self.quantity_spin.bind("<Return>", lambda e: self._select_all(self.price_entry))
        self.quantity_spin.bind("<FocusIn>", lambda e: self.quantity_spin.selection_range(0, END))
        self.price_entry.bind("<Return>", lambda e: self.add_item())
        self.price_entry.bind("<FocusIn>", lambda e: self.price_entry.selection_range(0, END))

        ttk.Label(card, textvariable=self.error_var, bootstyle="danger",
                  font=("", 10, "bold")).pack(anchor=W, pady=(6, 0))

        ttk.Button(card, text="➕  Ajouter l'article   (Entrée)", command=self.add_item,
                   bootstyle="success", cursor="hand2").pack(fill=X, ipady=TOUCH_IPADY, pady=(4, 0))

    def _create_items_card(self, parent):
        card = ttk.Labelframe(parent, text=" Articles du reçu ", bootstyle="secondary",
                              padding=(10, 6, 10, 10))
        card.pack(fill=BOTH, expand=YES, pady=(0, 10))
        self.items_card = card

        columns = [
            ("num", "#", 36, CENTER, False),
            ("name", "Produit", 260, W, True),
            ("qty", "Qté", 56, CENTER, False),
            ("price", "Prix unit.", 100, E, False),
            ("total", "Total", 110, E, False),
        ]
        tree_frame, self.items_tree = make_tree(card, columns, height=8, selectmode="browse")
        tree_frame.pack(fill=BOTH, expand=YES)
        self.items_tree.bind("<Delete>", lambda e: self.remove_item())
        self.items_tree.bind("<BackSpace>", lambda e: self.remove_item())
        self.items_tree.bind("<Double-1>", lambda e: self.edit_item())
        self.items_tree.bind("<<TreeviewSelect>>", lambda e: self._update_item_buttons())

        bar = ttk.Frame(card)
        bar.pack(fill=X, pady=(8, 0))
        self.edit_btn = ttk.Button(bar, text="✏  Modifier", command=self.edit_item,
                                   bootstyle="secondary-outline", cursor="hand2")
        self.remove_btn = ttk.Button(bar, text="🗑  Retirer  (Suppr)", command=self.remove_item,
                                     bootstyle="danger-outline", cursor="hand2")
        self.clear_btn = ttk.Button(bar, text="Vider le reçu", command=self.clear_items,
                                    bootstyle="warning-outline", cursor="hand2")
        for btn in (self.edit_btn, self.remove_btn, self.clear_btn):
            btn.pack(side=LEFT, padx=(0, 6), ipady=6, fill=X, expand=YES)

    def _create_total_and_actions(self, parent):
        total_card = ttk.Frame(parent, bootstyle="light", padding=(16, 10))
        total_card.pack(fill=X, pady=(0, 8))
        ttk.Label(total_card, text="TOTAL À PAYER", style="TotalCaption.TLabel",
                  background=ttk.Style().colors.light).pack(side=LEFT)
        self.total_label = ttk.Label(total_card, textvariable=self.total_var, style="Total.TLabel",
                                     background=ttk.Style().colors.light)
        self.total_label.pack(side=RIGHT)

        self.actions = ButtonBar(parent, wide_columns=2, narrow_columns=1, breakpoint=420)
        self.actions.pack(fill=X)
        self.thermal_btn = self.actions.add("🖨  Imprimer — thermique   (Ctrl+P)", self.print_thermal, "primary", span=2)
        self.laser_btn = self.actions.add("🖨  Imprimer — laser A6", self.print_laser, "info")
        self.pdf_btn = self.actions.add("📄  Enregistrer en PDF", self.generate_receipt, "info-outline")
        self.new_btn = self.actions.add("↺  Nouveau reçu", self.new_receipt, "secondary-outline", span=2)
        self.apply_settings()

    # ================= MISE EN PAGE =================

    def on_resize(self, event):
        if event.widget is self.frame:
            self._apply_layout(event.width >= WIDE_BREAKPOINT)

    def _apply_layout(self, wide):
        if wide == self.is_wide:
            return
        self.is_wide = wide
        self.left.grid_forget()
        self.right.grid_forget()
        for i in range(2):
            self.frame.columnconfigure(i, weight=0, uniform="")
            self.frame.rowconfigure(i, weight=0)
        if wide:
            self.frame.columnconfigure(0, weight=4, uniform="col")
            self.frame.columnconfigure(1, weight=5, uniform="col")
            self.frame.rowconfigure(0, weight=1)
            self.left.grid(row=0, column=0, sticky=NSEW, padx=(0, 10))
            self.right.grid(row=0, column=1, sticky=NSEW)
        else:
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(1, weight=1)
            self.left.grid(row=0, column=0, sticky=EW)
            self.right.grid(row=1, column=0, sticky=NSEW)

    def apply_settings(self):
        """Devise et visibilité du bouton laser selon les paramètres"""
        self.currency = self.controller.get_currency()
        self.actions.set_visible(self.laser_btn, self.controller.is_laser_enabled())
        self._update_line_total()
        self.refresh_current_items()

    def focus_product(self):
        self.frame.after(50, self.product_entry.focus_set)

    # ================= CLIENT =================

    def _update_client_preview(self, *args):
        name = self.client_name_var.get().strip()
        if not name:
            self.client_preview_var.set("Formaté automatiquement : NOM Prénom P.")
            return
        self.client_preview_var.set(f"Sur le reçu : {format_client_name(name)}")

    def get_client_contact(self):
        return self.client_contact_text.get("1.0", "end-1c").strip()

    # ================= RECHERCHE PRODUIT =================

    def on_product_search(self, *args):
        self.error_var.set("")
        if self._suppress_search:
            return
        query = self.search_var.get().strip()
        if not query:
            self._hide_suggestions()
            return
        products = self.controller.search_products(query)
        self.suggest_tree.delete(*self.suggest_tree.get_children())
        self.suggestions = {}
        if not products:
            self._hide_suggestions()
            return
        for i, (name, price, count, last_used) in enumerate(products):
            iid = self.suggest_tree.insert('', END, values=(name, fmt_money(price, self.currency)),
                                           tags=(row_tag(i),))
            self.suggestions[iid] = (name, price)
        self.suggest_tree.configure(height=min(5, len(products)))
        if not self.suggest_frame.winfo_ismapped():
            self.suggest_frame.pack(fill=X, pady=(4, 0), after=self.product_entry)

    def _hide_suggestions(self):
        if self.suggest_frame.winfo_ismapped():
            self.suggest_frame.pack_forget()

    def _focus_suggestions(self, event=None):
        children = self.suggest_tree.get_children()
        if self.suggest_frame.winfo_ismapped() and children:
            self.suggest_tree.focus_set()
            self.suggest_tree.selection_set(children[0])
            self.suggest_tree.focus(children[0])
        return "break"

    def _suggestion_up(self, event):
        children = self.suggest_tree.get_children()
        if children and self.suggest_tree.focus() == children[0]:
            self.product_entry.focus_set()
            return "break"

    def _on_suggestion_click(self, event):
        iid = self.suggest_tree.identify_row(event.y)
        if iid:
            self._apply_suggestion(iid)

    def _choose_suggestion(self, event=None):
        iid = self.suggest_tree.focus()
        if iid:
            self._apply_suggestion(iid)
        return "break"

    def _apply_suggestion(self, iid):
        name, price = self.suggestions.get(iid, (None, None))
        if name is None:
            return
        self._suppress_search = True
        self.search_var.set(name)
        self._suppress_search = False
        self.unit_price_var.set(fmt_qty(price))
        self._hide_suggestions()
        self._select_all(self.quantity_spin)

    def _on_product_return(self, event):
        # Entrée sur le produit : si une seule suggestion exacte, la prendre ; sinon aller à la quantité
        children = self.suggest_tree.get_children() if self.suggest_frame.winfo_ismapped() else ()
        typed = self.search_var.get().strip().lower()
        for iid in children:
            if self.suggestions[iid][0].lower() == typed:
                self._apply_suggestion(iid)
                return "break"
        self._hide_suggestions()
        self._select_all(self.quantity_spin)
        return "break"

    @staticmethod
    def _select_all(widget):
        widget.focus_set()
        try:
            widget.selection_range(0, END)
            widget.icursor(END)
        except Exception:
            pass
        return "break"

    def _update_line_total(self, *args):
        try:
            qty = parse_number(self.quantity_var.get())
            price = parse_number(self.unit_price_var.get())
            self.line_total_var.set(fmt_money(qty * price, self.currency) if qty > 0 and price > 0 else "—")
        except ValueError:
            self.line_total_var.set("—")

    # ================= ARTICLES =================

    def add_item(self):
        name = self.search_var.get().strip()
        if not name:
            return self._field_error("Saisissez le nom du produit", self.product_entry)
        try:
            quantity = parse_number(self.quantity_var.get())
        except ValueError:
            return self._field_error("Quantité invalide (ex : 2 ou 1,5)", self.quantity_spin)
        try:
            unit_price = parse_number(self.unit_price_var.get())
        except ValueError:
            return self._field_error("Prix unitaire invalide (ex : 5000 ou 5 000)", self.price_entry)

        success, result = self.controller.add_item(name, quantity, unit_price)
        if not success:
            target = self.quantity_spin if "quantité" in result.lower() else self.price_entry
            return self._field_error(result, target)

        self.error_var.set("")
        self.refresh_current_items(select_name=result['name'])
        self._suppress_search = True
        self.search_var.set("")
        self._suppress_search = False
        self._hide_suggestions()
        self.quantity_var.set("1")
        self.unit_price_var.set("")
        self.product_entry.focus_set()
        return "break"

    def _field_error(self, message, widget):
        self.error_var.set(f"⚠  {message}")
        self._select_all(widget)
        return "break"

    def _selected_index(self):
        selection = self.items_tree.selection()
        return self.items_tree.index(selection[0]) if selection else None

    def remove_item(self):
        index = self._selected_index()
        if index is None:
            self.main_window.toast.show("Sélectionnez d'abord un article dans la liste", "warning")
            return
        self.controller.remove_item(index)
        self.refresh_current_items()
        children = self.items_tree.get_children()
        if children:
            target = children[min(index, len(children) - 1)]
            self.items_tree.selection_set(target)
            self.items_tree.focus(target)

    def edit_item(self):
        """Remet l'article sélectionné dans le formulaire pour le corriger"""
        index = self._selected_index()
        if index is None:
            self.main_window.toast.show("Sélectionnez d'abord un article dans la liste", "warning")
            return
        ok, item = self.controller.remove_item(index)
        if not ok:
            return
        self._suppress_search = True
        self.search_var.set(item['name'])
        self._suppress_search = False
        self.quantity_var.set(fmt_qty(item['quantity']))
        self.unit_price_var.set(fmt_qty(item['unit_price']))
        self.refresh_current_items()
        self.main_window.toast.show("Article remis dans le formulaire : corrigez puis appuyez sur Entrée", "info")
        self._select_all(self.quantity_spin)

    def clear_items(self):
        if not self.controller.get_current_items():
            return
        if messagebox.askyesno("Vider le reçu", "Retirer tous les articles du reçu en cours ?",
                               parent=self.frame):
            self.controller.clear_current_items()
            self.refresh_current_items()

    def refresh_current_items(self, select_name=None):
        self.items_tree.delete(*self.items_tree.get_children())
        items = self.controller.get_current_items()
        selected = None
        for i, item in enumerate(items):
            iid = self.items_tree.insert('', END, tags=(row_tag(i),), values=(
                i + 1,
                item['name'],
                fmt_qty(item['quantity']),
                fmt_amount(item['unit_price']),
                fmt_amount(item['total']),
            ))
            if select_name and item['name'] == select_name:
                selected = iid
        if selected:
            self.items_tree.see(selected)
            self.items_tree.selection_set(selected)

        count = len(items)
        self.items_card.configure(text=f" Articles du reçu ({count}) " if count else " Articles du reçu ")
        self.total_var.set(fmt_money(self.controller.get_current_total(), self.currency))
        empty_state(self.items_tree, "Aucun article pour l'instant\nSaisissez un produit à gauche puis appuyez sur Entrée")

        state = NORMAL if count else DISABLED
        for btn in (self.thermal_btn, self.laser_btn, self.pdf_btn, self.clear_btn):
            btn.configure(state=state)
        self._update_item_buttons()

    def _update_item_buttons(self):
        state = NORMAL if self.items_tree.selection() else DISABLED
        self.edit_btn.configure(state=state)
        self.remove_btn.configure(state=state)

    # ================= ENREGISTREMENT / IMPRESSION =================

    def _summary(self):
        items = self.controller.get_current_items()
        n = len(items)
        return (f"Reçu {self.receipt_number_var.get()} — {n} article{'s' if n > 1 else ''}\n"
                f"Total : {fmt_money(self.controller.get_current_total(), self.currency)}")

    def _client_kwargs(self):
        return {
            'client_name': self.client_name_var.get().strip(),
            'client_contact': self.get_client_contact(),
            'payment_method': "Espèces",
        }

    def _after_save_attempt(self, success, message):
        """Le reçu a été enregistré dès que le contrôleur a vidé les articles,
        même si l'impression a échoué : on remet alors le formulaire à zéro."""
        saved = not self.controller.get_current_items()
        if saved:
            self.reset_form()
            self.main_window.refresh_all_tabs()
        if success:
            self.main_window.toast.show(message, "success")
        else:
            messagebox.showerror("Impression", message, parent=self.frame)

    def _shortcut_print(self, event=None):
        if self.main_window.notebook.index("current") == 0 and self.controller.get_current_items():
            self.print_thermal()
        return "break"

    def print_thermal(self):
        if not self.controller.get_current_items():
            return
        if not messagebox.askyesno("Imprimer — thermique", f"{self._summary()}\n\nImprimer sur l'imprimante thermique ?",
                                   parent=self.frame):
            return
        with busy(self.frame, self.main_window.toast, "Impression en cours…"):
            success, message = self.controller.print_thermal_receipt(**self._client_kwargs())
        self._after_save_attempt(success, message)

    def print_laser(self):
        if not self.controller.get_current_items():
            return
        if not messagebox.askyesno("Imprimer — laser A6", f"{self._summary()}\n\nImprimer sur l'imprimante laser (A6) ?",
                                   parent=self.frame):
            return
        with busy(self.frame, self.main_window.toast, "Impression en cours…"):
            success, message = self.controller.print_laser_receipt(**self._client_kwargs())
        self._after_save_attempt(success, message)

    def generate_receipt(self):
        if not self.controller.get_current_items():
            return
        with busy(self.frame, self.main_window.toast, "Génération du PDF…"):
            success, result = self.controller.save_and_generate_receipt(**self._client_kwargs())
        if not success:
            self._after_save_attempt(False, result)
            return
        self.reset_form()
        self.main_window.refresh_all_tabs()
        if messagebox.askyesno("PDF enregistré", f"Reçu enregistré :\n{result}\n\nOuvrir le PDF maintenant ?",
                               parent=self.frame):
            try:
                open_path(result)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {e}", parent=self.frame)

    def new_receipt(self):
        if self.controller.get_current_items() and not messagebox.askyesno(
                "Nouveau reçu", "Abandonner le reçu en cours (non enregistré) ?", parent=self.frame):
            return
        self.reset_form()

    def reset_form(self):
        self.controller.clear_current_items()
        self.client_name_var.set("")
        self.client_contact_text.delete("1.0", END)
        self._suppress_search = True
        self.search_var.set("")
        self._suppress_search = False
        self._hide_suggestions()
        self.quantity_var.set("1")
        self.unit_price_var.set("")
        self.error_var.set("")
        self.date_var.set(datetime.now().strftime('%d/%m/%Y'))
        self.refresh_current_items()
        self.update_receipt_number()
        self.client_entry.focus_set()

    def update_receipt_number(self):
        self.receipt_number_var.set(self.controller.db.get_next_receipt_number())
