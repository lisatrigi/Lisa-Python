import sys
import os
import random
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, status, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from models import User, UserRole, GuitarType, Guitar, GuitarCreate
from routers import auth_router, user_router, guitar_router, category_router
from routers.auth import AuthManager, get_current_user, get_admin_user


class DiscountRequest(BaseModel):
    discount_percent: float = Field(..., ge=0, le=100)
    target_type: str = Field(..., description="Type of target: 'guitar', 'brand', or 'type'")
    target_value: str = Field(..., description="Guitar ID, brand name, or guitar type")


class NotificationResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    username: str
    total: float
    is_read: bool
    created_at: str
    order_status: str


class GuitarScraper: #web scraping
    GUITAR_CATALOG = [
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


db = DatabaseManager("guitar_shop.db")
scraper = GuitarScraper()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting StringMaster Guitar Shop API...")
    result = scraper.populate_database(db)
    print(f"Database initialization: {result['message']}")
    
    if not db.get_user_by_username("admin"):
        admin = User(
            username="admin",
            email="admin@stringmaster.com",
            password_hash=AuthManager.hash_password("admin123"),
            role=UserRole.ADMIN
        )
        db.create_user(admin)
        print("Created admin user (username: admin, password: admin123)")
    
    yield
    print("Shutting down StringMaster Guitar Shop API...")


app = FastAPI(
    title="StringMaster Guitar Shop API",
    description="REST API for StringMaster Guitar Shop - Guitar Management, Shopping Cart, Orders, and Admin Dashboard",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(guitar_router)
app.include_router(category_router)


@app.get("/")
def root():
    return {
        "name": "StringMaster Guitar Shop API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health")
def health_check():
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
    stats = db.get_inventory_stats()
    return {
        "total_products": stats.get('total_products', 0),
        "total_units": stats.get('total_units', 0),
        "total_value": round(stats.get('total_value', 0) or 0, 2),
        "by_type": stats.get('by_type', {}),
        "by_brand": stats.get('by_brand', {}),
        "models_by_brand": stats.get('models_by_brand', {}),
        "total_orders": stats.get('total_orders', 0),
        "total_revenue": round(stats.get('total_revenue', 0) or 0, 2),
        "discounted_count": stats.get('discounted_count', 0)
    }


@app.get("/api/admin/online-users")
def get_online_users(admin: dict = Depends(get_admin_user)):
    users = db.get_online_users()
    return {
        "online_count": len(users),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "last_login": getattr(u, 'last_login', None)
            }
            for u in users
        ]
    }


@app.get("/api/admin/notifications")
def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(get_admin_user)
):
    if unread_only:
        notifications = db.get_unread_notifications()
    else:
        notifications = db.get_all_notifications(limit)
    
    return {
        "count": len(notifications),
        "notifications": notifications
    }


@app.post("/api/admin/notifications/mark-read")
def mark_notifications_read(
    notification_id: Optional[int] = Body(None),
    mark_all: bool = Body(False),
    admin: dict = Depends(get_admin_user)
):
    if mark_all:
        count = db.mark_all_notifications_read()
        return {"message": f"Marked {count} notifications as read"}
    elif notification_id:
        success = db.mark_notification_read(notification_id)
        if success:
            return {"message": "Notification marked as read"}
        raise HTTPException(status_code=404, detail="Notification not found")
    else:
        raise HTTPException(status_code=400, detail="Specify notification_id or mark_all=true")


@app.get("/api/admin/orders")
def get_all_orders(
    limit: int = Query(100, ge=1, le=500),
    admin: dict = Depends(get_admin_user)
):
    orders = db.get_all_orders(limit)
    return {
        "count": len(orders),
        "orders": orders
    }


@app.get("/api/admin/brand-statistics")
def get_brand_statistics(admin: dict = Depends(get_admin_user)):
    stats = db.get_brand_statistics()
    return {
        "brands": stats,
        "total_brands": len(stats)
    }


@app.get("/api/admin/type-statistics")
def get_type_statistics(admin: dict = Depends(get_admin_user)):
    stats = db.get_type_statistics()
    return {
        "types": stats,
        "total_types": len(stats)
    }


