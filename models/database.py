"""
Base de données - Gestion des produits, reçus et paramètres
Version avec support contact (téléphone ou adresse) et formatage noms
"""
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, db_path="data/receipts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self):
        """Obtenir une connexion à la base de données"""
        return sqlite3.connect(self.db_path, timeout=10)

    @contextmanager
    def _cursor(self, commit=False):
        """Connexion toujours fermée, transaction annulée en cas d'erreur"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_database(self):
        """Initialiser les tables de la base de données"""
        with self._cursor(commit=True) as cursor:
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_number TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    client_name TEXT,
                    client_contact TEXT,
                    items TEXT NOT NULL,
                    total REAL NOT NULL,
                    payment_method TEXT DEFAULT 'Espèces',
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Migration : ancienne colonne client_phone -> client_contact
            cursor.execute("PRAGMA table_info(receipts)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'client_phone' in columns and 'client_contact' not in columns:
                cursor.execute('''
                    CREATE TABLE receipts_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        receipt_number TEXT UNIQUE NOT NULL,
                        date TEXT NOT NULL,
                        client_name TEXT,
                        client_contact TEXT,
                        items TEXT NOT NULL,
                        total REAL NOT NULL,
                        payment_method TEXT DEFAULT 'Espèces',
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    INSERT INTO receipts_new
                    SELECT id, receipt_number, date, client_name, client_phone,
                           items, total, payment_method, notes, created_at
                    FROM receipts
                ''')
                cursor.execute('DROP TABLE receipts')
                cursor.execute('ALTER TABLE receipts_new RENAME TO receipts')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(date)')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')

            default_settings = {
                'company_name': 'MAGASIN Ly',
                'company_address': 'PAV No: 28 TSENEA\nMIARINARIVO 117',
                'company_phone': '033 01 830 14',
                'company_email': 'contact@magasinly.mg',
                'company_nif': '3000262366',
                'company_stat': '13 19840 30001',
                'company_rc': '2003A00087',
                'company_ce': '520/FOK/FIATA',
                'company_cif': '0189577 DGI-M du 03/06/2025',
                'receipt_counter': '1',
                'currency': 'Ar',
                'paper_width': '58',
                'receipt_type': 'Grossiste - Détaillants/ Vente à l\'utilisateur',
                'laser_printer_name': 'HP_LaserJet_1022n',
                'laser_paper_format': 'A6',
                'laser_enabled': 'true',
            }

            for key, value in default_settings.items():
                cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                               (key, value))

    # ========== PRODUITS ==========

    def _learn_product(self, cursor, name, unit_price, quantity=1, line_total=None):
        """Mémoriser un produit vendu (prix, nombre de ventes, chiffre d'affaires)"""
        if line_total is None:
            line_total = unit_price * quantity
        now = datetime.now().isoformat(timespec='seconds')

        cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
        result = cursor.fetchone()

        if result:
            cursor.execute('''
                UPDATE products
                SET unit_price = ?, count = count + 1, total_sold = total_sold + ?, last_used = ?
                WHERE id = ?
            ''', (unit_price, line_total, now, result[0]))
        else:
            cursor.execute('''
                INSERT INTO products (name, unit_price, count, total_sold, last_used, created_at)
                VALUES (?, ?, 1, ?, ?, ?)
            ''', (name, unit_price, line_total, now, now))

    def add_or_update_product(self, name, unit_price, quantity=1):
        """Ajouter ou mettre à jour un produit"""
        with self._cursor(commit=True) as cursor:
            self._learn_product(cursor, name, unit_price, quantity)

    def update_product_price(self, product_id, unit_price):
        """Modifier le prix mémorisé d'un produit"""
        with self._cursor(commit=True) as cursor:
            cursor.execute('UPDATE products SET unit_price = ? WHERE id = ?',
                           (unit_price, product_id))

    def search_products(self, query, limit=8):
        """Rechercher des produits"""
        with self._cursor() as cursor:
            cursor.execute('''
                SELECT name, unit_price, count, last_used
                FROM products
                WHERE name LIKE ?
                ORDER BY (name LIKE ?) DESC, count DESC, last_used DESC
                LIMIT ?
            ''', (f'%{query}%', f'{query}%', limit))
            return cursor.fetchall()

    def get_all_products(self, query=''):
        """Obtenir tous les produits (filtrés optionnellement)"""
        with self._cursor() as cursor:
            cursor.execute('''
                SELECT id, name, unit_price, count, total_sold, last_used
                FROM products
                WHERE name LIKE ?
                ORDER BY count DESC, name
            ''', (f'%{query}%',))
            return cursor.fetchall()

    def delete_product(self, product_id):
        """Supprimer un produit"""
        with self._cursor(commit=True) as cursor:
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))

    # ========== REÇUS ==========

    def _next_counter(self, cursor):
        """Prochain numéro libre : jamais inférieur au plus grand numéro déjà utilisé"""
        cursor.execute("SELECT value FROM settings WHERE key = 'receipt_counter'")
        row = cursor.fetchone()
        try:
            counter = int(row[0]) if row else 1
        except (TypeError, ValueError):
            counter = 1

        cursor.execute('''
            SELECT MAX(CAST(SUBSTR(receipt_number, 6) AS INTEGER))
            FROM receipts WHERE receipt_number LIKE 'FACT-%'
        ''')
        max_used = cursor.fetchone()[0] or 0
        return max(counter, max_used + 1, 1)

    def save_receipt(self, receipt_data):
        """
        Enregistrer un reçu dans une seule transaction :
        numéro attribué, reçu inséré, compteur incrémenté, produits appris.
        Met à jour receipt_data['receipt_number'] avec le numéro définitif.
        """
        with self._cursor(commit=True) as cursor:
            counter = self._next_counter(cursor)
            receipt_number = f"FACT-{counter:05d}"
            receipt_data['receipt_number'] = receipt_number

            cursor.execute('''
                INSERT INTO receipts
                (receipt_number, date, client_name, client_contact, items, total,
                 payment_method, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                receipt_number,
                receipt_data['date'],
                receipt_data.get('client_name', ''),
                receipt_data.get('client_contact', ''),
                json.dumps(receipt_data['items'], ensure_ascii=False),
                receipt_data['total'],
                receipt_data.get('payment_method', 'Espèces'),
                receipt_data.get('notes', ''),
                datetime.now().isoformat(timespec='seconds'),
            ))

            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('receipt_counter', ?)",
                           (str(counter + 1),))

            for item in receipt_data['items']:
                self._learn_product(cursor, item['name'], item['unit_price'],
                                    item['quantity'], item['total'])

        return receipt_number

    def get_all_receipts(self):
        """Obtenir tous les reçus"""
        return self.search_receipts('')

    def get_receipt_by_id(self, receipt_id):
        """Obtenir un reçu par ID"""
        with self._cursor() as cursor:
            cursor.execute('''
                SELECT receipt_number, date, client_name, client_contact, items, total,
                       payment_method, notes, created_at
                FROM receipts
                WHERE id = ?
            ''', (receipt_id,))
            result = cursor.fetchone()

        if not result:
            return None
        try:
            items = json.loads(result[4])
        except (TypeError, ValueError):
            items = []
        return {
            'receipt_number': result[0],
            'date': result[1],
            'client_name': result[2] or '',
            'client_contact': result[3] or '',
            'items': items,
            'total': result[5],
            'payment_method': result[6] or 'Espèces',
            'notes': result[7] or '',
            'created_at': result[8],
        }

    def search_receipts(self, query):
        """Rechercher des reçus (numéro, client, contact)"""
        like = f'%{query}%'
        with self._cursor() as cursor:
            cursor.execute('''
                SELECT id, receipt_number, date, client_name, total, created_at
                FROM receipts
                WHERE receipt_number LIKE ? OR client_name LIKE ? OR client_contact LIKE ?
                ORDER BY id DESC
            ''', (like, like, like))
            return cursor.fetchall()

    def delete_receipt(self, receipt_id):
        """Supprimer un reçu"""
        with self._cursor(commit=True) as cursor:
            cursor.execute('DELETE FROM receipts WHERE id = ?', (receipt_id,))

    # ========== PARAMÈTRES ==========

    def get_setting(self, key, default=''):
        """Obtenir un paramètre"""
        with self._cursor() as cursor:
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
        return result[0] if result else default

    def set_setting(self, key, value):
        """Définir un paramètre"""
        self.set_settings({key: value})

    def set_settings(self, settings_dict):
        """Définir plusieurs paramètres en une transaction"""
        with self._cursor(commit=True) as cursor:
            cursor.executemany('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                               [(k, str(v)) for k, v in settings_dict.items()])

    def get_all_settings(self):
        """Obtenir tous les paramètres"""
        with self._cursor() as cursor:
            cursor.execute('SELECT key, value FROM settings')
            return dict(cursor.fetchall())

    def increment_receipt_counter(self):
        """Incrémenter le compteur de reçus"""
        current = int(self.get_setting('receipt_counter', '1'))
        self.set_setting('receipt_counter', current + 1)

    def get_next_receipt_number(self):
        """Obtenir le prochain numéro de reçu (aperçu)"""
        with self._cursor() as cursor:
            return f"FACT-{self._next_counter(cursor):05d}"

    # ========== STATISTIQUES ==========

    def get_statistics(self):
        """Obtenir les statistiques"""
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')
        with self._cursor() as cursor:
            cursor.execute('SELECT COALESCE(SUM(total), 0), COUNT(*) FROM receipts')
            total_sales, total_receipts = cursor.fetchone()

            cursor.execute('SELECT COALESCE(SUM(total), 0), COUNT(*) FROM receipts WHERE date = ?',
                           (today,))
            today_sales, today_receipts = cursor.fetchone()

            cursor.execute("SELECT COALESCE(SUM(total), 0), COUNT(*) FROM receipts WHERE date LIKE ?",
                           (f'{month}%',))
            month_sales, month_receipts = cursor.fetchone()

            cursor.execute('SELECT COUNT(*) FROM products')
            unique_products = cursor.fetchone()[0] or 0

        return {
            'total_sales': total_sales,
            'total_receipts': total_receipts,
            'avg_sale': total_sales / total_receipts if total_receipts else 0,
            'unique_products': unique_products,
            'today_sales': today_sales,
            'today_receipts': today_receipts,
            'month_sales': month_sales,
            'month_receipts': month_receipts,
        }

    def get_top_products(self, limit=5):
        """Obtenir les produits les plus vendus"""
        with self._cursor() as cursor:
            cursor.execute('''
                SELECT name, count, total_sold
                FROM products
                ORDER BY total_sold DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def clear_all_receipts(self):
        """Effacer tous les reçus"""
        with self._cursor(commit=True) as cursor:
            cursor.execute('DELETE FROM receipts')

    def clear_all_products(self):
        """Effacer tous les produits"""
        with self._cursor(commit=True) as cursor:
            cursor.execute('DELETE FROM products')
