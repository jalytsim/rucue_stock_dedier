"""
Module d'impression thermique pour reçus
Imprime directement sur l'imprimante XP-Q300 sans passer par PDF
Version avec espacement réduit - Fournisseur à gauche (Sans NIF/STAT), Client à droite
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
            excess = total_len - self.line_width + 1
            if len(right) > len(left):
                right = right[:-excess]
            else:
                left = left[:-excess]

        spaces = self.line_width - len(left) - len(right)
        return left + (" " * spaces) + right + "\n"

    # -------------------------------
    # Header sans NIF et STAT
    # -------------------------------
    def _print_header(self, receipt_data):
        company = self.settings

        # Récupération des lignes client
        client_lines = receipt_data.get('client_contact', '').split("\n")
        client_lines = [l.strip() for l in client_lines if l.strip()]
        client_lines = client_lines[:4]  # Un peu plus de place pour le client

        # Lignes fournisseur (NIF et STAT supprimés)
        supplier_lines = [
            company.get('company_name', ''),
            company.get('company_phone', '')
        ]
        # On ajoute les lignes d'adresse fournisseur
        supplier_lines.extend(company.get('company_address', '').split("\n"))

        # Ligne 0: company_name | DOIT (en gras)
        self.printer.set(align='left')
        self.printer.set(width=1, height=1)
        self.printer.set(bold=True)
        self.printer.text(self.side_by_side(supplier_lines[0], "DOIT"))
        self.printer.set(bold=False)

        # Ligne 1: téléphone | nom client
        self.printer.text(self.side_by_side(
            supplier_lines[1] if len(supplier_lines) > 1 else "", 
            receipt_data.get('client_name', '(Non spécifié)')
        ))

        # Lignes suivantes : Adresse fournisseur | Adresse client
        # On boucle pour aligner le reste des informations
        max_lines = max(len(supplier_lines) - 2, len(client_lines))
        
        for i in range(max_lines):
            # Index pour supplier commence à 2 (après nom et tel)
            left = supplier_lines[i + 2] if (i + 2) < len(supplier_lines) else ""
            # Index pour client commence à 0
            right = client_lines[i] if i < len(client_lines) else ""
            
            if left or right:
                self.printer.text(self.side_by_side(left, right))

        self._print_separator('-')

        # No facture & date
        no_text = f"No: {receipt_data.get('receipt_number', '')}"
        try:
            d = datetime.strptime(receipt_data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {receipt_data.get('date', '')}"

        self.printer.set(bold=True)
        self.printer.text(self.side_by_side(no_text, date_text))
        self.printer.set(bold=False)
        self._print_separator()

    # -------------------------------
    # Print receipt
    # -------------------------------
    def print_receipt(self, receipt_data):
        try:
            if not self.printer:
                ok, msg = self.connect()
                if not ok:
                    return False, msg

            # Header
            self._print_header(receipt_data)

            # Liste des articles
            self.printer.set(align='center')
            self.printer.set(bold=True)
            self.printer.text("Liste des articles\n")
            self.printer.set(align='left')
            self.printer.set(bold=False)

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

            # Total
            self._print_separator()
            self.printer.set(align='center')
            self.printer.set(bold=True)
            self.printer.text("TOTAL A PAYER\n")
            self.printer.set(width=2, height=2)
            self.printer.text(f"{receipt_data['total']:,.0f} {currency}\n")
            self.printer.set(width=1, height=1)
            self.printer.set(bold=False)

            payment = receipt_data.get("payment_method", "Espèces")
            self.printer.text(f"Paiement: {payment}\n")

            # Pied de page
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
            "client_contact": "034 00 000 00\nQuartier Ambodonakanga\nAntananarivo",
            "items": [
                {"name": "Produit de test 1", "quantity": 2, "unit_price": 5000, "total": 10000},
                {"name": "Produit de test 2", "quantity": 1, "unit_price": 15000, "total": 15000},
            ],
            "total": 25000,
            "payment_method": "Espèces"
        }
        return self.print_receipt(data)

    def check_connection(self):
        ok, msg = self.connect()
        if ok:
            self.printer = None
        return ok, msg