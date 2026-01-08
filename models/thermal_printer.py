"""
Module d'impression thermique pour reçus
Imprime directement sur l'imprimante XP-Q300 sans passer par PDF
Respect du format du PDF pour cohérence
"""
from escpos.printer import Usb
from datetime import datetime


class ThermalPrinter:
    def __init__(self, settings):
        self.settings = settings
        self.printer = None
        self.paper_width = int(settings.get('paper_width', '58'))
        
    def connect(self):
        """Se connecter à l'imprimante XP-Q300"""
        try:
            # ID vendeur:produit et endpoints de votre XP-Q300
            self.printer = Usb(0x1fc9, 0x2016, in_ep=0x81, out_ep=0x02)
            return True, "Imprimante connectée"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"
    
    def _print_separator(self, char='='):
        """Imprimer une ligne de séparation"""
        width = 32 if self.paper_width == 58 else 48
        self.printer.text(char * width + "\n")
    
    def print_receipt(self, receipt_data):
        """
        Imprimer un reçu sur l'imprimante thermique
        Format identique au PDF : en-tête sur page 1, footer sur dernière page
        """
        try:
            # Se connecter si pas déjà fait
            if not self.printer:
                success, msg = self.connect()
                if not success:
                    return False, msg
            
            # Initialiser l'imprimante
            self.printer.set(align='center')
            
            # ========== EN-TÊTE (COMME PAGE 1 DU PDF) ==========
            
            # SECTION GAUCHE : Client (en haut à gauche conceptuellement)
            if receipt_data.get('client_name'):
                self.printer.set(align='left', bold=True)
                self.printer.text("CLIENT\n")
                self.printer.set(bold=False)
                self.printer.text(f"{receipt_data['client_name']}\n")
                if receipt_data.get('client_phone'):
                    self.printer.text(f"Tel: {receipt_data['client_phone']}\n")
                self.printer.text("\n")
            
            # SECTION DROITE : Entreprise (aligné à droite)
            self.printer.set(align='right')
            
            company_name = self.settings.get('company_name', '')
            if company_name:
                self.printer.set(bold=True, width=2, height=2)
                self.printer.text(f"{company_name}\n")
                self.printer.set(bold=False, width=1, height=1)
            
            # Adresse
            address = self.settings.get('company_address', '')
            if address:
                for line in address.split('\n'):
                    self.printer.text(f"{line}\n")
            
            # Coordonnées
            phone = self.settings.get('company_phone', '')
            email = self.settings.get('company_email', '')
            if phone:
                self.printer.text(f"Tel: {phone}\n")
            if email:
                self.printer.text(f"{email}\n")
            
            # Informations légales (petite taille)
            nif = self.settings.get('company_nif', '')
            stat = self.settings.get('company_stat', '')
            rc = self.settings.get('company_rc', '')
            ce = self.settings.get('company_ce', '')
            cif = self.settings.get('company_cif', '')
            
            if nif:
                self.printer.text(f"NIF: {nif}\n")
            if stat:
                self.printer.text(f"STAT: {stat}\n")
            if rc and ce:
                self.printer.text(f"R.C: {rc} - CE: {ce}\n")
            if cif:
                self.printer.text(f"CIF: {cif}\n")
            
            self.printer.text("\n")
            
            # Ligne de séparation
            self.printer.set(align='center')
            self._print_separator()
            self.printer.text("\n")
            
            # Type de vente
            receipt_type = self.settings.get('receipt_type', 'Vente')
            self.printer.text(f"{receipt_type}\n\n")
            
            # === INFORMATIONS DU REÇU ===
            self.printer.set(align='left')
            
            # Numéro et date
            self.printer.set(bold=True)
            self.printer.text(f"No: {receipt_data['receipt_number']}\n")
            self.printer.set(bold=False)
            
            # Formater la date
            try:
                date_obj = datetime.strptime(receipt_data['date'], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except:
                formatted_date = receipt_data['date']
            
            self.printer.text(f"Date: {formatted_date}\n\n")
            
            # Ligne de séparation
            self.printer.set(align='center')
            self._print_separator()
            self.printer.text("\n")
            
            # === TOTAL À PAYER (EN HAUT - COMME PAGE 1 DU PDF) ===
            currency = self.settings.get('currency', 'Ar')
            total = receipt_data['total']
            
            self.printer.set(align='center', bold=True)
            self.printer.text("TOTAL A PAYER\n")
            self.printer.set(width=2, height=2)
            self.printer.text(f"{total:,.0f} {currency}\n")
            self.printer.set(width=1, height=1)
            self.printer.text("\n")
            
            # Ligne de séparation
            self._print_separator()
            self.printer.text("\n")
            
            # === LISTE DES ARTICLES (AVEC PAGINATION POSSIBLE) ===
            self.printer.set(align='center', bold=True)
            self.printer.text("Liste des articles\n\n")
            
            self.printer.set(align='left', bold=False)
            
            for i, item in enumerate(receipt_data['items'], 1):
                # Nom du produit (gras)
                self.printer.set(bold=True)
                
                # Tronquer le nom si trop long
                max_chars = 30 if self.paper_width == 58 else 45
                item_name = item['name']
                if len(item_name) > max_chars:
                    item_name = item_name[:max_chars-3] + "..."
                
                self.printer.text(f"{i}. {item_name}\n")
                self.printer.set(bold=False)
                
                # Quantité x Prix = Total (avec indentation)
                qty = item['quantity']
                unit_price = item['unit_price']
                item_total = item['total']
                
                qty_line = f"   {qty:.0f} x {unit_price:,.0f} {currency} = {item_total:,.0f} {currency}\n"
                self.printer.text(qty_line)
                self.printer.text("\n")
            
            # === FOOTER (COMME DERNIÈRE PAGE DU PDF) ===
            
            # Espacement avant footer
            self.printer.text("\n")
            
            # Ligne de séparation avant footer
            self.printer.set(align='center')
            self._print_separator()
            self.printer.text("\n")
            
            # === RAPPEL DU TOTAL (EN BAS - COMME DERNIÈRE PAGE DU PDF) ===
            self.printer.set(align='center', bold=True)
            self.printer.text("TOTAL A PAYER (Rappel)\n")
            self.printer.set(width=2, height=2)
            self.printer.text(f"{total:,.0f} {currency}\n")
            self.printer.set(width=1, height=1)
            
            # Mode de paiement
            payment_method = receipt_data.get('payment_method', 'Especes')
            self.printer.text(f"\nPaiement: {payment_method}\n\n")
            
            # === PIED DE PAGE FINAL ===
            self._print_separator()
            self.printer.text("\n")
            self.printer.text("Merci pour votre achat!\n")
            self.printer.text("Mankasitraka Tompoko!\n")
            
            # Avancer le papier et couper
            self.printer.text("\n\n\n")
            self.printer.cut()
            
            return True, "Reçu imprimé avec succès"
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return False, f"Erreur d'impression: {str(e)}\n\nDétails:\n{error_detail}"
    
    def test_print(self):
        """Imprimer un reçu de test"""
        test_data = {
            'receipt_number': 'TEST-00001',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'client_name': 'Client Test',
            'client_phone': '034 00 000 00',
            'items': [
                {'name': 'Produit de test 1', 'quantity': 2, 'unit_price': 5000, 'total': 10000},
                {'name': 'Produit de test 2', 'quantity': 1, 'unit_price': 15000, 'total': 15000},
                {'name': 'Article avec un nom très très long pour tester', 'quantity': 3, 'unit_price': 2500, 'total': 7500}
            ],
            'total': 32500,
            'payment_method': 'Espèces'
        }
        
        return self.print_receipt(test_data)
    
    def check_connection(self):
        """Vérifier la connexion à l'imprimante"""
        success, msg = self.connect()
        if success and self.printer:
            self.printer = None  #