"""
Module d'impression laser pour reçus
Imprime sur imprimante HP LaserJet 1022n en format A6
Format identique au reçu thermique avec police monospace
"""

import subprocess
import tempfile
from datetime import datetime
import os


class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings
        # Nom de l'imprimante (configurable dans les paramètres)
        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'A6')
        # Largeur de ligne pour format texte monospace
        self.line_width = 48
    
    def check_connection(self):
        """Vérifier si l'imprimante est disponible"""
        try:
            result = subprocess.run(
                ["lpstat", "-p", self.printer_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, f"Imprimante {self.printer_name} disponible"
            else:
                return False, f"Imprimante {self.printer_name} non trouvée"
        except FileNotFoundError:
            return False, "Commande 'lpstat' non trouvée (système non Unix?)"
        except Exception as e:
            return False, f"Erreur de vérification: {str(e)}"
    
    def _print_separator(self, char='='):
        """Créer une ligne de séparation"""
        return char * self.line_width + "\n"
    
    def side_by_side(self, left, right):
        """
        Affiche deux textes sur la même ligne (48 chars)
        Même logique que thermal_printer
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
    
    def _format_receipt_text(self, receipt_data):
        """Formater le reçu - IDENTIQUE au format thermique"""
        lines = []
        
        # CLIENT & SOCIETE
        lines.append(self.side_by_side("CLIENT", self.settings.get('company_name', '')))
        
        lines.append(self.side_by_side(
            receipt_data.get('client_name', '(Non specifie)'),
            self.settings.get('company_phone', '')
        ))
        
        lines.append(self.side_by_side(
            receipt_data.get('client_phone', ''),
            f"NIF: {self.settings.get('company_nif', '')}" if self.settings.get('company_nif') else ""
        ))
        
        stat = self.settings.get('company_stat', '')
        if stat:
            lines.append(self.side_by_side("", f"STAT: {stat}"))
        
        address = self.settings.get('company_address', '')
        for line in address.split("\n"):
            lines.append(self.side_by_side("", line))
        
        lines.append(self._print_separator('-'))
        
        # NO FACTURE & DATE
        no_text = f"No: {receipt_data['receipt_number']}"
        try:
            d = datetime.strptime(receipt_data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {receipt_data['date']}"
        
        lines.append(self.side_by_side(no_text, date_text))
        
        lines.append(self._print_separator())
        
        # LISTE DES ARTICLES
        lines.append("Liste des articles".center(self.line_width) + "\n")
        
        currency = self.settings.get('currency', 'Ar')
        
        for i, item in enumerate(receipt_data['items'], 1):
            name = item["name"]
            if len(name) > 44:
                name = name[:41] + "..."
            
            lines.append(f"{i}. {name}\n")
            
            qty = item["quantity"]
            unit = item["unit_price"]
            total = item["total"]
            
            lines.append(f"   {qty:.0f} x {unit:,.0f} {currency} = {total:,.0f} {currency}\n")
        
        # TOTAL
        lines.append(self._print_separator())
        
        lines.append("TOTAL A PAYER".center(self.line_width) + "\n")
        lines.append(f"{receipt_data['total']:,.0f} {currency}".center(self.line_width) + "\n")
        
        payment = receipt_data.get("payment_method", "Especes")
        lines.append(f"Paiement: {payment}".center(self.line_width) + "\n")
        
        # PIED DE PAGE
        lines.append(self._print_separator())
        lines.append("Merci pour votre achat!".center(self.line_width) + "\n")
        lines.append("Mankasitraka Tompoko!".center(self.line_width) + "\n")
        
        lines.append("\n\n")
        
        return "".join(lines)
    
    def print_receipt(self, receipt_data):
        """Imprimer le reçu sur l'imprimante laser avec police monospace"""
        try:
            # Formater le contenu
            text_content = self._format_receipt_text(receipt_data)
            
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                suffix=".txt",
                encoding='utf-8'
            ) as tmp:
                tmp.write(text_content)
                tmp_path = tmp.name
            
            # IMPORTANT: Options pour police monospace et taille réduite
            result = subprocess.run(
                [
                    "lp",
                    "-d", self.printer_name,
                    "-o", f"media={self.paper_format}",
                    "-o", "cpi=17",  # 17 caractères par pouce = police plus petite
                    "-o", "lpi=8",   # 8 lignes par pouce = espacement vertical réduit
                    "-o", "page-left=10",  # Marge gauche 10pt
                    "-o", "page-right=10", # Marge droite 10pt
                    "-o", "page-top=10",   # Marge haut 10pt
                    "-o", "page-bottom=10", # Marge bas 10pt
                    tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            if result.returncode == 0:
                return True, f"Reçu envoyé à l'imprimante {self.printer_name}"
            else:
                return False, f"Erreur d'impression: {result.stderr}"
        
        except FileNotFoundError:
            return False, "Commande 'lp' non trouvée. Système non Unix?"
        except subprocess.TimeoutExpired:
            return False, "Timeout: l'imprimante ne répond pas"
        except Exception as e:
            import traceback
            return False, f"Erreur: {str(e)}\n\n{traceback.format_exc()}"
    
    def test_print(self):
        """Test d'impression"""
        data = {
            "receipt_number": "TEST-LASER-00001",
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