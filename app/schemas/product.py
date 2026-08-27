from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int = 0
    category_id: int


class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category_id: int
    category_name: str 
    model_config = {
        "from_attributes": True
    }

class ProductUpdate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category_id: int