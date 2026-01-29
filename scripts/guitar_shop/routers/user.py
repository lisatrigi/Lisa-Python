from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from models import User, UserRole, UserResponse
from database import DatabaseManager
from routers.auth import get_current_user, get_admin_user, AuthManager

router = APIRouter(prefix="/api/users", tags=["Users"])

db = DatabaseManager("guitar_shop.db")


@router.get("/", response_model=List[dict])
def list_users(admin: dict = Depends(get_admin_user)):
    users = db.get_all_users()
    return [user.to_dict() for user in users]


@router.get("/{user_id}", response_model=dict)
def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != UserRole.ADMIN.value and current_user['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.to_dict()


@router.put("/{user_id}")
def update_user(
    user_id: int,
    email: str = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user['role'] != UserRole.ADMIN.value and current_user['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updates = {}
    if email:
        if not AuthManager.validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        existing = db.get_user_by_email(email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")
        updates['email'] = email
    
    if updates:
        success = db.update_user(user_id, **updates)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update user")
    
    updated_user = db.get_user_by_id(user_id)
    return {"message": "User updated successfully", "user": updated_user.to_dict()}


@router.delete("/{user_id}")
def delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if admin['user_id'] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    success = db.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    
    return {"message": "User deleted successfully"}


@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    role: UserRole,
    admin: dict = Depends(get_admin_user)
):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if admin['user_id'] == user_id and role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Cannot demote your own admin account")
    
    success = db.update_user(user_id, role=role.value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user role")
    
    return {"message": f"User role updated to {role.value}"}


@router.get("/{user_id}/orders")
def get_user_orders(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != UserRole.ADMIN.value and current_user['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders"
        )
    
    orders = db.get_user_orders(user_id)
    return {"orders": orders}