@app.post("/api/admin/discounts")
def apply_discount(
    request: DiscountRequest,
    admin: dict = Depends(get_admin_user)
):
    target_type = request.target_type.lower()
    
    try:
        if target_type == "guitar":
            guitar_id = int(request.target_value)
            success = db.apply_discount_to_guitar(guitar_id, request.discount_percent)
            if success:
                return {"message": f"Applied {request.discount_percent}% discount to guitar ID {guitar_id}"}
            raise HTTPException(status_code=404, detail="Guitar not found")
        
        elif target_type == "brand":
            count = db.apply_discount_to_brand(request.target_value, request.discount_percent)
            return {"message": f"Applied {request.discount_percent}% discount to {count} {request.target_value} guitars"}
        
        elif target_type == "type":
            count = db.apply_discount_to_type(request.target_value, request.discount_percent)
            return {"message": f"Applied {request.discount_percent}% discount to {count} {request.target_value} guitars"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid target_type. Use 'guitar', 'brand', or 'type'")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/admin/discounts/clear")
def clear_discounts(admin: dict = Depends(get_admin_user)):
    count = db.clear_all_discounts()
    return {"message": f"Cleared discounts from {count} guitars"}


@app.get("/api/admin/discounted-guitars")
def get_discounted_guitars(admin: dict = Depends(get_admin_user)):
    guitars = db.get_discounted_guitars()
    return {
        "count": len(guitars),
        "guitars": [
            {
                **g.to_dict(),
                "discount_percent": getattr(g, 'discount_percent', 0),
                "discounted_price": round(g.price * (1 - getattr(g, 'discount_percent', 0) / 100), 2)
            }
            for g in guitars
        ]
    }


@app.post("/api/admin/guitars", status_code=status.HTTP_201_CREATED)
def admin_create_guitar(
    guitar_data: GuitarCreate,
    admin: dict = Depends(get_admin_user)
):
    guitar = Guitar(
        name=guitar_data.name,
        brand=guitar_data.brand,
        guitar_type=guitar_data.guitar_type,
        price=guitar_data.price,
        stock=guitar_data.stock,
        description=guitar_data.description,
        image_url=guitar_data.image_url
    )
    
    if db.guitar_exists(guitar.name, guitar.brand):
        raise HTTPException(status_code=400, detail="Guitar with this name and brand already exists")
    
    guitar_id = db.create_guitar(guitar)
    guitar.id = guitar_id
    
    return {
        "message": f"Successfully added {guitar.brand} {guitar.name} to inventory",
        "guitar": guitar.to_dict()
    }


@app.put("/api/admin/guitars/{guitar_id}/stock")
def update_guitar_stock(
    guitar_id: int,
    stock: int = Body(..., ge=0),
    admin: dict = Depends(get_admin_user)
):
    guitar = db.get_guitar(guitar_id)
    if not guitar:
        raise HTTPException(status_code=404, detail="Guitar not found")
    
    success = db.update_guitar(guitar_id, stock=stock)
    if success:
        return {"message": f"Stock updated to {stock} for {guitar.brand} {guitar.name}"}
    raise HTTPException(status_code=500, detail="Failed to update stock")


@app.delete("/api/admin/guitars/{guitar_id}")
def admin_delete_guitar(
    guitar_id: int,
    admin: dict = Depends(get_admin_user)
):
    guitar = db.get_guitar(guitar_id)
    if not guitar:
        raise HTTPException(status_code=404, detail="Guitar not found")
    
    success = db.delete_guitar(guitar_id)
    if success:
        return {"message": f"Successfully deleted {guitar.brand} {guitar.name}"}
    raise HTTPException(status_code=500, detail="Failed to delete guitar")


if __name__ == "__main__":
    import uvicorn
    print("Starting StringMaster Guitar Shop API v2.0")
    print("API Docs: http://localhost:8000/docs")
    print("Default Admin: username=admin, password=admin123")
    uvicorn.run(app, host="0.0.0.0", port=8000)
