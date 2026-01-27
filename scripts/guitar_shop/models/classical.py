"""
Classical Guitar Model - StringMaster Guitar Shop
OOP-based classical guitar class with specific attributes
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ClassicalGuitar:
    """
    Classical Guitar model with specific attributes
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
    
    # Classical guitar specific attributes
    top_wood: str = "Cedar"  # Cedar, Spruce
    back_sides_wood: str = "Rosewood"  # Rosewood, Mahogany, etc.
    string_type: str = "Nylon"  # Always nylon for classical
    scale_length: float = 25.6  # inches (650mm standard)
    nut_width: float = 2.0  # inches (wider than steel string)
    body_size: str = "Full Size"  # Full Size, 3/4, 1/2, 1/4
    finish_type: str = "Gloss"  # Gloss, Matte, French Polish
    has_cutaway: bool = False
    
    @property
    def guitar_type(self) -> str:
        """Return guitar type"""
        return "classical"
    
    def is_available(self) -> bool:
        """Check if guitar is in stock"""
        return self.stock > 0
    
    def apply_discount(self, percentage: float) -> float:
        """Calculate discounted price with validation"""
        if not 0 <= percentage <= 100:
            raise ValueError("Discount must be between 0 and 100")
        return self.price * (1 - percentage / 100)
    
    def is_full_size(self) -> bool:
        """Check if guitar is full size"""
        return self.body_size == "Full Size"
    
    def is_student_size(self) -> bool:
        """Check if guitar is a smaller student size"""
        return self.body_size in ["3/4", "1/2", "1/4"]
    
    def get_top_wood_characteristics(self) -> str:
        """Get description of top wood sound characteristics"""
        wood_descriptions = {
            "Cedar": "Warm, rich tone with quick response - ideal for fingerpicking",
            "Spruce": "Bright, articulate tone with more projection - versatile",
            "Redwood": "Similar to cedar but with more complexity",
            "Engelmann Spruce": "Lighter than Sitka, very responsive"
        }
        return wood_descriptions.get(self.top_wood, self.top_wood)
    
    def get_recommended_skill_level(self) -> str:
        """Get recommended skill level based on guitar features"""
        if self.price < 300:
            return "Beginner"
        elif self.price < 800:
            return "Intermediate"
        elif self.price < 2000:
            return "Advanced"
        else:
            return "Professional/Concert"
    
    def get_tonewoods(self) -> dict:
        """Get tonewood information"""
        return {
            "top": self.top_wood,
            "back_and_sides": self.back_sides_wood,
            "strings": self.string_type
        }
    
    def get_specifications(self) -> dict:
        """Get detailed specifications"""
        return {
            "top_wood": self.top_wood,
            "back_sides_wood": self.back_sides_wood,
            "string_type": self.string_type,
            "scale_length": f"{self.scale_length} inches",
            "nut_width": f"{self.nut_width} inches",
            "body_size": self.body_size,
            "finish": self.finish_type,
            "cutaway": "Yes" if self.has_cutaway else "No",
            "recommended_level": self.get_recommended_skill_level()
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
        size_suffix = f" ({self.body_size})" if self.body_size != "Full Size" else ""
        return f"{self.brand} {self.name} (Classical{size_suffix}) - ${self.price:.2f}"
    
    def __repr__(self) -> str:
        """Developer representation"""
        return f"ClassicalGuitar(name='{self.name}', brand='{self.brand}', price={self.price})"
