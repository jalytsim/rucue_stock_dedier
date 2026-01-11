import subprocess
import tempfile
from datetime import datetime
import os


class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'Custom.105x148mm')

        # Largeur réelle HP LaserJet sur A6 ≈ 40 colonnes
        self.line_width = 40

        # Hauteur réelle utilisable ≈ 36 lignes
        self.max_lines_per_page = 36

    # ----------------- SECTION HELPERS -----------------

    def _sep(self, char='='):
        return char * self.line_width + "\n"

    def side_by_side(self, left, right):
        left = left.strip()
        right = right.strip()

        total = len(left) + len(right)

        if total >= self.line_width:
            excess = total - self.line_width + 1
            if len(right) > len(left):
                right = right[:-excess]
            else:
                left = left[:-excess]

        spaces = self.line_width - len(left) - len(right)
        return left + (" " * spaces) + right + "\n"

    # ----------------- HEADER -----------------

    def _build_header(self, data):
        h = []

        h.append(self.side_by_side(self.settings.get('company_name', ''), "CLIENT"))
        h.append(self.side_by_side(self.settings.get('company_phone', ''), data.get('client_name', '')))
        h.append(self.side_by_side(f"NIF: {self.settings.get('company_nif', '')}", data.get('client_phone', '')))
        
        stat = self.settings.get('company_stat', '')
        if stat:
            h.append(self.side_by_side(f"STAT: {stat}", ""))

        for line in self.settings.get('company_address', '').split("\n"):
            h.append(self.side_by_side(line, ""))

        h.append(self._sep('-'))

        # Numéro et date
        no = f"No: {data['receipt_number']}"
        try:
            d = datetime.strptime(data['date'], "%Y-%m-%d")
            date = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date = f"Date: {data['date']}"

        h.append(self.side_by_side(no, date))

        h.append(self._sep())
        h.append("Liste des articles".center(self.line_width) + "\n")

        return h

    # ----------------- ITEMS -----------------

    def _build_items(self, data):
        currency = self.settings.get("currency", "Ar")
        out = []

        for i, item in enumerate(data["items"], 1):
            name = item["name"]
            if len(name) > self.line_width - 4:
                name = name[:self.line_width - 7] + "..."

            out.append(f"{i}. {name}\n")
            out.append(f"   {item['quantity']} x {item['unit_price']:,.0f} {currency} = {item['total']:,.0f} {currency}\n")

        return out

    # ----------------- FOOTER -----------------

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

    # ----------------- PAGINATION -----------------

    def _format_receipt_with_pagination(self, data):

        header = self._build_header(data)
        items = self._build_items(data)
        footer = self._build_footer(data)

        # On compte le nombre de lignes du footer
        footer_lines = len(footer)

        # Calcul total
        total_lines = len(header) + len(items) + footer_lines

        # ---------------------------------------------------------------------
        # CAS 1 : TOUT TIENS SUR UNE SEULE PAGE
        # footer doit être collé en bas → on insère des lignes vides
        # ---------------------------------------------------------------------
        if total_lines <= self.max_lines_per_page:
            lines = header + items

            # Nombre de lignes à remplir pour pousser le footer en bas
            padding = self.max_lines_per_page - len(lines) - footer_lines

            for _ in range(padding):
                lines.append("\n")

            lines.extend(footer)
            return "".join(lines)

        # ---------------------------------------------------------------------
        # CAS 2 : MULTIPAGE
        # Page 1 doit avoir footer en bas
        # Dernière page footer juste sous les items
        # ---------------------------------------------------------------------

        pages = []

        # PAGE 1 : header + premiers items + footer en bas
        page1 = []
        page1.extend(header)

        # combien de lignes dispo pour les items ?
        max_items_page1 = self.max_lines_per_page - len(header) - footer_lines

        page1_items = items[:max_items_page1]
        page1.extend(page1_items)

        # Ajouter padding pour pousser le footer en bas
        padding = self.max_lines_per_page - len(page1) - footer_lines
        for _ in range(padding):
            page1.append("\n")

        page1.extend(footer)

        pages.append("".join(page1))

        # ---------------------------------------------------------------------
        # PAGES INTERMÉDIAIRES : uniquement liste d’articles (remplies au max)
        # ---------------------------------------------------------------------

        remaining = items[max_items_page1:]
        temp = []

        for line in remaining:
            temp.append(line)

            if len(temp) == self.max_lines_per_page:
                pages.append("".join(temp))
                temp = []

        # ---------------------------------------------------------------------
        # Dernière page : pas besoin de mettre footer en bas
        # footer juste après les derniers articles
        # ---------------------------------------------------------------------

        if temp:
            temp.extend(footer)
            pages.append("".join(temp))

        return "\f".join(pages)

    # ----------------- PRINT -----------------

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
