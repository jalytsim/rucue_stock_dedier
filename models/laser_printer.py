import os
import shutil
import subprocess
import tempfile
from datetime import datetime

from utils.formatting import fmt_amount, fmt_qty, number_to_french
from utils.name_formatter import format_client_name

class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'Custom.105x148mm')
        self.line_width = 40 
        self.max_lines_per_page = 40
        
        # Tes quotas d'articles par page
        self.items_first_page = 14
        self.items_middle_page = 20
        self.items_last_page = 14

    def _number_to_french(self, n):
        """Convertit un nombre en lettres françaises"""
        return number_to_french(n)

    def _sep(self, char='='):
        return char * self.line_width + "\n"

    def side_by_side(self, left, right):
        left, right = str(left).strip(), str(right).strip()
        total_len = len(left) + len(right)
        if total_len >= self.line_width:
            excess = total_len - self.line_width + 1
            if len(right) > len(left): right = right[:-excess]
            else: left = left[:-excess]
        spaces = self.line_width - len(left) - len(right)
        return left + (" " * spaces) + right + "\n"

    def _build_header(self, data):
        h = []
        company = self.settings
        client_name = format_client_name(data.get('client_name', ''))
        client_lines = [l.strip() for l in data.get('client_contact', '').split("\n") if l.strip()][:3]
        
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
        
        for i, addr_line in enumerate(supplier_lines[4:6]):
            right_text = client_lines[2] if (i == 0 and len(client_lines) == 3) else ""
            h.append(self.side_by_side(addr_line, right_text))

        h.append(self._sep('-'))
        try:
            d = datetime.strptime(data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {data.get('date', '')}"
        h.append(self.side_by_side(f"No: {data.get('receipt_number', '')}", date_text))
        h.append(self._sep())
        return h

    def _get_item_row(self, item):
        name = item["name"][:17] 
        qty = fmt_qty(item['quantity'])
        price = fmt_amount(item['unit_price'])
        total = fmt_amount(item['total'])
        return f"{name:<18} {qty:>4} {price:>8} {total:>8}\n"

    def _build_footer(self, data):
        currency = self.settings.get("currency", "Ar")
        total_amount = int(data['total'])
        amount_in_words = self._number_to_french(total_amount).capitalize()
        
        f = [self._sep()]
        amount_str = f"{fmt_amount(total_amount)} {currency}"
        spaces_needed = self.line_width - len("Total") - len(amount_str)
        f.append("Total" + (" " * spaces_needed) + amount_str + "\n")
        
        words_line = f"En lettre: {amount_in_words} {currency.lower()}"
        if len(words_line) <= self.line_width:
            f.append(words_line + "\n")
        else:
            f.append("En lettre:\n")
            words = (amount_in_words + " " + currency.lower()).split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= self.line_width:
                    current_line += word + " "
                else:
                    f.append(current_line.strip() + "\n")
                    current_line = word + " "
            if current_line: f.append(current_line.strip() + "\n")
        
        f.append("\n" + "La gérance".rjust(self.line_width) + "\n")
        f.append("................".rjust(self.line_width) + "\n")
        f.append("\n" + self._sep())
        f.append("Merci pour votre achat!".center(self.line_width) + "\n")
        f.append("Mankasitraka Tompoko!".center(self.line_width) + "\n")
        return f

    def _format_receipt_with_pagination(self, data):
        items = data["items"]
        header = self._build_header(data)
        footer = self._build_footer(data)
        col_header = [f"{'Description':<18} {'Qté':>4} {'P.U':>8} {'Montant':>8}\n", "-"*self.line_width + "\n"]

        # --- DÉCOUPAGE PAR QUOTAS ---
        pages_items = []
        temp_items = list(items)

        if len(temp_items) <= self.items_first_page and len(temp_items) <= self.items_last_page:
            pages_items.append(temp_items)
        else:
            pages_items.append(temp_items[:self.items_first_page])
            temp_items = temp_items[self.items_first_page:]
            while len(temp_items) > self.items_last_page:
                pages_items.append(temp_items[:self.items_middle_page])
                temp_items = temp_items[self.items_middle_page:]
            if temp_items:
                pages_items.append(temp_items)

        total_pages = len(pages_items)
        final_output = []

        for i, page_content in enumerate(pages_items):
            page_num = i + 1
            is_first, is_last = (page_num == 1), (page_num == total_pages)
            
            p_text = []
            if is_first: p_text.extend(header)
            p_text.extend(col_header)

            for item in page_content:
                p_text.append(self._get_item_row(item))
                p_text.append("\n")

            used = len(p_text)
            reserved = (len(footer) if is_last else 0) + 1
            padding = self.max_lines_per_page - used - reserved
            if padding > 0: p_text.extend(["\n"] * padding)
            if is_last: p_text.extend(footer)

            p_text.append(f"Page: {page_num}/{total_pages}".rjust(self.line_width) + "\n")
            final_output.append("".join(p_text))

        return "\f".join(final_output)

    def _lp_available(self):
        return shutil.which("lp") is not None

    def print_receipt(self, data):
        if not self._lp_available():
            return False, ("Commande d'impression 'lp' (CUPS) introuvable.\n"
                           "L'impression laser directe fonctionne sous Linux avec CUPS.\n"
                           "Utilisez « Générer PDF » puis imprimez le PDF.")
        path = None
        try:
            content = self._format_receipt_with_pagination(data).strip()
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt",
                                             encoding="utf-8") as tmp:
                tmp.write(content)
                path = tmp.name

            result = subprocess.run(
                ["lp", "-d", self.printer_name, "-o", f"media={self.paper_format}",
                 "-o", "cpi=12", "-o", "lpi=8",
                 "-o", "page-left=5", "-o", "page-right=5",
                 "-o", "page-top=5", "-o", "page-bottom=5",
                 "-o", "fit-to-page", path],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, "Impression OK"
            return False, result.stderr.strip() or f"lp a échoué (code {result.returncode})"
        except subprocess.TimeoutExpired:
            return False, "L'imprimante ne répond pas (délai dépassé)"
        except Exception as e:
            return False, str(e)
        finally:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def check_connection(self):
        """Vérifier que l'imprimante est connue de CUPS et disponible"""
        if not shutil.which("lpstat"):
            return False, ("Commande 'lpstat' (CUPS) introuvable sur ce système.\n"
                           "L'impression laser directe nécessite Linux avec CUPS.")
        try:
            result = subprocess.run(["lpstat", "-p", self.printer_name],
                                    capture_output=True, text=True, timeout=5)
        except subprocess.TimeoutExpired:
            return False, "CUPS ne répond pas (délai dépassé)"
        if result.returncode != 0:
            return False, (f"Imprimante « {self.printer_name} » introuvable.\n"
                           f"{result.stderr.strip()}")
        status = result.stdout.strip()
        if "disabled" in status or "désactivée" in status:
            return False, f"Imprimante « {self.printer_name} » désactivée :\n{status}"
        return True, f"Imprimante « {self.printer_name} » disponible\n{status}"

    def test_print(self):
        """Imprimer un reçu de test"""
        data = {
            "receipt_number": "TEST-00001",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "client_name": "Client Test",
            "client_contact": "034 00 000 00\nAntananarivo",
            "items": [
                {"name": "Produit de test 1", "quantity": 2, "unit_price": 5000, "total": 10000},
                {"name": "Produit de test 2", "quantity": 1, "unit_price": 15000, "total": 15000},
            ],
            "total": 25000,
            "payment_method": "Espèces",
        }
        return self.print_receipt(data)
