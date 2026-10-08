from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated


Username = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)
]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]

class UserCreate(BaseModel):
    username: Username
    email: EmailStr
    password: Password
    

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    username: Username | None = None
    email: EmailStr
    password: Password


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str