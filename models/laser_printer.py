import subprocess
import tempfile
from datetime import datetime
import os


class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings

        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'Custom.105x148mm')

        self.line_width = 40       # largeur réelle imprimable en colonnes
        self.max_lines_per_page = 43  # hauteur réelle utilisable

    # ----------------------------------------------------
    # HELPERS
    # ----------------------------------------------------

    def _sep(self, char='='):
        return char * self.line_width + "\n"

    def side_by_side(self, left, right):
        """ Affiche deux textes alignés gauche + droite sur une seule ligne. """
        left = left.strip()
        right = right.strip()

        total = len(left) + len(right)

        # Tronquer si trop large
        if total >= self.line_width:
            excess = total - self.line_width + 1
            if len(right) > len(left):
                right = right[:-excess]
            else:
                left = left[:-excess]

        spaces = self.line_width - len(left) - len(right)
        return left + (" " * spaces) + right + "\n"

    # ----------------------------------------------------
    # HEADER
    # ----------------------------------------------------

    def _build_header(self, data):
        h = []

        company = self.settings

        # Récupération des infos client multi-lignes (max 3 lignes)
        client_contact_lines = data.get('client_contact', '').split("\n")
        client_contact_lines = [l.strip() for l in client_contact_lines if l.strip()]  # nettoyer les lignes vides
        client_contact_lines = client_contact_lines[:3]  # max 3 lignes

        # Préparation des lignes fournisseur
        supplier_lines = [
            company.get('company_name', ''),
            company.get('company_phone', ''),
            f"NIF: {company.get('company_nif', '')}",
            f"STAT: {company.get('company_stat', '')}"
        ]

        # Ajout des lignes d'adresse du fournisseur
        supplier_lines.extend(company.get('company_address', '').split("\n"))

        # Construction des paires fournisseur/client
        # ------------------------------------------------
        # Ligne 0 : company_name + "DOIT"
        h.append(self.side_by_side(supplier_lines[0], "DOIT"))

        # Ligne 1 : phone + nom client
        h.append(self.side_by_side(supplier_lines[1], data.get('client_name', '')))

        # Ligne 2 : NIF + 1ère ligne client (si existe)
        h.append(self.side_by_side(supplier_lines[2], client_contact_lines[0] if len(client_contact_lines) > 0 else ""))

        # Ligne 3 : STAT + 2ème ligne client
        h.append(self.side_by_side(supplier_lines[3], client_contact_lines[1] if len(client_contact_lines) > 1 else ""))

        # Ligne 4+ : adresses fournisseurs + 3ème ligne client si dispo
        addr_index = 4
        for i, addr_line in enumerate(supplier_lines[4:]):
            right_text = client_contact_lines[2] if (i == 0 and len(client_contact_lines) == 3) else ""
            h.append(self.side_by_side(addr_line, right_text))

        h.append(self._sep('-'))

        # DATE
        try:
            d = datetime.strptime(data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {data['date']}"

        h.append(self.side_by_side("", date_text))

        h.append(self._sep())
        h.append("Liste des articles".center(self.line_width) + "\n")

        return h



    # ----------------------------------------------------
    # ITEMS
    # ----------------------------------------------------

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

    # ----------------------------------------------------
    # FOOTER
    # ----------------------------------------------------

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

    # ----------------------------------------------------
    # PAGINATION
    # ----------------------------------------------------

    def _format_receipt_with_pagination(self, data):
        header = self._build_header(data)
        items = self._build_items(data)
        footer = self._build_footer(data)

        footer_lines = len(footer)
        total_lines = len(header) + len(items) + footer_lines

        # CAS 1 : une seule page
        if total_lines <= self.max_lines_per_page:
            lines = header + items
            footer_count = sum(f.count("\n") for f in footer)

            while len(lines) + footer_count < self.max_lines_per_page:
                lines.append("\n")

            lines.extend(footer)
            return "".join(lines)

        # --------------------------------------------------------
        # CAS 2 : MULTI-PAGES
        # --------------------------------------------------------

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

        # Pages intermédiaires
        remaining = items[max_items_page1:]
        temp = []

        for line in remaining:
            temp.append(line)
            if len(temp) == self.max_lines_per_page:
                pages.append("".join(temp))
                temp = []

        # Dernière page
        if temp:
            temp.extend(footer)
            pages.append("".join(temp))

        return "\f".join(pages)

    # ----------------------------------------------------
    # PRINT
    # ----------------------------------------------------

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
