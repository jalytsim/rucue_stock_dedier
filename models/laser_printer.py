import subprocess
import tempfile
from datetime import datetime
import os
from utils.name_formatter import format_client_name  # Chemin vers ton NameFormatter

class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'Custom.105x148mm')
        self.line_width = 40       # largeur réelle imprimable en colonnes
        self.max_lines_per_page = 43  # hauteur réelle utilisable

    # ----------------------------
    # HELPERS
    # ----------------------------
    def _sep(self, char='='):
        return char * self.line_width + "\n"

    def side_by_side(self, left, right):
        """ Affiche deux textes alignés gauche + droite sur une seule ligne """
        left = left.strip()
        right = right.strip()
        total_len = len(left) + len(right)
        if total_len >= self.line_width:
            excess = total_len - self.line_width + 1
            if len(right) > len(left):
                right = right[:-excess]
            else:
                left = left[:-excess]
        spaces = self.line_width - len(left) - len(right)
        return left + (" " * spaces) + right + "\n"

    # ----------------------------
    # HEADER
    # ----------------------------
    def _build_header(self, data):
        h = []
        company = self.settings

        # Nom du client formaté
        client_name_raw = data.get('client_name', '')
        client_name = format_client_name(client_name_raw)

        # Gestion multi-lignes du contact / adresse client (max 3 lignes)
        client_lines = data.get('client_contact', '').split("\n")
        client_lines = [l.strip() for l in client_lines if l.strip()]
        client_lines = client_lines[:3]

        # Lignes fournisseur
        supplier_lines = [
            company.get('company_name', ''),
            company.get('company_phone', ''),
            f"NIF: {company.get('company_nif', '')}",
            f"STAT: {company.get('company_stat', '')}"
        ]
        supplier_lines.extend(company.get('company_address', '').split("\n"))

        # Construction des lignes avec side_by_side
        h.append(self.side_by_side(supplier_lines[0], "DOIT"))
        h.append(self.side_by_side(supplier_lines[1], client_name))
        h.append(self.side_by_side(supplier_lines[2], client_lines[0] if len(client_lines) > 0 else ""))
        h.append(self.side_by_side(supplier_lines[3], client_lines[1] if len(client_lines) > 1 else ""))

        # Adresse fournisseur + 3ème ligne client si dispo
        for i, addr_line in enumerate(supplier_lines[4:]):
            right_text = client_lines[2] if (i == 0 and len(client_lines) == 3) else ""
            h.append(self.side_by_side(addr_line, right_text))

        h.append(self._sep('-'))

        # Date
        try:
            d = datetime.strptime(data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {data['date']}"
        h.append(self.side_by_side("", date_text))

        h.append(self._sep())
        h.append("Liste des articles".center(self.line_width) + "\n")
        return h

    # ----------------------------
    # ITEMS
    # ----------------------------
    def _build_items(self, data):
        currency = self.settings.get("currency", "Ar")
        out = []
        for i, item in enumerate(data["items"], 1):
            name = item["name"]
            max_len = self.line_width - 4
            if len(name) > max_len:
                name = name[:max_len - 3] + "..."
            out.append(f"{i}. {name}\n")
            out.append(f"   {item['quantity']} x {item['unit_price']:,.0f} {currency} = {item['total']:,.0f} {currency}\n")
        return out

    # ----------------------------
    # FOOTER
    # ----------------------------
    def _build_footer(self, data):
        currency = self.settings.get("currency", "Ar")
        f = []
        f.append(self._sep())
        f.append("TOTAL A PAYER".center(self.line_width) + "\n")
        f.append(f"{data['total']:,.0f} {currency}".center(self.line_width) + "\n")
        f.append(f"Paiement: {data.get('payment_method', 'Espèces')}".center(self.line_width) + "\n")
        f.append(self._sep())
        f.append("Merci pour votre achat!".center(self.line_width) + "\n")
        f.append("Mankasitraka Tompoko!".center(self.line_width) + "\n")
        return f

    # ----------------------------
    # PAGINATION
    # ----------------------------
    def _format_receipt_with_pagination(self, data):
        header = self._build_header(data)
        items = self._build_items(data)
        footer = self._build_footer(data)
        footer_lines = len(footer)
        total_lines = len(header) + len(items) + footer_lines

        if total_lines <= self.max_lines_per_page:
            lines = header + items
            footer_count = sum(f.count("\n") for f in footer)
            while len(lines) + footer_count < self.max_lines_per_page:
                lines.append("\n")
            lines.extend(footer)
            return "".join(lines)

        pages = []
        # Page 1
        page1 = header.copy()
        max_items_page1 = self.max_lines_per_page - len(header) - footer_lines
        page1_items = items[:max_items_page1]
        page1.extend(page1_items)
        padding = self.max_lines_per_page - len(page1) - footer_lines
        page1.extend(["\n"] * padding)
        page1.extend(footer)
        pages.append("".join(page1))

        # Pages suivantes
        remaining = items[max_items_page1:]
        temp = []
        for line in remaining:
            temp.append(line)
            if len(temp) == self.max_lines_per_page:
                pages.append("".join(temp))
                temp = []
        if temp:
            temp.extend(footer)
            pages.append("".join(temp))

        return "\f".join(pages)

    # ----------------------------
    # PRINT
    # ----------------------------
    def print_receipt(self, data):
        try:
            content = self._format_receipt_with_pagination(data)
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
                tmp.write(content)
                path = tmp.name

            result = subprocess.run(
                [
                    "lp",
                    "-d", self.printer_name,
                    "-o", f"media={self.paper_format}",
                    "-o", "cpi=12",
                    "-o", "lpi=8",
                    "-o", "page-left=5",
                    "-o", "page-right=5",
                    "-o", "page-top=5",
                    "-o", "page-bottom=5",
                    path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            os.unlink(path)
            if result.returncode == 0:
                return True, "Impression OK"
            return False, result.stderr
        except Exception as e:
            return False, str(e)
