"""
Module d'impression laser pour reçus
Imprime sur imprimante HP LaserJet 1022n en format A6
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
    
    def _format_receipt_text(self, receipt_data):
        """Formater le reçu en texte brut pour impression"""
        lines = []
        width = 48  # Largeur en caractères pour A6
        
        # En-tête entreprise
        lines.append("=" * width)
        lines.append(self.settings.get('company_name', '').center(width))
        lines.append("=" * width)
        
        address = self.settings.get('company_address', '')
        for line in address.split('\n'):
            lines.append(line.center(width))
        
        phone = self.settings.get('company_phone', '')
        if phone:
            lines.append(f"Tel: {phone}".center(width))
        
        nif = self.settings.get('company_nif', '')
        stat = self.settings.get('company_stat', '')
        if nif:
            lines.append(f"NIF: {nif}".center(width))
        if stat:
            lines.append(f"STAT: {stat}".center(width))
        
        lines.append("")
        lines.append("-" * width)
        
        # Informations client et reçu
        lines.append(f"CLIENT: {receipt_data.get('client_name', 'Non specifie')}")
        if receipt_data.get('client_phone'):
            lines.append(f"Tel: {receipt_data['client_phone']}")
        
        lines.append("")
        lines.append(f"No: {receipt_data['receipt_number']}")
        
        try:
            d = datetime.strptime(receipt_data['date'], "%Y-%m-%d")
            date_text = d.strftime('%d/%m/%Y')
        except:
            date_text = receipt_data['date']
        
        lines.append(f"Date: {date_text}")
        lines.append("")
        lines.append("=" * width)
        
        # Liste des articles
        lines.append("LISTE DES ARTICLES".center(width))
        lines.append("")
        
        currency = self.settings.get('currency', 'Ar')
        
        for i, item in enumerate(receipt_data['items'], 1):
            name = item["name"]
            if len(name) > 44:
                name = name[:41] + "..."
            
            lines.append(f"{i}. {name}")
            
            qty = item["quantity"]
            unit = item["unit_price"]
            total = item["total"]
            
            line_detail = f"   {qty:.0f} x {unit:,.0f} {currency} = {total:,.0f} {currency}"
            lines.append(line_detail)
            lines.append("")
        
        # Total
        lines.append("=" * width)
        lines.append("")
        lines.append("TOTAL A PAYER".center(width))
        lines.append(f"{receipt_data['total']:,.0f} {currency}".center(width))
        lines.append("")
        
        payment = receipt_data.get("payment_method", "Especes")
        lines.append(f"Paiement: {payment}".center(width))
        lines.append("")
        
        # Pied de page
        lines.append("-" * width)
        lines.append("Merci pour votre achat!".center(width))
        lines.append("Mankasitraka Tompoko!".center(width))
        lines.append("")
        lines.append("")
        
        return "\n".join(lines)
    
    def print_receipt(self, receipt_data):
        """Imprimer le reçu sur l'imprimante laser"""
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
            
            # Imprimer avec lp
            result = subprocess.run(
                [
                    "lp",
                    "-d", self.printer_name,
                    "-o", f"media={self.paper_format}",
                    "-o", "fit-to-page",
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