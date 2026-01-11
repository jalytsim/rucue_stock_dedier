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

        total_lines = len(header) + len(items) + len(footer)

        # --------- CAS 1 : 1 SEULE PAGE ---------
        if total_lines <= self.max_lines_per_page:
            return "".join(header + items + footer)

        # --------- CAS 2 : MULTI-PAGE ---------
        pages = []

        # Première page : Header + Items jusqu'à limite
        page1 = []
        page1.extend(header)

        lines_left = self.max_lines_per_page - len(page1) - len(footer)

        # Ajoute les items jusqu'à remplir la page
        page1.extend(items[:lines_left])
        pages.append("".join(page1))

        # Items restants
        remaining = items[lines_left:]
        current = []

        for line in remaining:
            current.append(line)

            if len(current) >= self.max_lines_per_page - len(footer):
                pages.append("".join(current))
                current = []

        # Ajouter dernier bloc + footer
        current.extend(footer)
        pages.append("".join(current))

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
