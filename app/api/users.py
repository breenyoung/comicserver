from fastapi import APIRouter, Depends, HTTPException
from typing import List, Annotated, Optional
from pydantic import BaseModel
from datetime import datetime

from app.api.deps import SessionDep, AdminUser
from app.models.user import User
from app.models.library import Library
from app.core.security import get_password_hash

router = APIRouter()


# Schemas
class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    is_superuser: bool = False
    library_ids: List[int] = []

class UserUpdateRequest(BaseModel):
    password: Optional[str] = None
    is_superuser: Optional[bool] = None
    is_active: Optional[bool] = None
    library_ids: Optional[List[int]] = None


class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    is_superuser: bool
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    # We don't necessarily need to return the full library objects in the list view,
    # but we might want the IDs for the edit form.
    accessible_library_ids: List[int] = []

# 1. List Users
@router.get("/", response_model=List[UserListResponse])
async def list_users(
        db: SessionDep,
        admin: AdminUser
):
    users = db.query(User).all()
    # Helper to format response with IDs
    results = []
    for u in users:
        results.append({
            **u.__dict__,
            "accessible_library_ids": [lib.id for lib in u.accessible_libraries]
        })

    return users


# 2. Create User (Admin Only)
@router.post("/", response_model=UserListResponse)
async def create_user(
        user_in: UserCreateRequest,
        db: SessionDep,
        admin: AdminUser
):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Fetch Libraries
    libraries = []
    if user_in.library_ids:
        libraries = db.query(Library).filter(Library.id.in_(user_in.library_ids)).all()

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_superuser=user_in.is_superuser,
        is_active=True,
        accessible_libraries = libraries
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        **user.__dict__,
        "accessible_library_ids": [lib.id for lib in user.accessible_libraries]
    }


# 3. Update User (e.g. Change Password)
@router.patch("/{user_id}")
async def update_user(
        user_id: int,
        updates: UserUpdateRequest,
        db: SessionDep,
        admin: AdminUser
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if updates.password:
        user.hashed_password = get_password_hash(updates.password)
    if updates.is_superuser is not None:
        user.is_superuser = updates.is_superuser
    if updates.is_active is not None:
        user.is_active = updates.is_active

    # Update Libraries
    if updates.library_ids is not None:
        libraries = db.query(Library).filter(Library.id.in_(updates.library_ids)).all()
        user.accessible_libraries = libraries

    db.commit()
    return {"message": "User updated"}


# 4. Delete User
@router.delete("/{user_id}")
async def delete_user(
        user_id: int,
        db: SessionDep,
        admin: AdminUser
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}