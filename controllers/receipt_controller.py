"""
Contrôleur principal de l'application
"""
from datetime import datetime
import os
from pathlib import Path

class ReceiptController:
    def __init__(self, database, pdf_generator):
        self.db = database
        self.pdf_generator = pdf_generator
        self.current_items = []
    
    def add_item(self, name, quantity, unit_price):
        """Ajouter un article au reçu en cours"""
        if not name or quantity <= 0 or unit_price <= 0:
            return False, "Données invalides"
        
        total = quantity * unit_price
        
        item = {
            'name': name,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': total
        }
        
        self.current_items.append(item)
        
        # Apprendre le produit
        self.db.add_or_update_product(name, unit_price)
        
        return True, item
    
    def remove_item(self, index):
        """Retirer un article"""
        if 0 <= index < len(self.current_items):
            removed = self.current_items.pop(index)
            return True, removed
        return False, None
    
    def get_current_items(self):
        """Obtenir les articles actuels"""
        return self.current_items
    
    def get_current_total(self):
        """Calculer le total actuel"""
        return sum(item['total'] for item in self.current_items)
    
    def clear_current_items(self):
        """Vider les articles actuels"""
        self.current_items = []
    
    def save_and_generate_receipt(self, client_name='', client_phone='', payment_method='Espèces', notes=''):
        """Sauvegarder et générer le reçu PDF"""
        if not self.current_items:
            return False, "Aucun article à facturer"
        
        # Préparer les données du reçu
        receipt_data = {
            'receipt_number': self.db.get_next_receipt_number(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'client_name': client_name,
            'client_phone': client_phone,
            'items': self.current_items.copy(),
            'total': self.get_current_total(),
            'payment_method': payment_method,
            'notes': notes
        }
        
        # Sauvegarder dans la base de données
        try:
            self.db.save_receipt(receipt_data)
        except Exception as e:
            return False, f"Erreur de sauvegarde: {str(e)}"
        
        # Générer le PDF
        try:
            output_dir = Path('exports')
            output_dir.mkdir(exist_ok=True)
            
            filename = f"{receipt_data['receipt_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = output_dir / filename
            
            settings = self.db.get_all_settings()
            self.pdf_generator.settings = settings
            
            self.pdf_generator.generate_receipt(receipt_data, str(output_path))
            
            # Vider les articles actuels
            self.clear_current_items()
            
            return True, str(output_path)
        
        except Exception as e:
            return False, f"Erreur de génération PDF: {str(e)}"
    
    def print_thermal_receipt(self, client_name='', client_phone='', payment_method='Espèces', notes=''):
        """Imprimer directement sur l'imprimante thermique et sauvegarder dans l'historique"""
        if not self.current_items:
            return False, "Aucun article à imprimer"
        
        # Préparer les données du reçu
        receipt_data = {
            'receipt_number': self.db.get_next_receipt_number(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'client_name': client_name,
            'client_phone': client_phone,
            'items': self.current_items.copy(),
            'total': self.get_current_total(),
            'payment_method': payment_method,
            'notes': notes
        }
        
        # Sauvegarder dans la base de données AVANT l'impression
        try:
            self.db.save_receipt(receipt_data)
        except Exception as e:
            return False, f"Erreur de sauvegarde: {str(e)}"
        
        # Imprimer sur l'imprimante thermique
        try:
            from models.thermal_printer import ThermalPrinter
            settings = self.db.get_all_settings()
            printer = ThermalPrinter(settings)
            
            success, message = printer.print_receipt(receipt_data)
            
            if success:
                # Vider les articles actuels seulement si impression réussie
                self.clear_current_items()
                return True, f"Reçu {receipt_data['receipt_number']} imprimé et sauvegardé"
            else:
                # L'impression a échoué mais le reçu est sauvegardé dans l'historique
                self.clear_current_items()
                return False, f"Reçu sauvegardé dans l'historique mais erreur d'impression:\n{message}"
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            # Le reçu est déjà sauvegardé dans l'historique
            self.clear_current_items()
            return False, f"Reçu sauvegardé dans l'historique mais erreur d'impression:\n{str(e)}\n\nDétails:\n{error_detail}"
    
    def test_thermal_printer(self):
        """Tester la connexion à l'imprimante thermique"""
        try:
            from models.thermal_printer import ThermalPrinter
            settings = self.db.get_all_settings()
            printer = ThermalPrinter(settings)
            return printer.check_connection()
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def search_products(self, query):
        """Rechercher des produits"""
        if not query:
            return []
        return self.db.search_products(query)
    
    def get_all_products(self):
        """Obtenir tous les produits"""
        return self.db.get_all_products()
    
    def delete_product(self, product_id):
        """Supprimer un produit"""
        self.db.delete_product(product_id)
    
    def get_all_receipts(self):
        """Obtenir tous les reçus"""
        return self.db.get_all_receipts()
    
    def search_receipts(self, query):
        """Rechercher des reçus"""
        return self.db.search_receipts(query)
    
    def get_receipt_details(self, receipt_id):
        """Obtenir les détails d'un reçu"""
        return self.db.get_receipt_by_id(receipt_id)
    
    def delete_receipt(self, receipt_id):
        """Supprimer un reçu"""
        self.db.delete_receipt(receipt_id)
    
    def regenerate_receipt(self, receipt_id):
        """Régénérer un reçu existant"""
        receipt_data = self.db.get_receipt_by_id(receipt_id)
        
        if not receipt_data:
            return False, "Reçu introuvable"
        
        try:
            output_dir = Path('exports')
            output_dir.mkdir(exist_ok=True)
            
            filename = f"{receipt_data['receipt_number']}_regenere_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = output_dir / filename
            
            settings = self.db.get_all_settings()
            self.pdf_generator.settings = settings
            
            self.pdf_generator.generate_receipt(receipt_data, str(output_path))
            
            return True, str(output_path)
        
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def reprint_thermal_receipt(self, receipt_id):
        """Réimprimer un reçu existant sur l'imprimante thermique"""
        receipt_data = self.db.get_receipt_by_id(receipt_id)
        
        if not receipt_data:
            return False, "Reçu introuvable"
        
        try:
            from models.thermal_printer import ThermalPrinter
            settings = self.db.get_all_settings()
            printer = ThermalPrinter(settings)
            
            success, message = printer.print_receipt(receipt_data)
            
            if success:
                return True, f"Reçu {receipt_data['receipt_number']} réimprimé avec succès"
            else:
                return False, message
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return False, f"Erreur de réimpression:\n{str(e)}\n\nDétails:\n{error_detail}"
        
    def print_laser_receipt(self, client_name='', client_phone='', payment_method='Espèces', notes=''):
        """Imprimer directement sur l'imprimante laser et sauvegarder dans l'historique"""
        if not self.current_items:
            return False, "Aucun article à imprimer"
        
        # Préparer les données du reçu
        receipt_data = {
            'receipt_number': self.db.get_next_receipt_number(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'client_name': client_name,
            'client_phone': client_phone,
            'items': self.current_items.copy(),
            'total': self.get_current_total(),
            'payment_method': payment_method,
            'notes': notes
        }
        
        # Sauvegarder dans la base de données AVANT l'impression
        try:
            self.db.save_receipt(receipt_data)
        except Exception as e:
            return False, f"Erreur de sauvegarde: {str(e)}"
        
        # Imprimer sur l'imprimante laser
        try:
            from models.laser_printer import LaserPrinter
            settings = self.db.get_all_settings()
            printer = LaserPrinter(settings)
            
            success, message = printer.print_receipt(receipt_data)
            
            if success:
                # Vider les articles actuels seulement si impression réussie
                self.clear_current_items()
                return True, f"Reçu {receipt_data['receipt_number']} imprimé (laser) et sauvegardé"
            else:
                # L'impression a échoué mais le reçu est sauvegardé dans l'historique
                self.clear_current_items()
                return False, f"Reçu sauvegardé dans l'historique mais erreur d'impression laser:\n{message}"
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            # Le reçu est déjà sauvegardé dans l'historique
            self.clear_current_items()
            return False, f"Reçu sauvegardé dans l'historique mais erreur d'impression laser:\n{str(e)}\n\nDétails:\n{error_detail}"

    def test_laser_printer(self):
        """Tester la connexion à l'imprimante laser"""
        try:
            from models.laser_printer import LaserPrinter
            settings = self.db.get_all_settings()
            printer = LaserPrinter(settings)
            return printer.check_connection()
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def reprint_laser_receipt(self, receipt_id):
        """Réimprimer un reçu existant sur l'imprimante laser"""
        receipt_data = self.db.get_receipt_by_id(receipt_id)
        
        if not receipt_data:
            return False, "Reçu introuvable"
        
        try:
            from models.laser_printer import LaserPrinter
            settings = self.db.get_all_settings()
            printer = LaserPrinter(settings)
            
            success, message = printer.print_receipt(receipt_data)
            
            if success:
                return True, f"Reçu {receipt_data['receipt_number']} réimprimé (laser) avec succès"
            else:
                return False, message
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return False, f"Erreur de réimpression laser:\n{str(e)}\n\nDétails:\n{error_detail}"
    
    def get_statistics(self):
        """Obtenir les statistiques"""
        return self.db.get_statistics()
    
    def get_top_products(self, limit=5):
        """Obtenir les produits les plus vendus"""
        return self.db.get_top_products(limit)
    
    def save_settings(self, settings_dict):
        """Sauvegarder les paramètres"""
        for key, value in settings_dict.items():
            self.db.set_setting(key, value)
    
    def get_settings(self):
        """Obtenir les paramètres"""
        return self.db.get_all_settings()
    
    def clear_all_data(self):
        """Effacer toutes les données"""
        self.db.clear_all_receipts()
        self.db.clear_all_products()
        self.clear_current_items()