from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from models import Category, CategoryCreate, CategoryResponse, GuitarType
from database import DatabaseManager
from routers.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/api/categories", tags=["Categories"])

db = DatabaseManager("guitar_shop.db")


@router.get("/", response_model=List[dict])
def list_categories():
    categories = db.get_all_categories()
    return [cat.to_dict() for cat in categories]


@router.get("/{category_id}")
def get_category(category_id: int):
    category = db.get_category(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category.to_dict()


@router.get("/{category_id}/guitars")
def get_guitars_by_category(category_id: int):
    category = db.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    guitars = db.get_guitars_by_category(category_id)
    
    return {
        "category": category.to_dict(),
        "guitars": [g.to_dict() for g in guitars],
        "count": len(guitars)
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    admin: dict = Depends(get_admin_user)
):
    existing = db.get_category_by_name(category_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    category = Category(
        name=category_data.name,
        description=category_data.description
    )
    
    category_id = db.create_category(category)
    category.id = category_id
    
    return {"message": "Category created successfully", "category": category.to_dict()}


@router.put("/{category_id}")
def update_category(
    category_id: int,
    name: str = None,
    description: str = None,
    admin: dict = Depends(get_admin_user)
):
    existing = db.get_category(category_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updates = {}
    if name:
        name_check = db.get_category_by_name(name)
        if name_check and name_check.id != category_id:
            raise HTTPException(status_code=400, detail="Category name already in use")
        updates['name'] = name
    
    if description is not None:
        updates['description'] = description
    
    if updates:
        success = db.update_category(category_id, **updates)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update category")
    
    updated = db.get_category(category_id)
    return {"message": "Category updated successfully", "category": updated.to_dict()}


@router.delete("/{category_id}")
def delete_category(category_id: int, admin: dict = Depends(get_admin_user)):
    category = db.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    guitars = db.get_guitars_by_category(category_id)
    if guitars:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {len(guitars)} guitars. Remove or reassign guitars first."
        )
    
    success = db.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete category")
    
    return {"message": "Category deleted successfully"}


@router.get("/type/{guitar_type}")
def get_category_by_type(guitar_type: GuitarType):
    type_to_name = {
        GuitarType.ELECTRIC: "Electric",
        GuitarType.ACOUSTIC: "Acoustic",
        GuitarType.BASS: "Bass",
        GuitarType.CLASSICAL: "Classical"
    }
    
    category_name = type_to_name.get(guitar_type)
    if not category_name:
        raise HTTPException(status_code=400, detail="Invalid guitar type")
    
    category = db.get_category_by_name(category_name)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    guitars = db.get_guitars_by_category(category.id)
    
    return {
        "category": category.to_dict(),
        "guitar_type": guitar_type.value,
        "guitars": [g.to_dict() for g in guitars],
        "count": len(guitars)
    }


@router.get("/stats/summary")
def get_category_stats(admin: dict = Depends(get_admin_user)):
    categories = db.get_all_categories()
    stats = []
    
    for category in categories:
        guitars = db.get_guitars_by_category(category.id)
        total_stock = sum(g.stock for g in guitars)
        total_value = sum(g.price * g.stock for g in guitars)
        
        stats.append({
            "category": category.to_dict(),
            "guitar_count": len(guitars),
            "total_stock": total_stock,
            "total_value": round(total_value, 2)
        })
    
    return {"category_stats": stats}
