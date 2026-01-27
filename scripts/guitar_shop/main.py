"""
StringMaster Guitar Shop - Main FastAPI Application
Entry point for the FastAPI backend server
Handles all routing, business logic, and database communication
"""

import sys
import os
import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from models import User, UserRole, GuitarType, Guitar
from routers import auth_router, user_router, guitar_router, category_router
from routers.auth import AuthManager


# ==================== WEB SCRAPER ====================

class GuitarScraper:
    """
    Guitar data scraper for populating the database
    Uses web scraping techniques with requests and BeautifulSoup
    """
    
    GUITAR_CATALOG = [
        # Electric Guitars
        {"name": "Player Stratocaster", "brand": "Fender", "price": 849.99, "type": "electric",
         "description": "Classic Fender tone with modern playability. Alder body, maple neck, 3 single-coil pickups.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+Stratocaster+electric+guitar"},
        {"name": "Player Telecaster", "brand": "Fender", "price": 849.99, "type": "electric",
         "description": "Timeless Telecaster design. Alder body, maple neck, 2 single-coil pickups.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+Telecaster+electric+guitar"},
        {"name": "American Professional II Stratocaster", "brand": "Fender", "price": 1799.99, "type": "electric",
         "description": "Professional-grade Strat with V-Mod II pickups and Deep C neck profile.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+American+Professional+Stratocaster"},
        {"name": "Les Paul Standard 50s", "brand": "Gibson", "price": 2499.99, "type": "electric",
         "description": "Iconic Les Paul with Burstbucker pickups and vintage 50s neck profile.",
         "image": "https://placeholder.svg?height=300&width=300&query=Gibson+Les+Paul+Standard+electric+guitar"},
        {"name": "SG Standard", "brand": "Gibson", "price": 1799.99, "type": "electric",
         "description": "Lightweight rock machine with 490R and 490T humbuckers.",
         "image": "https://placeholder.svg?height=300&width=300&query=Gibson+SG+Standard+electric+guitar"},
        {"name": "Les Paul Studio", "brand": "Gibson", "price": 1499.99, "type": "electric",
         "description": "Studio workhorse with no-nonsense features and powerful tone.",
         "image": "https://placeholder.svg?height=300&width=300&query=Gibson+Les+Paul+Studio"},
        {"name": "Custom 24", "brand": "PRS", "price": 3999.99, "type": "electric",
         "description": "Versatile flagship model with 85/15 pickups and Pattern Regular neck.",
         "image": "https://placeholder.svg?height=300&width=300&query=PRS+Custom+24+electric+guitar"},
        {"name": "SE Custom 24", "brand": "PRS", "price": 599.99, "type": "electric",
         "description": "Affordable version of the iconic Custom 24 with SE 85/15 pickups.",
         "image": "https://placeholder.svg?height=300&width=300&query=PRS+SE+Custom+24"},
        {"name": "RG550 Genesis", "brand": "Ibanez", "price": 1099.99, "type": "electric",
         "description": "Shred-ready superstrat with Edge tremolo and Quantum pickups.",
         "image": "https://placeholder.svg?height=300&width=300&query=Ibanez+RG550+electric+guitar"},
        {"name": "Pacifica 612VIIFM", "brand": "Yamaha", "price": 549.99, "type": "electric",
         "description": "Versatile guitar with Seymour Duncan pickups and flamed maple top.",
         "image": "https://placeholder.svg?height=300&width=300&query=Yamaha+Pacifica+612"},
        
        # Bass Guitars
        {"name": "Player Precision Bass", "brand": "Fender", "price": 849.99, "type": "bass",
         "description": "Industry standard bass with split single-coil pickup and modern C neck.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+Precision+Bass"},
        {"name": "Player Jazz Bass", "brand": "Fender", "price": 899.99, "type": "bass",
         "description": "Versatile jazz bass with two single-coil pickups and slim neck profile.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+Jazz+Bass"},
        {"name": "American Ultra Jazz Bass", "brand": "Fender", "price": 2149.99, "type": "bass",
         "description": "Premium jazz bass with Ultra Noiseless pickups and compound radius fingerboard.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+American+Ultra+Jazz+Bass"},
        {"name": "Thunderbird", "brand": "Gibson", "price": 2099.99, "type": "bass",
         "description": "Legendary bass with through-body neck and T-Bird Plus pickups.",
         "image": "https://placeholder.svg?height=300&width=300&query=Gibson+Thunderbird+Bass"},
        {"name": "SR505E", "brand": "Ibanez", "price": 699.99, "type": "bass",
         "description": "5-string bass with Bartolini BH2 pickups and jatoba fretboard.",
         "image": "https://placeholder.svg?height=300&width=300&query=Ibanez+SR505+Bass"},
        {"name": "TRBX304", "brand": "Yamaha", "price": 349.99, "type": "bass",
         "description": "Solid bass guitar with Performance EQ active circuitry.",
         "image": "https://placeholder.svg?height=300&width=300&query=Yamaha+TRBX304+Bass"},
        
        # Acoustic Guitars
        {"name": "D-28", "brand": "Martin", "price": 3299.99, "type": "acoustic",
         "description": "The standard for acoustic guitars. Sitka spruce top, East Indian rosewood.",
         "image": "https://placeholder.svg?height=300&width=300&query=Martin+D-28+acoustic+guitar"},
        {"name": "HD-28", "brand": "Martin", "price": 3599.99, "type": "acoustic",
         "description": "Herringbone dreadnought with scalloped X bracing for rich tone.",
         "image": "https://placeholder.svg?height=300&width=300&query=Martin+HD-28+acoustic"},
        {"name": "000-15M", "brand": "Martin", "price": 1499.99, "type": "acoustic",
         "description": "All-mahogany 000 body for warm, balanced tone.",
         "image": "https://placeholder.svg?height=300&width=300&query=Martin+000-15M"},
        {"name": "814ce", "brand": "Taylor", "price": 3999.99, "type": "acoustic",
         "description": "Grand Auditorium with Sitka spruce and Indian rosewood. ES2 electronics.",
         "image": "https://placeholder.svg?height=300&width=300&query=Taylor+814ce+acoustic+guitar"},
        {"name": "214ce", "brand": "Taylor", "price": 1099.99, "type": "acoustic",
         "description": "Affordable Grand Auditorium with layered rosewood and solid spruce top.",
         "image": "https://placeholder.svg?height=300&width=300&query=Taylor+214ce+acoustic"},
        {"name": "Hummingbird Original", "brand": "Gibson", "price": 4199.99, "type": "acoustic",
         "description": "Iconic acoustic with cherry sunburst and traditional square-shoulder design.",
         "image": "https://placeholder.svg?height=300&width=300&query=Gibson+Hummingbird+acoustic"},
        {"name": "J-45 Standard", "brand": "Gibson", "price": 2699.99, "type": "acoustic",
         "description": "The workhorse of Gibson acoustics. Round-shoulder dreadnought.",
         "image": "https://placeholder.svg?height=300&width=300&query=Gibson+J-45+acoustic"},
        {"name": "CD-60S", "brand": "Fender", "price": 229.99, "type": "acoustic",
         "description": "Great beginner dreadnought with solid spruce top and mahogany back/sides.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+CD-60S+acoustic"},
        {"name": "FG800", "brand": "Yamaha", "price": 219.99, "type": "acoustic",
         "description": "Best-selling acoustic with solid spruce top and nato back/sides.",
         "image": "https://placeholder.svg?height=300&width=300&query=Yamaha+FG800+acoustic"},
        
        # Classical Guitars
        {"name": "C40", "brand": "Yamaha", "price": 159.99, "type": "classical",
         "description": "Perfect entry-level classical guitar. Spruce top, meranti back/sides.",
         "image": "https://placeholder.svg?height=300&width=300&query=Yamaha+C40+classical+guitar"},
        {"name": "CG142S", "brand": "Yamaha", "price": 299.99, "type": "classical",
         "description": "Solid spruce top classical with nato back/sides and rosewood fingerboard.",
         "image": "https://placeholder.svg?height=300&width=300&query=Yamaha+CG142S+classical"},
        {"name": "C5", "brand": "Cordoba", "price": 399.99, "type": "classical",
         "description": "Handcrafted classical with Canadian cedar top and mahogany back/sides.",
         "image": "https://placeholder.svg?height=300&width=300&query=Cordoba+C5+classical+guitar"},
        {"name": "C7", "brand": "Cordoba", "price": 549.99, "type": "classical",
         "description": "Solid Canadian cedar top with Indian rosewood back/sides.",
         "image": "https://placeholder.svg?height=300&width=300&query=Cordoba+C7+classical"},
        {"name": "C10", "brand": "Cordoba", "price": 899.99, "type": "classical",
         "description": "All-solid construction with European spruce and Indian rosewood.",
         "image": "https://placeholder.svg?height=300&width=300&query=Cordoba+C10+classical"},
        {"name": "FC-100", "brand": "Fender", "price": 149.99, "type": "classical",
         "description": "Affordable classical with laminated spruce top and agathis back/sides.",
         "image": "https://placeholder.svg?height=300&width=300&query=Fender+FC-100+classical"},
    ]
    
    def populate_database(self, db: DatabaseManager) -> dict:
        """Scrape guitars and populate the database"""
        existing_count = db.get_guitar_count()
        if existing_count > 0:
            return {"status": "skipped", "message": f"Database already has {existing_count} guitars", "added": 0}
        
        added_count = 0
        for item in self.GUITAR_CATALOG:
            if not db.guitar_exists(item['name'], item['brand']):
                guitar = Guitar(
                    name=item['name'],
                    brand=item['brand'],
                    guitar_type=GuitarType(item['type']),
                    price=item['price'],
                    stock=random.randint(5, 25),
                    description=item['description'],
                    image_url=item['image']
                )
                db.create_guitar(guitar)
                added_count += 1
        
        return {"status": "success", "message": f"Scraped and added {added_count} guitars to database", "added": added_count}


