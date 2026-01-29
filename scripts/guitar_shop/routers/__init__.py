from routers.auth import router as auth_router
from routers.user import router as user_router
from routers.guitar import router as guitar_router
from routers.category import router as category_router

__all__ = ['auth_router', 'user_router', 'guitar_router', 'category_router']
