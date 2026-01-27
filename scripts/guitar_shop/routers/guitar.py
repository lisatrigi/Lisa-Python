"""
Guitar Router - StringMaster Guitar Shop
Handles guitar CRUD operations and purchases via FastAPI
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Query

from models import (
    Guitar, GuitarType, GuitarCreate, GuitarUpdate,
    ShoppingCart, CartItemCreate, UserRole
)
from database import DatabaseManager
from routers.auth import get_current_user, get_admin_user, get_customer_user

router = APIRouter(prefix="/api/guitars", tags=["Guitars"])

# Database instance
db = DatabaseManager("guitar_shop.db")

# In-memory cart storage (per user session)
user_carts: dict[int, ShoppingCart] = {}


# ==================== GUITAR ROUTES ====================

@router.get("/", response_model=List[dict])
def list_guitars(
    guitar_type: Optional[GuitarType] = Query(None, description="Filter by guitar type"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: bool = Query(False, description="Only show in-stock items"),
    category_id: Optional[int] = Query(None, description="Filter by category ID")
):
    """
    List all guitars with optional filters
    - No authentication required for browsing
    """
    guitars = db.get_all_guitars(
        guitar_type=guitar_type,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock,
        category_id=category_id
    )
    
    # Include discount information in response
    result = []
    for g in guitars:
        guitar_dict = g.to_dict()
        discount = getattr(g, 'discount_percent', 0)
        guitar_dict['discount_percent'] = discount
        if discount > 0:
            guitar_dict['original_price'] = g.price
            guitar_dict['discounted_price'] = round(g.price * (1 - discount / 100), 2)
        result.append(guitar_dict)
    
    return result


@router.get("/{guitar_id}")
def get_guitar(guitar_id: int):
    """Get single guitar by ID"""
    guitar = db.get_guitar(guitar_id)
    
    if not guitar:
        raise HTTPException(status_code=404, detail="Guitar not found")
    
    guitar_dict = guitar.to_dict()
    discount = getattr(guitar, 'discount_percent', 0)
    guitar_dict['discount_percent'] = discount
    if discount > 0:
        guitar_dict['original_price'] = guitar.price
        guitar_dict['discounted_price'] = round(guitar.price * (1 - discount / 100), 2)
    
    return guitar_dict


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_guitar(
    guitar_data: GuitarCreate,
    admin: dict = Depends(get_admin_user)
):
    """Create a new guitar (Admin only)"""
    guitar = Guitar(
        name=guitar_data.name,
        brand=guitar_data.brand,
        guitar_type=guitar_data.guitar_type,
        price=guitar_data.price,
        stock=guitar_data.stock,
        description=guitar_data.description,
        image_url=guitar_data.image_url
    )
    
    guitar_id = db.create_guitar(guitar)
    guitar.id = guitar_id
    
    return {"message": "Guitar created successfully", "guitar": guitar.to_dict()}


@router.put("/{guitar_id}")
def update_guitar(
    guitar_id: int,
    guitar_data: GuitarUpdate,
    admin: dict = Depends(get_admin_user)
):
    """Update guitar details (Admin only)"""
    existing = db.get_guitar(guitar_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Guitar not found")
    
    updates = guitar_data.model_dump(exclude_unset=True)
    
    if updates:
        success = db.update_guitar(guitar_id, **updates)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update guitar")
    
    updated = db.get_guitar(guitar_id)
    return {"message": "Guitar updated successfully", "guitar": updated.to_dict()}


@router.delete("/{guitar_id}")
def delete_guitar(guitar_id: int, admin: dict = Depends(get_admin_user)):
    """Delete a guitar (Admin only)"""
    if not db.get_guitar(guitar_id):
        raise HTTPException(status_code=404, detail="Guitar not found")
    
    success = db.delete_guitar(guitar_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete guitar")
    
    return {"message": "Guitar deleted successfully"}


# ==================== CART ROUTES (Customers Only) ====================

@router.get("/cart/items")
def get_cart(current_user: dict = Depends(get_customer_user)):
    """Get current user's shopping cart (Customers only - Admin cannot use cart)"""
    user_id = current_user['user_id']
    
    if user_id not in user_carts:
        user_carts[user_id] = ShoppingCart(user_id)
    
    cart = user_carts[user_id]
    items = []
    
    for item in cart.get_items():
        guitar_dict = item.guitar.to_dict()
        discount = getattr(item.guitar, 'discount_percent', 0)
        effective_price = item.guitar.price * (1 - discount / 100) if discount > 0 else item.guitar.price
        
        items.append({
            "guitar": guitar_dict,
            "quantity": item.quantity,
            "subtotal": round(effective_price * item.quantity, 2),
            "discount_percent": discount
        })
    
    # Calculate total with discounts
    total = sum(item['subtotal'] for item in items)
    
    return {
        "items": items,
        "total": round(total, 2),
        "item_count": cart.item_count
    }


