"""
Database Management Module - StringMaster Guitar Shop
SQLite database with CRUD operations using SQLAlchemy patterns
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Tuple
from datetime import datetime

from models import Guitar, GuitarType, User, UserRole, OrderStatus, Category


class DatabaseManager:
    """Database manager with connection pooling and CRUD operations"""
    
    def __init__(self, db_path: str = "guitar_shop.db"):
        """Initialize database with path"""
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with error handling"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self) -> None:
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT ''
                )
            """)
            
            # Guitars table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guitars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    guitar_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    description TEXT,
                    image_url TEXT,
                    category_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            """)
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'customer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Order items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    guitar_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price_at_purchase REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (guitar_id) REFERENCES guitars (id)
                )
            """)
            
            # Initialize default categories
            default_categories = [
                ("Electric", "Electric guitars with pickups and amplification"),
                ("Acoustic", "Steel-string acoustic guitars"),
                ("Bass", "Bass guitars for low-end frequencies"),
                ("Classical", "Nylon-string classical and flamenco guitars")
            ]
            
            for name, desc in default_categories:
                cursor.execute("""
                    INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)
                """, (name, desc))
    
    # ==================== CATEGORY CRUD ====================
    
    def create_category(self, category: Category) -> int:
        """Create a new category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categories (name, description) VALUES (?, ?)
            """, (category.name, category.description))
            return cursor.lastrowid
    
    def get_category(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cursor.fetchone()
            if row:
                return Category(id=row['id'], name=row['name'], description=row['description'])
            return None
    
    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(?)", (name,))
            row = cursor.fetchone()
            if row:
                return Category(id=row['id'], name=row['name'], description=row['description'])
            return None
    
    def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name")
            return [Category(id=row['id'], name=row['name'], description=row['description']) 
                    for row in cursor.fetchall()]
    
    def update_category(self, category_id: int, **kwargs) -> bool:
        """Update category fields"""
        if not kwargs:
            return False
        
        valid_fields = {'name', 'description'}
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [category_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE categories SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            return cursor.rowcount > 0
    
    def get_guitars_by_category(self, category_id: int) -> List[Guitar]:
        """Get all guitars in a category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guitars WHERE category_id = ?", (category_id,))
            return [self._row_to_guitar(row) for row in cursor.fetchall()]
    
    # ==================== GUITAR CRUD ====================
    
    def create_guitar(self, guitar: Guitar) -> int:
        """Insert a new guitar into database"""
        # Auto-assign category based on guitar type
        category_id = guitar.category_id
        if not category_id:
            category = self.get_category_by_name(guitar.guitar_type.value.capitalize())
            category_id = category.id if category else None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO guitars (name, brand, guitar_type, price, stock, description, image_url, category_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guitar.name, 
                guitar.brand, 
                guitar.guitar_type.value, 
                guitar.price, 
                guitar.stock, 
                guitar.description, 
                guitar.image_url,
                category_id
            ))
            return cursor.lastrowid
    
    def get_guitar(self, guitar_id: int) -> Optional[Guitar]:
        """Get guitar by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guitars WHERE id = ?", (guitar_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_guitar(row)
            return None
    
    def get_all_guitars(
        self, 
        guitar_type: Optional[GuitarType] = None, 
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        category_id: Optional[int] = None
    ) -> List[Guitar]:
        """Get all guitars with optional filters"""
        query = "SELECT * FROM guitars WHERE 1=1"
        params = []
        
        # Apply filters using conditional statements
        if guitar_type:
            query += " AND guitar_type = ?"
            params.append(guitar_type.value)
        
        if brand:
            query += " AND brand LIKE ?"
            params.append(f"%{brand}%")
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        
        if in_stock_only:
            query += " AND stock > 0"
        
        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)
        
        query += " ORDER BY created_at DESC"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [self._row_to_guitar(row) for row in cursor.fetchall()]
    
    def update_guitar(self, guitar_id: int, **kwargs) -> bool:
        """Update guitar fields dynamically"""
        if not kwargs:
            return False
        
        valid_fields = {'name', 'brand', 'guitar_type', 'price', 'stock', 'description', 'image_url', 'category_id'}
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return False
        
        # Handle guitar_type enum
        if 'guitar_type' in updates and isinstance(updates['guitar_type'], GuitarType):
            updates['guitar_type'] = updates['guitar_type'].value
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [guitar_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE guitars SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def delete_guitar(self, guitar_id: int) -> bool:
        """Delete a guitar from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM guitars WHERE id = ?", (guitar_id,))
            return cursor.rowcount > 0
    
    def update_stock(self, guitar_id: int, quantity_change: int) -> bool:
        """Update guitar stock (positive = add, negative = subtract)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE guitars SET stock = stock + ? 
                WHERE id = ? AND stock + ? >= 0
            """, (quantity_change, guitar_id, quantity_change))
            return cursor.rowcount > 0
    
    def guitar_exists(self, name: str, brand: str) -> bool:
        """Check if guitar already exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM guitars WHERE LOWER(name) = LOWER(?) AND LOWER(brand) = LOWER(?)",
                (name, brand)
            )
            return cursor.fetchone() is not None
    
    def get_guitar_count(self) -> int:
        """Get total number of guitars"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM guitars")
            return cursor.fetchone()[0]
    
    # ==================== USER CRUD ====================
    
    def create_user(self, user: User) -> int:
        """Create a new user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                """, (user.username, user.email, user.password_hash, user.role.value))
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                if "username" in str(e):
                    raise ValueError("Username already exists")
                elif "email" in str(e):
                    raise ValueError("Email already exists")
                raise
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [self._row_to_user(row) for row in cursor.fetchall()]
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user fields"""
        if not kwargs:
            return False
        
        valid_fields = {'email', 'password_hash', 'role'}
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0
    
    # ==================== ORDER OPERATIONS ====================
    
    def create_order(
        self, 
        user_id: int, 
        items: List[Tuple[int, int, float]], 
        total: float
    ) -> int:
        """Create order with items: [(guitar_id, quantity, price_at_purchase), ...]"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)
            """, (user_id, total, OrderStatus.PENDING.value))
            order_id = cursor.lastrowid
            
            for guitar_id, quantity, price in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, guitar_id, quantity, price_at_purchase)
                    VALUES (?, ?, ?, ?)
                """, (order_id, guitar_id, quantity, price))
            
            return order_id
    
    def get_user_orders(self, user_id: int) -> List[dict]:
        """Get all orders for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, oi.guitar_id, oi.quantity, oi.price_at_purchase, g.name as guitar_name, g.brand
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN guitars g ON oi.guitar_id = g.id
                WHERE o.user_id = ?
                ORDER BY o.created_at DESC
            """, (user_id,))
            
            orders = {}
            for row in cursor.fetchall():
                order_id = row['id']
                if order_id not in orders:
                    orders[order_id] = {
                        'id': order_id,
                        'total': row['total'],
                        'status': row['status'],
                        'created_at': row['created_at'],
                        'items': []
                    }
                orders[order_id]['items'].append({
                    'guitar_id': row['guitar_id'],
                    'guitar_name': f"{row['brand']} {row['guitar_name']}",
                    'quantity': row['quantity'],
                    'price': row['price_at_purchase']
                })
            
            return list(orders.values())
    
    def update_order_status(self, order_id: int, status: OrderStatus) -> bool:
        """Update order status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status.value, order_id)
            )
            return cursor.rowcount > 0
    
    # ==================== ANALYTICS ====================
    
    def get_sales_data(self) -> List[dict]:
        """Get sales data for analytics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.brand, g.guitar_type, 
                       SUM(oi.quantity) as units_sold,
                       SUM(oi.quantity * oi.price_at_purchase) as revenue
                FROM order_items oi
                JOIN guitars g ON oi.guitar_id = g.id
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status != 'cancelled'
                GROUP BY g.brand, g.guitar_type
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_inventory_stats(self) -> dict:
        """Get inventory statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_products,
                    SUM(stock) as total_units,
                    SUM(price * stock) as total_value,
                    AVG(price) as avg_price
                FROM guitars
            """)
            stats = dict(cursor.fetchone())
            
            cursor.execute("""
                SELECT guitar_type, SUM(stock) as count
                FROM guitars GROUP BY guitar_type
            """)
            stats['by_type'] = {row['guitar_type']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute("""
                SELECT brand, SUM(stock) as count
                FROM guitars GROUP BY brand
            """)
            stats['by_brand'] = {row['brand']: row['count'] for row in cursor.fetchall()}
            
            return stats
    
    # ==================== HELPER METHODS ====================
    
    def _row_to_guitar(self, row) -> Guitar:
        """Convert database row to Guitar object"""
        created_at = row['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = datetime.now()
        
        return Guitar(
            id=row['id'],
            name=row['name'],
            brand=row['brand'],
            guitar_type=GuitarType(row['guitar_type']),
            price=row['price'],
            stock=row['stock'],
            description=row['description'] or "",
            image_url=row['image_url'] or "",
            category_id=row['category_id'] if 'category_id' in row.keys() else None,
            created_at=created_at
        )
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        created_at = row['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = datetime.now()
        
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=UserRole(row['role']),
            created_at=created_at
        )
