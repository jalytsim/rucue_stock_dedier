"""
Base de données - Gestion des produits, reçus et paramètres
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class Database:
    def __init__(self, db_path="data/receipts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Obtenir une connexion à la base de données"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialiser les tables de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table des produits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                unit_price REAL NOT NULL,
                count INTEGER DEFAULT 0,
                total_sold REAL DEFAULT 0,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des reçus
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_number TEXT UNIQUE NOT NULL,
                date TEXT NOT NULL,
                client_name TEXT,
                client_phone TEXT,
                items TEXT NOT NULL,
                total REAL NOT NULL,
                payment_method TEXT DEFAULT 'Espèces',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des paramètres
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Initialiser les paramètres par défaut
        default_settings = {
            'company_name': 'COMPTOIR FIDAHOUSSEN',
            'company_address': '85 RUE DE LIEGE TSARALALANA\nANTANANARIVO 101',
            'company_phone': '020 76 231 43',
            'company_email': 'cf@moov.mg',
            'company_nif': '2000022547',
            'company_stat': '46101 11 1984 0 00029',
            'company_rc': '2003A00087',
            'company_ce': '520/FOK/FIATA',
            'company_cif': '0189577 DGI-M du 03/06/2025',
            'receipt_counter': '1',
            'currency': 'Ar',
            'paper_width': '58',  # mm
            'receipt_type': 'Grossiste - Détaillants/ Vente à l\'utilisateur'
        }
        
        for key, value in default_settings.items():
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
    
    # ========== PRODUITS ==========
    
    def add_or_update_product(self, name, unit_price):
        """Ajouter ou mettre à jour un produit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si le produit existe
        cursor.execute('SELECT id, count, total_sold FROM products WHERE name = ?', (name,))
        result = cursor.fetchone()
        
        if result:
            # Mise à jour
            product_id, count, total_sold = result
            cursor.execute('''
                UPDATE products 
                SET unit_price = ?, count = ?, total_sold = ?, last_used = ?
                WHERE id = ?
            ''', (unit_price, count + 1, total_sold + unit_price, datetime.now().isoformat(), product_id))
        else:
            # Insertion
            cursor.execute('''
                INSERT INTO products (name, unit_price, count, total_sold, last_used)
                VALUES (?, ?, 1, ?, ?)
            ''', (name, unit_price, unit_price, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def search_products(self, query):
        """Rechercher des produits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, unit_price, count, last_used
            FROM products
            WHERE name LIKE ?
            ORDER BY count DESC, last_used DESC
            LIMIT 10
        ''', (f'%{query}%',))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_products(self):
        """Obtenir tous les produits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, unit_price, count, total_sold, last_used
            FROM products
            ORDER BY count DESC
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def delete_product(self, product_id):
        """Supprimer un produit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
    
    # ========== REÇUS ==========
    
    def save_receipt(self, receipt_data):
        """Enregistrer un reçu"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        items_json = json.dumps(receipt_data['items'])
        
        cursor.execute('''
            INSERT INTO receipts 
            (receipt_number, date, client_name, client_phone, items, total, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            receipt_data['receipt_number'],
            receipt_data['date'],
            receipt_data.get('client_name', ''),
            receipt_data.get('client_phone', ''),
            items_json,
            receipt_data['total'],
            receipt_data.get('payment_method', 'Espèces'),
            receipt_data.get('notes', '')
        ))
        
        conn.commit()
        conn.close()
        
        # Incrémenter le compteur
        self.increment_receipt_counter()
    
    def get_all_receipts(self):
        """Obtenir tous les reçus"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, receipt_number, date, client_name, total, created_at
            FROM receipts
            ORDER BY created_at DESC
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_receipt_by_id(self, receipt_id):
        """Obtenir un reçu par ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT receipt_number, date, client_name, client_phone, items, total, payment_method, notes
            FROM receipts
            WHERE id = ?
        ''', (receipt_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'receipt_number': result[0],
                'date': result[1],
                'client_name': result[2],
                'client_phone': result[3],
                'items': json.loads(result[4]),
                'total': result[5],
                'payment_method': result[6],
                'notes': result[7]
            }
        return None
    
    def search_receipts(self, query):
        """Rechercher des reçus"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, receipt_number, date, client_name, total, created_at
            FROM receipts
            WHERE receipt_number LIKE ? OR client_name LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%'))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def delete_receipt(self, receipt_id):
        """Supprimer un reçu"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM receipts WHERE id = ?', (receipt_id,))
        conn.commit()
        conn.close()
    
    # ========== PARAMÈTRES ==========
    
    def get_setting(self, key, default=''):
        """Obtenir un paramètre"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default
    
    def set_setting(self, key, value):
        """Définir un paramètre"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, str(value)))
        conn.commit()
        conn.close()
    
    def get_all_settings(self):
        """Obtenir tous les paramètres"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        results = cursor.fetchall()
        conn.close()
        return dict(results)
    
    def increment_receipt_counter(self):
        """Incrémenter le compteur de reçus"""
        current = int(self.get_setting('receipt_counter', '1'))
        self.set_setting('receipt_counter', current + 1)
    
    def get_next_receipt_number(self):
        """Obtenir le prochain numéro de reçu"""
        counter = int(self.get_setting('receipt_counter', '1'))
        return f"FACT-{counter:05d}"
    
    # ========== STATISTIQUES ==========
    
    def get_statistics(self):
        """Obtenir les statistiques"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total des ventes
        cursor.execute('SELECT SUM(total) FROM receipts')
        total_sales = cursor.fetchone()[0] or 0
        
        # Nombre de reçus
        cursor.execute('SELECT COUNT(*) FROM receipts')
        total_receipts = cursor.fetchone()[0] or 0
        
        # Vente moyenne
        avg_sale = total_sales / total_receipts if total_receipts > 0 else 0
        
        # Nombre de produits uniques
        cursor.execute('SELECT COUNT(*) FROM products')
        unique_products = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_sales': total_sales,
            'total_receipts': total_receipts,
            'avg_sale': avg_sale,
            'unique_products': unique_products
        }
    
    def get_top_products(self, limit=5):
        """Obtenir les produits les plus vendus"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, count, total_sold
            FROM products
            ORDER BY total_sold DESC
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def clear_all_receipts(self):
        """Effacer tous les reçus"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM receipts')
        conn.commit()
        conn.close()
    
    def clear_all_products(self):
        """Effacer tous les produits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products')
        conn.commit()
        conn.close()
