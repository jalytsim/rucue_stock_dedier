"""
Onglet Paramètres - entreprise, préférences, imprimantes, données
"""
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame

from views.ui_helpers import TOUCH_IPADY, busy

COMPANY_FIELDS = [
    ('company_name', "Nom de l'entreprise", None),
    ('company_address', "Adresse", "une ligne par ligne imprimée"),
    ('company_phone', "Téléphone", None),
    ('company_email', "Email", None),
    ('company_nif', "NIF", None),
    ('company_stat', "STAT", None),
    ('company_rc', "R.C", None),
    ('company_ce', "CE", None),
    ('company_cif', "CIF", None),
]


class SettingsTab:
    def __init__(self, parent, controller, main_window):
        self.controller = controller
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        self.settings_vars = {}
        self.laser_enabled_var = ttk.BooleanVar()
        self.status_var = ttk.StringVar()

        self.create_widgets()
        self.load_settings()

    # ---------- Construction ----------

    def create_widgets(self):
        footer = ttk.Frame(self.frame, padding=(10, 8))
        footer.pack(fill=X, side=BOTTOM)
        ttk.Separator(self.frame, orient=HORIZONTAL).pack(fill=X, side=BOTTOM)
        ttk.Label(footer, textvariable=self.status_var, bootstyle="warning",
                  font=("", 10, "bold")).pack(side=LEFT, padx=6)
        ttk.Button(footer, text="↺  Annuler les modifications", command=self.load_settings,
                   bootstyle="secondary-outline", cursor="hand2").pack(side=RIGHT, padx=(6, 0), ipady=TOUCH_IPADY)
        ttk.Button(footer, text="💾  Enregistrer  (Ctrl+S)", command=self.save_settings,
                   bootstyle="success", cursor="hand2").pack(side=RIGHT, ipady=TOUCH_IPADY, ipadx=20)

        container = ScrolledFrame(self.frame, autohide=True)
        container.pack(fill=BOTH, expand=YES, padx=10, pady=(10, 0))
        content = container  # le ScrolledFrame lui-même est la zone défilante

        self._create_company_section(content)
        self._create_preferences_section(content)
        self._create_printers_section(content)
        self._create_danger_zone(content)

        self.frame.bind_all("<Control-s>", self._shortcut_save, add="+")

    def _section(self, parent, title, style):
        frame = ttk.Labelframe(parent, text=f" {title} ", bootstyle=style, padding=(16, 8, 16, 14))
        frame.pack(fill=X, pady=(0, 12), padx=(0, 12))
        frame.columnconfigure(1, weight=1)
        return frame

    def _row_label(self, parent, row, text, hint=None):
        cell = ttk.Frame(parent)
        cell.grid(row=row, column=0, sticky=NW, pady=6, padx=(0, 16))
        ttk.Label(cell, text=text, style="FieldLabel.TLabel").pack(anchor=W)
        if hint:
            ttk.Label(cell, text=hint, style="Muted.TLabel").pack(anchor=W)

    def _entry_row(self, parent, row, key, label, hint=None, widget="entry", values=None):
        self._row_label(parent, row, label, hint)
        var = ttk.StringVar()
        var.trace_add('write', self._mark_dirty)
        self.settings_vars[key] = var
        if widget == "combo":
            w = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", font=("", 12), width=18)
            w.grid(row=row, column=1, sticky=W, pady=6, ipady=3)
        else:
            w = ttk.Entry(parent, textvariable=var, font=("", 12))
            w.grid(row=row, column=1, sticky=EW, pady=6, ipady=3)
        return w

    def _create_company_section(self, parent):
        frame = self._section(parent, "Informations de l'entreprise (imprimées sur les reçus)", "primary")
        for row, (key, label, hint) in enumerate(COMPANY_FIELDS):
            if key == 'company_address':
                self._row_label(frame, row, label, hint)
                self.address_text = ttk.Text(frame, height=3, font=("", 12), wrap=WORD)
                self.address_text.grid(row=row, column=1, sticky=EW, pady=6)
                self.address_text.bind("<<Modified>>", self._on_address_modified)
                self.address_text.bind("<Tab>", lambda e: (e.widget.tk_focusNext().focus_set(), "break")[1])
            else:
                self._entry_row(frame, row, key, label, hint)

    def _create_preferences_section(self, parent):
        frame = self._section(parent, "Préférences", "info")
        self._entry_row(frame, 0, 'currency', "Devise", widget="combo", values=['Ar', '€', '$', 'FCFA'])
        self._entry_row(frame, 1, 'paper_width', "Largeur papier (mm)", "format du PDF",
                        widget="combo", values=['58', '80'])
        self._entry_row(frame, 2, 'receipt_type', "Type de vente")

    def _create_printers_section(self, parent):
        frame = self._section(parent, "Imprimantes", "success")

        self._row_label(frame, 0, "Thermique", "XP-Q300 (USB)")
        ttk.Button(frame, text="🔍  Tester la connexion", command=self.test_thermal_connection,
                   bootstyle="success-outline", cursor="hand2").grid(row=0, column=1, sticky=W, pady=6, ipady=6)

        ttk.Separator(frame).grid(row=1, column=0, columnspan=2, sticky=EW, pady=8)

        self._row_label(frame, 2, "Laser activée", "affiche les boutons « Laser A6 »")
        ttk.Checkbutton(frame, variable=self.laser_enabled_var, bootstyle="success-round-toggle",
                        command=self._mark_dirty).grid(row=2, column=1, sticky=W, pady=6)
        self._entry_row(frame, 3, 'laser_printer_name', "Nom de l'imprimante", "nom CUPS, ex : HP_LaserJet_1022n")
        self._entry_row(frame, 4, 'laser_paper_format', "Format papier", widget="combo", values=["A6", "A5", "A4"])

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=1, sticky=W, pady=6)
        ttk.Button(buttons, text="🔍  Tester la connexion", command=self.test_laser_connection,
                   bootstyle="success-outline", cursor="hand2").pack(side=LEFT, ipady=6, padx=(0, 8))
        ttk.Button(buttons, text="🖨  Imprimer une page de test", command=self.test_laser_print,
                   bootstyle="success-outline", cursor="hand2").pack(side=LEFT, ipady=6)

    def _create_danger_zone(self, parent):
        frame = self._section(parent, "Zone dangereuse — actions irréversibles", "danger")
        ttk.Label(frame, text="Ces actions suppriment définitivement des données. Faites une copie du dossier "
                              "« data » avant si nécessaire.", style="Muted.TLabel",
                  wraplength=700, justify=LEFT).grid(row=0, column=0, columnspan=2, sticky=W, pady=(0, 8))
        buttons = ttk.Frame(frame)
        buttons.grid(row=1, column=0, columnspan=2, sticky=W)
        for text, cmd in (("Effacer l'historique", self.clear_history),
                          ("Effacer les produits", self.clear_products),
                          ("Tout réinitialiser", self.reset_all)):
            ttk.Button(buttons, text=text, command=cmd, bootstyle="danger-outline",
                       cursor="hand2").pack(side=LEFT, padx=(0, 8), ipady=6)

    # ---------- Chargement / sauvegarde ----------

    def _mark_dirty(self, *args):
        if not getattr(self, "_loading", False):
            self.status_var.set("●  Modifications non enregistrées")

    def _on_address_modified(self, event=None):
        if self.address_text.edit_modified():
            self._mark_dirty()
            self.address_text.edit_modified(False)

    def load_settings(self):
        self._loading = True
        settings = self.controller.get_settings()
        for key, var in self.settings_vars.items():
            var.set(settings.get(key, ''))
        self.address_text.delete("1.0", END)
        self.address_text.insert("1.0", settings.get('company_address', ''))
        self.address_text.edit_modified(False)
        self.laser_enabled_var.set(settings.get('laser_enabled', 'true') == 'true')
        self._loading = False
        self.status_var.set("")

    def _shortcut_save(self, event=None):
        if self.main_window.notebook.select() == str(self.frame):
            self.save_settings()
            return "break"

    def save_settings(self):
        settings_dict = {key: var.get().strip() for key, var in self.settings_vars.items()}
        if not settings_dict.get('company_name'):
            messagebox.showwarning("Champ obligatoire", "Le nom de l'entreprise est obligatoire.", parent=self.frame)
            return
        address_lines = [l.strip() for l in self.address_text.get("1.0", "end-1c").splitlines()]
        settings_dict['company_address'] = "\n".join(l for l in address_lines if l)
        settings_dict['laser_enabled'] = 'true' if self.laser_enabled_var.get() else 'false'

        self.controller.save_settings(settings_dict)
        self.status_var.set("")
        self.main_window.refresh_all_tabs()
        self.main_window.toast.show("Paramètres enregistrés")

    # ---------- Tests imprimantes ----------

    def _show_result(self, success, message):
        if success:
            messagebox.showinfo("Test réussi", message, parent=self.frame)
        else:
            messagebox.showerror("Test échoué", message, parent=self.frame)

    def test_thermal_connection(self):
        with busy(self.frame):
            result = self.controller.test_thermal_printer()
        self._show_result(*result)

    def test_laser_connection(self):
        with busy(self.frame):
            result = self.controller.test_laser_printer()
        self._show_result(*result)

    def test_laser_print(self):
        with busy(self.frame):
            result = self.controller.test_laser_print()
        self._show_result(*result)

    # ---------- Zone dangereuse ----------

    def _confirm(self, title, message):
        return messagebox.askyesno(title, f"{message}\n\nCette action est irréversible.",
                                   icon="warning", parent=self.frame)

    def clear_history(self):
        if self._confirm("Effacer l'historique", "Supprimer TOUS les reçus de l'historique ?"):
            self.controller.db.clear_all_receipts()
            self.main_window.refresh_all_tabs()
            self.main_window.toast.show("Historique effacé")

    def clear_products(self):
        if self._confirm("Effacer les produits", "Supprimer TOUS les produits mémorisés ?"):
            self.controller.db.clear_all_products()
            self.main_window.refresh_all_tabs()
            self.main_window.toast.show("Produits effacés")

    def reset_all(self):
        if self._confirm("Tout réinitialiser", "Supprimer TOUS les reçus et TOUS les produits ?") and \
                messagebox.askyesno("Dernière confirmation", "Êtes-vous vraiment sûr de vouloir tout supprimer ?",
                                    icon="warning", parent=self.frame):
            self.controller.clear_all_data()
            self.main_window.new_receipt_tab.reset_form()
            self.main_window.refresh_all_tabs()
            self.main_window.toast.show("Toutes les données ont été réinitialisées")
