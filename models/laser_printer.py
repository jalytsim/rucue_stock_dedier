import subprocess
import tempfile
from datetime import datetime
import os


class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'Custom.105x148mm')
        self.line_width = 48

        # Avec cpi=12 & lpi=8 sur A6 ≈ 40 lignes max
        self.max_lines_per_page = 40

    def check_connection(self):
        """Vérifier si l'imprimante existe et répond"""
        try:
            result = subprocess.run(
                ["lpstat", "-p", self.printer_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, f"Imprimante {self.printer_name} disponible"
            return False, f"Imprimante {self.printer_name} non trouvée"
        except FileNotFoundError:
            return False, "Commande 'lpstat' introuvable"
        except Exception as e:
            return False, f"Erreur: {e}"

    # --------------------------------------------------------
    #   SECTIONS : HEADER / ITEMS / FOOTER
    # --------------------------------------------------------

    def _print_separator(self, char='='):
        return char * self.line_width + "\n"

    def side_by_side(self, left, right):
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

    def _build_header(self, data):
        header = []
        currency = self.settings.get("currency", "Ar")

        header.append(self.side_by_side(self.settings.get('company_name', ''), "CLIENT"))
        header.append(self.side_by_side(self.settings.get('company_phone', ''), data.get('client_name', '(Non spécifié)')))
        header.append(self.side_by_side(f"NIF: {self.settings.get('company_nif', '')}", data.get('client_phone', '')))

        stat = self.settings.get('company_stat', '')
        if stat:
            header.append(self.side_by_side(f"STAT: {stat}", ""))

        address = self.settings.get('company_address', '')
        for line in address.split("\n"):
            header.append(self.side_by_side(line, ""))

        header.append(self._print_separator('-'))

        # Numéro facture + Date
        no_text = f"No: {data['receipt_number']}"
        try:
            d = datetime.strptime(data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {data['date']}"

        header.append(self.side_by_side(no_text, date_text))
        header.append(self._print_separator())
        header.append("Liste des articles".center(self.line_width) + "\n")

        return header

    def _build_items(self, data):
        currency = self.settings.get("currency", "Ar")
        items_list = []

        for i, item in enumerate(data["items"], 1):
            name = item["name"]
            if len(name) > 44:
                name = name[:41] + "..."

            items_list.append(f"{i}. {name}\n")
            items_list.append(f"   {item['quantity']} x {item['unit_price']:,.0f} {currency} = {item['total']:,.0f} {currency}\n")

        return items_list

    def _build_footer(self, data):
        currency = self.settings.get("currency", "Ar")
        footer = []

        footer.append(self._print_separator())
        footer.append("TOTAL A PAYER".center(self.line_width) + "\n")
        footer.append(f"{data['total']:,.0f} {currency}".center(self.line_width) + "\n")

        payment = data.get("payment_method", "Espèces")
        footer.append(f"Paiement: {payment}".center(self.line_width) + "\n")

        footer.append(self._print_separator())
        footer.append("Merci pour votre achat!".center(self.line_width) + "\n")
        footer.append("Mankasitraka Tompoko!".center(self.line_width) + "\n")
        footer.append("\n")

        return footer

    # --------------------------------------------------------
    #   PAGINATION STRICTE
    # --------------------------------------------------------

    def _format_receipt_with_pagination(self, data):

        header = self._build_header(data)
        items = self._build_items(data)
        footer = self._build_footer(data)

        pages = []

        # ---------------------
        # PAGE 1
        # ---------------------
        page1 = []
        page1.extend(header)

        first_page_items = items[:8]  # MAX 8 ARTICLE SUR PAGE 1
        page1.extend(first_page_items)

        pages.append("".join(page1))

        # ---------------------
        # PAGES SUIVANTES
        # ---------------------
        remaining_items = items[8:]
        current_page = []

        for line in remaining_items:
            current_page.append(line)

            # Si la page est presque pleine, on la valide
            if len(current_page) >= self.max_lines_per_page - len(footer) - 2:
                pages.append("".join(current_page))
                current_page = []

        # ---------------------
        # FOOTER sur dernière page
        # ---------------------
        current_page.extend(footer)
        pages.append("".join(current_page))

        return "\f".join(pages)

    # --------------------------------------------------------
    #   IMPRESSION
    # --------------------------------------------------------

    def print_receipt(self, data):
        try:
            text_content = self._format_receipt_with_pagination(data)

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
                tmp.write(text_content)
                tmp_path = tmp.name

            result = subprocess.run(
                [
                    "lp",
                    "-d", self.printer_name,
                    "-o", f"media={self.paper_format}",
                    "-o", "cpi=12",      # police plus grande
                    "-o", "lpi=8",
                    "-o", "page-left=10",
                    "-o", "page-right=10",
                    "-o", "page-top=10",
                    "-o", "page-bottom=10",
                    tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            os.unlink(tmp_path)

            if result.returncode == 0:
                return True, f"Reçu envoyé à l'imprimante {self.printer_name}"
            return False, f"Erreur impression : {result.stderr}"

        except FileNotFoundError:
            return False, "Commande 'lp' introuvable"
        except subprocess.TimeoutExpired:
            return False, "Timeout : imprimante ne répond pas"
        except Exception as e:
            import traceback
            return False, f"Erreur: {e}\n{traceback.format_exc()}"

    def test_print(self):
        data = {
            "receipt_number": "TEST-LASER-001",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "client_name": "Client Test Laser",
            "client_phone": "034 00 000 00",
            "items": [
                {"name": "Produit test 1", "quantity": 2, "unit_price": 5000, "total": 10000},
                {"name": "Produit test 2", "quantity": 1, "unit_price": 15000, "total": 15000},
            ],
            "total": 25000,
            "payment_method": "Espèces"
        }
        return self.print_receipt(data)
