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
            f"NIF: {company.get('company_nif', '')}",
            f"STAT: {company.get('company_stat', '')}"
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
    # TABLE ROWS GENERATOR
    # ----------------------------
    def _get_item_row(self, item):
        name = item["name"][:17] 
        qty = str(item['quantity'])
        price = f"{item['unit_price']:,.0f}"
        total = f"{item['total']:,.0f}"
        return f"{name:<18} {qty:>4} {price:>8} {total:>8}\n"

    # ----------------------------
    # FOOTER
    # ----------------------------
    def _build_footer(self, data, page_num, total_pages):
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
    # PAGINATION LOGIC
    # ----------------------------
    def _format_receipt_with_pagination(self, data):
        items = data["items"]
        header = self._build_header(data)
        
        # 1. Découpage des items (Page 1 max 15 items, puis ~18 par page suite car pas de header)
        pages_items_list = []
        if len(items) > 15:
            pages_items_list.append(items[:15])
            remaining = items[15:]
            # Pour les pages suivantes, on peut mettre plus d'items car le header n'est pas répété
            # (ou vous pouvez choisir de répéter le header, ici on ne le répète pas pour gagner de la place)
            chunk_size = 18 
            for i in range(0, len(remaining), chunk_size):
                pages_items_list.append(remaining[i:i + chunk_size])
        else:
            pages_items_list.append(items)

        total_pages = len(pages_items_list) + 1 # +1 pour la page du footer
        formatted_pages = []

        # 2. Construction des pages d'articles
        for i, page_items in enumerate(pages_items_list):
            curr_num = i + 1
            page_output = []
            
            # On ne met le header que sur la première page
            if curr_num == 1:
                page_output.extend(header)
            
            # En-tête du tableau
            page_output.append(f"{'Description':<18} {'Qté':>4} {'P.U':>8} {'Montant':>8}\n")
            page_output.append("-" * self.line_width + "\n")
            
            # Contenu des articles
            for item in page_items:
                page_output.append(self._get_item_row(item))
                page_output.append("\n") # Espacement entre lignes
            
            # Bas de page : Numérotation uniquement
            padding = self.max_lines_per_page - len(page_output) - 1
            if padding > 0:
                page_output.extend(["\n"] * padding)
            page_output.append(f"Page: {curr_num}/{total_pages}".rjust(self.line_width) + "\n")
            
            formatted_pages.append("".join(page_output))

        # 3. Construction de la page finale (FOOTER SEUL)
        footer_page = []
        footer_content = self._build_footer(data, total_pages, total_pages)
        
        # Pousser le footer tout en bas de la page 43
        padding_footer = self.max_lines_per_page - len(footer_content)
        if padding_footer > 0:
            footer_page.extend(["\n"] * padding_footer)
        
        footer_page.extend(footer_content)
        formatted_pages.append("".join(footer_page))

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