from pydantic import BaseModel
from typing import Optional

# serves as the base model and providing the default values
class UserConstraintBase(BaseModel):
    user_id: int
    shift_id: int
    team_id: int
    day_id: int
    is_available: bool = True
    is_preferred: bool = False
    # ensuring compatability with ORM (object-relational mapping model) models
    class Config:
        from_attributes = True

# pass all the fields from the basemodel to the create model without adding any additional fields
class UserConstraintCreate(UserConstraintBase):
    pass  

# used for updating existing data. Contains two optional values as they don't need to be passed
class UserConstraintUpdate(BaseModel):
    is_available: Optional[bool] = None
    is_preferred: Optional[bool] = None

    class Config:
        from_attributes = True