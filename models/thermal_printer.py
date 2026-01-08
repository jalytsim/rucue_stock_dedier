"""
Module d'impression thermique pour reçus
Imprime directement sur l'imprimante XP-Q300 sans passer par PDF
"""

from escpos.printer import Usb
from datetime import datetime


class ThermalPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer = None
        self.paper_width = int(settings.get('paper_width', '58'))

        # Largeur en caractères selon le papier
        self.line_width = 32 if self.paper_width == 58 else 48

    def connect(self):
        try:
            self.printer = Usb(0x1fc9, 0x2016, in_ep=0x81, out_ep=0x02)
            return True, "Imprimante connectée"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"

    def _print_separator(self, char='='):
        self.printer.text(char * self.line_width + "\n")

    def side_by_side(self, left, right):
        """
        Affiche réellement deux textes sur la même ligne.
        Gestion automatique de troncature et des espaces.
        """
        left = left.strip()
        right = right.strip()

        # Tronquer si trop long
        max_left = self.line_width // 2
        max_right = self.line_width - max_left

        if len(left) > max_left:
            left = left[:max_left - 3] + "..."

        if len(right) > max_right:
            right = right[:max_right - 3] + "..."

        # Calcul des espaces restants
        spaces = self.line_width - len(left) - len(right)
        if spaces < 1:
            spaces = 1

        return left + (" " * spaces) + right + "\n"

    def print_receipt(self, receipt_data):
        try:
            # Connexion auto si nécessaire
            if not self.printer:
                ok, msg = self.connect()
                if not ok:
                    return False, msg

            self.printer.set(align='left', bold=True)

            # ============================
            #    CLIENT & SOCIETE
            # ============================
            company_name = self.settings.get('company_name', '')
            self.printer.text(self.side_by_side("CLIENT", company_name))
            self.printer.set(bold=False)

            # CLIENT & TELEPHONE SOCIETE
            client_name = receipt_data.get('client_name', '(Non spécifié)')
            company_phone = self.settings.get('company_phone', '')
            self.printer.text(self.side_by_side(client_name, company_phone))

            # TEL CLIENT & NIF
            client_phone = receipt_data.get('client_phone', '')
            company_nif = self.settings.get('company_nif', '')
            self.printer.text(self.side_by_side(client_phone, f"NIF: {company_nif}" if company_nif else ""))

            # STAT seulement à droite
            company_stat = self.settings.get('company_stat', '')
            if company_stat:
                self.printer.text(self.side_by_side("", f"STAT: {company_stat}"))

            # Adresse à droite (gestion multilignes)
            address = self.settings.get('company_address', '')
            for line in address.split("\n"):
                self.printer.text(self.side_by_side("", line))

            self.printer.text("\n")
            self._print_separator('-')
            self.printer.text("\n")

            # ============================
            #   NO FACTURE & DATE COTE À COTE
            # ============================
            self.printer.set(bold=True)

            no_text = f"No: {receipt_data['receipt_number']}"
            try:
                d = datetime.strptime(receipt_data['date'], "%Y-%m-%d")
                formatted_date = d.strftime("%d/%m/%Y")
            except:
                formatted_date = receipt_data['date']

            date_text = f"Date: {formatted_date}"

            self.printer.text(self.side_by_side(no_text, date_text))

            self.printer.set(bold=False)
            self.printer.text("\n")

            self._print_separator()
            self.printer.text("\n")

            # ============================
            #       LISTE DES ARTICLES
            # ============================
            self.printer.set(align='center', bold=True)
            self.printer.text("Liste des articles\n\n")
            self.printer.set(align='left', bold=False)

            currency = self.settings.get('currency', 'Ar')
            max_chars = 30 if self.paper_width == 58 else 45

            for i, item in enumerate(receipt_data['items'], 1):
                name = item["name"]
                if len(name) > max_chars:
                    name = name[:max_chars - 3] + "..."

                # Nom du produit
                self.printer.set(bold=True)
                self.printer.text(f"{i}. {name}\n")
                self.printer.set(bold=False)

                qty = item["quantity"]
                unit = item["unit_price"]
                total = item["total"]

                self.printer.text(f"   {qty:.0f} x {unit:,.0f} {currency} = {total:,.0f} {currency}\n\n")

            # ============================
            #           TOTAL
            # ============================
            self._print_separator()
            self.printer.text("\n")

            self.printer.set(align='center', bold=True)
            self.printer.text("TOTAL A PAYER\n")
            self.printer.set(width=2, height=2)
            self.printer.text(f"{receipt_data['total']:,.0f} {currency}\n")
            self.printer.set(width=1, height=1, bold=False)

            payment = receipt_data.get("payment_method", "Espèces")
            self.printer.text(f"\nPaiement: {payment}\n\n")

            # ============================
            #       PIED DE PAGE
            # ============================
            self._print_separator()
            self.printer.text("\nMerci pour votre achat!\n")
            self.printer.text("Mankasitraka Tompoko!\n")

            self.printer.text("\n\n\n")
            self.printer.cut()

            return True, "Reçu imprimé avec succès"

        except Exception:
            import traceback
            return False, traceback.format_exc()

    def test_print(self):
        data = {
            "receipt_number": "TEST-00001",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "client_name": "Client Test",
            "client_phone": "034 00 000 00",
            "items": [
                {"name": "Produit de test 1", "quantity": 2, "unit_price": 5000, "total": 10000},
                {"name": "Produit de test 2", "quantity": 1, "unit_price": 15000, "total": 15000},
                {"name": "Article nom très long pour test", "quantity": 3, "unit_price": 2500, "total": 7500},
            ],
            "total": 32500,
            "payment_method": "Espèces"
        }
        return self.print_receipt(data)

    def check_connection(self):
        ok, msg = self.connect()
        if ok:
            self.printer = None
        return ok, msg
