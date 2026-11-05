"""
Contrôleur principal de l'application
Version avec formatage intelligent des noms et support adresse
"""
from datetime import datetime
from pathlib import Path
import traceback

from utils.name_formatter import format_client_name

EXPORTS_DIR = Path('exports')


class ReceiptController:
    def __init__(self, database, pdf_generator):
        self.db = database
        self.pdf_generator = pdf_generator
        self.current_items = []

    # ========== ARTICLES EN COURS ==========

    def add_item(self, name, quantity, unit_price):
        """Ajouter un article au reçu en cours (fusionne avec une ligne identique)"""
        name = (name or '').strip()
        if not name:
            return False, "Le nom du produit est obligatoire"
        if quantity <= 0:
            return False, "La quantité doit être supérieure à 0"
        if unit_price <= 0:
            return False, "Le prix unitaire doit être supérieur à 0"

        for item in self.current_items:
            if item['name'].lower() == name.lower() and item['unit_price'] == unit_price:
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['unit_price']
                return True, item

        item = {
            'name': name,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': quantity * unit_price,
        }
        self.current_items.append(item)
        # Le produit est mémorisé lors de l'enregistrement du reçu (pas ici),
        # sinon un article ajouté puis retiré gonflait les statistiques.
        return True, item

    def remove_item(self, index):
        """Retirer un article"""
        if 0 <= index < len(self.current_items):
            return True, self.current_items.pop(index)
        return False, None

    def get_current_items(self):
        return self.current_items

    def get_current_total(self):
        return sum(item['total'] for item in self.current_items)

    def clear_current_items(self):
        self.current_items = []

    # ========== ENREGISTREMENT / IMPRESSION ==========

    def _prepare_receipt_data(self, client_name='', client_contact='', payment_method='Espèces', notes=''):
        """Préparer les données du reçu avec formatage du nom"""
        client_name = (client_name or '').strip()
        return {
            'receipt_number': self.db.get_next_receipt_number(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'client_name': format_client_name(client_name) if client_name else 'Client',
            'client_contact': (client_contact or '').strip(),
            'items': [dict(item) for item in self.current_items],
            'total': self.get_current_total(),
            'payment_method': payment_method,
            'notes': notes,
        }

    def _save_current(self, **client):
        """Enregistre le reçu en cours. Retourne (receipt_data, erreur)."""
        if not self.current_items:
            return None, "Aucun article dans le reçu"
        receipt_data = self._prepare_receipt_data(**client)
        try:
            self.db.save_receipt(receipt_data)
        except Exception as e:
            return None, f"Erreur de sauvegarde : {e}"
        self.clear_current_items()
        return receipt_data, None

    def _generate_pdf(self, receipt_data, suffix=''):
        EXPORTS_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = EXPORTS_DIR / f"{receipt_data['receipt_number']}{suffix}_{stamp}.pdf"
        self.pdf_generator.settings = self.db.get_all_settings()
        self.pdf_generator.generate_receipt(receipt_data, str(output_path))
        return str(output_path.resolve())

    def _make_printer(self, kind):
        settings = self.db.get_all_settings()
        if kind == 'thermal':
            from models.thermal_printer import ThermalPrinter
            return ThermalPrinter(settings)
        from models.laser_printer import LaserPrinter
        return LaserPrinter(settings)

    def _print(self, kind, receipt_data):
        """Imprime receipt_data. Retourne (succès, message)."""
        try:
            printer = self._make_printer(kind)
            return printer.print_receipt(receipt_data)
        except ImportError as e:
            return False, (f"Module d'impression manquant : {e}\n"
                           "Installez-le avec : pip install python-escpos")
        except Exception as e:
            return False, f"{e}\n\nDétails :\n{traceback.format_exc()}"

    def save_and_generate_receipt(self, client_name='', client_contact='', payment_method='Espèces', notes=''):
        """Sauvegarder et générer le reçu PDF. Retourne (succès, chemin_ou_erreur)."""
        receipt_data, error = self._save_current(client_name=client_name, client_contact=client_contact,
                                                 payment_method=payment_method, notes=notes)
        if error:
            return False, error
        try:
            return True, self._generate_pdf(receipt_data)
        except Exception as e:
            return False, (f"Reçu {receipt_data['receipt_number']} enregistré dans l'historique, "
                           f"mais la génération du PDF a échoué :\n{e}")

    def _save_and_print(self, kind, label, **client):
        receipt_data, error = self._save_current(**client)
        if error:
            return False, error
        success, message = self._print(kind, receipt_data)
        number = receipt_data['receipt_number']
        if success:
            return True, f"Reçu {number} imprimé ({label}) et enregistré"
        return False, (f"Reçu {number} enregistré dans l'historique, mais l'impression {label} a échoué.\n"
                       f"Vous pourrez le réimprimer depuis l'Historique.\n\n{message}")

    def print_thermal_receipt(self, client_name='', client_contact='', payment_method='Espèces', notes=''):
        return self._save_and_print('thermal', 'thermique', client_name=client_name,
                                    client_contact=client_contact, payment_method=payment_method, notes=notes)

    def print_laser_receipt(self, client_name='', client_contact='', payment_method='Espèces', notes=''):
        return self._save_and_print('laser', 'laser', client_name=client_name,
                                    client_contact=client_contact, payment_method=payment_method, notes=notes)

    def test_thermal_printer(self):
        try:
            return self._make_printer('thermal').check_connection()
        except ImportError as e:
            return False, f"Module d'impression manquant : {e}\nInstallez-le avec : pip install python-escpos"
        except Exception as e:
            return False, f"Erreur : {e}"

    def test_laser_printer(self):
        try:
            return self._make_printer('laser').check_connection()
        except Exception as e:
            return False, f"Erreur : {e}"

    def test_laser_print(self):
        try:
            return self._make_printer('laser').test_print()
        except Exception as e:
            return False, f"Erreur : {e}"

    def is_laser_enabled(self):
        return self.db.get_setting('laser_enabled', 'true') == 'true'

    # ========== PRODUITS ==========

    def search_products(self, query):
        if not query:
            return []
        return self.db.search_products(query)

    def get_all_products(self, query=''):
        return self.db.get_all_products(query)

    def delete_product(self, product_id):
        self.db.delete_product(product_id)

    def update_product_price(self, product_id, unit_price):
        self.db.update_product_price(product_id, unit_price)

    # ========== HISTORIQUE ==========

    def get_all_receipts(self):
        return self.db.get_all_receipts()

    def search_receipts(self, query):
        return self.db.search_receipts(query)

    def get_receipt_details(self, receipt_id):
        return self.db.get_receipt_by_id(receipt_id)

    def delete_receipt(self, receipt_id):
        self.db.delete_receipt(receipt_id)

    def regenerate_receipt(self, receipt_id):
        receipt_data = self.db.get_receipt_by_id(receipt_id)
        if not receipt_data:
            return False, "Reçu introuvable"
        try:
            return True, self._generate_pdf(receipt_data, suffix='_regenere')
        except Exception as e:
            return False, f"Erreur : {e}"

    def _reprint(self, kind, label, receipt_id):
        receipt_data = self.db.get_receipt_by_id(receipt_id)
        if not receipt_data:
            return False, "Reçu introuvable"
        success, message = self._print(kind, receipt_data)
        if success:
            return True, f"Reçu {receipt_data['receipt_number']} réimprimé ({label})"
        return False, f"Erreur de réimpression {label} :\n{message}"

    def reprint_thermal_receipt(self, receipt_id):
        return self._reprint('thermal', 'thermique', receipt_id)

    def reprint_laser_receipt(self, receipt_id):
        return self._reprint('laser', 'laser', receipt_id)

    # ========== STATISTIQUES / PARAMÈTRES ==========

    def get_statistics(self):
        return self.db.get_statistics()

    def get_top_products(self, limit=5):
        return self.db.get_top_products(limit)

    def save_settings(self, settings_dict):
        self.db.set_settings(settings_dict)

    def get_settings(self):
        return self.db.get_all_settings()

    def get_currency(self):
        return self.db.get_setting('currency', 'Ar')

    def clear_all_data(self):
        self.db.clear_all_receipts()
        self.db.clear_all_products()
        self.clear_current_items()
