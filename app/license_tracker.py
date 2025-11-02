#!/usr/bin/env python3
"""
LAC TRANSLATE - License Tracker
Database SQLite per tracciare licenze vendute e attivate
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class LicenseTracker:
    """Gestore database tracking licenze vendute"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "license_tracking.db"
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Inizializza database SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_key TEXT UNIQUE NOT NULL,
                customer_name TEXT,
                customer_email TEXT,
                customer_company TEXT,
                hardware_id TEXT,
                license_type TEXT DEFAULT 'FULL',
                sold_date DATE,
                sold_price REAL,
                activated_date DATE,
                activation_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indice per ricerca veloce
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_serial_key ON licenses(serial_key)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON licenses(status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sold_date ON licenses(sold_date)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"License tracker database initialized: {self.db_path}")
    
    def add_license(self, serial_key: str, customer_name: str = None, 
                    customer_email: str = None, customer_company: str = None,
                    sold_price: float = None, license_type: str = 'FULL',
                    notes: str = None) -> bool:
        """Aggiungi licenza venduta al database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO licenses 
                (serial_key, customer_name, customer_email, customer_company,
                 sold_price, license_type, status, notes, sold_date)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            ''', (serial_key, customer_name, customer_email, customer_company,
                  sold_price, license_type, notes, datetime.now().date()))
            conn.commit()
            logger.info(f"License added to database: {serial_key[:8]}...")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Serial key already exists: {serial_key[:8]}...")
            return False  # Serial key già esistente
        except Exception as e:
            logger.error(f"Error adding license: {e}")
            return False
        finally:
            conn.close()
    
    def activate_license(self, serial_key: str, hardware_id: str) -> bool:
        """Registra attivazione licenza"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE licenses 
                SET hardware_id = ?,
                    activated_date = ?,
                    activation_count = activation_count + 1,
                    status = 'activated',
                    updated_at = CURRENT_TIMESTAMP
                WHERE serial_key = ?
            ''', (hardware_id, datetime.now().date(), serial_key))
            
            success = cursor.rowcount > 0
            conn.commit()
            
            if success:
                logger.info(f"License activated: {serial_key[:8]}... on hardware {hardware_id[:8]}...")
            else:
                logger.warning(f"License not found for activation: {serial_key[:8]}...")
            
            conn.close()
            return success
        except Exception as e:
            logger.error(f"Error activating license: {e}")
            conn.close()
            return False
    
    def get_license_info(self, serial_key: str) -> Optional[Dict]:
        """Ottieni informazioni licenza"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM licenses WHERE serial_key = ?', (serial_key,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting license info: {e}")
            return None
        finally:
            conn.close()
    
    def list_licenses(self, status: str = None, limit: int = 100) -> List[Dict]:
        """Lista licenze con filtri"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute('''
                    SELECT * FROM licenses 
                    WHERE status = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT * FROM licenses 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error listing licenses: {e}")
            return []
        finally:
            conn.close()
    
    def get_sales_report(self, start_date: str = None, end_date: str = None) -> Dict:
        """Report vendite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT 
                    COUNT(*) as total_sold,
                    SUM(sold_price) as total_revenue,
                    COUNT(CASE WHEN status = 'activated' THEN 1 END) as total_activated,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as total_pending
                FROM licenses
            '''
            
            params = []
            if start_date or end_date:
                query += ' WHERE 1=1'
                if start_date:
                    query += ' AND sold_date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND sold_date <= ?'
                    params.append(end_date)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            return {
                'total_sold': result[0] or 0,
                'total_revenue': result[1] or 0.0,
                'total_activated': result[2] or 0,
                'total_pending': result[3] or 0
            }
        except Exception as e:
            logger.error(f"Error generating sales report: {e}")
            return {
                'total_sold': 0,
                'total_revenue': 0.0,
                'total_activated': 0,
                'total_pending': 0
            }
        finally:
            conn.close()
    
    def export_to_json(self, output_path: Path) -> bool:
        """Esporta database in JSON per backup"""
        licenses = self.list_licenses(limit=10000)
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(licenses, f, indent=2, default=str, ensure_ascii=False)
            logger.info(f"Database exported to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting database: {e}")
            return False
    
    def update_license_status(self, serial_key: str, status: str, notes: str = None) -> bool:
        """Aggiorna status licenza (es. revoked, expired)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if notes:
                cursor.execute('''
                    UPDATE licenses 
                    SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE serial_key = ?
                ''', (status, notes, serial_key))
            else:
                cursor.execute('''
                    UPDATE licenses 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE serial_key = ?
                ''', (status, serial_key))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"License status updated: {serial_key[:8]}... -> {status}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating license status: {e}")
            conn.close()
            return False

