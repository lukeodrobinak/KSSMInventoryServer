import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import json

class InventoryDatabase:
    def __init__(self, db_path: str = "inventory.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                barcode TEXT UNIQUE,
                serial_number TEXT,
                storage_location TEXT,
                is_checked_out INTEGER DEFAULT 0,
                checked_out_by TEXT,
                checked_out_date TEXT,
                image_url TEXT,
                notes TEXT,
                created_date TEXT NOT NULL,
                last_modified_date TEXT NOT NULL
            )
        """)
        
        # Create check in/out history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkout_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                person_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_item(self, item_data: Dict) -> int:
        """Add a new item to the inventory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO items (
                name, description, category, barcode, serial_number,
                storage_location, image_url, notes, created_date, last_modified_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_data.get('name'),
            item_data.get('description'),
            item_data.get('category'),
            item_data.get('barcode'),
            item_data.get('serial_number'),
            item_data.get('storage_location'),
            item_data.get('image_url'),
            item_data.get('notes'),
            now,
            now
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
    
    def get_all_items(self) -> List[Dict]:
        """Get all items in the inventory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM items ORDER BY name")
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append(dict(row))
        
        conn.close()
        return items
    
    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get a single item by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_item(self, item_id: int, item_data: Dict) -> bool:
        """Update an existing item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE items SET
                name = ?,
                description = ?,
                category = ?,
                barcode = ?,
                serial_number = ?,
                storage_location = ?,
                image_url = ?,
                notes = ?,
                last_modified_date = ?
            WHERE id = ?
        """, (
            item_data.get('name'),
            item_data.get('description'),
            item_data.get('category'),
            item_data.get('barcode'),
            item_data.get('serial_number'),
            item_data.get('storage_location'),
            item_data.get('image_url'),
            item_data.get('notes'),
            now,
            item_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_item(self, item_id: int) -> bool:
        """Delete an item from the inventory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Delete history first
        cursor.execute("DELETE FROM checkout_history WHERE item_id = ?", (item_id,))
        
        # Delete item
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def checkout_item(self, item_id: int, person_name: str, notes: str = "") -> bool:
        """Check out an item to a person"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Update item status
        cursor.execute("""
            UPDATE items SET
                is_checked_out = 1,
                checked_out_by = ?,
                checked_out_date = ?,
                last_modified_date = ?
            WHERE id = ? AND is_checked_out = 0
        """, (person_name, now, now, item_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return False
        
        # Add to history
        cursor.execute("""
            INSERT INTO checkout_history (item_id, action, person_name, timestamp, notes)
            VALUES (?, 'checkout', ?, ?, ?)
        """, (item_id, person_name, now, notes))
        
        conn.commit()
        conn.close()
        
        return True
    
    def checkin_item(self, item_id: int, person_name: str, notes: str = "") -> bool:
        """Check in an item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Update item status
        cursor.execute("""
            UPDATE items SET
                is_checked_out = 0,
                checked_out_by = NULL,
                checked_out_date = NULL,
                last_modified_date = ?
            WHERE id = ? AND is_checked_out = 1
        """, (now, item_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return False
        
        # Add to history
        cursor.execute("""
            INSERT INTO checkout_history (item_id, action, person_name, timestamp, notes)
            VALUES (?, 'checkin', ?, ?, ?)
        """, (item_id, person_name, now, notes))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_item_history(self, item_id: int) -> List[Dict]:
        """Get the checkout history for an item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM checkout_history
            WHERE item_id = ?
            ORDER BY timestamp DESC
        """, (item_id,))
        
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append(dict(row))
        
        conn.close()
        return history
    
    def search_items(self, query: str) -> List[Dict]:
        """Search items by name, description, or barcode"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_query = f"%{query}%"
        
        cursor.execute("""
            SELECT * FROM items
            WHERE name LIKE ? OR description LIKE ? OR barcode LIKE ?
            ORDER BY name
        """, (search_query, search_query, search_query))
        
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append(dict(row))
        
        conn.close()
        return items
