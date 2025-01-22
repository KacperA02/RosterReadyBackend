from pydantic import BaseModel

class DayCreate(BaseModel):
    name: str

class DayResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

