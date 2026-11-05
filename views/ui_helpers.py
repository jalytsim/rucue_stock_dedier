"""
Composants et helpers d'interface partagés par tous les onglets
"""
import os
import platform
import subprocess
from contextlib import contextmanager
from tkinter import font as tkfont

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Taille minimale d'une cible tactile (px)
TOUCH_IPADY = 10
COMPACT_BREAKPOINT = 1000


def setup_styles(root):
    """Typographie et styles globaux (une seule fois, au démarrage)"""
    for name, size in (("TkDefaultFont", 11), ("TkTextFont", 12), ("TkMenuFont", 11),
                       ("TkHeadingFont", 11)):
        try:
            tkfont.nametofont(name).configure(size=size)
        except Exception:
            pass

    style = ttk.Style()
    colors = style.colors
    style.configure("Treeview", rowheight=36, font=("", 11))
    style.configure("Treeview.Heading", font=("", 11, "bold"), padding=(6, 8))
    style.configure("TButton", font=("", 11, "bold"))
    style.configure("TNotebook.Tab", font=("", 12, "bold"), padding=(18, 10))
    style.configure("TLabelframe.Label", font=("", 12, "bold"))
    style.configure("Muted.TLabel", foreground=colors.secondary, font=("", 10))
    style.configure("FieldLabel.TLabel", font=("", 11, "bold"))
    style.configure("Big.TEntry", padding=8)
    style.configure("Total.TLabel", font=("", 30, "bold"), foreground=colors.primary)
    style.configure("TotalCaption.TLabel", font=("", 11, "bold"), foreground=colors.secondary)
    return style


def stripe_tree(tree):
    """Lignes alternées pour une lecture plus facile"""
    style = ttk.Style()
    tree.tag_configure("odd", background=style.colors.light)
    tree.tag_configure("even", background=style.colors.bg)


def row_tag(index):
    return "odd" if index % 2 else "even"


def make_tree(parent, columns, height=10, **kwargs):
    """Treeview + scrollbar dans un cadre. columns = [(id, titre, largeur, ancrage, stretch)]"""
    frame = ttk.Frame(parent)
    ids = [c[0] for c in columns]
    tree = ttk.Treeview(frame, columns=ids, show="headings", height=height,
                        bootstyle="primary", **kwargs)
    for col_id, title, width, anchor, stretch in columns:
        tree.heading(col_id, text=title, anchor=anchor)
        tree.column(col_id, width=width, minwidth=50, anchor=anchor, stretch=stretch)
    scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview, bootstyle="round")
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side=LEFT, fill=BOTH, expand=YES)
    scrollbar.pack(side=RIGHT, fill=Y, padx=(4, 0))
    stripe_tree(tree)
    return frame, tree


def empty_state(tree, message):
    """Affiche un message centré quand la liste est vide"""
    label = getattr(tree, "_empty_label", None)
    if label is None:
        label = ttk.Label(tree, text="", style="Muted.TLabel", anchor=CENTER, justify=CENTER)
        tree._empty_label = label
    if tree.get_children():
        label.place_forget()
    else:
        label.configure(text=message)
        label.place(relx=0.5, rely=0.5, anchor=CENTER)


class ButtonBar(ttk.Frame):
    """Barre de boutons qui passe sur plusieurs lignes quand la largeur est faible"""

    def __init__(self, parent, wide_columns=4, narrow_columns=2, breakpoint=COMPACT_BREAKPOINT):
        super().__init__(parent)
        self.buttons = []
        self.hidden = set()
        self.wide_columns = wide_columns
        self.narrow_columns = narrow_columns
        self.breakpoint = breakpoint
        self._columns = None
        self.bind("<Configure>", self._on_configure)

    def add(self, text, command, bootstyle="primary", span=1):
        btn = ttk.Button(self, text=text, command=command, bootstyle=bootstyle, cursor="hand2")
        self.buttons.append((btn, span))
        self._layout(self.wide_columns if self._columns is None else self._columns, force=True)
        return btn

    def set_visible(self, btn, visible):
        if visible:
            self.hidden.discard(btn)
        else:
            self.hidden.add(btn)
        self._layout(self._columns or self.wide_columns, force=True)

    def _on_configure(self, event):
        cols = self.wide_columns if event.width >= self.breakpoint else self.narrow_columns
        self._layout(cols)

    def _layout(self, cols, force=False):
        if cols == self._columns and not force:
            return
        self._columns = cols
        for i in range(max(self.wide_columns, self.narrow_columns)):
            self.columnconfigure(i, weight=1 if i < cols else 0, uniform="btn" if i < cols else "")
        row = col = 0
        for btn, span in self.buttons:
            if btn in self.hidden:
                btn.grid_remove()
                continue
            span = min(span, cols)
            if col + span > cols:
                row, col = row + 1, 0
            btn.grid(row=row, column=col, columnspan=span, sticky="ew", padx=3, pady=3,
                     ipady=TOUCH_IPADY)
            col += span


class Toast:
    """Notification non bloquante, affichée dans la fenêtre et fermée automatiquement"""

    def __init__(self, root):
        self.root = root
        self.frame = None
        self.after_id = None

    def show(self, message, bootstyle="success", duration=3500):
        self.hide()
        icons = {"success": "✔", "danger": "✖", "warning": "!", "info": "i"}
        self.frame = ttk.Frame(self.root, bootstyle=bootstyle, padding=(16, 12))
        ttk.Label(self.frame, text=f"{icons.get(bootstyle, '')}  {message}",
                  bootstyle=f"inverse-{bootstyle}", font=("", 12, "bold"),
                  wraplength=520, justify=LEFT).pack()
        self.frame.place(relx=1.0, rely=1.0, anchor=SE, x=-24, y=-64)
        self.frame.lift()
        self.frame.bind("<Button-1>", lambda e: self.hide())
        for child in self.frame.winfo_children():
            child.bind("<Button-1>", lambda e: self.hide())
        self.after_id = self.root.after(duration, self.hide)

    def hide(self):
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        if self.frame is not None:
            self.frame.destroy()
            self.frame = None


@contextmanager
def busy(widget, toast=None, message=None):
    """Curseur d'attente + message pendant une opération bloquante (impression...)"""
    root = widget.winfo_toplevel()
    if toast and message:
        toast.show(message, "info", duration=60000)
    root.configure(cursor="watch")
    root.update_idletasks()
    root.update()
    try:
        yield
    finally:
        root.configure(cursor="")
        if toast and message:
            toast.hide()


def open_path(path):
    """Ouvrir un fichier ou dossier avec l'application par défaut"""
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def center_dialog(dialog, parent, width, height):
    parent = parent.winfo_toplevel()
    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    dialog.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
