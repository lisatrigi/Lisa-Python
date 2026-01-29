import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Tuple
from datetime import datetime

from models import Guitar, GuitarType, User, UserRole, OrderStatus, Category


class DatabaseManager:
    def __init__(self, db_path: str = "guitar_shop.db"):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT ''
                )
            """)
            
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
                    discount_percent REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'customer',
                    is_online INTEGER DEFAULT 0,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    total REAL NOT NULL,
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
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
    
    def create_category(self, category: Category) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categories (name, description) VALUES (?, ?)
            """, (category.name, category.description))
            return cursor.lastrowid
    
    def get_category(self, category_id: int) -> Optional[Category]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cursor.fetchone()
            if row:
                return Category(id=row['id'], name=row['name'], description=row['description'])
            return None
    
    def get_category_by_name(self, name: str) -> Optional[Category]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(?)", (name,))
            row = cursor.fetchone()
            if row:
                return Category(id=row['id'], name=row['name'], description=row['description'])
            return None
    
    def get_all_categories(self) -> List[Category]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name")
            return [Category(id=row['id'], name=row['name'], description=row['description']) 
                    for row in cursor.fetchall()]
    
    def update_category(self, category_id: int, **kwargs) -> bool:
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            return cursor.rowcount > 0
    
    def get_guitars_by_category(self, category_id: int) -> List[Guitar]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guitars WHERE category_id = ?", (category_id,))
            return [self._row_to_guitar(row) for row in cursor.fetchall()]
    
    def create_guitar(self, guitar: Guitar) -> int:
        category_id = guitar.category_id
        if not category_id:
            category = self.get_category_by_name(guitar.guitar_type.value.capitalize())
            category_id = category.id if category else None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO guitars (name, brand, guitar_type, price, stock, description, image_url, category_id, discount_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guitar.name, 
                guitar.brand, 
                guitar.guitar_type.value, 
                guitar.price, 
                guitar.stock, 
                guitar.description, 
                guitar.image_url,
                category_id,
                getattr(guitar, 'discount_percent', 0)
            ))
            return cursor.lastrowid
    
    def get_guitar(self, guitar_id: int) -> Optional[Guitar]:
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
        query = "SELECT * FROM guitars WHERE 1=1"
        params = []
        
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
        if not kwargs:
            return False
        
        valid_fields = {'name', 'brand', 'guitar_type', 'price', 'stock', 'description', 'image_url', 'category_id', 'discount_percent'}
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return False
        
        if 'guitar_type' in updates and isinstance(updates['guitar_type'], GuitarType):
            updates['guitar_type'] = updates['guitar_type'].value
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [guitar_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE guitars SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def delete_guitar(self, guitar_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM guitars WHERE id = ?", (guitar_id,))
            return cursor.rowcount > 0
    
    def update_stock(self, guitar_id: int, quantity_change: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE guitars SET stock = stock + ? 
                WHERE id = ? AND stock + ? >= 0
            """, (quantity_change, guitar_id, quantity_change))
            return cursor.rowcount > 0
    
    def guitar_exists(self, name: str, brand: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM guitars WHERE LOWER(name) = LOWER(?) AND LOWER(brand) = LOWER(?)",
                (name, brand)
            )
            return cursor.fetchone() is not None
    
    def get_guitar_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM guitars")
            return cursor.fetchone()[0]
    
    def apply_discount_to_guitar(self, guitar_id: int, discount_percent: float) -> bool:
        if not 0 <= discount_percent <= 100:
            raise ValueError("Discount must be between 0 and 100")
        return self.update_guitar(guitar_id, discount_percent=discount_percent)
    
    def apply_discount_to_brand(self, brand: str, discount_percent: float) -> int:
        if not 0 <= discount_percent <= 100:
            raise ValueError("Discount must be between 0 and 100")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE guitars SET discount_percent = ? WHERE LOWER(brand) = LOWER(?)
            """, (discount_percent, brand))
            return cursor.rowcount
    
    def apply_discount_to_type(self, guitar_type: str, discount_percent: float) -> int:
        if not 0 <= discount_percent <= 100:
            raise ValueError("Discount must be between 0 and 100")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE guitars SET discount_percent = ? WHERE LOWER(guitar_type) = LOWER(?)
            """, (discount_percent, guitar_type))
            return cursor.rowcount
    
    def clear_all_discounts(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE guitars SET discount_percent = 0 WHERE discount_percent > 0")
            return cursor.rowcount
    
    def get_discounted_guitars(self) -> List[Guitar]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guitars WHERE discount_percent > 0 ORDER BY discount_percent DESC")
            return [self._row_to_guitar(row) for row in cursor.fetchall()]
    
    def create_user(self, user: User) -> int:
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
    
    def get_all_users(self) -> List[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return [self._row_to_user(row) for row in cursor.fetchall()]
    
    def get_online_users(self) -> List[User]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE is_online = 1 AND role != 'admin' ORDER BY last_login DESC")
            return [self._row_to_user(row) for row in cursor.fetchall()]
    
    def set_user_online(self, user_id: int, is_online: bool) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if is_online:
                cursor.execute("""
                    UPDATE users SET is_online = 1, last_login = CURRENT_TIMESTAMP WHERE id = ?
                """, (user_id,))
            else:
                cursor.execute("""
                    UPDATE users SET is_online = 0 WHERE id = ?
                """, (user_id,))
            return cursor.rowcount > 0
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        
        valid_fields = {'email', 'password_hash', 'role', 'is_online', 'last_login'}
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0
    
    def create_purchase_notification(self, order_id: int, user_id: int, username: str, total: float) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchase_notifications (order_id, user_id, username, total)
                VALUES (?, ?, ?, ?)
            """, (order_id, user_id, username, total))
            return cursor.lastrowid
    
    def get_unread_notifications(self) -> List[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pn.*, o.status as order_status
                FROM purchase_notifications pn
                JOIN orders o ON pn.order_id = o.id
                WHERE pn.is_read = 0
                ORDER BY pn.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_notifications(self, limit: int = 50) -> List[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pn.*, o.status as order_status
                FROM purchase_notifications pn
                JOIN orders o ON pn.order_id = o.id
                ORDER BY pn.created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_notification_read(self, notification_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE purchase_notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            return cursor.rowcount > 0
    
    def mark_all_notifications_read(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE purchase_notifications SET is_read = 1 WHERE is_read = 0")
            return cursor.rowcount
    
    def create_order(
        self, 
        user_id: int, 
        items: List[Tuple[int, int, float]], 
        total: float
    ) -> int:
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
    
    def get_all_orders(self, limit: int = 100) -> List[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, u.username, oi.guitar_id, oi.quantity, oi.price_at_purchase, g.name as guitar_name, g.brand
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN order_items oi ON o.id = oi.order_id
                JOIN guitars g ON oi.guitar_id = g.id
                ORDER BY o.created_at DESC
                LIMIT ?
            """, (limit,))
            
            orders = {}
            for row in cursor.fetchall():
                order_id = row['id']
                if order_id not in orders:
                    orders[order_id] = {
                        'id': order_id,
                        'user_id': row['user_id'],
                        'username': row['username'],
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status.value, order_id)
            )
            return cursor.rowcount > 0
    
    def get_sales_data(self) -> List[dict]:
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
                FROM guitars GROUP BY brand ORDER BY count DESC
            """)
            stats['by_brand'] = {row['brand']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute("""
                SELECT brand, COUNT(*) as model_count
                FROM guitars GROUP BY brand ORDER BY model_count DESC
            """)
            stats['models_by_brand'] = {row['brand']: row['model_count'] for row in cursor.fetchall()}
            
            cursor.execute("""
                SELECT COUNT(*) as total_orders, 
                       COALESCE(SUM(total), 0) as total_revenue
                FROM orders WHERE status != 'cancelled'
            """)
            sales_stats = dict(cursor.fetchone())
            stats['total_orders'] = sales_stats['total_orders']
            stats['total_revenue'] = sales_stats['total_revenue']
            
            cursor.execute("SELECT COUNT(*) as discounted FROM guitars WHERE discount_percent > 0")
            stats['discounted_count'] = cursor.fetchone()['discounted']
            
            return stats
    
    def get_brand_statistics(self) -> List[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    brand,
                    COUNT(*) as model_count,
                    SUM(stock) as total_stock,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    SUM(price * stock) as inventory_value
                FROM guitars
                GROUP BY brand
                ORDER BY model_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_type_statistics(self) -> List[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    guitar_type,
                    COUNT(*) as model_count,
                    SUM(stock) as total_stock,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    SUM(price * stock) as inventory_value
                FROM guitars
                GROUP BY guitar_type
                ORDER BY model_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def _row_to_guitar(self, row) -> Guitar:
        created_at = row['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = datetime.now()
        
        guitar = Guitar(
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
        if 'discount_percent' in row.keys():
            guitar.discount_percent = row['discount_percent'] or 0
        else:
            guitar.discount_percent = 0
        return guitar
    
    def _row_to_user(self, row) -> User:
        created_at = row['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = datetime.now()
        
        user = User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=UserRole(row['role']),
            created_at=created_at
        )
        if 'is_online' in row.keys():
            user.is_online = bool(row['is_online'])
        else:
            user.is_online = False
        if 'last_login' in row.keys():
            user.last_login = row['last_login']
        else:
            user.last_login = None
        return user
