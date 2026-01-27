"""
Electric Guitar Model - StringMaster Guitar Shop
OOP-based electric guitar class with specific attributes
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class ElectricGuitar:
    """
    Electric Guitar model with specific attributes
    Demonstrates OOP principles with inheritance-ready design
    """
    name: str
    brand: str
    price: float
    stock: int
    description: str = ""
    image_url: str = ""
    id: Optional[int] = None
    category_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Electric guitar specific attributes
    pickup_configuration: str = "HSS"  # e.g., "SSS", "HSS", "HH"
    num_frets: int = 22
    tremolo_type: Optional[str] = None  # e.g., "Floyd Rose", "Vintage"
    body_wood: str = "Alder"
    neck_wood: str = "Maple"
    fingerboard_wood: str = "Rosewood"
    scale_length: float = 25.5  # inches
    
    @property
    def guitar_type(self) -> str:
        """Return guitar type"""
        return "electric"
    
    def is_available(self) -> bool:
        """Check if guitar is in stock"""
        return self.stock > 0
    
    def apply_discount(self, percentage: float) -> float:
        """Calculate discounted price with validation"""
        if not 0 <= percentage <= 100:
            raise ValueError("Discount must be between 0 and 100")
        return self.price * (1 - percentage / 100)
    
    def get_pickup_info(self) -> str:
        """Get human-readable pickup configuration"""
        pickup_map = {
            "SSS": "3 Single Coil pickups",
            "HSS": "Humbucker + 2 Single Coils",
            "HSH": "Humbucker + Single Coil + Humbucker",
            "HH": "2 Humbucker pickups",
            "SS": "2 Single Coil pickups",
            "P90": "P90 pickups"
        }
        return pickup_map.get(self.pickup_configuration, self.pickup_configuration)
    
    def has_tremolo(self) -> bool:
        """Check if guitar has tremolo system"""
        return self.tremolo_type is not None
    
    def get_specifications(self) -> dict:
        """Get detailed specifications"""
        return {
            "pickup_configuration": self.pickup_configuration,
            "num_frets": self.num_frets,
            "tremolo": self.tremolo_type or "None",
            "body_wood": self.body_wood,
            "neck_wood": self.neck_wood,
            "fingerboard": self.fingerboard_wood,
            "scale_length": f"{self.scale_length} inches"
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "guitar_type": self.guitar_type,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "image_url": self.image_url,
            "category_id": self.category_id,
            "available": self.is_available(),
            "specifications": self.get_specifications(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.brand} {self.name} (Electric) - ${self.price:.2f}"
    
    def __repr__(self) -> str:
        """Developer representation"""
        return f"ElectricGuitar(name='{self.name}', brand='{self.brand}', price={self.price})"
