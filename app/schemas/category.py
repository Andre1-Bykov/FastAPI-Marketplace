from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated


CategoryName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class CategoryCreate(BaseModel):
    name: CategoryName
    description: str | None = Field(default=None, max_length=2000)


class CategoryRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)

class CategoryUpdate(BaseModel):
    name: CategoryName
    description: str | None = Field(default=None, max_length=2000)

class CategoryShort(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)