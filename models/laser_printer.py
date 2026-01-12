import subprocess
import tempfile
from datetime import datetime
import os
from utils.name_formatter import format_client_name

class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'Custom.105x148mm')
        self.line_width = 40 
        self.max_lines_per_page = 43

    # ----------------------------
    # HELPERS
    # ----------------------------
    def _sep(self, char='='):
        return char * self.line_width + "\n"

    def side_by_side(self, left, right):
        left = str(left).strip()
        right = str(right).strip()
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
        client_name_raw = data.get('client_name', '')
        client_name = format_client_name(client_name_raw)

        client_lines = data.get('client_contact', '').split("\n")
        client_lines = [l.strip() for l in client_lines if l.strip()]
        client_lines = client_lines[:3]

        supplier_lines = [
            company.get('company_name', ''),
            company.get('company_phone', ''),
            f"NIF:{company.get('company_nif', '')}",
            f"STAT:{company.get('company_stat', '')}"
        ]
        supplier_lines.extend(company.get('company_address', '').split("\n"))

        h.append(self.side_by_side(supplier_lines[0], "DOIT"))
        h.append(self.side_by_side(supplier_lines[1], client_name))
        h.append(self.side_by_side(supplier_lines[2], client_lines[0] if len(client_lines) > 0 else ""))
        h.append(self.side_by_side(supplier_lines[3], client_lines[1] if len(client_lines) > 1 else ""))

        for i, addr_line in enumerate(supplier_lines[4:]):
            right_text = client_lines[2] if (i == 0 and len(client_lines) == 3) else ""
            h.append(self.side_by_side(addr_line, right_text))

        h.append(self._sep('-'))

        try:
            d = datetime.strptime(data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {data['date']}"
        h.append(self.side_by_side("", date_text))

        h.append(self._sep())
        return h

    # ----------------------------
    # ITEMS (Tableau avec Espacement)
    # ----------------------------
    def _build_items_table_lines(self, items_list):
        """ Crée les lignes du tableau avec un saut de ligne entre articles """
        table_lines = []
        # En-tête : Desc (18), Qté (4), P.U (8), Montant (8)
        header_row = f"{'Description':<18} {'Qté':>4} {'P.U':>8} {'Montant':>8}\n"
        table_lines.append(header_row)
        table_lines.append("-" * self.line_width + "\n")

        for item in items_list:
            name = item["name"][:17] 
            qty = str(item['quantity'])
            price = f"{item['unit_price']:,.0f}"
            total = f"{item['total']:,.0f}"
            
            # Ligne de l'article
            table_lines.append(f"{name:<18} {qty:>4} {price:>8} {total:>8}\n")
            # AJOUT D'UN ESPACE entre chaque article
            table_lines.append("\n") 
        
        return table_lines

    # ----------------------------
    # FOOTER
    # ----------------------------
    def _build_footer(self, data, page_num=1, total_pages=1):
        currency = self.settings.get("currency", "Ar")
        f = []
        f.append(self._sep())
        f.append("TOTAL A PAYER".center(self.line_width) + "\n")
        f.append(f"{data['total']:,.0f} {currency}".center(self.line_width) + "\n")
        f.append(f"Paiement: {data.get('payment_method', 'Espèces')}".center(self.line_width) + "\n")
        f.append(self._sep())
        f.append("Merci pour votre achat!".center(self.line_width) + "\n")
        f.append("Mankasitraka Tompoko!".center(self.line_width) + "\n")
        f.append(f"Page: {page_num}/{total_pages}".rjust(self.line_width) + "\n")
        return f

    # ----------------------------
    # PAGINATION
    # ----------------------------
    def _format_receipt_with_pagination(self, data):
        header = self._build_header(data)
        item_lines = self._build_items_table_lines(data["items"])
        
        # On calcule le nombre de lignes du footer complet
        temp_footer = self._build_footer(data, 1, 1)
        footer_len = len(temp_footer)
        
        # Zone disponible pour les articles (marge de sécurité de 2 lignes)
        available_lines = self.max_lines_per_page - len(header) - 2
        
        # Découpage par pages
        pages_items = []
        current_chunk = []
        for line in item_lines:
            current_chunk.append(line)
            if len(current_chunk) >= available_lines:
                pages_items.append(current_chunk)
                current_chunk = []
        if current_chunk:
            pages_items.append(current_chunk)
            
        total_pages = len(pages_items)
        formatted_pages = []
        
        for i, page_content in enumerate(pages_items):
            curr_num = i + 1
            page_output = []
            page_output.extend(header)
            page_output.extend(page_content)
            
            if curr_num == total_pages:
                # Page finale : On pousse le footer vers le bas
                padding = self.max_lines_per_page - len(page_output) - footer_len
                if padding > 0:
                    page_output.extend(["\n"] * padding)
                page_output.extend(self._build_footer(data, curr_num, total_pages))
            else:
                # Page intermédiaire : Juste le numéro de page en bas
                padding = self.max_lines_per_page - len(page_output) - 1
                if padding > 0:
                    page_output.extend(["\n"] * padding)
                page_output.append(f"Page: {curr_num}/{total_pages}".rjust(self.line_width) + "\n")
            
            formatted_pages.append("".join(page_output))

        return "\f".join(formatted_pages)

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
                    "lp", "-d", self.printer_name,
                    "-o", f"media={self.paper_format}",
                    "-o", "cpi=12", "-o", "lpi=8",
                    "-o", "page-left=5", "-o", "page-right=5",
                    "-o", "page-top=5", "-o", "page-bottom=5",
                    path
                ],
                capture_output=True, text=True, timeout=10
            )
            os.unlink(path)
            if result.returncode == 0:
                return True, "Impression OK"
            return False, result.stderr
        except Exception as e:
            return False, str(e)