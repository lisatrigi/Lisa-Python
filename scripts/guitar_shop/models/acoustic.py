"""
Acoustic Guitar Model - StringMaster Guitar Shop
OOP-based acoustic guitar class with specific attributes
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AcousticGuitar:
    """
    Acoustic Guitar model with specific attributes
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
    
    # Acoustic guitar specific attributes
    body_shape: str = "Dreadnought"  # e.g., "Dreadnought", "Concert", "Jumbo", "Parlor"
    top_wood: str = "Spruce"  # Solid Spruce, Cedar, etc.
    back_sides_wood: str = "Mahogany"  # Rosewood, Mahogany, etc.
    has_electronics: bool = False  # Acoustic-electric
    preamp_model: Optional[str] = None  # e.g., "Fishman", "Taylor ES2"
    bracing_pattern: str = "X-bracing"
    nut_width: float = 1.69  # inches
    
    @property
    def guitar_type(self) -> str:
        """Return guitar type"""
        return "acoustic"
    
    def is_available(self) -> bool:
        """Check if guitar is in stock"""
        return self.stock > 0
    
    def apply_discount(self, percentage: float) -> float:
        """Calculate discounted price with validation"""
        if not 0 <= percentage <= 100:
            raise ValueError("Discount must be between 0 and 100")
        return self.price * (1 - percentage / 100)
    
    def is_acoustic_electric(self) -> bool:
        """Check if guitar has built-in electronics"""
        return self.has_electronics
    
    def get_body_description(self) -> str:
        """Get description of body shape and its characteristics"""
        body_descriptions = {
            "Dreadnought": "Full, powerful sound with strong bass response",
            "Concert": "Balanced tone, comfortable for fingerpicking",
            "Jumbo": "Maximum volume and bass, ideal for strumming",
            "Parlor": "Vintage-style, intimate sound, easy to hold",
            "Grand Auditorium": "Versatile, balanced across all frequencies",
            "Orchestra": "Focused midrange, great for recording"
        }
        return body_descriptions.get(self.body_shape, self.body_shape)
    
    def get_tonewoods(self) -> dict:
        """Get tonewood information"""
        return {
            "top": self.top_wood,
            "back_and_sides": self.back_sides_wood,
            "bracing": self.bracing_pattern
        }
    
    def get_specifications(self) -> dict:
        """Get detailed specifications"""
        specs = {
            "body_shape": self.body_shape,
            "top_wood": self.top_wood,
            "back_sides_wood": self.back_sides_wood,
            "bracing_pattern": self.bracing_pattern,
            "nut_width": f"{self.nut_width} inches",
            "electronics": "Yes" if self.has_electronics else "No"
        }
        if self.preamp_model:
            specs["preamp"] = self.preamp_model
        return specs
    
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
        electric_suffix = " (Acoustic-Electric)" if self.has_electronics else ""
        return f"{self.brand} {self.name} (Acoustic{electric_suffix}) - ${self.price:.2f}"
    
    def __repr__(self) -> str:
        """Developer representation"""
        return f"AcousticGuitar(name='{self.name}', brand='{self.brand}', price={self.price})"