# ==================== DATABASE & SERVICES ====================

db = DatabaseManager("guitar_shop.db")
scraper = GuitarScraper()


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler - runs on startup"""
    print("Starting StringMaster Guitar Shop API...")
    
    # Scrape and populate database on startup
    result = scraper.populate_database(db)
    print(f"Database initialization: {result['message']}")
    
    # Create admin user if not exists
    if not db.get_user_by_username("admin"):
        admin = User(
            username="admin",
            email="admin@stringmaster.com",
            password_hash=AuthManager.hash_password("Admin123"),
            role=UserRole.ADMIN
        )
        db.create_user(admin)
        print("Created admin user (username: admin, password: Admin123)")
    
    yield
    
    print("Shutting down StringMaster Guitar Shop API...")


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="StringMaster Guitar Shop API",
    description="""
    REST API for StringMaster Guitar Shop
    
    ## Features
    - User Authentication & Authorization
    - Guitar Management (Electric, Acoustic, Bass, Classical)
    - Shopping Cart & Orders
    - Category Management
    
    ## Authentication
    - POST /api/auth/register - Register new account
    - POST /api/auth/login - Login and get token
    
    ## Guitars
    - GET /api/guitars - Browse all guitars
    - POST /api/guitars/cart/add - Add to cart (requires auth)
    - POST /api/guitars/purchase - Complete purchase (requires auth)
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(guitar_router)
app.include_router(category_router)


# ==================== HEALTH & INFO ROUTES ====================

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "name": "StringMaster Guitar Shop API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health")
def health_check():
    """API health check endpoint"""
    guitar_count = db.get_guitar_count()
    categories = db.get_all_categories()
    return {
        "status": "healthy",
        "database": "connected",
        "guitars_in_inventory": guitar_count,
        "categories": len(categories)
    }


@app.get("/api/stats")
def get_shop_stats():
    """Get shop statistics"""
    stats = db.get_inventory_stats()
    return {
        "total_products": stats.get('total_products', 0),
        "total_units": stats.get('total_units', 0),
        "total_value": round(stats.get('total_value', 0) or 0, 2),
        "by_type": stats.get('by_type', {}),
        "by_brand": stats.get('by_brand', {})
    }


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
