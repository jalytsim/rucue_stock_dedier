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
        self.max_lines_per_page = 40
        
        # Quotas d'articles par type de page
        self.items_first_page = 14
        self.items_middle_page = 20
        self.items_last_page = 14

    def _number_to_french(self, n):
        """Convertit un nombre en lettres françaises (version simplifiée)"""
        if n == 0: return "zéro"
        units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        teens = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
        tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante", "quatre-vingt", "quatre-vingt"]
        
        def convert_below_100(n):
            if n < 10: return units[n]
            elif n < 20: return teens[n - 10]
            elif n < 70:
                u, t = n % 10, n // 10
                if u == 0: return tens[t]
                return f"{tens[t]} et un" if u == 1 else f"{tens[t]}-{units[u]}"
            elif n < 80: return f"soixante-{teens[n - 70]}"
            elif n < 100:
                u = n % 10
                if n == 80: return "quatre-vingts"
                return f"quatre-vingt-{units[u]}"
            return ""

        def convert_below_1000(n):
            if n < 100: return convert_below_100(n)
            h, r = n // 100, n % 100
            res = "cent" if h == 1 else f"{units[h]} cent"
            if r == 0: return res + ("s" if h > 1 else "")
            return f"{res} {convert_below_100(r)}"

        if n < 1000: return convert_below_1000(n)
        if n < 1000000:
            th, r = n // 1000, n % 1000
            res = "mille" if th == 1 else f"{convert_below_1000(th)} mille"
            return f"{res} {convert_below_1000(r)}" if r > 0 else res
        return "nombre trop grand"

    def _sep(self, char='='):
        return char * self.line_width + "\n"

    def side_by_side(self, left, right):
        left, right = str(left).strip(), str(right).strip()
        spaces = max(1, self.line_width - len(left) - len(right))
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
        
        for i, addr_line in enumerate(supplier_lines[4:6]): # Limité pour gagner de la place
            right_text = client_lines[2] if (i == 0 and len(client_lines) == 3) else ""
            h.append(self.side_by_side(addr_line, right_text))

        h.append(self._sep('-'))
        d_str = data.get('date', datetime.now().strftime("%Y-%m-%d"))
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {d_str}"
        h.append(self.side_by_side("", date_text))
        h.append(self._sep())
        return h

    def _get_item_row(self, item):
        name = item["name"][:17] 
        qty = str(item['quantity'])
        price = f"{item['unit_price']:,.0f}"
        total = f"{item['total']:,.0f}"
        return f"{name:<18} {qty:>4} {price:>8} {total:>8}\n"

    def _build_footer(self, data):
        currency = self.settings.get("currency", "Ar")
        total_amount = int(data['total'])
        amount_in_words = self._number_to_french(total_amount).capitalize()
        
        f = [self._sep()]
        amount_str = f"{total_amount:,.0f} {currency}"
        f.append(self.side_by_side("TOTAL", amount_str))
        
        words_line = f"En lettre: {amount_in_words} {currency.lower()}"
        # Gestion du retour à la ligne pour le montant en lettres
        if len(words_line) > self.line_width:
            f.append("En lettre:\n")
            words = (amount_in_words + " " + currency.lower()).split()
            line = ""
            for w in words:
                if len(line) + len(w) + 1 <= self.line_width:
                    line += w + " "
                else:
                    f.append(line.strip() + "\n")
                    line = w + " "
            f.append(line.strip() + "\n")
        else:
            f.append(words_line + "\n")
        
        f.append("\n" + "La gérance".rjust(self.line_width) + "\n")
        f.append("................".rjust(self.line_width) + "\n")
        f.append(self._sep())
        f.append("Merci pour votre achat!".center(self.line_width) + "\n")
        return f

    def _format_receipt_with_pagination(self, data):
        items = data["items"]
        header = self._build_header(data)
        footer = self._build_footer(data)
        col_header = [f"{'Description':<18} {'Qté':>4} {'P.U':>8} {'Total':>8}\n", "-"*self.line_width + "\n"]

        # --- LOGIQUE DE DÉCOUPAGE ---
        pages_items = []
        temp_items = list(items)

        # 1. Si tout tient sur une seule page
        if len(temp_items) <= self.items_last_page and len(temp_items) <= self.items_first_page:
            pages_items.append(temp_items)
        else:
            # 2. On prend la première page
            pages_items.append(temp_items[:self.items_first_page])
            temp_items = temp_items[self.items_first_page:]

            # 3. On prend les pages intermédiaires (tant qu'il en reste plus que pour la dernière)
            while len(temp_items) > self.items_last_page:
                pages_items.append(temp_items[:self.items_middle_page])
                temp_items = temp_items[self.items_middle_page:]
            
            # 4. On ajoute le reste sur la dernière page
            if temp_items:
                pages_items.append(temp_items)

        # --- CONSTRUCTION DU TEXTE ---
        total_pages = len(pages_items)
        final_output = []

        for i, page_content in enumerate(pages_items):
            page_num = i + 1
            is_first = (page_num == 1)
            is_last = (page_num == total_pages)
            
            current_page_text = []
            if is_first: current_page_text.extend(header)
            current_page_text.extend(col_header)

            for item in page_content:
                current_page_text.append(self._get_item_row(item))
                current_page_text.append("\n") # Ligne vide sous chaque article

            # Calcul du padding pour pousser le footer/numéro en bas
            used_lines = len(current_page_text)
            reserved = (len(footer) if is_last else 0) + 1 # +1 pour le numéro de page
            padding = self.max_lines_per_page - used_lines - reserved
            
            if padding > 0:
                current_page_text.extend(["\n"] * padding)
            
            if is_last:
                current_page_text.extend(footer)

            # Numéro de page tout en bas
            current_page_text.append(f"Page: {page_num}/{total_pages}".rjust(self.line_width) + "\n")
            final_output.append("".join(current_page_text))

        return "\f".join(final_output)

    def print_receipt(self, data):
        try:
            content = self._format_receipt_with_pagination(data)
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
                tmp.write(content)
                path = tmp.name

            result = subprocess.run(
                ["lp", "-d", self.printer_name, "-o", f"media={self.paper_format}",
                 "-o", "cpi=12", "-o", "lpi=8", "-o", "fit-to-page", path],
                capture_output=True, text=True, timeout=10
            )
            os.unlink(path)
            return (True, "Impression OK") if result.returncode == 0 else (False, result.stderr)
        except Exception as e:
            return False, str(e)