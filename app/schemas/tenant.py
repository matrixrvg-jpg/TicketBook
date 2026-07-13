from pydantic import BaseModel, EmailStr, ConfigDict

# INPUT: What the user sends us
class TenantCreate(BaseModel):
    name: str
    business_email: EmailStr  # Natively validates email string formats

# OUTPUT: The thin response for POST endpoints
class TenantIdResponse(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)

# OUTPUT: The full response for GET endpoints
class TenantResponse(BaseModel):
    id: int
    name: str
    business_email: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)