
from typing import Optional
from fastapi import Header
from replit import db

# User class definition
class User:
    def __init__(self, user_id: str, credits: int = 1):
        self.user_id = user_id
        self.credits = credits
    
    def to_dict(self):
        return {"user_id": self.user_id, "credits": self.credits}
    
    @classmethod
    def from_dict(cls, data):
        return cls(user_id=data["user_id"], credits=data["credits"])

# Store and retrieve users using Replit DB
def save_user(user: User):
    db[f"user:{user.user_id}"] = user.to_dict()

def get_user(user_id: str) -> Optional[User]:
    user_data = db.get(f"user:{user_id}")
    if user_data:
        return User.from_dict(user_data)
    return None

# Authentication dependency
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    if not authorization:
        return None

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    return get_user(token)
