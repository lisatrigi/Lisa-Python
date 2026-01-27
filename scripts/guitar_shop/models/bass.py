"""
Bass Guitar Model - StringMaster Guitar Shop
OOP-based bass guitar class with specific attributes
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BassGuitar:
    """
    Bass Guitar model with specific attributes
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
    
    # Bass guitar specific attributes
    num_strings: int = 4  # 4, 5, or 6 string
    pickup_type: str = "Passive"  # Passive, Active
    pickup_configuration: str = "PJ"  # P, J, PJ, MM, etc.
    scale_length: float = 34.0  # inches (standard is 34")
    fretted: bool = True  # True for fretted, False for fretless
    num_frets: int = 20
    body_wood: str = "Alder"
    neck_construction: str = "Bolt-on"  # Bolt-on, Set-neck, Neck-through
    
    @property
    def guitar_type(self) -> str:
        """Return guitar type"""
        return "bass"
    
    def is_available(self) -> bool:
        """Check if guitar is in stock"""
        return self.stock > 0
    
    def apply_discount(self, percentage: float) -> float:
        """Calculate discounted price with validation"""
        if not 0 <= percentage <= 100:
            raise ValueError("Discount must be between 0 and 100")
        return self.price * (1 - percentage / 100)
    
    def is_extended_range(self) -> bool:
        """Check if bass is extended range (more than 4 strings)"""
        return self.num_strings > 4
    
    def is_fretless(self) -> bool:
        """Check if bass is fretless"""
        return not self.fretted
    
    def has_active_electronics(self) -> bool:
        """Check if bass has active electronics"""
        return self.pickup_type.lower() == "active"
    
    def get_pickup_info(self) -> str:
        """Get human-readable pickup configuration"""
        pickup_map = {
            "P": "Precision Bass (Split Coil)",
            "J": "Jazz Bass (Single Coil)",
            "PJ": "Precision + Jazz combination",
            "JJ": "Dual Jazz pickups",
            "MM": "Music Man style Humbucker",
            "Soapbar": "Soapbar/EMG style pickups"
        }
        return pickup_map.get(self.pickup_configuration, self.pickup_configuration)
    
    def get_scale_description(self) -> str:
        """Get description of scale length"""
        if self.scale_length < 32:
            return "Short scale - easier playability"
        elif self.scale_length < 34:
            return "Medium scale - balanced feel"
        elif self.scale_length == 34:
            return "Standard scale - industry standard"
        else:
            return "Extra long scale - tighter low end"
    
    def get_specifications(self) -> dict:
        """Get detailed specifications"""
        return {
            "num_strings": self.num_strings,
            "pickup_type": self.pickup_type,
            "pickup_configuration": self.pickup_configuration,
            "scale_length": f"{self.scale_length} inches",
            "fretted": "Yes" if self.fretted else "Fretless",
            "num_frets": self.num_frets if self.fretted else "N/A",
            "body_wood": self.body_wood,
            "neck_construction": self.neck_construction
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
        fretless_suffix = " (Fretless)" if not self.fretted else ""
        return f"{self.brand} {self.name} ({self.num_strings}-String Bass{fretless_suffix}) - ${self.price:.2f}"
    
    def __repr__(self) -> str:
        """Developer representation"""
        return f"BassGuitar(name='{self.name}', brand='{self.brand}', num_strings={self.num_strings}, price={self.price})"
