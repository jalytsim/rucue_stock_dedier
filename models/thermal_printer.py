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

    def _print_header(self, receipt_data):
        """Header sans NIF et STAT"""
        company = self.settings

        # Récupération des lignes client
        client_lines = receipt_data.get('client_contact', '').split("\n")
        client_lines = [l.strip() for l in client_lines if l.strip()]
        client_lines = client_lines[:4]

        # Lignes fournisseur (NIF et STAT supprimés)
        supplier_lines = [
            company.get('company_name', ''),
            company.get('company_phone', '')
        ]
        supplier_lines.extend(company.get('company_address', '').split("\n"))

        # Ligne 0: company_name | DOIT (en gras)
        # On utilise directement text() avec double hauteur pour le gras
        self.printer.set(width=2, height=2)
        self.printer.text(self.side_by_side(supplier_lines[0][:20], "DOIT"))
        self.printer.set(width=1, height=1)

        # Ligne 1: téléphone | nom client
        self.printer.text(self.side_by_side(
            supplier_lines[1] if len(supplier_lines) > 1 else "", 
            receipt_data.get('client_name', '(Non spécifié)')
        ))

        # Lignes suivantes : Adresse fournisseur | Adresse client
        max_lines = max(len(supplier_lines) - 2, len(client_lines))
        
        for i in range(max_lines):
            left = supplier_lines[i + 2] if (i + 2) < len(supplier_lines) else ""
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

        self.printer.set(width=2, height=2)
        self.printer.text(self.side_by_side(no_text[:20], date_text[:20]))
        self.printer.set(width=1, height=1)
        self._print_separator()

    def print_receipt(self, receipt_data):
        """Imprimer le reçu"""
        try:
            if not self.printer:
                ok, msg = self.connect()
                if not ok:
                    return False, msg

            # Header
            self._print_header(receipt_data)

            # Liste des articles - titre centré
            self.printer.text("\n")
            title = "Liste des articles"
            spaces = (self.line_width - len(title)) // 2
            self.printer.set(width=2, height=2)
            self.printer.text(" " * spaces + title + "\n")
            self.printer.set(width=1, height=1)
            self.printer.text("\n")

            currency = self.settings.get('currency', 'Ar')
            
            # Articles
            for i, item in enumerate(receipt_data['items'], 1):
                name = item["name"]
                if len(name) > 44:
                    name = name[:41] + "..."

                # Nom du produit en gras (double taille)
                self.printer.set(width=2, height=2)
                self.printer.text(f"{i}. {name[:20]}\n")
                self.printer.set(width=1, height=1)

                qty = item["quantity"]
                unit = item["unit_price"]
                total = item["total"]

                self.printer.text(f"   {qty:.0f} x {unit:,.0f} {currency} = {total:,.0f} {currency}\n")

            # Total
            self._print_separator()
            
            # Titre centré
            title = "TOTAL A PAYER"
            spaces = (self.line_width - len(title)) // 2
            self.printer.text(" " * spaces + title + "\n")
            
            # Montant en grand
            amount_str = f"{receipt_data['total']:,.0f} {currency}"
            spaces = (self.line_width - len(amount_str) * 2) // 2
            self.printer.set(width=2, height=2)
            self.printer.text(" " * (spaces // 2) + amount_str + "\n")
            self.printer.set(width=1, height=1)

            payment = receipt_data.get("payment_method", "Espèces")
            payment_line = f"Paiement: {payment}"
            spaces = (self.line_width - len(payment_line)) // 2
            self.printer.text(" " * spaces + payment_line + "\n")

            # Pied de page
            self._print_separator()
            
            msg1 = "Merci pour votre achat!"
            msg2 = "Mankasitraka Tompoko!"
            spaces1 = (self.line_width - len(msg1)) // 2
            spaces2 = (self.line_width - len(msg2)) // 2
            
            self.printer.text(" " * spaces1 + msg1 + "\n")
            self.printer.text(" " * spaces2 + msg2 + "\n")
            self.printer.text("\n\n")
            self.printer.cut()

            return True, "Reçu imprimé avec succès"

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            return False, f"Erreur d'impression: {error_msg}"

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
        try:
            ok, msg = self.connect()
            if ok and self.printer:
                self.printer = None
            return ok, msg
        except Exception as e:
            return False, str(e)