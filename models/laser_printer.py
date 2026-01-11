"""
Module d'impression laser pour reçus
Imprime sur imprimante HP LaserJet 1022n en format A6 (10,5 x 14,8 cm)
Fournisseur à gauche, Client à droite
Gestion intelligente des sauts de page (ne coupe jamais la section footer)
"""

import subprocess
import tempfile
from datetime import datetime
import os


class LaserPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer_name = settings.get('laser_printer_name', 'HP_LaserJet_1022n')
        self.paper_format = settings.get('laser_paper_format', 'A6')
        self.line_width = 48
        
        # Hauteur A6 = 148mm ≈ 14,8cm
        # Avec marges et police 8pt → environ 50 lignes max par page
        self.max_lines_per_page = 50
    
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
    
    def _format_receipt_with_pagination(self, receipt_data):
        """
        Formater le reçu avec gestion intelligente des pages
        SECTION 1: En-tête (ne jamais couper)
        SECTION 2: Articles (peut être coupée)
        SECTION 3: Footer (ne jamais couper - toujours sur dernière page)
        """
        currency = self.settings.get('currency', 'Ar')
        
        # ========== SECTION 1: EN-TÊTE (FOURNISSEUR | CLIENT) ==========
        header_lines = []
        
        # LIGNE 1: NOM SOCIETE | CLIENT
        header_lines.append(self.side_by_side(self.settings.get('company_name', ''), "CLIENT"))
        
        # LIGNE 2: TELEPHONE SOCIETE | NOM CLIENT
        header_lines.append(self.side_by_side(
            self.settings.get('company_phone', ''),
            receipt_data.get('client_name', '(Non specifie)')
        ))
        
        # LIGNE 3: NIF SOCIETE | TEL CLIENT
        header_lines.append(self.side_by_side(
            f"NIF: {self.settings.get('company_nif', '')}" if self.settings.get('company_nif') else "",
            receipt_data.get('client_phone', '')
        ))
        
        # LIGNE 4: STAT | (vide)
        stat = self.settings.get('company_stat', '')
        if stat:
            header_lines.append(self.side_by_side(f"STAT: {stat}", ""))
        
        # LIGNES SUIVANTES: ADRESSE | (vide)
        address = self.settings.get('company_address', '')
        for line in address.split("\n"):
            header_lines.append(self.side_by_side(line, ""))
        
        header_lines.append(self._print_separator('-'))
        
        # NO FACTURE & DATE
        no_text = f"No: {receipt_data['receipt_number']}"
        try:
            d = datetime.strptime(receipt_data['date'], "%Y-%m-%d")
            date_text = f"Date: {d.strftime('%d/%m/%Y')}"
        except:
            date_text = f"Date: {receipt_data['date']}"
        
        header_lines.append(self.side_by_side(no_text, date_text))
        header_lines.append(self._print_separator())
        header_lines.append("Liste des articles".center(self.line_width) + "\n")
        
        # ========== SECTION 2: ARTICLES ==========
        items_lines = []
        
        for i, item in enumerate(receipt_data['items'], 1):
            name = item["name"]
            if len(name) > 44:
                name = name[:41] + "..."
            
            items_lines.append(f"{i}. {name}\n")
            
            qty = item["quantity"]
            unit = item["unit_price"]
            total = item["total"]
            
            items_lines.append(f"   {qty:.0f} x {unit:,.0f} {currency} = {total:,.0f} {currency}\n")
        
        # ========== SECTION 3: FOOTER (NE JAMAIS COUPER) ==========
        footer_lines = []
        
        footer_lines.append(self._print_separator())
        footer_lines.append("TOTAL A PAYER".center(self.line_width) + "\n")
        footer_lines.append(f"{receipt_data['total']:,.0f} {currency}".center(self.line_width) + "\n")
        
        payment = receipt_data.get("payment_method", "Especes")
        footer_lines.append(f"Paiement: {payment}".center(self.line_width) + "\n")
        
        footer_lines.append(self._print_separator())
        footer_lines.append("Merci pour votre achat!".center(self.line_width) + "\n")
        footer_lines.append("Mankasitraka Tompoko!".center(self.line_width) + "\n")
        footer_lines.append("\n\n")
        
        # ========== ASSEMBLAGE AVEC GESTION DES PAGES ==========
        pages = []
        current_page = []
        
        # PAGE 1: En-tête + début articles
        current_page.extend(header_lines)
        header_size = len(header_lines)
        footer_size = len(footer_lines)
        
        # Espace disponible sur page 1 pour les articles
        space_page1 = self.max_lines_per_page - header_size - footer_size - 2  # -2 pour sécurité
        
        items_added = 0
        for line in items_lines:
            if len(current_page) < (self.max_lines_per_page - footer_size - 2):
                current_page.append(line)
                items_added += 1
            else:
                # Page pleine, créer nouvelle page
                pages.append("".join(current_page))
                current_page = []
        
        # Ajouter le footer à la dernière page
        current_page.extend(footer_lines)
        pages.append("".join(current_page))
        
        # Si une seule page, retourner directement
        if len(pages) == 1:
            return pages[0]
        
        # Sinon, joindre avec saut de page (form feed)
        return "\f".join(pages)
    
    def print_receipt(self, receipt_data):
        """Imprimer le reçu sur l'imprimante laser avec pagination intelligente"""
        try:
            # Formater le contenu avec pagination
            text_content = self._format_receipt_with_pagination(receipt_data)
            
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                suffix=".txt",
                encoding='utf-8'
            ) as tmp:
                tmp.write(text_content)
                tmp_path = tmp.name
            
            # Options pour A6 (10,5 x 14,8 cm) avec police monospace
            result = subprocess.run(
                [
                    "lp",
                    "-d", self.printer_name,
                    "-o", f"media={self.paper_format}",
                    "-o", "cpi=17",  # 17 caractères par pouce
                    "-o", "lpi=8",   # 8 lignes par pouce
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