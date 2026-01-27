"""
Models Package - StringMaster Guitar Shop
OOP-based guitar models organized by type
"""

from models.electric import ElectricGuitar
from models.acoustic import AcousticGuitar
from models.bass import BassGuitar
from models.classical import ClassicalGuitar

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== ENUMS ====================

class GuitarType(str, Enum):
    """Enumeration for guitar types"""
    ELECTRIC = "electric"
    ACOUSTIC = "acoustic"
    BASS = "bass"
    CLASSICAL = "classical"


class UserRole(str, Enum):
    """User roles for authorization"""
    CUSTOMER = "customer"
    ADMIN = "admin"


class OrderStatus(str, Enum):
    """Order status tracking"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ==================== PYDANTIC MODELS (API Schemas) ====================

class GuitarCreate(BaseModel):
    """Schema for creating a new guitar via API"""
    name: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=50)
    guitar_type: GuitarType
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    description: str = Field(default="")
    image_url: str = Field(default="")


class GuitarUpdate(BaseModel):
    """Schema for updating a guitar"""
    name: Optional[str] = None
    brand: Optional[str] = None
    guitar_type: Optional[GuitarType] = None
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None


class GuitarResponse(BaseModel):
    """Schema for guitar API response"""
    id: int
    name: str
    brand: str
    guitar_type: GuitarType
    price: float
    stock: int
    description: str
    image_url: str
    available: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user API response"""
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class CartItemCreate(BaseModel):
    """Schema for adding item to cart"""
    guitar_id: int
    quantity: int = Field(default=1, ge=1)


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    items: List[CartItemCreate]


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CategoryCreate(BaseModel):
    """Schema for creating a category"""
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="")


class CategoryResponse(BaseModel):
    """Schema for category API response"""
    id: int
    name: str
    description: str


# ==================== DATACLASSES (Internal Models) ====================

@dataclass
class Guitar:
    """Base Guitar product model with OOP principles"""
    name: str
    brand: str
    guitar_type: GuitarType
    price: float
    stock: int
    description: str = ""
    image_url: str = ""
    id: Optional[int] = None
    category_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_available(self) -> bool:
        """Check if guitar is in stock"""
        return self.stock > 0
    
    def apply_discount(self, percentage: float) -> float:
        """Calculate discounted price"""
        if not 0 <= percentage <= 100:
            raise ValueError("Discount must be between 0 and 100")
        return self.price * (1 - percentage / 100)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "guitar_type": self.guitar_type.value,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "image_url": self.image_url,
            "category_id": self.category_id,
            "available": self.is_available(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class User:
    """User model with authentication data"""
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.CUSTOMER
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role == UserRole.ADMIN
    
    def to_dict(self) -> dict:
        """Safe dictionary representation (no password)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Category:
    """Category model for guitar types"""
    name: str
    description: str = ""
    id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }


@dataclass
class CartItem:
    """Shopping cart item"""
    guitar: Guitar
    quantity: int
    
    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this item"""
        return self.guitar.price * self.quantity


@dataclass
class Order:
    """Order model"""
    id: int
    user_id: int
    items: List[CartItem]
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total(self) -> float:
        """Calculate order total"""
        return sum(item.subtotal for item in self.items)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "items": [
                {
                    "guitar_id": item.guitar.id,
                    "guitar_name": item.guitar.name,
                    "quantity": item.quantity,
                    "subtotal": item.subtotal
                } for item in self.items
            ],
            "total": self.total,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ShoppingCart:
    """Shopping cart with data structure manipulation"""
    
    def __init__(self, user_id: int):
        """Initialize cart for a user"""
        self.user_id = user_id
        self._items: dict[int, CartItem] = {}
    
    def add_item(self, guitar: Guitar, quantity: int = 1) -> None:
        """Add guitar to cart with validation"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > guitar.stock:
            raise ValueError(f"Only {guitar.stock} items available in stock")
        
        if guitar.id in self._items:
            new_quantity = self._items[guitar.id].quantity + quantity
            if new_quantity > guitar.stock:
                raise ValueError(f"Cannot add more. Only {guitar.stock} available")
            self._items[guitar.id].quantity = new_quantity
        else:
            self._items[guitar.id] = CartItem(guitar, quantity)
    
    def remove_item(self, guitar_id: int) -> None:
        """Remove item from cart"""
        if guitar_id in self._items:
            del self._items[guitar_id]
    
    def update_quantity(self, guitar_id: int, quantity: int) -> None:
        """Update item quantity"""
        if guitar_id not in self._items:
            raise KeyError("Item not in cart")
        if quantity <= 0:
            self.remove_item(guitar_id)
        else:
            guitar = self._items[guitar_id].guitar
            if quantity > guitar.stock:
                raise ValueError(f"Only {guitar.stock} available")
            self._items[guitar_id].quantity = quantity
    
    def get_items(self) -> List[CartItem]:
        """Get all cart items as list"""
        return list(self._items.values())
    
    @property
    def total(self) -> float:
        """Calculate cart total"""
        return sum(item.subtotal for item in self._items.values())
    
    @property
    def item_count(self) -> int:
        """Total number of items in cart"""
        return sum(item.quantity for item in self._items.values())
    
    def clear(self) -> None:
        """Empty the cart"""
        self._items.clear()
    
    def is_empty(self) -> bool:
        """Check if cart is empty"""
        return len(self._items) == 0


# Export all models
__all__ = [
    # Enums
    'GuitarType', 'UserRole', 'OrderStatus',
    # Pydantic Schemas
    'GuitarCreate', 'GuitarUpdate', 'GuitarResponse',
    'UserCreate', 'UserLogin', 'UserResponse',
    'CartItemCreate', 'OrderCreate', 'TokenResponse',
    'CategoryCreate', 'CategoryResponse',
    # Dataclasses
    'Guitar', 'User', 'Category', 'CartItem', 'Order', 'ShoppingCart',
    # Guitar Type Classes
    'ElectricGuitar', 'AcousticGuitar', 'BassGuitar', 'ClassicalGuitar'
]
