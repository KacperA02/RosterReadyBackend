from pydantic import BaseModel

class RoleBase(BaseModel):
    name: str

class RoleResponse(RoleBase):
    id: int
    name: str

    class Config:
        from_attributes = True
