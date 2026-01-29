from models.electric import ElectricGuitar
from models.acoustic import AcousticGuitar
from models.bass import BassGuitar
from models.classical import ClassicalGuitar

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class GuitarType(str, Enum):
    ELECTRIC = "electric"
    ACOUSTIC = "acoustic"
    BASS = "bass"
    CLASSICAL = "classical"


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class GuitarCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=50)
    guitar_type: GuitarType
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    description: str = Field(default="")
    image_url: str = Field(default="")


class GuitarUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    guitar_type: Optional[GuitarType] = None
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None


class GuitarResponse(BaseModel):
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
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class CartItemCreate(BaseModel):
    guitar_id: int
    quantity: int = Field(default=1, ge=1)


class OrderCreate(BaseModel):
    items: List[CartItemCreate]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="")


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str


@dataclass
class Guitar:
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
        return self.stock > 0
    
    def apply_discount(self, percentage: float) -> float:
        if not 0 <= percentage <= 100:
            raise ValueError("Discount must be between 0 and 100")
        return self.price * (1 - percentage / 100)
    
    def to_dict(self) -> dict:
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
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.CUSTOMER
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Category:
    name: str
    description: str = ""
    id: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }


@dataclass
class CartItem:
    guitar: Guitar
    quantity: int
    
    @property
    def subtotal(self) -> float:
        return self.guitar.price * self.quantity


@dataclass
class Order:
    id: int
    user_id: int
    items: List[CartItem]
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)
    
    def to_dict(self) -> dict:
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
    def __init__(self, user_id: int):
        self.user_id = user_id
        self._items: dict[int, CartItem] = {}
    
    def add_item(self, guitar: Guitar, quantity: int = 1) -> None:
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
        if guitar_id in self._items:
            del self._items[guitar_id]
    
    def update_quantity(self, guitar_id: int, quantity: int) -> None:
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
        return list(self._items.values())
    
    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self._items.values())
    
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self._items.values())
    
    def clear(self) -> None:
        self._items.clear()
    
    def is_empty(self) -> bool:
        return len(self._items) == 0


__all__ = [
    'GuitarType', 'UserRole', 'OrderStatus',
    'GuitarCreate', 'GuitarUpdate', 'GuitarResponse',
    'UserCreate', 'UserLogin', 'UserResponse',
    'CartItemCreate', 'OrderCreate', 'TokenResponse',
    'CategoryCreate', 'CategoryResponse',
    'Guitar', 'User', 'Category', 'CartItem', 'Order', 'ShoppingCart',
    'ElectricGuitar', 'AcousticGuitar', 'BassGuitar', 'ClassicalGuitar'
]
