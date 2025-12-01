import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from passlib.context import CryptContext
import hashlib

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _prepare_password(password: str) -> bytes:
    """Pre-hash password with SHA256 to ensure it's under bcrypt's 72-byte limit"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')

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

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_date TEXT NOT NULL,
                last_login TEXT
            )
        """)

        # Create item_requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id INTEGER NOT NULL,
                request_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                description TEXT NOT NULL,
                item_id INTEGER,
                status TEXT DEFAULT 'pending',
                denial_reason TEXT,
                created_date TEXT NOT NULL,
                reviewed_date TEXT,
                reviewed_by_id INTEGER,
                FOREIGN KEY (requester_id) REFERENCES users(id),
                FOREIGN KEY (reviewed_by_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)

        # Create categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_by_id INTEGER NOT NULL,
                created_date TEXT NOT NULL,
                FOREIGN KEY (created_by_id) REFERENCES users(id)
            )
        """)

        # Create locations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_by_id INTEGER NOT NULL,
                created_date TEXT NOT NULL,
                FOREIGN KEY (created_by_id) REFERENCES users(id)
            )
        """)

        conn.commit()

        # Create default quartermaster account if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            self._create_default_quartermaster(conn)

        conn.close()

    def _create_default_quartermaster(self, conn):
        """Create default quartermaster account"""
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Default credentials: admin / ChangeMe123!
        default_username = "admin"
        default_password = "ChangeMe123!"
        password_hash = pwd_context.hash(_prepare_password(default_password))

        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (default_username, password_hash, "Default Quartermaster", "quartermaster", now))

        conn.commit()
        print(f"\n{'='*60}")
        print("Default Quartermaster Account Created")
        print(f"{'='*60}")
        print(f"Username: {default_username}")
        print(f"Password: {default_password}")
        print(f"{'='*60}")
        print("IMPORTANT: Please change these credentials after first login!")
        print(f"{'='*60}\n")
    
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

    # MARK: - User Management Methods

    def create_user(self, username: str, password: str, full_name: str, role: str) -> int:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        password_hash = pwd_context.hash(_prepare_password(password))

        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, full_name, role, now))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return user_id

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users ORDER BY created_date DESC")
        rows = cursor.fetchall()

        users = []
        for row in rows:
            users.append(dict(row))

        conn.close()
        return users

    def update_user(self, user_id: int, user_data: Dict) -> bool:
        """Update user information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build update query dynamically based on provided fields
        update_fields = []
        values = []

        if 'username' in user_data and user_data['username'] is not None:
            update_fields.append("username = ?")
            values.append(user_data['username'])

        if 'full_name' in user_data and user_data['full_name'] is not None:
            update_fields.append("full_name = ?")
            values.append(user_data['full_name'])

        if 'role' in user_data and user_data['role'] is not None:
            update_fields.append("role = ?")
            values.append(user_data['role'])

        if 'password' in user_data and user_data['password'] is not None:
            update_fields.append("password_hash = ?")
            values.append(pwd_context.hash(_prepare_password(user_data['password'])))

        if 'is_active' in user_data:
            update_fields.append("is_active = ?")
            values.append(user_data['is_active'])

        if not update_fields:
            conn.close()
            return False

        values.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"

        cursor.execute(query, values)
        success = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return success

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
        success = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return success

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(_prepare_password(plain_password), hashed_password)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user (soft delete by setting is_active to 0)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        success = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return success

    # MARK: - Item Request Methods

    def create_item_request(self, requester_id: int, request_type: str, item_name: str, description: str, item_id: Optional[int] = None) -> int:
        """Create a new item request"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO item_requests (requester_id, request_type, item_name, description, item_id, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (requester_id, request_type, item_name, description, item_id, now))

        request_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return request_id

    def get_all_requests(self) -> List[Dict]:
        """Get all item requests with user information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ir.*,
                u1.full_name as requester_name,
                u2.full_name as reviewed_by_name
            FROM item_requests ir
            LEFT JOIN users u1 ON ir.requester_id = u1.id
            LEFT JOIN users u2 ON ir.reviewed_by_id = u2.id
            ORDER BY ir.created_date DESC
        """)

        rows = cursor.fetchall()

        requests = []
        for row in rows:
            requests.append(dict(row))

        conn.close()
        return requests

    def get_requests_by_user(self, user_id: int) -> List[Dict]:
        """Get all requests created by a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ir.*,
                u1.full_name as requester_name,
                u2.full_name as reviewed_by_name
            FROM item_requests ir
            LEFT JOIN users u1 ON ir.requester_id = u1.id
            LEFT JOIN users u2 ON ir.reviewed_by_id = u2.id
            WHERE ir.requester_id = ?
            ORDER BY ir.created_date DESC
        """, (user_id,))

        rows = cursor.fetchall()

        requests = []
        for row in rows:
            requests.append(dict(row))

        conn.close()
        return requests

    def get_pending_requests(self) -> List[Dict]:
        """Get all pending requests"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ir.*,
                u1.full_name as requester_name,
                u2.full_name as reviewed_by_name
            FROM item_requests ir
            LEFT JOIN users u1 ON ir.requester_id = u1.id
            LEFT JOIN users u2 ON ir.reviewed_by_id = u2.id
            WHERE ir.status = 'pending'
            ORDER BY ir.created_date DESC
        """)

        rows = cursor.fetchall()

        requests = []
        for row in rows:
            requests.append(dict(row))

        conn.close()
        return requests

    def update_request_status(self, request_id: int, status: str, reviewed_by_id: int, denial_reason: Optional[str] = None) -> bool:
        """Update the status of an item request"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE item_requests
            SET status = ?, reviewed_by_id = ?, reviewed_date = ?, denial_reason = ?
            WHERE id = ?
        """, (status, reviewed_by_id, now, denial_reason, request_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def get_request_by_id(self, request_id: int) -> Optional[Dict]:
        """Get a specific request by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ir.*,
                u1.full_name as requester_name,
                u2.full_name as reviewed_by_name
            FROM item_requests ir
            LEFT JOIN users u1 ON ir.requester_id = u1.id
            LEFT JOIN users u2 ON ir.reviewed_by_id = u2.id
            WHERE ir.id = ?
        """, (request_id,))

        row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    # MARK: - Category Management

    def create_category(self, name: str, created_by_id: int) -> int:
        """Create a new category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO categories (name, created_by_id, created_date)
            VALUES (?, ?, ?)
        """, (name, created_by_id, now))

        category_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return category_id

    def get_all_categories(self) -> List[Dict]:
        """Get all categories"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.id, c.name, c.created_date, u.full_name as created_by
            FROM categories c
            LEFT JOIN users u ON c.created_by_id = u.id
            ORDER BY c.name ASC
        """)

        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return categories

    def get_category(self, category_id: int) -> Optional[Dict]:
        """Get a specific category by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.id, c.name, c.created_date, u.full_name as created_by
            FROM categories c
            LEFT JOIN users u ON c.created_by_id = u.id
            WHERE c.id = ?
        """, (category_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def update_category(self, category_id: int, name: str) -> bool:
        """Update a category name"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE categories
            SET name = ?
            WHERE id = ?
        """, (name, category_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def delete_category(self, category_id: int) -> bool:
        """Delete a category"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    # MARK: - Location Management

    def create_location(self, name: str, created_by_id: int) -> int:
        """Create a new location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO locations (name, created_by_id, created_date)
            VALUES (?, ?, ?)
        """, (name, created_by_id, now))

        location_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return location_id

    def get_all_locations(self) -> List[Dict]:
        """Get all locations"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT l.id, l.name, l.created_date, u.full_name as created_by
            FROM locations l
            LEFT JOIN users u ON l.created_by_id = u.id
            ORDER BY l.name ASC
        """)

        locations = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return locations

    def get_location(self, location_id: int) -> Optional[Dict]:
        """Get a specific location by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT l.id, l.name, l.created_date, u.full_name as created_by
            FROM locations l
            LEFT JOIN users u ON l.created_by_id = u.id
            WHERE l.id = ?
        """, (location_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def update_location(self, location_id: int, name: str) -> bool:
        """Update a location name"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE locations
            SET name = ?
            WHERE id = ?
        """, (name, location_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def delete_location(self, location_id: int) -> bool:
        """Delete a location"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM locations WHERE id = ?", (location_id,))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success
