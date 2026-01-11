"""
Module d'impression thermique pour reçus
Imprime directement sur l'imprimante XP-Q300 sans passer par PDF
Version avec espacement réduit - Fournisseur à gauche, Client à droite
"""

from escpos.printer import Usb
from datetime import datetime


class ThermalPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer = None

        # Force votre XP-Q300 en 80 mm = 48 caractères
        self.paper_width = int(settings.get('paper_width', '80'))
        self.line_width = 48

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
        Affiche deux textes sur la même ligne (80mm = 48 chars).
        LEFT = FOURNISSEUR, RIGHT = CLIENT
        """
        left = left.strip()
        right = right.strip()

        total_len = len(left) + len(right)

        if total_len >= self.line_width:
            # tronquer uniquement ce qui dépasse
            excess = total_len - self.line_width + 1
            if len(right) > len(left):
                right = right[:-excess]
            else:
                left = left[:-excess]

        spaces = self.line_width - len(left) - len(right)
        return left + (" " * spaces) + right + "\n"

    def print_receipt(self, receipt_data):
        try:
            if not self.printer:
                ok, msg = self.connect()
                if not ok:
                    return False, msg

            self.printer.set(align='left', bold=True)

            # ============================
            #    FOURNISSEUR & CLIENT (inversé)
            # ============================
            # LIGNE 1: NOM SOCIETE | CLIENT
            self.printer.text(self.side_by_side(self.settings.get('company_name', ''), "CLIENT"))
            self.printer.set(bold=False)

            # LIGNE 2: TELEPHONE SOCIETE | NOM CLIENT
            self.printer.text(self.side_by_side(
                self.settings.get('company_phone', ''),
                receipt_data.get('client_name', '(Non specifie)')
            ))

            # LIGNE 3: NIF SOCIETE | TEL CLIENT
            self.printer.text(self.side_by_side(
                f"NIF: {self.settings.get('company_nif', '')}" if self.settings.get('company_nif') else "",
                receipt_data.get('client_phone', '')
            ))

            # LIGNE 4: STAT | (vide)
            stat = self.settings.get('company_stat', '')
            if stat:
                self.printer.text(self.side_by_side(f"STAT: {stat}", ""))

            # LIGNES SUIVANTES: ADRESSE | (vide)
            address = self.settings.get('company_address', '')
            for line in address.split("\n"):
                self.printer.text(self.side_by_side(line, ""))

            self._print_separator('-')

            # ============================
            #    NO FACTURE & DATE
            # ============================
            self.printer.set(bold=True)

            no_text = f"No: {receipt_data['receipt_number']}"
            try:
                d = datetime.strptime(receipt_data['date'], "%Y-%m-%d")
                date_text = f"Date: {d.strftime('%d/%m/%Y')}"
            except:
                date_text = f"Date: {receipt_data['date']}"

            self.printer.text(self.side_by_side(no_text, date_text))
            self.printer.set(bold=False)

            self._print_separator()

            # ============================
            #     LISTE DES ARTICLES
            # ============================
            self.printer.set(align='center', bold=True)
            self.printer.text("Liste des articles\n")
            self.printer.set(align='left', bold=False)

            currency = self.settings.get('currency', 'Ar')

            for i, item in enumerate(receipt_data['items'], 1):
                name = item["name"]
                if len(name) > 44:
                    name = name[:41] + "..."

                self.printer.set(bold=True)
                self.printer.text(f"{i}. {name}\n")
                self.printer.set(bold=False)

                qty = item["quantity"]
                unit = item["unit_price"]
                total = item["total"]

                self.printer.text(f"   {qty:.0f} x {unit:,.0f} {currency} = {total:,.0f} {currency}\n")

            # ============================
            #            TOTAL
            # ============================
            self._print_separator()

            self.printer.set(align='center', bold=True)
            self.printer.text("TOTAL A PAYER\n")
            self.printer.set(width=2, height=2)
            self.printer.text(f"{receipt_data['total']:,.0f} {currency}\n")
            self.printer.set(width=1, height=1, bold=False)

            payment = receipt_data.get("payment_method", "Espèces")
            self.printer.text(f"Paiement: {payment}\n")

            # ============================
            #       PIED DE PAGE
            # ============================
            self._print_separator()
            self.printer.text("Merci pour votre achat!\n")
            self.printer.text("Mankasitraka Tompoko!\n")

            self.printer.text("\n\n")
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