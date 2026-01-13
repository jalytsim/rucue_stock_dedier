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

    def _number_to_french(self, n):
        """Convertit un nombre en lettres françaises"""
        if n == 0:
            return "zéro"
        
        units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        teens = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", 
                 "dix-sept", "dix-huit", "dix-neuf"]
        tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", 
                "soixante", "quatre-vingt", "quatre-vingt"]
        
        def convert_below_100(n):
            if n < 10:
                return units[n]
            elif n < 20:
                return teens[n - 10]
            elif n < 70:
                unit = n % 10
                ten = n // 10
                if unit == 0:
                    return tens[ten]
                elif unit == 1 and ten != 8:
                    return tens[ten] + " et un"
                else:
                    return tens[ten] + "-" + units[unit]
            elif n < 80:
                return "soixante-" + teens[n - 70]
            elif n < 100:
                unit = n % 10
                if n == 80:
                    return "quatre-vingts"
                elif unit == 0:
                    return "quatre-vingt-" + units[unit] if unit else "quatre-vingts"
                else:
                    return "quatre-vingt-" + units[unit]
        
        def convert_below_1000(n):
            if n < 100:
                return convert_below_100(n)
            else:
                hundred = n // 100
                rest = n % 100
                if hundred == 1:
                    result = "cent"
                else:
                    result = units[hundred] + " cent"
                if rest == 0:
                    if hundred > 1:
                        result += "s"
                else:
                    result += " " + convert_below_100(rest)
                return result
        
        if n < 1000:
            return convert_below_1000(n)
        elif n < 1000000:
            thousand = n // 1000
            rest = n % 1000
            if thousand == 1:
                result = "mille"
            else:
                result = convert_below_1000(thousand) + " mille"
            if rest > 0:
                result += " " + convert_below_1000(rest)
            return result
        elif n < 1000000000:
            million = n // 1000000
            rest = n % 1000000
            if million == 1:
                result = "un million"
            else:
                result = convert_below_1000(million) + " millions"
            if rest > 0:
                if rest < 1000:
                    result += " " + convert_below_1000(rest)
                else:
                    result += " " + convert_below_1000(rest // 1000) + " mille"
                    if rest % 1000 > 0:
                        result += " " + convert_below_1000(rest % 1000)
            return result
        else:
            return "nombre trop grand"

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

    def _get_item_row(self, item):
        name = item["name"][:17] 
        qty = str(item['quantity'])
        price = f"{item['unit_price']:,.0f}"
        total = f"{item['total']:,.0f}"
        return f"{name:<18} {qty:>4} {price:>8} {total:>8}\n"

    def _build_footer(self, data):
        """Construit le footer avec le montant en lettres"""
        currency = self.settings.get("currency", "Ar")
        total_amount = int(data['total'])
        amount_in_words = self._number_to_french(total_amount).capitalize()
        
        f = []
        f.append(self._sep())
        f.append("TOTAL A PAYER".center(self.line_width) + "\n")
        f.append(f"{total_amount:,.0f} {currency}".center(self.line_width) + "\n")
        
        # Montant en lettres (peut prendre plusieurs lignes si long)
        # On découpe intelligemment si le texte est trop long
        words_line = f"({amount_in_words} {currency.lower()})"
        if len(words_line) <= self.line_width:
            f.append(words_line.center(self.line_width) + "\n")
        else:
            # Découpe en plusieurs lignes si nécessaire
            words = words_line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= self.line_width:
                    current_line += word + " "
                else:
                    f.append(current_line.strip().center(self.line_width) + "\n")
                    current_line = word + " "
            if current_line:
                f.append(current_line.strip().center(self.line_width) + "\n")
        
        f.append("\n")
        f.append("La gérance".rjust(self.line_width) + "\n")
        f.append("................".rjust(self.line_width) + "\n")
        f.append("\n")
        f.append(self._sep())
        f.append("Merci pour votre achat!".center(self.line_width) + "\n")
        f.append("Mankasitraka Tompoko!".center(self.line_width) + "\n")
        return f

    def _format_receipt_with_pagination(self, data):
        items = data["items"]
        header = self._build_header(data)
        footer = self._build_footer(data)
        
        # Taille du header et footer en lignes
        header_size = len(header)
        footer_size = len(footer) + 1  # +1 pour le numéro de page
        
        # En-tête des colonnes (2 lignes)
        column_header = [
            f"{'Description':<18} {'Qté':>4} {'P.U':>8} {'Montant':>8}\n",
            "-" * self.line_width + "\n"
        ]
        column_header_size = len(column_header)
        
        # Chaque item = 2 lignes (ligne produit + ligne vide)
        lines_per_item = 2
        
        # Calcul de l'espace disponible pour la première page
        first_page_available = self.max_lines_per_page - header_size - column_header_size - footer_size
        first_page_items = first_page_available // lines_per_item
        
        # Calcul pour les pages suivantes
        other_page_available = self.max_lines_per_page - column_header_size - footer_size
        other_page_items = other_page_available // lines_per_item
        
        # Découpage intelligent des items
        pages_items_list = []
        
        if len(items) <= first_page_items:
            # Tout tient sur une page
            pages_items_list.append(items)
        else:
            # Première page
            pages_items_list.append(items[:first_page_items])
            remaining = items[first_page_items:]
            
            # Pages suivantes
            while remaining:
                pages_items_list.append(remaining[:other_page_items])
                remaining = remaining[other_page_items:]
        
        total_pages = len(pages_items_list)
        formatted_pages = []
        
        # Construction des pages
        for page_num, page_items in enumerate(pages_items_list, 1):
            page_output = []
            
            # Header uniquement sur la première page
            if page_num == 1:
                page_output.extend(header)
            
            # En-tête des colonnes
            page_output.extend(column_header)
            
            # Items de la page
            for item in page_items:
                page_output.append(self._get_item_row(item))
                page_output.append("\n")
            
            # Footer
            page_output.extend(footer)
            
            # Numéro de page
            page_number_line = f"Page: {page_num}/{total_pages}".rjust(self.line_width)
            
            # Padding pour remplir la page
            current_lines = len(page_output)
            padding_needed = self.max_lines_per_page - current_lines - 1  # -1 pour la ligne de numéro
            
            if padding_needed > 0:
                page_output.extend(["\n"] * padding_needed)
            
            page_output.append(page_number_line)
            
            formatted_pages.append("".join(page_output))
        
        return "\f".join(formatted_pages)

    def print_receipt(self, data):
        try:
            content = self._format_receipt_with_pagination(data)
            content = content.strip()
            
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
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
            os.unlink(path)
            return (True, "Impression OK") if result.returncode == 0 else (False, result.stderr)
        except Exception as e:
            return False, str(e)