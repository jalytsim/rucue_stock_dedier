"""
Onglet Historique - consultation, réimpression et suppression des reçus
"""
import os
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from utils.formatting import fmt_amount, fmt_date, fmt_datetime, fmt_money, fmt_qty
from views.ui_helpers import (ButtonBar, busy, center_dialog, empty_state, make_tree,
                              open_path, row_tag)


class HistoryTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        self.frame = ttk.Frame(parent, padding=10)

        self.search_var = ttk.StringVar()
        self.summary_var = ttk.StringVar()
        self._search_after = None

        self.create_widgets()
        self.refresh_history()
        self.search_var.trace_add('write', self._schedule_search)

    # ---------- Construction ----------

    def create_widgets(self):
        top = ttk.Frame(self.frame)
        top.pack(fill=X, pady=(0, 8))
        ttk.Label(top, text="🔍", font=("", 14)).pack(side=LEFT, padx=(0, 6))
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, font=("", 13))
        self.search_entry.pack(side=LEFT, fill=X, expand=YES, ipady=4)
        self.search_entry.bind("<Escape>", lambda e: self.search_var.set(""))
        self.search_entry.bind("<Down>", self._focus_list)
        ttk.Label(top, text="N° de reçu, nom ou contact du client", style="Muted.TLabel").pack(side=LEFT, padx=10)

        columns = [
            ("number", "N° reçu", 130, W, False),
            ("date", "Date", 110, CENTER, False),
            ("client", "Client", 260, W, True),
            ("total", "Total", 150, E, False),
            ("created", "Enregistré le", 160, CENTER, False),
        ]
        tree_frame, self.history_tree = make_tree(self.frame, columns, height=14, selectmode="browse")
        tree_frame.pack(fill=BOTH, expand=YES)
        self.history_tree.bind("<Double-1>", lambda e: self.view_receipt_details())
        self.history_tree.bind("<Return>", lambda e: self.view_receipt_details())
        self.history_tree.bind("<Delete>", lambda e: self.delete_receipt())
        self.history_tree.bind("<<TreeviewSelect>>", lambda e: self._update_buttons())

        ttk.Label(self.frame, textvariable=self.summary_var, style="Muted.TLabel").pack(anchor=W, pady=(6, 4))

        self.bar = ButtonBar(self.frame, wide_columns=6, narrow_columns=3)
        self.bar.pack(fill=X)
        self.view_btn = self.bar.add("👁  Détails", self.view_receipt_details, "primary")
        self.thermal_btn = self.bar.add("🖨  Thermique", self.reprint_thermal_receipt, "info")
        self.laser_btn = self.bar.add("🖨  Laser A6", self.reprint_laser_receipt, "info")
        self.pdf_btn = self.bar.add("📄  PDF", self.regenerate_receipt, "info-outline")
        self.folder_btn = self.bar.add("📁  Dossier PDF", self.open_exports_folder, "secondary-outline")
        self.delete_btn = self.bar.add("🗑  Supprimer", self.delete_receipt, "danger-outline")
        self._update_buttons()

    def focus_search(self):
        self.frame.after(50, self.search_entry.focus_set)

    def _focus_list(self, event=None):
        children = self.history_tree.get_children()
        if children:
            self.history_tree.focus_set()
            self.history_tree.selection_set(children[0])
            self.history_tree.focus(children[0])
        return "break"

    def _update_buttons(self):
        state = NORMAL if self.history_tree.selection() else DISABLED
        for btn in (self.view_btn, self.thermal_btn, self.laser_btn, self.pdf_btn, self.delete_btn):
            btn.configure(state=state)
        self.bar.set_visible(self.laser_btn, self.controller.is_laser_enabled())

    # ---------- Données ----------

    def _schedule_search(self, *args):
        # Petite temporisation : évite une requête par touche tapée
        if self._search_after:
            self.frame.after_cancel(self._search_after)
        self._search_after = self.frame.after(200, self.refresh_history)

    def refresh_history(self):
        self._search_after = None
        query = self.search_var.get().strip()
        receipts = self.controller.search_receipts(query) if query else self.controller.get_all_receipts()
        currency = self.controller.get_currency()

        selected = self.history_tree.selection()
        self.history_tree.delete(*self.history_tree.get_children())
        total = 0
        for i, (receipt_id, number, date, client, amount, created) in enumerate(receipts):
            total += amount or 0
            self.history_tree.insert('', END, iid=str(receipt_id), tags=(row_tag(i),), values=(
                number, fmt_date(date), client or "Client", fmt_money(amount, currency), fmt_datetime(created)))
        if selected and self.history_tree.exists(selected[0]):
            self.history_tree.selection_set(selected[0])

        n = len(receipts)
        label = "résultat" if query else "reçu"
        self.summary_var.set(f"{n} {label}{'s' if n > 1 else ''} • Total : {fmt_money(total, currency)}" if n else "")
        empty_state(self.history_tree,
                    f"Aucun reçu ne correspond à « {query} »" if query else
                    "Aucun reçu enregistré pour l'instant")
        self._update_buttons()

    # Compatibilité avec l'ancien nom
    search_history = refresh_history

    def _selected_id(self):
        selection = self.history_tree.selection()
        if not selection:
            self.main_window.toast.show("Sélectionnez d'abord un reçu dans la liste", "warning")
            return None
        return int(selection[0])

    # ---------- Actions ----------

    def view_receipt_details(self):
        receipt_id = self._selected_id()
        if receipt_id is None:
            return
        receipt = self.controller.get_receipt_details(receipt_id)
        if not receipt:
            messagebox.showerror("Erreur", "Reçu introuvable", parent=self.frame)
            return
        ReceiptDetailsDialog(self, receipt_id, receipt)

    def regenerate_receipt(self, receipt_id=None):
        receipt_id = receipt_id or self._selected_id()
        if receipt_id is None:
            return
        with busy(self.frame):
            success, result = self.controller.regenerate_receipt(receipt_id)
        if not success:
            messagebox.showerror("Erreur", result, parent=self.frame)
            return
        try:
            open_path(result)
            self.main_window.toast.show("PDF régénéré et ouvert")
        except Exception:
            self.main_window.toast.show(f"PDF régénéré : {result}")

    def _reprint(self, kind, receipt_id=None):
        receipt_id = receipt_id or self._selected_id()
        if receipt_id is None:
            return
        label = "thermique" if kind == 'thermal' else "laser (A6)"
        number = self.history_tree.set(str(receipt_id), "number") if self.history_tree.exists(str(receipt_id)) else ""
        if not messagebox.askyesno("Réimprimer", f"Réimprimer le reçu {number} sur l'imprimante {label} ?",
                                   parent=self.frame):
            return
        with busy(self.frame, self.main_window.toast, "Impression en cours…"):
            if kind == 'thermal':
                success, message = self.controller.reprint_thermal_receipt(receipt_id)
            else:
                success, message = self.controller.reprint_laser_receipt(receipt_id)
        if success:
            self.main_window.toast.show(message)
        else:
            messagebox.showerror("Erreur d'impression", message, parent=self.frame)

    def reprint_thermal_receipt(self, receipt_id=None):
        self._reprint('thermal', receipt_id)

    def reprint_laser_receipt(self, receipt_id=None):
        self._reprint('laser', receipt_id)

    def delete_receipt(self, receipt_id=None):
        receipt_id = receipt_id or self._selected_id()
        if receipt_id is None:
            return False
        number = self.history_tree.set(str(receipt_id), "number") if self.history_tree.exists(str(receipt_id)) else ""
        if not messagebox.askyesno("Supprimer le reçu",
                                   f"Supprimer définitivement le reçu {number} ?\n\nCette action est irréversible.",
                                   icon="warning", parent=self.frame):
            return False
        self.controller.delete_receipt(receipt_id)
        self.main_window.refresh_all_tabs()
        self.main_window.toast.show(f"Reçu {number} supprimé")
        return True

    def open_exports_folder(self):
        exports_path = os.path.abspath('exports')
        os.makedirs(exports_path, exist_ok=True)
        try:
            open_path(exports_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier : {e}", parent=self.frame)


class ReceiptDetailsDialog:
    """Fenêtre de détail d'un reçu, avec les actions directement accessibles"""

    def __init__(self, tab, receipt_id, receipt):
        self.tab = tab
        self.receipt_id = receipt_id
        parent = tab.frame.winfo_toplevel()
        currency = tab.controller.get_currency()

        self.win = ttk.Toplevel(title=f"Reçu {receipt['receipt_number']}")
        self.win.transient(parent)
        center_dialog(self.win, parent, 720, 600)
        self.win.bind("<Escape>", lambda e: self.win.destroy())

        body = ttk.Frame(self.win, padding=20)
        body.pack(fill=BOTH, expand=YES)

        head = ttk.Frame(body)
        head.pack(fill=X)
        ttk.Label(head, text=receipt['receipt_number'], font=("", 18, "bold"), bootstyle="primary").pack(side=LEFT)
        ttk.Label(head, text=fmt_date(receipt['date']), font=("", 13)).pack(side=RIGHT)

        info = ttk.Frame(body)
        info.pack(fill=X, pady=(12, 10))
        rows = [("Client", receipt['client_name'] or "Client"),
                ("Contact", receipt['client_contact'] or "—"),
                ("Paiement", receipt['payment_method']),
                ("Enregistré le", fmt_datetime(receipt.get('created_at')))]
        for r, (label, value) in enumerate(rows):
            ttk.Label(info, text=label, style="Muted.TLabel").grid(row=r, column=0, sticky=NW, pady=2, padx=(0, 16))
            ttk.Label(info, text=value, font=("", 11), wraplength=520, justify=LEFT).grid(row=r, column=1, sticky=W, pady=2)

        columns = [
            ("name", "Produit", 300, W, True),
            ("qty", "Qté", 70, CENTER, False),
            ("price", "Prix unit.", 120, E, False),
            ("total", "Total", 130, E, False),
        ]
        tree_frame, tree = make_tree(body, columns, height=7)
        tree_frame.pack(fill=BOTH, expand=YES)
        for i, item in enumerate(receipt['items']):
            tree.insert('', END, tags=(row_tag(i),), values=(
                item['name'], fmt_qty(item['quantity']), fmt_amount(item['unit_price']), fmt_amount(item['total'])))

        total_row = ttk.Frame(body)
        total_row.pack(fill=X, pady=(10, 12))
        ttk.Label(total_row, text="TOTAL", style="TotalCaption.TLabel").pack(side=LEFT)
        ttk.Label(total_row, text=fmt_money(receipt['total'], currency), font=("", 20, "bold"),
                  bootstyle="primary").pack(side=RIGHT)

        bar = ButtonBar(body, wide_columns=4, narrow_columns=2, breakpoint=500)
        bar.pack(fill=X)
        bar.add("🖨  Thermique", lambda: tab.reprint_thermal_receipt(receipt_id), "info")
        laser = bar.add("🖨  Laser A6", lambda: tab.reprint_laser_receipt(receipt_id), "info")
        bar.set_visible(laser, tab.controller.is_laser_enabled())
        bar.add("📄  PDF", lambda: tab.regenerate_receipt(receipt_id), "info-outline")
        bar.add("Fermer", self.win.destroy, "secondary-outline")

        self.win.focus_set()
