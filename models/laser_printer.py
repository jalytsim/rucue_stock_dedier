"""
Module d'impression thermique pour reçus
Imprime directement sur l'imprimante XP-Q300 sans passer par PDF
Version avec espacement réduit - Fournisseur à gauche, Client à droite
"""

from escpos.printer import Usb
from datetime import datetime
from name_formatter import format_client_name  # ton module NameFormatter


class ThermalPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer = None

        # Force XP-Q300 en 80 mm = 48 caractères
        self.paper_width = int(settings.get('paper_width', '80'))
        self.line_width = 48

    # -------------------------------
    # Connexion
    # -------------------------------
    def connect(self):
        try:
            self.printer = Usb(0x1fc9, 0x2016, in_ep=0x81, out_ep=0x02)
            return True, "Imprimante connectée"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"

    # -------------------------------
    # Ligne séparatrice
    # -------------------------------
    def _print_separator(self, char='='):
        self.printer.text(char * self.line_width + "\n")

    # -------------------------------
    # Texte côte à côte
    # -------------------------------
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

    # -------------------------------
    # Header
    # -------------------------------
    def _print_header(self, receipt_data):
        company = self.settings

        # Formatage client
        client_name = format_client_name(receipt_data.get('client_name', '(Non spécifié)'))

        # Découper si Nom + Prénom > 20 caractères
        parts = client_name.split()
        if len(parts) >= 2 and len(parts[0] + " " + parts[1]) > 20:
            parts[1] = parts[1][:20 - len(parts[0])]
            client_name = " ".join(parts)

        # Récupération des lignes client (max 3)
        client_lines = receipt_data.get('client_contact', '').split("\n")
        client_lines = [l.strip() for l in client_lines if l.strip()][:3]

        # Lignes fournisseur
        supplier_lines = [
            company.get('company_name', ''),
            company.get('company_phone', ''),
            f"NIF: {company.get('company_nif', '')}" if company.get('company_nif') else "",
            f"STAT: {company.get('company_stat', '')}" if company.get('company_stat') else ""
        ]
        supplier_lines.extend(company.get('company_address', '').split("\n"))

        # Construction des lignes
        self.printer.set(bold=True)
        self.printer.text(self.side_by_side(supplier_lines[0], "DOIT"))
        self.printer.set(bold=False)

        self.printer.text(self.side_by_side(supplier_lines[1], client_name))
        self.printer.text(self.side_by_side(supplier_lines[2], client_lines[0] if len(client_lines) > 0 else ""))
        self.printer.text(self.side_by_side(supplier_lines[3], client_lines[1] if len(client_lines) > 1 else ""))

        for i, addr_line in enumerate(supplier_lines[4:]):
            right = client_lines[2] if i == 0 and len(client_lines) == 3 else ""
            self.printer.text(self.side_by_side(addr_line, right))

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
    # Impression reçu
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
                self.printer.text(f"   {item['quantity']:.0f} x {item['unit_price']:,.0f} {currency} = {item['total']:,.0f} {currency}\n")

            # Total
            self._print_separator()
            self.printer.set(align='center', bold=True)
            self.printer.text("TOTAL A PAYER\n")
            self.printer.set(width=2, height=2)
            self.printer.text(f"{receipt_data['total']:,.0f} {currency}\n")
            self.printer.set(width=1, height=1, bold=False)

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

    # -------------------------------
    # Test print
    # -------------------------------
    def test_print(self):
        data = {
            "receipt_number": "TEST-00001",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "client_name": "Rabearisoa Marie Monique",
            "client_contact": "034 00 000 00\nQuartier Ambodonakanga\nAntananarivo",
            "items": [
                {"name": "Produit de test 1", "quantity": 2, "unit_price": 5000, "total": 10000},
                {"name": "Produit de test 2", "quantity": 1, "unit_price": 15000, "total": 15000},
                {"name": "Article nom très long pour test", "quantity": 3, "unit_price": 2500, "total": 7500},
            ],
            "total": 32500,
            "payment_method": "Espèces"
        }
        return self.print_receipt(data)

    # -------------------------------
    # Vérifier connexion
    # -------------------------------
    def check_connection(self):
        ok, msg = self.connect()
        if ok:
            self.printer = None
        return ok, msg