@router.post("/cart/add")
def add_to_cart(
    item: CartItemCreate,
    current_user: dict = Depends(get_customer_user)
):
    """Add item to cart (Customers only - Admin cannot purchase)"""
    user_id = current_user['user_id']
    
    if user_id not in user_carts:
        user_carts[user_id] = ShoppingCart(user_id)
    
    cart = user_carts[user_id]
    
    guitar = db.get_guitar(item.guitar_id)
    if not guitar:
        raise HTTPException(status_code=404, detail="Guitar not found")
    
    try:
        cart.add_item(guitar, item.quantity)
        return {"message": f"Added {guitar.brand} {guitar.name} to cart"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/cart/{guitar_id}")
def update_cart_item(
    guitar_id: int,
    quantity: int = Query(..., ge=0),
    current_user: dict = Depends(get_customer_user)
):
    """Update cart item quantity (Customers only)"""
    user_id = current_user['user_id']
    
    if user_id not in user_carts:
        raise HTTPException(status_code=404, detail="Cart is empty")
    
    cart = user_carts[user_id]
    
    try:
        if quantity == 0:
            cart.remove_item(guitar_id)
            return {"message": "Item removed from cart"}
        else:
            cart.update_quantity(guitar_id, quantity)
            return {"message": "Cart updated"}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cart/{guitar_id}")
def remove_from_cart(guitar_id: int, current_user: dict = Depends(get_customer_user)):
    """Remove item from cart (Customers only)"""
    user_id = current_user['user_id']
    
    if user_id not in user_carts:
        raise HTTPException(status_code=404, detail="Cart is empty")
    
    user_carts[user_id].remove_item(guitar_id)
    return {"message": "Item removed from cart"}


@router.delete("/cart/clear")
def clear_cart(current_user: dict = Depends(get_customer_user)):
    """Clear entire cart (Customers only)"""
    user_id = current_user['user_id']
    
    if user_id in user_carts:
        user_carts[user_id].clear()
    
    return {"message": "Cart cleared"}


# ==================== ORDER/PURCHASE ROUTES (Customers Only) ====================

@router.post("/purchase", status_code=status.HTTP_201_CREATED)
def purchase_guitars(current_user: dict = Depends(get_customer_user)):
    """
    Checkout cart and create order (Purchase)
    - Customers only - Admin cannot purchase guitars
    - Creates order from current cart
    - Updates stock levels
    - Creates notification for admin
    """
    user_id = current_user['user_id']
    username = current_user['username']
    
    if user_id not in user_carts or user_carts[user_id].is_empty():
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    cart = user_carts[user_id]
    
    # Prepare order items with discount-adjusted prices
    items = []
    order_total = 0
    
    for cart_item in cart.get_items():
        guitar = db.get_guitar(cart_item.guitar.id)
        if not guitar or guitar.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {cart_item.guitar.name}"
            )
        
        # Apply discount if any
        discount = getattr(guitar, 'discount_percent', 0)
        effective_price = guitar.price * (1 - discount / 100) if discount > 0 else guitar.price
        effective_price = round(effective_price, 2)
        
        items.append((cart_item.guitar.id, cart_item.quantity, effective_price))
        order_total += effective_price * cart_item.quantity
    
    order_total = round(order_total, 2)
    
    # Create order
    order_id = db.create_order(user_id, items, order_total)
    
    # Create notification for admin
    db.create_purchase_notification(order_id, user_id, username, order_total)
    
    # Update stock for each item
    for guitar_id, quantity, _ in items:
        db.update_stock(guitar_id, -quantity)
    
    # Clear cart
    cart.clear()
    
    return {
        "message": "Purchase successful! Order placed.",
        "order_id": order_id,
        "total": order_total
    }


@router.get("/orders/history")
def get_order_history(current_user: dict = Depends(get_current_user)):
    """Get current user's order history"""
    orders = db.get_user_orders(current_user['user_id'])
    return {"orders": orders}
