from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None


class CategoryRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {
        "from_attributes": True
    }

class CategoryUpdate(BaseModel):
    name: str
    description: str | None = None

class CategoryShort(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }